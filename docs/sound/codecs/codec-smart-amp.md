# Smart speaker amplifiers

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A smart speaker amplifier is a boosted Class-D amplifier that adds an on-chip DSP, a current and voltage (I/V) sense path tapped at the speaker terminals, and per-speaker calibration, so the part can run an excursion and thermal protection model on the same silicon that drives the speaker. In ASoC the class shows up as three traits beyond a plain DAC codec. The [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) declares a capture direction alongside playback to carry the I/V feedback, the component probe downloads protection firmware onto the DSP and holds audio until it is present, and a calibration blob written at the factory is read from a UEFI variable and pushed into the DSP. The Cirrus Logic CS35L56 (driven through [`struct wm_adsp`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm_adsp.h#L27) and [`struct cs_dsp`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/firmware/cirrus/cs_dsp.h#L150)) and the Texas Instruments TAS2783 (a SoundWire [`SDCA_FUNCTION_TYPE_SMART_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L73) Function) are the two worked examples used throughout this page; MAX98373 and RT1308 are the same class.

```
    A smart amplifier: speaker drive plus an I/V-sense feedback loop
    ────────────────────────────────────────────────────────────────

       host playback stream  (SoundWire RX port / TDM rx slot)
              │
              ▼
       ┌──────┬─────────────────────────────────────────────────┐
       │   DAC ──▶ boost ──▶ Class-D drive ──▶ SPK              │
       │                                          │ I, V tap    │
       │   protection DSP ◀──── I/V-sense ADC ◀───┤             │
       │   excursion + thermal limit              │             │
       │   firmware + per-speaker calibration     │             │
       └──────────────────────────────────────────┼─────────────┘
                                                  │
                                                  ▼
       host I/V-sense capture stream  (SoundWire TX port / TDM tx slot)

    the forward path drives the speaker through the boosted DAC; the
    reverse path feeds the measured current and voltage to the
    protection DSP and returns it to the host on the capture stream
```

## SUMMARY

The defining trait of the class is the second DAI direction. A plain DAC codec declares a single playback capability because it only receives audio. A smart amplifier declares both, and the capture capability carries the current and voltage measured at the speaker terminals into the protection model. The CS35L56 splits the two directions across two SoundWire DAIs in [`cs35l56_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L668), [`cs35l56-sdw1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L691) for the speaker stream and [`cs35l56-sdw1c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L704) for the I/V feedback, while the TAS2783 folds both into one [`tas_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L985) named `tas2783-codec`. Either way the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op turns the PCM stream direction into a SoundWire data port and joins the peripheral to a manager-allocated stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117).

The second trait is the gated DSP firmware. The amplifier's protection runs on an on-chip DSP that the host loads at bring-up, and audio is held off until the load completes. The CS35L56 queues [`cs35l56_dsp_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L858) off the component probe, downloads the wmfw and bin images through [`wm_adsp_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm_adsp.c#L987), and stalls the [`cs35l56_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L1330) transition until patching finishes; the TAS2783 requests its RCA image with [`request_firmware_nowait()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/firmware_loader/main.c#L1226) and writes it in [`tas2783_fw_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L728), and [`tas_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L893) refuses to start a stream until [`fw_dl_success`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L102) is set.

The third trait is per-speaker calibration. A factory process measures each speaker and stores coefficients in a UEFI variable, which the driver reads at probe, validates, matches to the right amplifier, and writes into the DSP. The CS35L56 reads its entry with [`cs_amp_get_efi_calibration_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L608) keyed by the silicon UID and applies it with [`cs_amp_write_cal_coeffs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L210); the TAS2783 reads, validates, and applies its blob in [`tas2783_update_calibdata()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L650), matching each amplifier by [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665). When several amplifiers share one bus, the machine layer gives each a distinct [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L77) so their controls stay separate.

## SPECIFICATIONS

A smart amplifier is a hardware class, so it has no single Linux specification; the kernel-facing contracts come from the bus and the device-class layer the part attaches through. On the Intel SoundWire reference platforms both example parts enumerate as MIPI SoundWire peripherals, and the TAS2783 is described entirely through the MIPI SoundWire Device Class for Audio (SDCA), whose [`SDCA_FUNCTION_TYPE_SMART_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L73) Function Type its kerneldoc records as "Amplifier with protection features" from SDCA specification v1.0a Section 5.1.2. The CS35L56 follows the same SDCA register layout but drives its DSP through the Cirrus firmware framework. The calibration store is a UEFI variable read through [`efi.get_variable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/efi.h#L327). The MIPI specifications are membership-gated, so the layouts here are described from the kernel source.

- MIPI SoundWire Device Class for Audio (SDCA), section 5.1.2: Function Types (Smart Amplifier, 0x01)
- MIPI SoundWire Specification: peripheral attach, data ports, and stream prepare
- UEFI Specification: GetVariable for the per-amplifier calibration variable store

## LINUX KERNEL

### The two-direction DAI (soc-dai.h, cs35l56.c, tas2783-sdw.c)

- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the DAI descriptor; a smart amplifier fills both its [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capabilities
- [`'cs35l56_dai':'sound/soc/codecs/cs35l56.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L668): the CS35L56 DAI array, with `cs35l56-sdw1` playback and `cs35l56-sdw1c` capture as two separate SoundWire DAIs
- [`'tas_dai_driver':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L985): the TAS2783 single DAI carrying both a `Playback` and a `Capture` capability
- [`'\<cs35l56_sdw_dai_hw_params\>':'sound/soc/codecs/cs35l56.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L587): selects [`CS35L56_SDW1_PLAYBACK_PORT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs35l56.h#L311) (1) or [`CS35L56_SDW1_CAPTURE_PORT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs35l56.h#L312) (3) by PCM direction
- [`'\<tas_sdw_hw_params\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L893): gates on [`fw_dl_success`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L102), requests PDE23 power, and selects port 1 (playback) or 2 (capture)

### DSP firmware download (cs35l56.c, wm_adsp.c, tas2783-sdw.c)

- [`'\<cs35l56_dsp_work\>':'sound/soc/codecs/cs35l56.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L858): the work item queued off probe that patches or reinitialises the protection firmware
- [`'\<cs35l56_patch\>':'sound/soc/codecs/cs35l56.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L782): downloads firmware through [`cs35l56_dsp_download_and_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L741), soft-resets, then writes calibration
- [`'\<wm_adsp_power_up\>':'sound/soc/codecs/wm_adsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm_adsp.c#L987): the Cirrus framework call that loads the wmfw image and bin coefficients onto the DSP
- [`'\<cs35l56_read_prot_status\>':'sound/soc/codecs/cs35l56-shared.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56-shared.c#L1337): reads the firmware-missing flag that decides between a full patch and a tunings-only reinit
- [`'\<tas_io_init\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L1136): software-resets the part and requests the RCA firmware with [`request_firmware_nowait()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/firmware_loader/main.c#L1226)
- [`'\<tas2783_fw_ready\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L728): the firmware completion that writes each image block, applies calibration, and sets [`fw_dl_success`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L102)

### Per-speaker calibration (cs-amp-lib.c, tas2783-sdw.c)

- [`'\<cs_amp_get_efi_calibration_data\>':'sound/soc/codecs/cs-amp-lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L608): reads the calibration UEFI variable and copies the matching entry into a [`struct cirrus_amp_cal_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs-amp-lib.h#L15), keyed by silicon UID with a fallback to the array index
- [`'\<cs_amp_write_cal_coeffs\>':'sound/soc/codecs/cs-amp-lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L210): writes a [`struct cirrus_amp_cal_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs-amp-lib.h#L15) to the named firmware controls
- [`'\<struct cirrus_amp_cal_data\>':'include/sound/cs-amp-lib.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs-amp-lib.h#L15): one calibration entry (calTarget, calTime, calAmbient, calStatus, calR)
- [`'\<tas2783_update_calibdata\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L650): reads the `SmartAmpCalibrationData` UEFI variable through [`efi.get_variable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/efi.h#L327), validates it, and applies it
- [`'\<tas2783_validate_calibdata\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L563): checks the calibration magic number 2783, speaker count, size, and CRC32
- [`'\<tas2783_set_calib_params_to_device\>':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L615): matches the per-amp [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and writes the calibration registers in [`tas2783_cali_reg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L49)

### SDCA power domain and slot assignment (sdca_function.h, soc-dai.h, soc_sdw_utils.c)

- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): packs a Function, Entity, Control selector, and Control number into one 32-bit SDCA Control address
- [`'\<TAS2783_SDCA_ENT_PDE23\>':'sound/soc/codecs/tas2783.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783.h#L63): the speaker amplifier power-domain entity, driven on at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and off at [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)
- [`'\<struct sdca_entity_pde\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020): the parsed Power-Domain Entity, with the [`managed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) entity array and the [`max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) transition timings
- [`'\<cs35l56_sdw_dai_set_tdm_slot\>':'sound/soc/codecs/cs35l56.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L575): records the channel masks that pick the part's SoundWire channel slots
- [`'codec_info_list':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74): the machine-layer table whose amplifier entries set the per-part [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L77)
- [`'\<create_sdw_dailink\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876): copies each endpoint's prefix into a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) so two amps expose separately named controls

## KERNEL DOCUMENTATION

- [`Documentation/sound/codecs/cs35l56.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/codecs/cs35l56.rst): the CS35L56 firmware files, the per-speaker calibration flow, and the SoundWire versus HDA driver split
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the playback and IV-sense DAIs join through [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC component and DAI driver model both parts implement
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget and route model the amplifier graphs build

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [linux-firmware repository (amplifier DSP firmware files)](https://gitlab.com/kernel-firmware/linux-firmware)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

A smart amplifier exposes its protection state through DSP coefficient memory and, on an SDCA part, through SDCA Control addresses, with the specific addresses differing across the class, so the representative registers below come from the two example parts. The speaker power gate is a Power-Domain Entity Control. The TAS2783 packs the address for PDE23's requested-power-state Control with [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), writing the active state (0) at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and the off state (3) at [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269). The calibration coefficients are written into named DSP controls, on the Cirrus parts a [`struct cirrus_amp_cal_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs-amp-lib.h#L15) and on the TAS2783 the five [`tas2783_cali_reg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L49) addresses.

## DETAILS

### A smart amplifier pairs a speaker DAC with an I/V-sense capture stream

A plain DAC codec declares a single playback capability because it only receives audio. A smart amplifier declares both directions, and the capture capability carries the current and voltage measured at the speaker terminals into the protection model. The CS35L56 places the two directions on two separate SoundWire DAIs that share one [`cs35l56_sdw_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L660), one playback-only and one capture-only:

```c
/* sound/soc/codecs/cs35l56.c:691 */
	{
		.name = "cs35l56-sdw1",
		.id = 1,
		.playback = {
			.stream_name = "SDW1 Playback",
			.channels_min = 1,
			.channels_max = 2,
			...
		},
		.ops = &cs35l56_sdw_dai_ops,
	},
	{
		.name = "cs35l56-sdw1c",
		.id = 2,
		.capture = {
			.stream_name = "SDW1 Capture",
			.channels_min = 1,
			.channels_max = 4,
			...
		},
		.ops = &cs35l56_sdw_dai_ops,
	},
```

The capture channel count exceeds the stereo playback because the amplifier can place several monitor signals (measured current, measured voltage, and DSP state) on the feedback port. The TAS2783 reaches the same arrangement with one [`tas_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L985) entry that fills both capabilities, and its [`tas_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L868) routes the `ASI` playback widget through the FU21 and FU23 Feature Units to `SPK`, and the `DMIC` I/V tap to the `ASI OUT` capture widget. The forward path drives the speaker through the boosted DAC, and the reverse path returns the measurement the protection firmware consumes:

```
    Forward drive and reverse I/V-sense on one amplifier
    ─────────────────────────────────────────────────────

       playback DAI                         capture DAI
       (RX, port 1)                         (TX, port 3 or 2)
            │                                     ▲
            ▼                                     │
       ┌─────────┐    ┌────────────┐    ┌─────────┴───────────┐
       │  DAC +  │──▶ │  Class-D   │──▶ │ speaker terminals   │
       │  boost  │    │  drive     │    │   I, V tap          │
       └────┬────┘    └────────────┘    └─────────┬───────────┘
            ▲                                     │
            │  excursion / thermal limit          ▼
       ┌────┴─────────────────────────────────────────────┐
       │ on-chip DSP protection (firmware + per-speaker cal)│
       └────────────────────────────────────────────────────┘

    playback feeds the DSP and the boosted drive; the I/V-sense
    ADC feeds the DSP locally and the host capture stream
```

### The stream direction selects the data port

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op turns the PCM stream direction into a SoundWire data port and direction. On the CS35L56 a playback stream becomes [`SDW_DATA_DIR_RX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L173) into [`CS35L56_SDW1_PLAYBACK_PORT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs35l56.h#L311), and a capture stream becomes [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L174) out of [`CS35L56_SDW1_CAPTURE_PORT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/cs35l56.h#L312), the direction names being from the peripheral's point of view so RX is the speaker stream arriving and TX is the feedback leaving:

```c
/* sound/soc/codecs/cs35l56.c:296 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		sconfig.direction = SDW_DATA_DIR_RX;
		pconfig.num = CS35L56_SDW1_PLAYBACK_PORT;
		pconfig.ch_mask = cs35l56->rx_mask;
	} else {
		sconfig.direction = SDW_DATA_DIR_TX;
		pconfig.num = CS35L56_SDW1_CAPTURE_PORT;
		pconfig.ch_mask = cs35l56->tx_mask;
	}
```

The TAS2783 follows the same shape in [`tas_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L893), selecting port 1 for a playback stream and port 2 for the I/V-sense capture, then both parts call [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) to join the peripheral to the manager-allocated stream. The two parts encode the same speaker-versus-feedback split on different port numbers:

```
    PCM direction maps to a SoundWire port and direction
    ─────────────────────────────────────────────────────

    PCM stream            SDW dir    CS35L56 port      TAS2783 port
    ────────────────────  ─────────  ────────────────  ────────────
    SNDRV_..._PLAYBACK    DIR_RX     playback (1)      playback (1)
       (speaker in)
    SNDRV_..._CAPTURE     DIR_TX     capture  (3)      capture  (2)
       (I/V sense out)

    RX and TX are from the peripheral's point of view;
    sdw_stream_add_slave then joins the amp to that stream
```

### Protection firmware loads onto the DSP and gates audio

The excursion and thermal limiter runs on the amplifier's on-chip DSP, and the host loads that firmware at bring-up before any audio is allowed. The CS35L56 queues [`cs35l56_dsp_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L858) off [`cs35l56_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L1236) so the patch sequence runs off the probe thread, reads the firmware-missing flag with [`cs35l56_read_prot_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56-shared.c#L1337), and either downloads the wmfw and bin images through [`cs35l56_patch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L782) and [`wm_adsp_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm_adsp.c#L987) or reinitialises tunings when firmware is already resident; its [`cs35l56_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L1330) holds the BIAS_STANDBY transition until that work finishes. The TAS2783 makes the gate explicit in [`tas_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L893), which returns an error until [`tas2783_fw_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L728) has set [`fw_dl_success`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L102):

```c
/* sound/soc/codecs/tas2783-sdw.c:906 */
	if (!tas_dev->fw_dl_success) {
		dev_err(tas_dev->dev, "error playback without fw download");
		return -EINVAL;
	}

	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);
	if (!sdw_stream)
		return -EINVAL;
```

Because firmware arrives asynchronously through [`request_firmware_nowait()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/firmware_loader/main.c#L1226), the gate is what serialises a stream start against the download. The bring-up runs in a fixed order, and a stream attempted before the firmware is present is refused at the gate:

```
    Bring-up order: firmware gates the first stream
    ────────────────────────────────────────────────

       probe ─▶ request firmware (async, _nowait)
                         │
                         ▼
            ┌─────────────────────────┐   not ready
       ┌───▶│ firmware download done? │──────────────▶ hw_params
       │    └────────────┬────────────┘                returns error
       │                 │ ready
       │                 ▼
       │      write image blocks to the DSP
       │                 │
       │                 ▼
       │      apply per-speaker calibration
       │                 │
       │                 ▼
       │      set fw_dl_success / patch complete ─▶ audio allowed
       │                 │
       └─────────────────┘  (retry on the next stream start)
```

### Per-speaker calibration flows from a UEFI variable into the DSP

A factory process measures each speaker's DC resistance and stores per-speaker coefficients in a UEFI variable that a manufacturing step or a prior Windows boot wrote. The driver reads that variable at bring-up, validates it, selects the entry for this amplifier, and writes the coefficients into the DSP. The Cirrus parts copy the matching entry into a small fixed record keyed by the silicon UID:

```c
/* include/sound/cs-amp-lib.h:15 */
struct cirrus_amp_cal_data {
	u32 calTarget[2];
	u32 calTime[2];
	s8 calAmbient;
	u8 calStatus;
	u16 calR;
};
```

[`cs_amp_get_efi_calibration_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L608) reads the UEFI variable and searches it for the entry whose UID matches this part, and [`cs_amp_write_cal_coeffs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs-amp-lib.c#L210) writes the record to the named firmware controls. The TAS2783 runs the same provenance through its own helpers: [`tas2783_update_calibdata()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L650) reads the `SmartAmpCalibrationData` variable through [`efi.get_variable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/efi.h#L327), [`tas2783_validate_calibdata()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L563) checks the magic number 2783, the speaker count, the size, and a CRC32, and [`tas2783_set_calib_params_to_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L615) matches this amplifier by [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and writes the five [`tas2783_cali_reg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L49) registers. The validated blob feeds a per-amp selection before the coefficients reach the DSP:

```
    Calibration: UEFI variable to per-amp DSP coefficients
    ───────────────────────────────────────────────────────

    ┌──────────────────────────────┐
    │ UEFI variable                │  written by a factory step
    │  header + per-speaker records│  or a prior Windows boot
    └───────────────┬──────────────┘
                    │ efi.get_variable
                    ▼
    ┌──────────────────────────────┐
    │ validate                     │  magic 2783, speaker count,
    │  (reject on mismatch / CRC)  │  size, CRC32
    └───────────────┬──────────────┘
                    │ select this amp
                    ▼
    ┌──────────────────────────────┐   match key:
    │ one per-speaker record       │     TAS2783 ─▶ unique_id
    │  (calR, calTarget, ...)      │     CS35L56 ─▶ silicon UID
    └───────────────┬──────────────┘
                    │ write coefficients
                    ▼
    ┌──────────────────────────────┐
    │ DSP calibration controls     │  cs_amp_write_cal_coeffs /
    │  (protection model trims)    │  tas2783_cali_reg writes
    └──────────────────────────────┘
```

### Several amps share one bus, each addressed and slotted on its own

A stereo or multi-way speaker set puts two or more amplifiers on one bus, and each one is reached and slotted independently. On SoundWire each amplifier is a separate peripheral with its own enumerated address, so the bus distinguishes them by hardware id and the machine layer gives each a distinct [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L77) through [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) and [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) so their controls stay separate. Within a stream, each amplifier owns distinct channel slots, and the machine driver hands the codec a channel mask through [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297), which on the CS35L56 records the masks the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op later applies, crossing the CPU-side senses because the codec and CPU views are opposite:

```c
/* sound/soc/codecs/cs35l56.c:575 */
static int cs35l56_sdw_dai_set_tdm_slot(struct snd_soc_dai *dai, unsigned int tx_mask,
					unsigned int rx_mask, int slots, int slot_width)
{
	struct cs35l56_private *cs35l56 = snd_soc_component_get_drvdata(dai->component);

	/* rx/tx are from point of view of the CPU end so opposite to our rx/tx */
	cs35l56->rx_mask = tx_mask;
	cs35l56->tx_mask = rx_mask;

	return 0;
}
```

The board-side decision of which amplifier drives which speaker, and on which physical slots, is the machine driver's job and is covered with the rest of the board wiring elsewhere. From the amplifier's own point of view, the result is that its playback and feedback land on the channels its mask selects while the peer amplifier uses the others. Two amplifiers on one bus partition the channels of the shared stream between them:

```
    Two amps on one bus, each owning distinct channels
    ───────────────────────────────────────────────────

       one SoundWire link (or one TDM frame)
       ┌──────────┬──────────┬──────────┬──────────┐
       │ chan 0   │ chan 1   │ chan 2   │ chan 3   │
       └────┬─────┴────┬─────┴────┬─────┴────┬─────┘
            │ AMP "L"  │ AMP "L"  │ AMP "R"  │ AMP "R"
            ▼ ch_mask  ▼          ▼ ch_mask  ▼
       ┌──────────────────┐  ┌──────────────────┐
       │ amp L (prefix L) │  │ amp R (prefix R) │
       │  unique_id / _ADR│  │  unique_id / _ADR│
       └──────────────────┘  └──────────────────┘

    each amp is a distinct peripheral (own id / name_prefix);
    set_tdm_slot gives each the channel mask it claims
```

### Runtime power, mute, and the protection power domain

Once firmware and calibration are in place, a stream start powers the amplifier's output stage and unmutes it, and a stream stop reverses both. On the TAS2783 the output stage is an SDCA Power-Domain Entity, and [`tas_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L893) requests its on state through the SDCA Control address that [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) packs from the Function, the PDE23 entity, and the requested-power-state selector, retrying because a power-on can transiently fail:

```c
/* sound/soc/codecs/tas2783-sdw.c:920 */
	do {
		ret = regmap_write(tas_dev->regmap,
				   SDW_SDCA_CTL(1, TAS2783_SDCA_ENT_PDE23,
						TAS2783_SDCA_CTL_REQ_POW_STATE, 0),
						TAS2783_SDCA_POW_STATE_ON);
		if (!ret)
			break;
		usleep_range(2000, 2200);
	} while (retry--);
```

The matching [`tas_sdw_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L956) writes [`TAS2783_SDCA_POW_STATE_OFF`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783.h#L93) back to the same control, and the mute itself rides on DAPM, where the FU21 and FU23 Feature-Unit widgets are event-driven and their power-up and power-down events write the [`TAS2783_SDCA_CTL_FU_MUTE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783.h#L86) control. The CS35L56 reaches the same runtime gating through its DAPM graph and [`cs35l56_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c#L1330). The amplifier therefore advances through a small set of states from cold power to active drive and back:

```
    Smart amplifier runtime states (one output stage)
    ──────────────────────────────────────────────────

         ┌──────────┐  firmware + calibration applied
         │   OFF    │  (PDE23 = PS3, muted)
         └────┬─────┘
              │ bring-up complete
              ▼
         ┌──────────┐  idle, ready to run
         │  READY   │  (gate open, still muted)
         └────┬─────┘
              │ hw_params: PDE23 ─▶ PS0 (on)
              ▼
         ┌──────────┐  FU mute cleared on widget power-up
         │    ON     │  boosted drive + live protection
         └────┬─────┘
              │ hw_free: FU mute set, PDE23 ─▶ PS3
              ▼
            back to READY (firmware stays resident)
```
