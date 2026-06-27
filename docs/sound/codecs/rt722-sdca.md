# RT722 SDCA codec

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Realtek RT722 is a multi-function SDCA (SoundWire Device Class for Audio) codec that an x86-64 ACPI platform enumerates over a SoundWire link, and the kernel drives it through two cooperating drivers, the ASoC component [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) that presents three Digital Audio Interfaces with their [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697), [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996), [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043), and jack, and the SoundWire peripheral driver [`rt722_sdca_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L541) that binds the device with a [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) named [`rt722_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410), builds the MBQ regmap [`rt722_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195), and routes the codec interrupt. Every register access is a SoundWire MBQ (Multi-Byte Quantity) read or write whose address the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) macro builds from an SDCA function number, an entity, a control selector, and a channel, so the driver names a control on a function entity (a feature unit, a power-domain entity, a clock source) rather than a raw offset. The three interfaces in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) map to four SoundWire data ports, DP1 carries headphone playback and DP2 the headset-mic capture on `aif1`, DP3 carries speaker playback on `aif2`, and DP6 carries the four-channel digital-microphone capture on `aif3`, and the shared function pointer struct [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246) joins each DAI to its SoundWire stream from [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116).

```
    rt722-sdca codec  (SoundWire peripheral 0x025d:0x722, SDCA)
    ──────────────────────────────────────────────────────────

    ASoC component  soc_sdca_dev_rt722
    ┌──────────────────────────────────────────────────────────┐
    │ controls (FU05/FU0F/FU44/FU06/FU1E/FU15 volume + switch) │
    │ dapm_widgets + audio_map (PDE/FU/Mux + AIF endpoints)    │
    │ set_jack ─▶ rt722_sdca_set_jack_detect                   │
    │                                                          │
    │  rt722_sdca_dai[3]            ops ─▶ rt722_sdca_ops      │
    │ ┌──────────┬──────────┬──────────┐                       │
    │ │  aif1    │  aif2    │  aif3    │                       │
    │ └─────┬────┴─────┬────┴─────┬────┘                       │
    └───────┼──────────┼──────────┼────────────────────────────┘
            │          │          │   hw_params: sdw_stream_add_slave
        DP1 ▼ DP2      ▼ DP3      ▼ DP6
       headphone     speaker    DMIC x4
       + headset                (capture)
        mic cap
            │          │          │
            ▼          ▼          ▼
    regmap  rt722_sdca_regmap  (reg_bits 32, val_bits 16, MBQ)
    ┌──────────────────────────────────────────────────────────┐
    │ SDW_SDCA_CTL(func, entity, control, channel) addressing  │
    └───────┬───────────────┬───────────────┬──────────────────┘
            ▼               ▼               ▼
    FUNC_NUM_JACK_CODEC  FUNC_NUM_AMP   FUNC_NUM_MIC_ARRAY
       (0x01)              (0x04)          (0x02)
    CS01/CS11 FU05 FU0F  CS31 FU06 OT23  CS1F FU1E FU15 IT26
    PDE40 PDE12 GE49     PDE23           PDE2A
```

## SUMMARY

The RT722 meets the kernel through the private data [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18), shared by both drivers. On the SoundWire side, [`rt722_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416) builds the MBQ regmap with [`devm_regmap_init_sdw_mbq_cfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1226) and hands it to [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299), which allocates the private data, stores the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and the [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35), arms the two delayed works for jack and button handling, and registers the ASoC component with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). The bus driver supplies [`rt722_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410), whose [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242) advertises the source and sink data ports, whose [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) runs the first-attach hardware init, and whose [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt722_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314) reads the SDCA interrupt status registers and queues the jack work. The generic SoundWire bind contract is [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and the generic SDCA function model is [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419); this page documents the rt722 concrete use of both.

The component driver [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) carries the mixer controls in [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697), the DAPM graph in [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) and [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043), and the jack hook [`rt722_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321) in its [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) field. The three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) all point at [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246), which fills only four callbacks. [`rt722_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102) stores the SoundWire stream handle, [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) selects the data port from the DAI id and direction, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), then programs the clock-source sample rate by a [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) write, [`rt722_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226) removes it with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228), and [`rt722_sdca_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1110) clears the stored handle. The controls, the DAPM power-domain widgets, and the jack all reach hardware through the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address space, so the entire codec is expressed as a set of SDCA function entities and their controls.

## SPECIFICATIONS

The register addressing follows the MIPI SoundWire Device Class for Audio (SDCA) control-address format layered on the MIPI SoundWire bus, encoded by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The header comment above the macro reproduces the v1.2 SDCA address mapping the macro implements, naming the control-prefix, function-number, entity, control-selector, and control-number fields and the bit positions they occupy, and the REGISTERS section below draws it. These documents are membership-gated, so the encoding here is described from that kernel header rather than from the specification text. The four SDCA function numbers the driver uses, [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L156) (0x01), [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L157) (0x02), [`FUNC_NUM_HID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L158) (0x03), and [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L159) (0x04), are the SDCA function types the device exposes. The audio sample formats and rates the DAIs declare (S16_LE, S20_3LE, S24_LE at 44.1/48/96/192 kHz) and the SoundWire stream transport that carries them are defined by their respective standards.

## LINUX KERNEL

### Private data and SDCA address encoding (rt722-sdca.h, sdw_registers.h)

- [`'\<struct rt722_sdca_priv\>':'sound/soc/codecs/rt722-sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18): the per-device state shared by both drivers; holds the [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L19), the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L21), the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L20), the jack pointer [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L31), the two delayed works, and the cached interrupt status [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L29)/[`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L30)
- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): packs the function number, entity, control selector, and channel into one 32-bit MBQ register address; every codec control, power-domain entity, and clock source is reached through it
- [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L156) / [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L157) / [`FUNC_NUM_HID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L158) / [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L159): the four SDCA function numbers (0x01, 0x02, 0x03, 0x04) the codec presents
- [`RT722_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L164) / [`RT722_SDCA_ENT_USER_FU0F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L166) / [`RT722_SDCA_ENT_USER_FU06`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L165) / [`RT722_SDCA_ENT_USER_FU1E`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L168): the feature-unit entities behind the headphone, headset-mic, amp, and DMIC volume and switch controls
- [`RT722_SDCA_ENT_FU15`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L169) / [`RT722_SDCA_ENT_PLATFORM_FU44`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L184): the DMIC and headphone boost feature units whose [`RT722_SDCA_CTL_FU_CH_GAIN`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L201) control the boost mixer addresses
- [`RT722_SDCA_ENT_PDE40`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L171) / [`RT722_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L170) / [`RT722_SDCA_ENT_PDE2A`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L174) / [`RT722_SDCA_ENT_PDE12`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L173): the power-domain entities the DAPM supply widgets drive
- [`RT722_SDCA_ENT_CS01`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L175) / [`RT722_SDCA_ENT_CS11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L176) / [`RT722_SDCA_ENT_CS31`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L179) / [`RT722_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L177): the clock-source entities whose [`RT722_SDCA_CTL_SAMPLE_FREQ_INDEX`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L190) (0x10) control selects the sample rate
- [`RT722_SDCA_ENT_GE49`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L163): the group entity whose [`RT722_SDCA_CTL_DETECTED_MODE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L198) (0x02) control reports the detected jack insertion mode
- [`RT722_SDCA_ENT_XU03`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L185) / [`RT722_SDCA_ENT_XU0D`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L186): the jack-detection cross-point units the init takes out of bypass via [`RT722_SDCA_CTL_SELECTED_MODE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L197) (0x01)
- [`RT722_SDCA_CTL_FU_VOLUME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L192) (0x02) / [`RT722_SDCA_CTL_FU_MUTE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L191) (0x01) / [`RT722_SDCA_CTL_FU_CH_GAIN`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L201) (0x0b) / [`RT722_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L199) (0x01): the SDCA control selectors the controls, DAPM events, and jack use

### Component driver and DAIs (rt722-sdca.c)

- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) wiring controls, DAPM, [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), and [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99)
- [`'rt722_sdca_controls':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697): the mixer control array, each control addressing a feature unit by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335)
- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) / [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the DAPM widget list and routes that connect the AIF endpoints to the feature units and power-domain entities
- [`'\<rt722_sdca_probe\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1075): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78) op recording the component back pointer and resuming the device
- [`'\<rt722_sdca_set_jack_detect\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op storing [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L31) and calling [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293)
- [`'\<rt722_sdca_jack_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293): unmasks the two SDCA interrupt sources and triggers the group-entity detection interrupt
- [`'\<rt722_sdca_jack_detect_handler\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L183): the [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L32) handler that reads insertion and button state and reports through [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33)
- [`'\<rt722_sdca_pde23_event\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L921): the speaker power-domain supply event that writes [`RT722_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L199) on [`RT722_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L170)
- [`'rt722_sdca_ops':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) shared by all three DAIs, populating [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)
- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries `aif1`, `aif2`, `aif3`, declaring the DP1/DP2/DP3/DP6 streams
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): selects the SoundWire data port, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), then writes the clock-source sample rate
- [`'\<rt722_sdca_pcm_hw_free\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226): removes the codec from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)
- [`'\<rt722_sdca_set_sdw_stream\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op storing the stream handle with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506)
- [`'\<rt722_sdca_shutdown\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1110): the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op clearing the stored handle with [`snd_soc_dai_set_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L505)
- [`'\<rt722_sdca_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299): allocates the private data, stores the slave and regmap, arms the jack works, and registers the component with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'\<rt722_sdca_io_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525): the first-attach hardware init run from [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), presetting the three functions and enabling runtime PM

### SoundWire peripheral driver (rt722-sdca-sdw.c)

- [`'rt722_sdca_sdw_driver':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L541): the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) registered with [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34)
- [`'rt722_sdca_id':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L447): the one-entry match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717)
- [`'rt722_sdca_slave_ops':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410): the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) with [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<rt722_sdca_sdw_probe\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416): builds the MBQ regmap and calls [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299)
- [`'\<rt722_sdca_update_status\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208): runs hardware init when the slave reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) and restores interrupt masks
- [`'\<rt722_sdca_read_prop\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242): fills the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) with the source and sink port bitmaps and per-port [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308)
- [`'\<rt722_sdca_interrupt_callback\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314): reads [`SDW_SCP_SDCA_INT1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L136)/[`SDW_SCP_SDCA_INT2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L146), caches them, and queues [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L32)
- [`'rt722_sdca_regmap':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195): the [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit addresses, 16-bit values, [`REGCACHE_MAPLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L73))
- [`'rt722_mbq_config':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L150): the [`struct regmap_sdw_mbq_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L539) whose [`mbq_size`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L539) callback [`rt722_sdca_mbq_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L19) returns 1 or 2 bytes per register
- [`'\<rt722_sdca_readable_register\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L154): reuses [`rt722_sdca_mbq_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L19) to decide which addresses are readable

### SoundWire stream and regmap helpers (generic infrastructure)

- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the generic peripheral callback contract the codec fills; documented as a separate SoundWire-bind page
- [`'\<struct sdca_function_data\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419): the generic parsed-SDCA-function model; the rt722 driver hardcodes its function/entity/control ids rather than parsing this
- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): allocate the slave runtime, configure its ports, and advance the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928)
- [`'\<sdw_stream_remove_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228): free the slave port and runtime from the stream
- [`'\<devm_regmap_init_sdw_mbq_cfg\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1226): build a device-managed SoundWire MBQ regmap from the config and the MBQ size callback
- [`'\<snd_soc_jack_report\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33): apply the reported status to the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), enable or disable the associated DAPM pins, and notify userspace
- [`'\<regmap_write\>':'drivers/base/regmap/regmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c#L1981) / [`'\<regmap_read\>':'drivers/base/regmap/regmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c#L2867): the MBQ accessors the codec uses against [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addresses
- [`'\<sdw_write_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480) / [`'\<sdw_read_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L557) / [`'\<sdw_update_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L570): the no-PM bus accessors the interrupt and jack paths use for the SCP interrupt registers

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the codec joins from its hw_params op with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus model, master, peripheral, and data port concepts behind the rt722 ports
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the bus locking the stream add and remove paths take
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): the bus-clash and parity error handling the read_prop callback enables through [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372)
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC codec component guide covering the component driver, DAI driver, and ops the page describes
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the Dynamic Audio Power Management widget and route model the codec's DAPM graph builds
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack abstraction the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) callback drives

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Intel SoundWire support on Linux, 01.org archive notes](https://www.kernel.org/doc/html/latest/driver-api/soundwire/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The codec has no flat register window. Every register is an SDCA control reached by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), which packs four operands into one 32-bit MBQ address. The header comment in [`sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L315) gives the v1.2 SDCA address mapping the macro implements, and the figure below plots where each operand lands in the 32-bit word. The mapping splits two operands across the word, the Entity into a high bit and a low six-bit field, and the Control Selector into a high two-bit field and a low four-bit field, so the macro recombines each from two shifts. The channel the driver passes occupies the same low bits the mapping labels Control Number, since the addressed control instance is the per-channel copy of the named control.

```
    SDW_SDCA_CTL(fun, ent, ctl, ch)  SDCA control address (32-bit MBQ)
    ──────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │0│ prefix  │0│ fun │E│cS │0│ cN  │N│M│    ent    │  cS   │ cN  │
          │ │  (P)    │ │24:22│ │ H │ │  H  │ │ │   12:7    │   L   │  L  │
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

    P      = Control Prefix, bits 30:26 = 0b10000  (set by BIT(30))
    fun    = Function Number[2:0], bits 24:22
    E      = Entity[6], bit 21
    cS H   = Control Selector[5:4], bits 20:19
    cN H   = Control Number[5:3], bits 17:15
    N      = Next, bit 14            M = MBQ, bit 13
    ent    = Entity[5:0], bits 12:7
    cS L   = Control Selector[3:0], bits 6:3
    cN L   = Control Number[2:0], bits 2:0
    bits 31, 25, 18 are 0 (reserved)
    Entity = (E << 6) | ent;  Control Selector = (cS H << 4) | cS L
    the channel operand is encoded into the Control Number field (cN H, cN L)
```

The driver passes mnemonic operands that the macro resolves to bit positions. A headphone playback volume write goes to `SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05, RT722_SDCA_CTL_FU_VOLUME, CH_L)`, a speaker power-domain request to `SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_PDE23, RT722_SDCA_CTL_REQ_POWER_STATE, 0)`, and a DMIC clock-source rate to `SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT722_SDCA_ENT_CS1F, RT722_SDCA_CTL_SAMPLE_FREQ_INDEX, 0)`. The size of each control, one byte or two, is decided per address by [`rt722_sdca_mbq_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L19), and the [`max_register`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L200) field is 0x44ffffff to cover both the SDCA control space and the vendor HID buffer addresses at [`RT722_BUF_ADDR_HID1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L152).

## DETAILS

### The codec is registered over two bus models

The RT722 binds first as a SoundWire peripheral. The match table [`rt722_sdca_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L447) holds the single MIPI id, and on a match the bus calls [`rt722_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416), which creates the MBQ regmap and passes it to [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:447 */
static const struct sdw_device_id rt722_sdca_id[] = {
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0),
	{},
};
MODULE_DEVICE_TABLE(sdw, rt722_sdca_id);
```

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:416 */
static int rt722_sdca_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap;

	/* Regmap Initialization */
	regmap = devm_regmap_init_sdw_mbq_cfg(&slave->dev, slave,
					      &rt722_sdca_regmap,
					      &rt722_mbq_config);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt722_sdca_init(&slave->dev, regmap, slave);
}
```

[`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) allocates the [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18), stores the slave and the regmap, starts the regmap in cache-only mode until the device attaches, initializes the two delayed works, and registers the ASoC component. According to the comment "HW init will be performed when device reports present", the function sets the [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) flags false and defers the real device programming to attach time:

```c
/* sound/soc/codecs/rt722-sdca.c:1299 */
int rt722_sdca_init(struct device *dev, struct regmap *regmap, struct sdw_slave *slave)
{
	struct rt722_sdca_priv *rt722;

	rt722 = devm_kzalloc(dev, sizeof(*rt722), GFP_KERNEL);
	if (!rt722)
		return -ENOMEM;

	dev_set_drvdata(dev, rt722);
	rt722->slave = slave;
	rt722->regmap = regmap;

	regcache_cache_only(rt722->regmap, true);

	mutex_init(&rt722->calibrate_mutex);
	mutex_init(&rt722->disable_irq_lock);

	INIT_DELAYED_WORK(&rt722->jack_detect_work, rt722_sdca_jack_detect_handler);
	INIT_DELAYED_WORK(&rt722->jack_btn_check_work, rt722_sdca_btn_check_handler);

	/*
	 * Mark hw_init to false
	 * HW init will be performed when device reports present
	 */
	rt722->hw_init = false;
	rt722->first_hw_init = false;
	...
	return devm_snd_soc_register_component(dev,
			&soc_sdca_dev_rt722, rt722_sdca_dai, ARRAY_SIZE(rt722_sdca_dai));
}
```

The [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) is the meeting point between the two drivers. The SoundWire side stores the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L21), [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L19), and the cached interrupt status, and the ASoC side stores the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L20), the [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L31) pointer, and the DMIC and headphone mute caches:

```c
/* sound/soc/codecs/rt722-sdca.h:18 */
struct  rt722_sdca_priv {
	struct regmap *regmap;
	struct snd_soc_component *component;
	struct sdw_slave *slave;
	struct sdw_bus_params params;
	bool hw_init;
	bool first_hw_init;
	struct mutex calibrate_mutex;
	struct mutex disable_irq_lock;
	bool disable_irq;
	/* For Headset jack & Headphone */
	unsigned int scp_sdca_stat1;
	unsigned int scp_sdca_stat2;
	struct snd_soc_jack *hs_jack;
	struct delayed_work jack_detect_work;
	struct delayed_work jack_btn_check_work;
	int jack_type;
	int jd_src;
	bool fu0f_dapm_mute;
	bool fu0f_mixer_l_mute;
	bool fu0f_mixer_r_mute;
	/* For DMIC */
	bool fu1e_dapm_mute;
	bool fu1e_mixer_mute[4];
	int hw_vid;
};
```

The figure shows which side writes each member, the SoundWire file setting the regmap, the slave, and the cached interrupt status and the ASoC file setting the component, the jack pointer, and the mute caches, over a shared band of init flags and locks:

```
    struct rt722_sdca_priv: one struct, fields filled by each driver
    ────────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ struct rt722_sdca_priv  (shared meeting point)           │
    ├──────────────────────────────────────────────────────────┤
    │ SoundWire side (rt722-sdca-sdw.c)                        │
    │   regmap          ◀── devm_regmap_init_sdw_mbq_cfg()     │
    │   slave           ◀── sdw_slave at probe                 │
    │   params          ◀── sdw_bus_params                     │
    │   scp_sdca_stat1  ◀── cached SDW_SCP_SDCA_INT1           │
    │   scp_sdca_stat2  ◀── cached SDW_SCP_SDCA_INT2           │
    ├──────────────────────────────────────────────────────────┤
    │ ASoC side (rt722-sdca.c)                                 │
    │   component       ◀── set at component probe             │
    │   hs_jack         ◀── set_jack hook                      │
    │   jack_detect_work / jack_btn_check_work                 │
    │   fu0f_* mutes    ◀── headphone mute caches              │
    │   fu1e_* mutes    ◀── DMIC mutes, fu1e_mixer_mute[4]     │
    ├──────────────────────────────────────────────────────────┤
    │ shared: hw_init / first_hw_init   calibrate_mutex        │
    │         disable_irq / disable_irq_lock   hw_vid          │
    └──────────────────────────────────────────────────────────┘
```

### SDW_SDCA_CTL addresses an SDCA function entity

Because the codec has no flat register layout, every regmap access is an SDCA control address built by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The macro masks each operand and shifts it into its field, with the entity and the control selector each split across the word as the SDCA v1.2 mapping requires, and [`BIT(30)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) setting the control prefix:

```c
/* include/linux/soundwire/sdw_registers.h:335 */
#define SDW_SDCA_CTL(fun, ent, ctl, ch)		(BIT(30) |				\
						 (((fun) & GENMASK(2, 0)) << 22) |	\
						 (((ent) & BIT(6)) << 15) |		\
						 (((ent) & GENMASK(5, 0)) << 7) |	\
						 (((ctl) & GENMASK(5, 4)) << 15) |	\
						 (((ctl) & GENMASK(3, 0)) << 3) |	\
						 (((ch) & GENMASK(5, 3)) << 12) |	\
						 ((ch) & GENMASK(2, 0)))
```

The driver supplies the four operands by name. A function number such as [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L156) (0x01) selects which SDCA function the address targets, an entity such as [`RT722_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L164) (0x05) names a feature unit inside it, a control selector such as [`RT722_SDCA_CTL_FU_VOLUME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L192) (0x02) names a control on that entity, and a channel such as [`CH_L`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L206) (0x01) picks the channel. These constants are defined in the codec header:

```c
/* sound/soc/codecs/rt722-sdca.h:155 */
/* RT722 SDCA Control - function number */
#define FUNC_NUM_JACK_CODEC			0x01
#define FUNC_NUM_MIC_ARRAY			0x02
#define FUNC_NUM_HID				0x03
#define FUNC_NUM_AMP				0x04
```

The size of the value at a given address is not uniform, so the regmap is built with a per-register size callback. [`rt722_sdca_mbq_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L19) is a switch over the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addresses that returns 1 for single-byte controls such as the mutes and power states, 2 for two-byte controls such as the feature-unit volumes and channel gains, and 0 for unreadable addresses, and [`rt722_sdca_readable_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L154) reuses it to decide readability:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:19 */
static int rt722_sdca_mbq_size(struct device *dev, unsigned int reg)
{
	switch (reg) {
	...
	case SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			  RT722_SDCA_CTL_FU_MUTE, CH_L) ...
	     SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			  RT722_SDCA_CTL_FU_MUTE, CH_R):
	...
		return 1;
	...
	case SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_USER_FU06, RT722_SDCA_CTL_FU_VOLUME, CH_L):
	case SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_USER_FU06, RT722_SDCA_CTL_FU_VOLUME, CH_R):
	...
		return 2;
	default:
		return 0;
	}
}
```

That callback is wired into the regmap through [`rt722_mbq_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L150), and the [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) named [`rt722_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195) declares 32-bit addresses and 16-bit values with a maple-tree cache:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:150 */
static const struct regmap_sdw_mbq_cfg rt722_mbq_config = {
	.mbq_size = rt722_sdca_mbq_size,
};
...
static const struct regmap_config rt722_sdca_regmap = {
	.reg_bits = 32,
	.val_bits = 16,
	.readable_reg = rt722_sdca_readable_register,
	.volatile_reg = rt722_sdca_volatile_register,
	.max_register = 0x44ffffff,
	.reg_defaults = rt722_sdca_reg_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt722_sdca_reg_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};
```

[`devm_regmap_init_sdw_mbq_cfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1226) combines the two configs, passing the [`struct regmap_sdw_mbq_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L539) so the MBQ transport knows how many bytes to move for each register:

```c
/* include/linux/regmap.h:1226 */
#define devm_regmap_init_sdw_mbq_cfg(dev, sdw, config, mbq_config)	\
	__regmap_lockdep_wrapper(__devm_regmap_init_sdw_mbq,		\
				#config, dev, sdw, config, mbq_config)
```

### The component driver presents controls, DAPM, and the jack

The ASoC face of the codec is [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090), a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that binds the control array, the DAPM widget and route arrays, the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), and the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) hook. The [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) bit is set because the SoundWire transport fixes the wire byte order:

```c
/* sound/soc/codecs/rt722-sdca.c:1090 */
static const struct snd_soc_component_driver soc_sdca_dev_rt722 = {
	.probe = rt722_sdca_probe,
	.controls = rt722_sdca_controls,
	.num_controls = ARRAY_SIZE(rt722_sdca_controls),
	.dapm_widgets = rt722_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt722_sdca_dapm_widgets),
	.dapm_routes = rt722_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt722_sdca_audio_map),
	.set_jack = rt722_sdca_set_jack_detect,
	.endianness = 1,
};
```

Each entry in [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697) is a mixer control whose register operands are a [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address into a feature unit. The headphone playback volume reads and writes [`RT722_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L164) on [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L156), the headset-mic capture volume reads [`RT722_SDCA_ENT_USER_FU0F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L166), the speaker playback volume reads [`RT722_SDCA_ENT_USER_FU06`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L165) on [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L159), and the DMIC capture switch and volume read [`RT722_SDCA_ENT_USER_FU1E`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L168) on [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L157):

```c
/* sound/soc/codecs/rt722-sdca.c:697 */
static const struct snd_kcontrol_new rt722_sdca_controls[] = {
	/* Headphone playback settings */
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_R), 0, 0x57, 0,
		rt722_sdca_set_gain_get, rt722_sdca_set_gain_put, out_vol_tlv),
	...
	/* DMIC capture settings */
	RT722_SDCA_FU_CTRL("FU1E Capture Switch",
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT722_SDCA_ENT_USER_FU1E,
			RT722_SDCA_CTL_FU_MUTE, CH_01), 1, 1, 4),
	RT722_SDCA_EXT_TLV("FU1E Capture Volume",
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT722_SDCA_ENT_USER_FU1E,
			RT722_SDCA_CTL_FU_VOLUME, CH_01),
		rt722_sdca_dmic_set_gain_get, rt722_sdca_dmic_set_gain_put,
			4, 0x3f, mic_vol_tlv),
	RT722_SDCA_EXT_TLV("FU15 Boost Volume",
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT722_SDCA_ENT_FU15,
			RT722_SDCA_CTL_FU_CH_GAIN, CH_01),
		rt722_sdca_dmic_set_gain_get, rt722_sdca_dmic_set_gain_put,
			4, 3, boost_vol_tlv),
};
```

The DAPM graph in [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) names the analog pins, the feature-unit DAC and ADC widgets, the input muxes, the power-domain supply widgets, and one AIF endpoint per data port. The AIF widgets carry the same stream names the DAIs declare, so the core can connect the playback and capture paths to the front end:

```c
/* sound/soc/codecs/rt722-sdca.c:996 */
static const struct snd_soc_dapm_widget rt722_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("MIC2"),
	...
	SND_SOC_DAPM_SUPPLY("PDE 23", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde23_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	...
	SND_SOC_DAPM_AIF_IN("DP1RX", "DP1 Headphone Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP2TX", "DP2 Headset Capture", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_IN("DP3RX", "DP3 Speaker Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP6TX", "DP6 DMic Capture", 0, SND_SOC_NOPM, 0, 0),
};
```

The routes in [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) connect those endpoints to the feature units and pull in the matching power-domain supply for each path, so that powering up the headphone output (`HP`) requires the `PDE 47` supply, the speaker output (`SPK`) requires `PDE 23`, the headset-mic capture (`DP2TX`) requires `PDE 12`, and the DMIC capture (`DP6TX`) requires `PDE 11`:

```c
/* sound/soc/codecs/rt722-sdca.c:1043 */
static const struct snd_soc_dapm_route rt722_sdca_audio_map[] = {
	{"FU 42", NULL, "DP1RX"},
	{"FU 21", NULL, "DP3RX"},
	...
	{"FU 36", NULL, "PDE 12"},
	{"FU 36", NULL, "ADC 22 Mux"},
	{"FU 113", NULL, "PDE 11"},
	...
	{"DP2TX", NULL, "FU 36"},
	{"DP6TX", NULL, "FU 113"},

	{"HP", NULL, "PDE 47"},
	{"HP", NULL, "FU 42"},
	{"SPK", NULL, "PDE 23"},
	{"SPK", NULL, "FU 21"},
};
```

A power-domain supply widget runs an event handler that writes the SDCA [`RT722_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L199) control of its entity, requesting power state 0 on power-up and power state 3 on power-down. The speaker handler [`rt722_sdca_pde23_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L921) writes [`RT722_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L170) on [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L159):

```c
/* sound/soc/codecs/rt722-sdca.c:921 */
static int rt722_sdca_pde23_event(struct snd_soc_dapm_widget *w,
	struct snd_kcontrol *kcontrol, int event)
{
	struct snd_soc_component *component =
		snd_soc_dapm_to_component(w->dapm);
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	unsigned char ps0 = 0x0, ps3 = 0x3;

	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_PDE23,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps0);
		rt722_pde_transition_delay(rt722, FUNC_NUM_AMP, RT722_SDCA_ENT_PDE23, ps0);
		break;
	case SND_SOC_DAPM_PRE_PMD:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_PDE23,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps3);
		rt722_pde_transition_delay(rt722, FUNC_NUM_AMP, RT722_SDCA_ENT_PDE23, ps3);
		break;
	}
	return 0;
}
```

This PDE 23 supply feeds the speaker path drawn here, where each AIF runs through a feature unit to its pin, DP1RX reaching HP through FU 42 on playback and ADC 22 reaching DP2TX through FU 36 on capture:

```
    rt722_sdca_audio_map: data path AIF ──▶ feature unit ──▶ pin
    ────────────────────────────────────────────────────────────────
    (──▶ is the data direction; PDE nn = the path's power supply)

    playback (RX)
      "DP1RX"      ──▶ "FU 42" ──▶ "HP"      supply: "HP"  ◀── "PDE 47"
      "DP3RX"      ──▶ "FU 21" ──▶ "SPK"     supply: "SPK" ◀── "PDE 23"

    capture (TX)
      "ADC 22 Mux" ──▶ "FU 36" ──▶ "DP2TX"   supply: "FU 36"  ◀── "PDE 12"
                       "FU 113" ──▶ "DP6TX"  supply: "FU 113" ◀── "PDE 11"
```

### Three DAIs over four data ports

The codec presents three interfaces in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253). The `aif1` entry declares both a playback capability with the `DP1 Headphone Playback` stream name and a capture capability with the `DP2 Headset Capture` stream name, the `aif2` entry declares the `DP3 Speaker Playback` stream, and the `aif3` entry declares the four-channel `DP6 DMic Capture` stream, and all three point at [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246):

```c
/* sound/soc/codecs/rt722-sdca.c:1253 */
static struct snd_soc_dai_driver rt722_sdca_dai[] = {
	{
		.name = "rt722-sdca-aif1",
		.id = RT722_AIF1,
		.playback = {
			.stream_name = "DP1 Headphone Playback",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.capture = {
			.stream_name = "DP2 Headset Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.ops = &rt722_sdca_ops,
	},
	{
		.name = "rt722-sdca-aif2",
		.id = RT722_AIF2,
		.playback = {
			.stream_name = "DP3 Speaker Playback",
			...
		},
		.ops = &rt722_sdca_ops,
	},
	{
		.name = "rt722-sdca-aif3",
		.id = RT722_AIF3,
		.capture = {
			.stream_name = "DP6 DMic Capture",
			.channels_min = 1,
			.channels_max = 4,
			...
		},
		.ops = &rt722_sdca_ops,
	}
};
```

The DAI ids are an enum in the codec header, with [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) for the headset and headphone, [`RT722_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L227) for the speaker, and [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228) for the DMIC:

```c
/* sound/soc/codecs/rt722-sdca.h:225 */
enum {
	RT722_AIF1, /* For headset mic and headphone */
	RT722_AIF2, /* For speaker */
	RT722_AIF3, /* For dmic */
	RT722_AIFS,
};
```

All three DAIs share one function pointer struct, and it fills only four callbacks, so the ASoC core treats every other op as a no-op behind its wrapper guards:

```c
/* sound/soc/codecs/rt722-sdca.c:1246 */
static const struct snd_soc_dai_ops rt722_sdca_ops = {
	.hw_params	= rt722_sdca_pcm_hw_params,
	.hw_free	= rt722_sdca_pcm_hw_free,
	.set_stream	= rt722_sdca_set_sdw_stream,
	.shutdown	= rt722_sdca_shutdown,
};
```

The machine layer hands the codec a SoundWire stream handle through the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, and [`rt722_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102) stores it per direction with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506), while [`rt722_sdca_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1110) clears it:

```c
/* sound/soc/codecs/rt722-sdca.c:1102 */
static int rt722_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}

static void rt722_sdca_shutdown(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	snd_soc_dai_set_dma_data(dai, substream, NULL);
}
```

With the handle stored, the params op maps each direction and DAI id to one port, playback taking port 1 on aif1 and port 3 on aif2 and capture taking port 2 on aif1 and port 6 on aif3:

```
    hw_params: (substream direction, dai->id) ──▶ SoundWire port
    ────────────────────────────────────────────────────────────────

    ┌───────────┬────────────┬──────┬──────────────────────────┐
    │ direction │ dai->id    │ port │ stream_name              │
    ├───────────┼────────────┼──────┼──────────────────────────┤
    │ PLAYBACK  │ RT722_AIF1 │  1   │ DP1 Headphone Playback   │
    │ (RX)      │ RT722_AIF2 │  3   │ DP3 Speaker Playback     │
    ├───────────┼────────────┼──────┼──────────────────────────┤
    │ CAPTURE   │ RT722_AIF1 │  2   │ DP2 Headset Capture      │
    │ (TX)      │ RT722_AIF3 │  6   │ DP6 DMic Capture         │
    └───────────┴────────────┴──────┴──────────────────────────┘
    any other (direction, id) pair ──▶ -EINVAL
```

### hw_params selects the data port and joins the stream

[`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) reads the stored handle back with [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497), then maps the DAI id and the substream direction to one SoundWire data port. The comment in the function enumerates the mapping, with [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) port 1 for headphone playback, [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) port 2 for headset-mic capture, [`RT722_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L227) port 3 for speaker playback, and [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228) port 6 for digital-mic capture:

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
	/*
	 * RT722_AIF1 with port = 1 for headphone playback
	 * RT722_AIF1 with port = 2 for headset-mic capture
	 * RT722_AIF2 with port = 3 for speaker playback
	 * RT722_AIF3 with port = 6 for digital-mic capture
	 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		direction = SDW_DATA_DIR_RX;
		if (dai->id == RT722_AIF1)
			port = 1;
		else if (dai->id == RT722_AIF2)
			port = 3;
		else
			return -EINVAL;
	} else {
		direction = SDW_DATA_DIR_TX;
		if (dai->id == RT722_AIF1)
			port = 2;
		else if (dai->id == RT722_AIF3)
			port = 6;
		else
			return -EINVAL;
	}
```

It then fills a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) from the negotiated parameters and a [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) with the channel mask and the chosen port, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt722->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
```

[`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) allocates the master and slave runtimes, configures the slave port, and advances the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) on the first slave add. After the slave is added, the op programs the sample rate into the SDCA clock-source entity for the active interface, again by name. For [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) it writes both [`RT722_SDCA_ENT_CS01`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L175) and [`RT722_SDCA_ENT_CS11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L176) on [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L156); for [`RT722_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L227) it writes [`RT722_SDCA_ENT_CS31`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L179) on [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L159); for [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228) it writes [`RT722_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L177) on [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L157):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
	/* set sampling frequency */
	if (dai->id == RT722_AIF1) {
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_CS01,
				RT722_SDCA_CTL_SAMPLE_FREQ_INDEX, 0), sampling_rate);
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_CS11,
				RT722_SDCA_CTL_SAMPLE_FREQ_INDEX, 0), sampling_rate);
	}

	if (dai->id == RT722_AIF2)
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT722_SDCA_ENT_CS31,
				RT722_SDCA_CTL_SAMPLE_FREQ_INDEX, 0), sampling_rate);

	if (dai->id == RT722_AIF3)
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT722_SDCA_ENT_CS1F,
				RT722_SDCA_CTL_SAMPLE_FREQ_INDEX, 0), sampling_rate);
```

The teardown is the mirror image. [`rt722_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226) reads the same stored handle and removes the codec from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228), which frees the slave port and runtime:

```c
/* sound/soc/codecs/rt722-sdca.c:1226 */
static int rt722_sdca_pcm_hw_free(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_runtime *sdw_stream =
		snd_soc_dai_get_dma_data(dai, substream);

	if (!rt722->slave)
		return -EINVAL;

	sdw_stream_remove_slave(rt722->slave, sdw_stream);
	return 0;
}
```

The sample-rate write itself fans out by interface, aif1 reaching CS01 and CS11 under the jack-codec function, aif2 reaching CS31 under the amp, and aif3 reaching CS1F under the mic array:

```
    set sample rate: each DAI ──▶ function ──▶ clock-source entity
    ────────────────────────────────────────────────────────────────
    (write RT722_SDCA_CTL_SAMPLE_FREQ_INDEX on each entity below)

    RT722_AIF1 ──▶ FUNC_NUM_JACK_CODEC ──┬─▶ RT722_SDCA_ENT_CS01
                                         └─▶ RT722_SDCA_ENT_CS11
    RT722_AIF2 ──▶ FUNC_NUM_AMP        ────▶ RT722_SDCA_ENT_CS31
    RT722_AIF3 ──▶ FUNC_NUM_MIC_ARRAY  ────▶ RT722_SDCA_ENT_CS1F
```

### The bus driver binds the device and advertises its ports

The SoundWire peripheral driver [`rt722_sdca_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L541) supplies the probe, the remove, the PM ops, the [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), and the slave ops:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:541 */
static struct sdw_driver rt722_sdca_sdw_driver = {
	.driver = {
		.name = "rt722-sdca",
		.pm = pm_ptr(&rt722_sdca_pm),
	},
	.probe = rt722_sdca_sdw_probe,
	.remove = rt722_sdca_sdw_remove,
	.ops = &rt722_sdca_slave_ops,
	.id_table = rt722_sdca_id,
};
module_sdw_driver(rt722_sdca_sdw_driver);
```

The bus calls back into the codec through [`rt722_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410), which fills the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) members of the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:410 */
static const struct sdw_slave_ops rt722_sdca_slave_ops = {
	.read_prop = rt722_sdca_read_prop,
	.interrupt_callback = rt722_sdca_interrupt_callback,
	.update_status = rt722_sdca_update_status,
};
```

[`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242) declares which data ports the device drives by setting the [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) bitmaps in the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), then allocates a [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) for each set bit. The source ports are 6 and 2 (the capture ports), the sink ports are 3 and 1 (the playback ports), matching the data ports the DAIs select, and it also sets [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) so the bus enables the bus-clash and parity interrupts:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:242 */
	prop->scp_int1_mask = SDW_SCP_INT1_BUS_CLASH | SDW_SCP_INT1_PARITY;
	prop->quirks = SDW_SLAVE_QUIRKS_INVALID_INITIAL_PARITY;

	prop->paging_support = true;

	/*
	 * port = 1 for headphone playback
	 * port = 2 for headset-mic capture
	 * port = 3 for speaker playback
	 * port = 6 for digital-mic capture
	 */
	prop->source_ports = BIT(6) | BIT(2); /* BITMAP: 01000100 */
	prop->sink_ports = BIT(3) | BIT(1); /* BITMAP:  00001010 */

	nval = hweight32(prop->source_ports);
	prop->src_dpn_prop = devm_kcalloc(&slave->dev, nval,
		sizeof(*prop->src_dpn_prop), GFP_KERNEL);
	if (!prop->src_dpn_prop)
		return -ENOMEM;

	i = 0;
	dpn = prop->src_dpn_prop;
	addr = prop->source_ports;
	for_each_set_bit(bit, &addr, 32) {
		dpn[i].num = bit;
		dpn[i].type = SDW_DPN_FULL;
		dpn[i].simple_ch_prep_sm = true;
		dpn[i].ch_prep_timeout = 10;
		i++;
	}
```

### update_status runs the deferred hardware init

[`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) is the entry point that turns an attach event into device programming. When the slave reports [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) it marks [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) false, and when it reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) with [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) still false it runs [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525). On re-attach with the jack already in use it rewrites the SDCA interrupt masks, because, according to the comment, "the SCP_SDCA_INTMASK will be cleared by any reset":

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:208 */
static int rt722_sdca_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt722->hw_init = false;

	if (status == SDW_SLAVE_ATTACHED) {
		if (rt722->hs_jack) {
		...
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK1,
				SDW_SCP_SDCA_INTMASK_SDCA_0);
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK2,
				SDW_SCP_SDCA_INTMASK_SDCA_8);
		}
	}

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt722->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt722_sdca_io_init(&slave->dev, slave);
}
```

[`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) takes the regmap out of cache-only mode, presets the three SDCA functions through [`rt722_sdca_dmic_preset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1335) and its amp and jack peers, enables runtime PM on the first attach, and marks [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) true:

```c
/* sound/soc/codecs/rt722-sdca.c:1525 */
int rt722_sdca_io_init(struct device *dev, struct sdw_slave *slave)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(dev);
	unsigned int val;

	rt722->disable_irq = false;

	if (rt722->hw_init)
		return 0;

	regcache_cache_only(rt722->regmap, false);
	if (rt722->first_hw_init) {
		regcache_cache_bypass(rt722->regmap, true);
	} else {
		/*
		 * PM runtime is only enabled when a Slave reports as Attached
		 */
		...
		pm_runtime_enable(&slave->dev);
	}

	pm_runtime_get_noresume(&slave->dev);
	...
	rt722_sdca_dmic_preset(rt722);
	rt722_sdca_amp_preset(rt722);
	rt722_sdca_jack_preset(rt722);
	...
	/* Mark Slave initialization complete */
	rt722->hw_init = true;

	pm_runtime_put_autosuspend(&slave->dev);
	...
	return 0;
}
```

### The interrupt routes through the SDCA cascade to the jack work

A device interrupt arrives at [`rt722_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314) in thread context. It reads the two SDCA interrupt status registers [`SDW_SCP_SDCA_INT1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L136) (0x58) and [`SDW_SCP_SDCA_INT2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L146) (0x59) with [`sdw_read_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L557), caches them in [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L29) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L30), clears the SDCA_0 and SDCA_8 bits in a retry loop with [`sdw_update_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L570) and [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480), and queues [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L32) when the [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L529) status in the [`struct sdw_slave_intr_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) argument is set:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:314 */
	ret = sdw_read_no_pm(rt722->slave, SDW_SCP_SDCA_INT1);
	if (ret < 0)
		goto io_error;
	rt722->scp_sdca_stat1 = ret;
	ret = sdw_read_no_pm(rt722->slave, SDW_SCP_SDCA_INT2);
	if (ret < 0)
		goto io_error;
	rt722->scp_sdca_stat2 = ret;
	...
	if (status->sdca_cascade && !rt722->disable_irq)
		mod_delayed_work(system_power_efficient_wq,
			&rt722->jack_detect_work, msecs_to_jiffies(280));
```

The cached status drives the work handler. [`rt722_sdca_jack_detect_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L183) runs headset detection when [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137) is set in the cached [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L29), runs button detection when [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147) is set in [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L30), and reports the result with [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33):

```c
/* sound/soc/codecs/rt722-sdca.c:183 */
	/* SDW_SCP_SDCA_INT_SDCA_0 is used for jack detection */
	if (rt722->scp_sdca_stat1 & SDW_SCP_SDCA_INT_SDCA_0) {
		ret = rt722_sdca_headset_detect(rt722);
		if (ret < 0)
			return;
	}

	/* SDW_SCP_SDCA_INT_SDCA_8 is used for button detection */
	if (rt722->scp_sdca_stat2 & SDW_SCP_SDCA_INT_SDCA_8)
		btn_type = rt722_sdca_button_detect(rt722);
	...
	snd_soc_jack_report(rt722->hs_jack, rt722->jack_type | btn_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);
```

The jack is wired in when the machine driver calls the component [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op. [`rt722_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321) stores the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) pointer in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L31) and calls [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293):

```c
/* sound/soc/codecs/rt722-sdca.c:321 */
static int rt722_sdca_set_jack_detect(struct snd_soc_component *component,
	struct snd_soc_jack *hs_jack, void *data)
{
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	int ret;

	rt722->hs_jack = hs_jack;

	ret = pm_runtime_resume_and_get(component->dev);
	if (ret < 0) {
		if (ret != -EACCES) {
			dev_err(component->dev, "%s: failed to resume %d\n", __func__, ret);
			return ret;
		}
		/* pm_runtime not enabled yet */
		dev_dbg(component->dev,	"%s: skipping jack init for now\n", __func__);
		return 0;
	}

	rt722_sdca_jack_init(rt722);

	pm_runtime_put_autosuspend(component->dev);

	return 0;
}
```

[`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293) unmasks the two SDCA interrupt sources with [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480) by writing [`SDW_SCP_SDCA_INTMASK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L176) (0x5C) and [`SDW_SCP_SDCA_INTMASK2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L186) (0x5D), takes the jack-detection cross-point units out of bypass by writing the [`RT722_SDCA_CTL_SELECTED_MODE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L197) control of [`RT722_SDCA_ENT_XU03`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L185) and [`RT722_SDCA_ENT_XU0D`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L186), and triggers the group-entity interrupt so an already-inserted jack is reported at init:

```c
/* sound/soc/codecs/rt722-sdca.c:293 */
static void rt722_sdca_jack_init(struct rt722_sdca_priv *rt722)
{
	mutex_lock(&rt722->calibrate_mutex);
	if (rt722->hs_jack) {
		/* set SCP_SDCA_IntMask1[0]=1 */
		sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK1,
			SDW_SCP_SDCA_INTMASK_SDCA_0);
		/* set SCP_SDCA_IntMask2[0]=1 */
		sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK2,
			SDW_SCP_SDCA_INTMASK_SDCA_8);
		...
		/* set XU(et03h) & XU(et0Dh) to Not bypassed */
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_XU03,
				RT722_SDCA_CTL_SELECTED_MODE, 0), 0);
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_XU0D,
				RT722_SDCA_CTL_SELECTED_MODE, 0), 0);
		...
	}
	mutex_unlock(&rt722->calibrate_mutex);
}
```

The whole codec reduces to this one model. The controls, the DAPM power-domain widgets, the clock-source rate writes, and the jack-detection cross-point writes all address SDCA function entities through the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) space, and the three DAIs differ only in which function and data port their [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op selects, so adding a feature to the codec is a matter of naming a new entity and control rather than decoding a new register block.

### SDW_SDCA_CTL control-address bit layout

The [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) macro packs the function number, entity, control selector, control number, and channel into one 32-bit MBQ control address, splitting the entity and the control selector across the word so the macro recombines each operand from two shifts.

```
    SDW_SDCA_CTL(fun, ent, ctl, ch)  SDCA control address (32-bit MBQ)
    ──────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │0│P│0│ fun │e│csH│0│ cnoH│N│M│  ent[5:0] │csL  │ chH │ cnoL│chL│
          └─┴─┴─┴─────┴─┴───┴─┴─────┴─┴─┴───────────┴─────┴─────┴─────┴───┘

    P     = bit 30 Control Prefix (set by BIT(30))
    fun   = 24:22 Function Number[2:0]   e   = 21 Entity[6]
    csH   = 20:19 Control Selector[5:4]  cnoH = 17:15 Control Number[5:3]
    N     = 14 Next                      M   = 13 MBQ
    ent   = 12:7 Entity[5:0]             csL = 6:3 Control Selector[3:0]
    chH   = (channel high bits)          cnoL = 2:0 Control Number[2:0]
    chL   = (channel low bits)           bits 31, 25, 18 are 0
    (Entity[6] and the split Control Selector/Number recombine the operands)
```

### Codec object model across the SoundWire link

The [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) component presents three DAIs from [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) across four SoundWire data ports, each sharing [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246) to join its stream with [`sdw_stream_add_slave`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) and the jack hook [`rt722_sdca_set_jack_detect`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321), and every register access reaches hardware through [`rt722_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195) as an [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address into an SDCA function entity.

```
    rt722-sdca codec  (SoundWire peripheral 0x025d:0x722, SDCA)
    ──────────────────────────────────────────────────────────

    ASoC component  soc_sdca_dev_rt722
    ┌──────────────────────────────────────────────────────────┐
    │ controls (FU05/FU0F/FU06/FU1E/FU15 volume + switch)      │
    │ dapm_widgets + audio_map (PDE/FU/Mux + AIF endpoints)    │
    │ set_jack ─▶ rt722_sdca_set_jack_detect                   │
    │                                                          │
    │  rt722_sdca_dai[3]            ops ─▶ rt722_sdca_ops      │
    │ ┌──────────┬──────────┬──────────┐                       │
    │ │  aif1    │  aif2    │  aif3    │                       │
    │ └─────┬────┴─────┬────┴─────┬────┘                       │
    └───────┼──────────┼──────────┼────────────────────────────┘
            │          │          │   hw_params: sdw_stream_add_slave
        DP1 ▼ DP2      ▼ DP3      ▼ DP6
       headphone     speaker    DMIC x4
       + headset                (capture)
        mic cap
            │          │          │
            ▼          ▼          ▼
    regmap  rt722_sdca_regmap  (reg_bits 32, val_bits 16, MBQ)
    ┌──────────────────────────────────────────────────────────┐
    │ SDW_SDCA_CTL(func, entity, control, channel) addressing  │
    └───────┬───────────────┬───────────────┬──────────────────┘
            ▼               ▼               ▼
    FUNC_NUM_JACK_CODEC  FUNC_NUM_AMP   FUNC_NUM_MIC_ARRAY
       (0x01)              (0x04)          (0x02)
    CS01/CS11 FU05 FU0F  CS31 FU06 OT23  CS1F FU1E FU15 IT26
    PDE40 PDE12 GE49     PDE23           PDE2A
```
