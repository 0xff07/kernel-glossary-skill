# PDM audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

PDM (pulse-density modulation) is the wire format a digital microphone uses to send audio to the system, a single data line carrying a 1-bit stream clocked at a few megahertz where the local density of 1 bits tracks the analog signal amplitude, and a decimation filter downstream converts that oversampled bitstream into multi-bit PCM. ASoC names the protocol with [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33), which aliases [`SND_SOC_DAI_FORMAT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L156) (value 7) in the low nibble selected by [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f), the same field that selects I2S, DSP_A, or Left-Justified. On x86-64 ACPI platforms the microphones are wired to a DSP or PCH input rather than to a serial-audio codec, so the kernel never programs [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33) into a [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op for them; the PDM clock and decimation are configured inside the DSP through Sound Open Firmware, parameterised from the platform NHLT (Non HD Audio Link Table) firmware description, and ASoC sees only a capture back-end DAI named DMIC.

```
    PDM stereo capture: two mics on one data line, one DSP clock
    ───────────────────────────────────────────────────────────

    PDM_CLK   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌──
        ──────┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
              ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲
              L   R   L   R   L   R   L   R   L   R   L   R
            rise fall                (mic A drives on rising edge,
                                      mic B drives on falling edge)

    PDM_DATA  ┌───┐       ┌───────┐   ┌───┐           ┌───┐
        ──────┘   └───────┘       └───┘   └───────────┘   └───
              1   0   1   1   0   1   1   0   0   0   1   0
              └ high local density ┘   └ low local density ┘
                (signal near peak)       (signal near trough)

    decimation filter (in DSP / PCH)
        1-bit @ 2.4 MHz ──▶ low-pass + downsample ──▶ PCM 48 kHz S24/S32

    one PDM_CLK period yields one data bit; the analog level is the
    fraction of 1 bits over a sliding window, MSB has no per-sample word
```

## SUMMARY

PDM is a capture-direction microphone format, a one-way input path unlike the bidirectional I2S link, and the kernel touches it at two levels. At the ASoC protocol layer [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33) is one of the format codes a [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op can receive through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), encoded in the low nibble of the format word. At the platform layer the actual PDM mics on an x86-64 ACPI machine are wired to the DSP, and the DSP does the pulse-density-to-PCM decimation, so the format the host configures is the DSP DMIC interface rather than a codec serial port.

ASoC does not model a raw PDM link as a userspace-visible object; it models the microphones as a capture DAI named DMIC, and the PDM-to-PCM conversion happens below that DAI in the DSP or PCH. The generic [`dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c) codec is the smallest such representation, one capture-only DAI [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) with no register map, only an enable GPIO and a mode-switch delay. On a Sound Open Firmware Intel platform the per-controller PDM settings (which microphone of the stereo pair is enabled, its polarity, the data clock edge, the sampling skew) are carried in [`struct sof_ipc_dai_dmic_pdm_ctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L131) inside [`struct sof_ipc_dai_dmic_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L176), and the microphone count comes from the NHLT geometry read by [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29). A SoundDevice Class for Audio (SDCA) part such as the Realtek RT722 instead digitises its PDM mics internally and presents them over SoundWire as the four-channel capture DAI [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1285).

## SPECIFICATIONS

PDM is a serial-microphone signalling convention defined by microphone vendors rather than by a single ratified standard; the de facto reference is the common datasheet behaviour the kernel comments describe, a 1-bit data line clocked between roughly 1.0 and 3.2 MHz with two mics multiplexed on opposite clock edges. According to the comment on [`struct sof_ipc_dai_dmic_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L176), "The microphone clock needs to be usually about 50-80 times the used audio sample rate", which fixes the oversampling ratio the decimation filter reverses. On x86-64 ACPI the PDM endpoint count and channel geometry are described by the platform NHLT table, consumed by [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29), and the SOF DMIC IPC parameter block is defined by the Sound Open Firmware ABI.

## LINUX KERNEL

### Format code and the DAI format word (soc-dai.h, asoc.h)

- [`'\<SND_SOC_DAIFMT_PDM\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33): the ASoC protocol selector for PDM, an alias of [`SND_SOC_DAI_FORMAT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L156)
- [`'\<SND_SOC_DAI_FORMAT_PDM\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L156): the uapi constant 7, "Pulse density modulation", in the same enumeration as I2S (1) and AC97 (6)
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): 0x000f, the low nibble of the format word that holds the protocol code
- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): the wrapper that delivers a `SND_SOC_DAIFMT_*` word to the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, returning `-ENOTSUPP` when the op is absent

### Generic DMIC codec (codecs/dmic.c)

- [`'\<dmic_dai\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89): the single capture-only [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) that represents 1 to 8 PDM mics
- [`'dmic_dai_ops':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L52): the function pointer struct with only a [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op (a mode-switch delay on stop)
- [`'soc_dmic':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) with the DMIC AIF and DMic input widgets, no register map
- [`'\<dmic_dev_probe\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168): registers [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'\<struct dmic\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27): the codec private state, an enable GPIO, an optional vref regulator, a wakeup delay, and a mode-switch delay

### SOF Intel DMIC interface (sof/dai.h, sof/dai-intel.h)

- [`'\<enum sof_ipc_dai_type\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76): the DAI-type enumeration whose [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) member selects the PDM-microphone back end
- [`'\<struct sof_ipc_dai_dmic_params\>':'include/sound/sof/dai-intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L176): the global DMIC settings (PDM clock min/max, FIFO sample rate and word length, active controller count, the per-controller array)
- [`'\<struct sof_ipc_dai_dmic_pdm_ctrl\>':'include/sound/sof/dai-intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L131): the per-2ch-PDM-controller block with [`enable_mic_a`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L135)/[`enable_mic_b`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L136), [`polarity_mic_a`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L138)/[`polarity_mic_b`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L139), [`clk_edge`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L141), and [`skew`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L142)
- [`'\<struct sof_ipc_dai_config\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L96): the general DAI configuration message whose [`dmic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L112) union member carries the DMIC parameters to the DSP

### NHLT geometry and SDCA mic (intel-nhlt.c, rt722-sdca.c)

- [`'\<intel_nhlt_get_dmic_geo\>':'sound/hda/core/intel-nhlt.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29): walk the NHLT endpoints, find the DMIC link, and return the microphone-channel count
- [`'\<struct nhlt_acpi_table\>':'include/sound/intel-nhlt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78): the ACPI NHLT table header and endpoint descriptor array the DMIC geometry is read from
- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the DAI array whose `aif3` entry is the four-channel DMIC capture interface the part's PDM mics appear on over SoundWire

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface families ASoC supports, the layer at which the PDM format code is one option
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component model the generic DMIC codec follows
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM and back-end DAIs, the shape the SOF DMIC capture path takes
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the Intel multi-link controller that hosts the DMIC and SoundWire links on x86 ACPI platforms

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

PDM has no host-visible register block. The microphones are clocked and decimated inside the DSP or the PCH digital-microphone unit, and the host configures that unit through the SOF IPC message [`struct sof_ipc_dai_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L96) carrying [`struct sof_ipc_dai_dmic_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L176) rather than by writing PDM registers directly. The fields that stand in for a register map are the per-controller PDM settings in [`struct sof_ipc_dai_dmic_pdm_ctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L131), one block per stereo pair of microphones.

```
    sof_ipc_dai_dmic_pdm_ctrl (one per 2-channel PDM controller)
    ────────────────────────────────────────────────────────────

    id              PDM controller index (0 .. NUM_CTRL-1)
    enable_mic_a    1 = capture left mic  (driven on one clock edge)
    enable_mic_b    1 = capture right mic (driven on the other edge)
    polarity_mic_a  optionally invert mic A signal (0 or 1)
    polarity_mic_b  optionally invert mic B signal (0 or 1)
    clk_edge        swap which data clock edge samples (0 or 1)
    skew            shift sampling instant vs clock, 0 .. 15

    sof_ipc_dai_dmic_params (global, then pdm[SOF_DAI_INTEL_DMIC_NUM_CTRL])
    ──────────────────────────────────────────────────────────────────────

    pdmclk_min / pdmclk_max   PDM clock bounds in Hz (e.g. 1.0 .. 3.2 MHz)
    fifo_fs                   decimated PCM sample rate in Hz (8000..96000)
    fifo_bits                 decimated PCM word length (16 or 32)
    num_pdm_active            how many pdm[] controllers are enabled
```

The [`enable_mic_a`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L135) and [`enable_mic_b`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L136) fields are the firmware expression of the two-mics-on-one-line arrangement in the figure, one microphone of the pair selected per data-line edge, and [`clk_edge`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L141) swaps which edge samples which mic. The [`pdmclk_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L180)/[`pdmclk_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L181) pair bounds the oversampling clock and [`fifo_fs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L183) names the PCM rate the decimation filter produces, so the ratio between them is the decimation factor.

## DETAILS

### PDM is one protocol code in the DAI format word

The audio protocol a DAI runs is encoded in the low nibble of the `SND_SOC_DAIFMT_*` word, and [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33) is the value 7 in that nibble, defined as an alias of the uapi constant so topology files and machine drivers can name it:

```c
/* include/uapi/sound/asoc.h:150 */
#define SND_SOC_DAI_FORMAT_I2S          1 /* I2S mode */
#define SND_SOC_DAI_FORMAT_RIGHT_J      2 /* Right Justified mode */
#define SND_SOC_DAI_FORMAT_LEFT_J       3 /* Left Justified mode */
#define SND_SOC_DAI_FORMAT_DSP_A        4 /* L data MSB after FRM LRC */
#define SND_SOC_DAI_FORMAT_DSP_B        5 /* L data MSB during FRM LRC */
#define SND_SOC_DAI_FORMAT_AC97         6 /* AC97 */
#define SND_SOC_DAI_FORMAT_PDM          7 /* Pulse density modulation */
```

A codec that supported PDM as a serial protocol would receive [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33) in its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op through the wrapper, which delivers the word unchanged and treats an absent op as not-supported:

```c
/* sound/soc/soc-dai.c:194 */
int snd_soc_dai_set_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
	int ret = -ENOTSUPP;

	if (dai->driver->ops && dai->driver->ops->set_fmt)
		ret = dai->driver->ops->set_fmt(dai, fmt);

	return soc_dai_ret(dai, ret);
}
```

On an x86-64 ACPI machine the PDM microphones are not on a serial port the host programs this way; they are wired to the DSP, so the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) path is not where the PDM clock is set up. The DSP configuration carries an equivalent code, [`SOF_DAI_FMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L29), in the SOF DAI format word, mirroring the ASoC nibble on the firmware side.

```
    PDM = 7 in the FMT nibble of the SND_SOC_DAIFMT_* word
    ─────────────────────────────────────────────────────
    (SND_SOC_DAIFMT_FORMAT_MASK = 0x000f selects this nibble)

    bit         3   2   1   0
              ┌───┬───┬───┬───┐
    fmt word  │    FMT (3:0)  │
              └───────┬───────┘
                      │  value names one protocol:
                      ▼
         I2S=1  RIGHT_J=2  LEFT_J=3  DSP_A=4
         DSP_B=5  AC97=6  PDM=7  ◀── pulse-density modulation

    host set_fmt path is unused for PDM mics on x86 ACPI;
    the DSP side carries the mirror code SOF_DAI_FMT_PDM
```

### The DMIC DAI is the ASoC representation of the PDM mics

ASoC models the microphones as a capture DAI named DMIC, and the PDM-to-PCM conversion happens below that DAI. The generic [`dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c) codec is the smallest such representation, one capture-only DAI that declares 1 to 8 channels of decimated PCM and carries no PDM-level register state:

```c
/* sound/soc/codecs/dmic.c:89 */
static struct snd_soc_dai_driver dmic_dai = {
	.name = "dmic-hifi",
	.capture = {
		.stream_name = "Capture",
		.channels_min = 1,
		.channels_max = 8,
		.rates = SNDRV_PCM_RATE_CONTINUOUS,
		.formats = SNDRV_PCM_FMTBIT_S32_LE
			| SNDRV_PCM_FMTBIT_S24_LE
			| SNDRV_PCM_FMTBIT_S16_LE
			| SNDRV_PCM_FMTBIT_DSD_U8
			| SNDRV_PCM_FMTBIT_DSD_U16_LE
			| SNDRV_PCM_FMTBIT_DSD_U32_LE
			| SNDRV_PCM_FMTBIT_DSD_U16_BE
			| SNDRV_PCM_FMTBIT_DSD_U32_BE,
	},
	.ops    = &dmic_dai_ops,
};
```

The declared formats are the decimated PCM word the DAI delivers (S16/S24/S32 little-endian) plus the DSD (Direct Stream Digital) 1-bit formats for the case where the raw oversampled stream is passed through undecimated. The DAI has only a [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capability and no playback, which marks PDM as a microphone-input format in the ASoC model rather than a bidirectional link like I2S. The function pointer struct fills in only a [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, which exists only to honour a mode-switch settling delay when the stream stops:

```c
/* sound/soc/codecs/dmic.c:35 */
static int dmic_daiops_trigger(struct snd_pcm_substream *substream,
			       int cmd, struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct dmic *dmic = snd_soc_component_get_drvdata(component);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_STOP:
		if (dmic->modeswitch_delay)
			mdelay(dmic->modeswitch_delay);

		break;
	}

	return 0;
}

static const struct snd_soc_dai_ops dmic_dai_ops = {
	.trigger	= dmic_daiops_trigger,
};
```

The codec private state in [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27) is just an enable line, an optional voltage reference, and two timing delays, with no PDM clock divider or decimation control because those are not in the host's hands:

```c
/* sound/soc/codecs/dmic.c:27 */
struct dmic {
	struct gpio_desc *gpio_en;
	struct regulator *vref;
	int wakeup_delay;
	/* Delay after DMIC mode switch */
	int modeswitch_delay;
};
```

The component is registered with no register map at all, only the DAPM widgets that route the DMic input into the capture AIF, by [`dmic_dev_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168):

```c
/* sound/soc/codecs/dmic.c:168 */
static int dmic_dev_probe(struct platform_device *pdev)
{
	int err;
	u32 chans;
	struct snd_soc_dai_driver *dai_drv = &dmic_dai;

	if (pdev->dev.of_node) {
		err = of_property_read_u32(pdev->dev.of_node, "num-channels", &chans);
		if (err && (err != -EINVAL))
			return err;

		if (!err) {
			if (chans < 1 || chans > 8)
				return -EINVAL;

			dai_drv = devm_kzalloc(&pdev->dev, sizeof(*dai_drv), GFP_KERNEL);
			if (!dai_drv)
				return -ENOMEM;

			memcpy(dai_drv, &dmic_dai, sizeof(*dai_drv));
			dai_drv->capture.channels_max = chans;
		}
	}

	return devm_snd_soc_register_component(&pdev->dev,
			&soc_dmic, dai_drv, 1);
}
```

The probe takes a copy of [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) and narrows its `channels_max` when an `of` `num-channels` count is present, capping the PDM-mic count at 8, then registers it against [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157). The DMIC DAI is therefore the ASoC representation, and the PDM microphone is the physical interface it stands for; everything specific to PDM (the clock rate, the edge multiplexing, the decimation) is handled below the DAI.

### The firmware block expresses the PDM wire format

On an x86 ACPI machine the PDM settings travel to the DSP in [`struct sof_ipc_dai_dmic_pdm_ctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L131), one block per stereo PDM pair. Its fields are the firmware form of exactly the wire arrangement the figure shows, the two mics that share one data line and the clock edge each is sampled on:

```c
/* include/sound/sof/dai-intel.h:131 */
struct sof_ipc_dai_dmic_pdm_ctrl {
	struct sof_ipc_hdr hdr;
	uint16_t id;		/**< PDM controller ID */

	uint16_t enable_mic_a;	/**< Use A (left) channel mic (0 or 1)*/
	uint16_t enable_mic_b;	/**< Use B (right) channel mic (0 or 1)*/

	uint16_t polarity_mic_a; /**< Optionally invert mic A signal (0 or 1) */
	uint16_t polarity_mic_b; /**< Optionally invert mic B signal (0 or 1) */

	uint16_t clk_edge;	/**< Optionally swap data clock edge (0 or 1) */
	uint16_t skew;		/**< Adjust PDM data sampling vs. clock (0..15) */

	uint16_t reserved[3];	/**< Make sure the total size is 4 bytes aligned */
} __packed;
```

According to the comment on [`clk_edge`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L141), the data clock edge is swapped "If the microphones in a stereo pair do not appear in captured stream in desired order due to board schematics choises", which is the firmware control over the rising-edge/falling-edge multiplexing in the figure, and [`skew`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L142) shifts the sampling instant "If PDM bit errors are seen in capture (poor quality)". The global block around it sets the oversampling clock and the decimated rate:

```c
/* include/sound/sof/dai-intel.h:176 */
struct sof_ipc_dai_dmic_params {
	struct sof_ipc_hdr hdr;
	uint32_t driver_ipc_version;	/**< Version (1..N) */

	uint32_t pdmclk_min;	/**< Minimum microphone clock in Hz (100000..N) */
	uint32_t pdmclk_max;	/**< Maximum microphone clock in Hz (min...N) */

	uint32_t fifo_fs;	/**< FIFO sample rate in Hz (8000..96000) */
	...
	uint32_t num_pdm_active; /**< Number of active pdm controllers. */
	...
	struct sof_ipc_dai_dmic_pdm_ctrl pdm[SOF_DAI_INTEL_DMIC_NUM_CTRL];
} __packed;
```

The [`pdmclk_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L180)/[`pdmclk_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L181) pair is the oversampling clock the DSP runs on the PDM_CLK line, and [`fifo_fs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L183) is the PCM rate after decimation, so their ratio is the decimation factor. Which back end a DAI config addresses is named by [`enum sof_ipc_dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76), and the PDM microphones are the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) member:

```c
/* include/sound/sof/dai.h:75 */
/** \brief Types of DAI */
enum sof_ipc_dai_type {
	SOF_DAI_INTEL_NONE = 0,		/**< None */
	SOF_DAI_INTEL_SSP,		/**< Intel SSP */
	SOF_DAI_INTEL_DMIC,		/**< Intel DMIC */
	SOF_DAI_INTEL_HDA,		/**< Intel HD/A */
	SOF_DAI_INTEL_ALH,		/**< Intel ALH  */
	...
	SOF_DAI_IMX_MICFIL,		/** < i.MX MICFIL PDM */
	SOF_DAI_AMD_SDW,		/**< AMD ACP SDW */
};
```

The whole DMIC parameter block travels to the DSP inside the [`dmic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L112) union member of [`struct sof_ipc_dai_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L96), the general DAI message whose [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) field carries the [`enum sof_ipc_dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76) value and whose [`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L102) field carries the `SOF_DAI_FMT_` protocol code:

```c
/* include/sound/sof/dai.h:95 */
/* general purpose DAI configuration */
struct sof_ipc_dai_config {
	struct sof_ipc_cmd_hdr hdr;
	uint32_t type;		/**< DAI type - enum sof_ipc_dai_type */
	uint32_t dai_index;	/**< index of this type dai */

	/* physical protocol and clocking */
	uint16_t format;	/**< SOF_DAI_FMT_ */
	uint8_t group_id;	/**< group ID, 0 means no group (ABI 3.17) */
	uint8_t flags;		/**< SOF_DAI_CONFIG_FLAGS_ (ABI 3.19) */

	/* reserved for future use */
	uint32_t reserved[8];

	/* HW specific data */
	union {
		struct sof_ipc_dai_ssp_params ssp;
		struct sof_ipc_dai_dmic_params dmic;
		struct sof_ipc_dai_hda_params hda;
		...
		struct sof_ipc_dai_acp_sdw_params acp_sdw;
	};
} __packed;
```

When [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) is [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) the active union arm is [`dmic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L112), the [`struct sof_ipc_dai_dmic_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L176) shown above with its per-controller PDM array; the host never touches the bitstream, and the DSP produces decimated PCM that flows up the capture DAI.

```
    DMIC params reach the DSP nested in a tagged union
    ──────────────────────────────────────────────────
    (type selects the union arm; dmic carries the PDM array)

    struct sof_ipc_dai_config
    ┌──────────────────────────────────────────────────┐
    │ type   = SOF_DAI_INTEL_DMIC ┐ (tag)              │
    │ format = SOF_DAI_FMT_PDM    │                    │
    │ union {                     │                    │
    │   ssp  ...                  ▼                    │
    │   dmic : sof_ipc_dai_dmic_params ─────────┐      │
    │   hda  ...                                │      │
    │ }                                         │      │
    └───────────────────────────────────────────┼──────┘
                                                ▼

    struct sof_ipc_dai_dmic_params
    ┌──────────────────────────────────────────────────┐
    │ pdmclk_min / pdmclk_max   fifo_fs   fifo_bits    │
    │ num_pdm_active                                   │
    │ pdm[SOF_DAI_INTEL_DMIC_NUM_CTRL] ───┐            │
    └─────────────────────────────────────┼────────────┘
                                          ▼

    struct sof_ipc_dai_dmic_pdm_ctrl  (one per stereo pair)
    ┌──────────────────────────────────────────────────┐
    │ id  enable_mic_a/b  polarity_mic_a/b             │
    │ clk_edge  skew                                   │
    └──────────────────────────────────────────────────┘
```

### NHLT geometry supplies the PDM microphone count

The microphone-channel count those controllers feed comes from the platform NHLT geometry that [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) reads from the ACPI [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78). The table is an ACPI header followed by a variable-length endpoint array:

```c
/* include/sound/intel-nhlt.h:78 */
struct nhlt_acpi_table {
	struct acpi_table_header header;
	u8 endpoint_count;
	struct nhlt_endpoint desc[];
} __packed;
```

The geometry walk iterates the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L81) endpoints, skips any whose `linktype` is not `NHLT_LINK_DMIC`, and returns the microphone count the DMIC link describes:

```c
/* sound/hda/core/intel-nhlt.c:29 */
int intel_nhlt_get_dmic_geo(struct device *dev, struct nhlt_acpi_table *nhlt)
{
	struct nhlt_endpoint *epnt;
	struct nhlt_dmic_array_config *cfg;
	...
	for (j = 0, epnt = nhlt->desc; j < nhlt->endpoint_count; j++,
	     epnt = (struct nhlt_endpoint *)((u8 *)epnt + epnt->length)) {

		if (epnt->linktype != NHLT_LINK_DMIC)
			continue;
		...
		switch (cfg->array_type) {
		case NHLT_MIC_ARRAY_2CH_SMALL:
		case NHLT_MIC_ARRAY_2CH_BIG:
			dmic_geo = MIC_ARRAY_2CH;
			break;

		case NHLT_MIC_ARRAY_4CH_1ST_GEOM:
		case NHLT_MIC_ARRAY_4CH_L_SHAPED:
		case NHLT_MIC_ARRAY_4CH_2ND_GEOM:
			dmic_geo = MIC_ARRAY_4CH;
			break;
		...
		}
		...
	}

	return dmic_geo;
}
```

A two-microphone array (one [`struct sof_ipc_dai_dmic_pdm_ctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai-intel.h#L131) worth of mics, both on one PDM data line) reports `MIC_ARRAY_2CH`, a four-microphone array `MIC_ARRAY_4CH`; that count is how many decimated PCM channels the capture DAI carries, the host-visible result of the PDM-to-PCM conversion the DSP runs below the DAI.

```
    intel_nhlt_get_dmic_geo: array_type maps to mic count
    ─────────────────────────────────────────────────────
    (walk desc[]; skip linktype != NHLT_LINK_DMIC; then:)

    cfg->array_type                          dmic_geo
    ┌──────────────────────────────────┐     ┌──────────────┐
    │ NHLT_MIC_ARRAY_2CH_SMALL         │ ──▶ │ MIC_ARRAY_2CH│
    │ NHLT_MIC_ARRAY_2CH_BIG           │     │   (2 mics)   │
    └──────────────────────────────────┘     └──────────────┘
    ┌──────────────────────────────────┐     ┌──────────────┐
    │ NHLT_MIC_ARRAY_4CH_1ST_GEOM      │ ──▶ │ MIC_ARRAY_4CH│
    │ NHLT_MIC_ARRAY_4CH_L_SHAPED      │     │   (4 mics)   │
    │ NHLT_MIC_ARRAY_4CH_2ND_GEOM      │     └──────────────┘
    └──────────────────────────────────┘
    the returned count = decimated PCM channels on the DAI
```

### SDCA microphones reach the system over SoundWire

A SoundDevice Class for Audio part takes a different route. The microphones are still PDM internally, but the codec digitises and decimates them and presents PCM over SoundWire, so the host sees a SoundWire capture DAI rather than a DMIC link or a raw PDM line. The Realtek RT722 publishes three SoundWire DAIs in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253), the headphone/headset `aif1`, the speaker `aif2`, and the microphone `aif3`:

```c
/* sound/soc/codecs/rt722-sdca.c:1253 */
static struct snd_soc_dai_driver rt722_sdca_dai[] = {
	{
		.name = "rt722-sdca-aif1",
		.id = RT722_AIF1,
		...
	},
	{
		.name = "rt722-sdca-aif2",
		.id = RT722_AIF2,
		...
	},
	...
};
```

The microphone interface is the four-channel `aif3` entry of that array:

```c
/* sound/soc/codecs/rt722-sdca.c:1285 */
	{
		.name = "rt722-sdca-aif3",
		.id = RT722_AIF3,
		.capture = {
			.stream_name = "DP6 DMic Capture",
			.channels_min = 1,
			.channels_max = 4,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.ops = &rt722_sdca_ops,
	}
```

The capture stream is named "DP6 DMic Capture" and routes from a DAPM AIF output widget on SoundWire data port 6:

```c
/* sound/soc/codecs/rt722-sdca.c:1040 */
	SND_SOC_DAPM_AIF_OUT("DP6TX", "DP6 DMic Capture", 0, SND_SOC_NOPM, 0, 0),
```

The microphones are PDM at the silicon level, but the ASoC representation is a SoundWire capture DAI, the same principle as the DMIC case, the PDM mic the physical interface and the DAI the representation, just transported over SoundWire and already decimated to PCM inside the SDCA part. On an x86-64 ACPI laptop both paths coexist, the SOF DMIC back end for mics wired directly to the PCH and the SDCA SoundWire DAI for mics behind an SDCA codec, and in both cases the PDM signalling and its decimation are below the DAI the host configures.

```
    Two ways PDM mics reach the host, both PDM below the DAI
    ────────────────────────────────────────────────────────

                     PDM microphones
                  (1-bit oversampled)
              ┌───────────┴───────────┐
              ▼                       ▼
     wired to PCH/DSP        inside an SDCA codec
              │                       │
     SOF DMIC back end       digitise + decimate
     decimates in DSP        then SoundWire DP6
              │                       │
              ▼                       ▼
     DMIC capture DAI        rt722-sdca-aif3 DAI
     (dmic-hifi, 1..8ch)     (DP6 DMic Capture, 4ch)
              └───────────┬───────────┘
                          ▼
             host sees a capture DAI of decimated PCM
```
