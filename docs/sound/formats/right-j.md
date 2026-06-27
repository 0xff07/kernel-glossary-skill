# Right-justified audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The right-justified serial-audio format carries one stereo sample per LRCLK period and places each channel's sample so its least-significant bit lands on the trailing edge of the LRCLK half-period that frames it, sending the most-significant bit first. ASoC names this format [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28), value 2 within the four-bit field [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f), and a machine driver requests it through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which forwards the value to the codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback. Because the sample is anchored at the right edge, the bit at which the most-significant bit begins is a function of the word length, so a codec that supports right-justified mode reads the sample width in its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback to position the bits. The Conexant [`cx2072x`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c) codec, a platform-agnostic I2C/I2S part driven on x86 ACPI machines, is the worked example. Its [`cx2072x_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L996) accepts [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) and caches it, and [`cx2072x_config_i2spcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L668) computes the in-slot bit position from the cached sample and frame size.

```
    Right-justified stereo frame, MSB first
    (16-bit sample in a 16-bit half-period; LSB on the trailing LRCLK edge)
    ──────────────────────────────────────────────────────────────────────

            ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
    BCLK  ──┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └──

            ┌───────────────────────────┐
    LRCLK ──┘      left  channel        └───── right channel ─────
            ◀ MSB ▶ ◀  ...  ▶ ◀ LSB ▶   ◀ MSB ▶ ◀ ... ▶ ◀ LSB ▶
    SD    ──◀ b15 ▶─◀ b14.. ▶─◀  b0 ▶───◀ b15 ▶─◀ ... ▶─◀  b0 ▶──
                                    ▲                          ▲
                          LSB at right edge          LSB at right edge
                          of left half-period        of right half-period

    The MSB (b15) starts late inside the half-period; with a 24-bit
    sample in the same 16-bit half-period the MSB would start even
    later, because the LSB stays pinned to the trailing edge.
```

## SUMMARY

Right-justified, also spelled LSB-justified and aliased as [`SND_SOC_DAIFMT_LSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L37), is one of the serial-audio protocols encoded in the low four bits of the format word a machine driver hands to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194). The protocol field [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) selects among [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) (value 1), [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) (value 2), [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) (value 3), and the [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) family. In the right-justified frame the LRCLK level selects the channel, and within each half-period the sample is shifted so its last bit coincides with the level transition, most-significant bit first.

A machine driver records the protocol in the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and at card bring-up [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) passes it to [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which calls [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) on every codec and CPU DAI. A right-justified codec cannot fully place the bits from [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) alone, because the most-significant-bit start position depends on the sample width that is not known until [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294), so [`cx2072x_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L996) caches the format and [`cx2072x_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L902) recomputes the slot layout once it has the width.

## SPECIFICATIONS

Right-justified serial audio is a de-facto interface convention rather than a single published standard; it is the LSB-justified mode of the inter-IC sound family that surrounds the Philips I2S specification, and individual codec datasheets define the exact clock edges. The ASoC software encoding is fixed in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h), where [`SND_SOC_DAI_FORMAT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L151) is value 2 with the comment "Right Justified mode", and the kernel-facing alias [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) is defined in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h).

## LINUX KERNEL

### Format constants (asoc.h, soc-dai.h)

- [`'\<SND_SOC_DAI_FORMAT_RIGHT_J\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L151): the userspace/topology value 2 for right-justified mode
- [`'\<SND_SOC_DAIFMT_RIGHT_J\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28): the kernel alias a codec switch compares against
- [`'\<SND_SOC_DAIFMT_LSB\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L37): the alternate name for the same value, naming the LSB-justified convention
- [`'\<SND_SOC_DAIFMT_LEFT_J\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L152): value 3, the MSB-justified contrast where the sample begins at the LRCLK edge
- [`'\<SND_SOC_DAIFMT_I2S\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150): value 1, the most-significant bit delayed one BCLK after the LRCLK edge
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): the 0x000f field that isolates the protocol bits from the clock and polarity bits

### Format application path (soc-dai.c, soc-core.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): the wrapper that calls the DAI [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op and returns `-ENOTSUPP` when none is present
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): applies one format to every codec and CPU DAI of a runtime, flipping the clock-provider role for the CPU end
- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): the bring-up site that reads [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) from the link and calls the setter
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the machine-driver link description; its [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field carries the static format
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct whose [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) and [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) members a codec fills in

### Word-length helpers (soc-utils.c, pcm_misc.c)

- [`'\<snd_soc_params_to_frame_size\>':'sound/soc/soc-utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L51): turn the negotiated params into the total bits per frame
- [`'\<snd_soc_calc_frame_size\>':'sound/soc/soc-utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L45): multiply sample size, channel count, and slot count
- [`'\<snd_pcm_format_width\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335): return a format's significant-bit count, the sample width the right-justified placement depends on

### cx2072x worked example (codecs/cx2072x.c)

- [`'\<cx2072x_set_dai_fmt\>':'sound/soc/codecs/cx2072x.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L996): the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op accepting [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28), and [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), then caching the word
- [`'\<cx2072x_hw_params\>':'sound/soc/codecs/cx2072x.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L902): read [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347) into the cached sample size and frame size, then reconfigure the port
- [`'\<cx2072x_config_i2spcm\>':'sound/soc/codecs/cx2072x.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L668): build the serial-port register set, computing the right-channel slot and pause position from the frame and sample size
- [`'soc_codec_cx2072x_dai':'sound/soc/codecs/cx2072x.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L1554): the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array declaring the cx2072x-hifi interface
- [`'cx2072x_dai_ops':'sound/soc/codecs/cx2072x.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L1528): the function pointer struct wiring [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) and [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294)

### Other codec set_fmt examples

- [`'\<wm8731_set_dai_fmt\>':'sound/soc/codecs/wm8731.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8731.c#L406) / [`'\<wm8731_hw_params\>':'sound/soc/codecs/wm8731.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8731.c#L313): a single-register codec whose format case leaves the IFACE format bits at 0 for right-justify and whose width bits are set in [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294)
- [`'\<wm8962_set_dai_fmt\>':'sound/soc/codecs/wm8962.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748) / [`'\<wm8962_hw_params\>':'sound/soc/codecs/wm8962.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2647): the same split, with the audio-interface word-length field set from [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347)
- [`'\<es8326_set_dai_fmt\>':'sound/soc/codecs/es8326.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/es8326.c#L509): a codec that rejects [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) with `-EINVAL`, showing the format is opt-in per part

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families, including the I2S group that right-justify belongs to
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the BCLK and LRCLK relationship the frame figure plots
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec DAI driver and its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The cx2072x serial port is configured through a block of I2S/PCM control registers, and the right-justified placement is encoded in the per-channel slot and word-size fields of [`CX2072X_I2SPCM_CONTROL1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.h) together with the pause fields of [`CX2072X_I2SPCM_CONTROL6`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.h). The format selector that [`cx2072x_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L996) records and the width that [`cx2072x_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L902) supplies converge in [`cx2072x_config_i2spcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L668), which writes those registers.

```
    cx2072x I2SPCM_CONTROL1 fields used for slot placement
    (one slot is BITS_PER_SLOT = 8 bits wide)
    ──────────────────────────────────────────────────────────────────

    field            set by config_i2spcm           meaning
    ┌──────────────┬──────────────────────────────┬───────────────────┐
    │ rx_sa_size   │ sample_size / 8 - 1          │ sample bits / 8   │
    │ rx_frm_len   │ frame_len / 8 - 1            │ frame bits / 8    │
    │ rx_ws_wid    │ pulse_len - 1                │ LRCLK high width  │
    │ rx_slot_2    │ (frame_len / 2) / 8          │ right-channel slot│
    └──────────────┴──────────────────────────────┴───────────────────┘

    The right-channel slot and the right-pause interval are derived from
    frame_len / 2, so a wider frame shifts where the right sample begins,
    while the left sample starts at slot 0. The same fields exist on the
    tx side (tx_sa_size, tx_frm_len, tx_ws_wid, tx_slot_2), copied from rx.
```

The slot arithmetic is a function of [`BITS_PER_SLOT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L34), defined as 8 in [`cx2072x.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c), so the register values move with the sample and frame width, which is the concrete reason the right-justified layout cannot be fixed before [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294).

## DETAILS

### The format value and the protocol field

The four serial-audio protocols share one four-bit field. [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) is 0x000f, and each protocol is a small integer the kernel aliases from the topology header:

```c
/* include/uapi/sound/asoc.h:150 */
#define SND_SOC_DAI_FORMAT_I2S		1 /* I2S mode */
#define SND_SOC_DAI_FORMAT_RIGHT_J	2 /* Right Justified mode */
#define SND_SOC_DAI_FORMAT_LEFT_J	3 /* Left Justified mode */
#define SND_SOC_DAI_FORMAT_DSP_A	4 /* L data MSB after FRM LRC */
#define SND_SOC_DAI_FORMAT_DSP_B	5 /* L data MSB during FRM LRC */
#define SND_SOC_DAI_FORMAT_AC97		6 /* AC97 */
#define SND_SOC_DAI_FORMAT_PDM		7 /* Pulse density modulation */
```

The kernel-facing names in [`soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h) point at those values, and the file also defines the MSB/LSB aliases that name the justification directly:

```c
/* include/sound/soc-dai.h:36 */
/* left and right justified also known as MSB and LSB respectively */
#define SND_SOC_DAIFMT_MSB		SND_SOC_DAIFMT_LEFT_J
#define SND_SOC_DAIFMT_LSB		SND_SOC_DAIFMT_RIGHT_J
```

The name [`SND_SOC_DAIFMT_LSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L37) restates the defining property of the format, the sample's least-significant bit is the anchored bit, and [`SND_SOC_DAIFMT_MSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36) names the opposite anchor used by [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29).

```
    FMT nibble values and the MSB/LSB justification aliases
    ───────────────────────────────────────────────────────
    (SND_SOC_DAIFMT_FORMAT_MASK = 0x000f selects this nibble)

    bit         3   2   1   0
              ┌───┬───┬───┬───┐
    fmt word  │    FMT (3:0)  │
              └───────┬───────┘
                      │
        ┌───────────┬─┴──────────┬───────────────┐
        ▼           ▼            ▼               ▼
        I2S = 1     RIGHT_J=2    LEFT_J=3        DSP_A=4 / DSP_B=5
                      │            │
                      ▼            ▼
                  ..._LSB      ..._MSB
                (LSB-anchored) (MSB-anchored)
```

### Right-justification depends on the word length

In a right-justified frame the LSB is pinned to the trailing edge of the LRCLK half-period and the bits run MSB first toward that edge, so the number of idle BCLK cycles before the MSB is the half-period length minus the sample width. A 16-bit sample inside a 16-bit half-period fills the half-period exactly and the MSB starts at the first BCLK after the level transition. A 24-bit sample inside a 32-bit half-period leaves eight leading idle bits, and a 16-bit sample inside the same 32-bit half-period leaves sixteen. The LSB position is fixed while the MSB position floats with the width, which is why the codec must know the width to drive the bits. [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) anchors the MSB at the level transition instead, so its leading edge is fixed and its trailing idle bits float, and [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) places the MSB one BCLK after the transition with the sample straddling the LRCLK edge.

The kernel makes the width available where it is needed. [`snd_soc_params_to_frame_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L51) derives the total frame bits from the sample width and channel count, calling [`snd_pcm_format_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335) for the per-sample bit count:

```c
/* sound/soc/soc-utils.c:51 */
int snd_soc_params_to_frame_size(const struct snd_pcm_hw_params *params)
{
	int sample_size;

	sample_size = snd_pcm_format_width(params_format(params));
	if (sample_size < 0)
		return sample_size;

	return snd_soc_calc_frame_size(sample_size, params_channels(params),
				       1);
}
```

[`snd_soc_calc_frame_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L45) is the product the codec needs, and the right-channel slot is one half of it:

```c
/* sound/soc/soc-utils.c:45 */
int snd_soc_calc_frame_size(int sample_size, int channels, int tdm_slots)
{
	return sample_size * channels * tdm_slots;
}
```

Halving that product gives the per-channel window the picture plots, where b0 stays pinned to the trailing edge and a narrower sample pushes its MSB later behind more idle BCLKs:

```
    Right-justified: idle bits before MSB = half-period - sample width
    ──────────────────────────────────────────────────────────────────
    (one 32-bit half-period; LSB b0 pinned to the trailing edge; bits
     run MSB first toward it, so a narrower sample idles longer first)

                32-bit half-period (one channel)        trailing edge
                ◀─────────────────────────────────────────────────┐
                                                                  ▲ b0

    24-bit              ┌────┬───────────────────────────────┬────┐
    sample      ░░░░░░░░│MSB │        b22 ........ b1        │ b0 │
                ◀──────▶ 8 idle BCLKs before MSB

    16-bit                      ┌────┬───────────────────────┬────┐
    sample      ░░░░░░░░░░░░░░░░│MSB │      b14 .... b1      │ b0 │
                ◀──────────────▶ 16 idle BCLKs before MSB
```

### snd_soc_dai_set_fmt dispatches to the codec op

A machine driver does not touch codec registers; it names a format and the core delivers it through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which defaults to `-ENOTSUPP` so a DAI with no format op is reported as not supporting the request rather than silently succeeding:

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

For a statically configured card the machine driver places the protocol in [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749), and [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) hands it to [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which applies it to every codec DAI and then to each CPU DAI with the clock-provider role flipped. An `-ENOTSUPP` return from one DAI is tolerated, so a codec that does not implement right-justify does not fail the whole card.

### The link carries the static format in dai_fmt

A machine driver names its CPU and codec ends and the static protocol in one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). The [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field is where a board that wants right-justified audio records [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) together with its clock and inversion bits, leaving the per-codec register programming to the core path below:

```c
/* include/sound/soc.h:749 */
	unsigned int dai_fmt;           /* format to set on init */
```

### soc_init_pcm_runtime applies the link format at bring-up

Card bring-up walks each runtime through [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512), which reads the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) and passes it to [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) before any PCM is created, so a right-justified link is programmed into the codec once at probe rather than per stream:

```c
/* sound/soc/soc-core.c:1512 */
static int soc_init_pcm_runtime(struct snd_soc_card *card,
				struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *cpu_dai = snd_soc_rtd_to_cpu(rtd, 0);
	int ret;

	/* do machine specific initialization */
	ret = snd_soc_link_init(rtd);
	if (ret < 0)
		return ret;

	snd_soc_runtime_get_dai_fmt(rtd);
	ret = snd_soc_runtime_set_dai_fmt(rtd, dai_link->dai_fmt);
	if (ret)
		goto err;
	...
}
```

### snd_soc_runtime_set_dai_fmt fans the format out to every DAI

[`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) is the fan-out. It calls [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) on each codec DAI with the link format, then flips the clock-provider role and repeats for each CPU DAI, so the same [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) word reaches every codec [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op. A return that is neither 0 nor `-ENOTSUPP` aborts, but a codec without a format op is skipped:

```c
/* sound/soc/soc-core.c:1459 */
int snd_soc_runtime_set_dai_fmt(struct snd_soc_pcm_runtime *rtd,
				unsigned int dai_fmt)
{
	struct snd_soc_dai *cpu_dai;
	struct snd_soc_dai *codec_dai;
	unsigned int ext_fmt;
	unsigned int i;
	int ret;

	if (!dai_fmt)
		return 0;
	...
	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		ext_fmt = rtd->dai_link->codecs[i].ext_fmt;
		ret = snd_soc_dai_set_fmt(codec_dai, dai_fmt | ext_fmt);
		if (ret != 0 && ret != -ENOTSUPP)
			return ret;
	}

	/* Flip the polarity for the "CPU" end of link */
	/* Will effect only for 4. SND_SOC_DAIFMT_CLOCK_PROVIDER */
	dai_fmt = snd_soc_daifmt_clock_provider_flipped(dai_fmt);

	for_each_rtd_cpu_dais(rtd, i, cpu_dai) {
		ext_fmt = rtd->dai_link->cpus[i].ext_fmt;
		ret = snd_soc_dai_set_fmt(cpu_dai, dai_fmt | ext_fmt);
		if (ret != 0 && ret != -ENOTSUPP)
			return ret;
	}

	return 0;
}
```

The two loops become the two branches the tree draws, the codec end taking the word as-is and the CPU end taking it after the provider-role flip, every DAI reached through the format helper:

```
    snd_soc_runtime_set_dai_fmt fans one word out to every DAI
    ──────────────────────────────────────────────────────────
    (link dai_fmt sent to each DAI; CPU end gets its provider
     role flipped by snd_soc_daifmt_clock_provider_flipped)

                    dai_link->dai_fmt
                    (SND_SOC_DAIFMT_RIGHT_J)
                              │
                  snd_soc_runtime_set_dai_fmt
                              │
               ┌──────────────┴────────────────┐
               ▼                               ▼
           codec DAIs                       CPU DAIs
         (fmt word as-is)                (provider flipped)
               │                               │
       ┌───────┼───────┐               ┌───────┴───────┐
       ▼       ▼       ▼               ▼       ▼       ▼
      codec0 codec1   ...             cpu0   cpu1     ...
    each reached through snd_soc_dai_set_fmt to its set_fmt op
    (-ENOTSUPP from a DAI with no set_fmt op is tolerated)
```

### A codec set_fmt switch that supports RIGHT_J

A platform-agnostic codec implements its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op as a switch over [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135). [`cx2072x_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L996) validates the clock role, the protocol, and the polarity, accepts [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) alongside [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) and [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), and stores the whole word rather than programming registers, because the bit placement still needs the width:

```c
/* sound/soc/codecs/cx2072x.c:996 */
static int cx2072x_set_dai_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
	struct snd_soc_component *codec = dai->component;
	struct cx2072x_priv *cx2072x = snd_soc_component_get_drvdata(codec);
	struct device *dev = codec->dev;
	...
	/* set format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
	case SND_SOC_DAIFMT_RIGHT_J:
	case SND_SOC_DAIFMT_LEFT_J:
		break;

	default:
		dev_err(dev, "Unsupported DAI format\n");
		return -EINVAL;
	}
	...
	cx2072x->dai_fmt = fmt;
	return 0;
}
```

The codec advertises the support in its DAI driver array. [`soc_codec_cx2072x_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L1554) declares the cx2072x-hifi interface and points it at the function pointer struct [`cx2072x_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L1528):

```c
/* sound/soc/codecs/cx2072x.c:1528 */
static const struct snd_soc_dai_ops cx2072x_dai_ops = {
	.set_sysclk = cx2072x_set_dai_sysclk,
	.set_fmt = cx2072x_set_dai_fmt,
	.hw_params = cx2072x_hw_params,
	.set_bclk_ratio = cx2072x_set_dai_bclk_ratio,
};
```

### hw_params supplies the width and places the bits

The placement is finished in [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294). [`cx2072x_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L902) reads the sample width with [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347) and the frame size with [`snd_soc_params_to_frame_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L51), caches both, and calls [`cx2072x_config_i2spcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L668) so the new width takes effect:

```c
/* sound/soc/codecs/cx2072x.c:902 */
static int cx2072x_hw_params(struct snd_pcm_substream *substream,
			     struct snd_pcm_hw_params *params,
			     struct snd_soc_dai *dai)
{
	...
	sample_size = params_width(params);
	if (sample_size < 0)
		return sample_size;

	frame_size = snd_soc_params_to_frame_size(params);
	if (frame_size < 0)
		return frame_size;
	...
	cx2072x->frame_size = frame_size;
	cx2072x->sample_size = sample_size;
	...
	if (cx2072x->i2spcm_changed) {
		cx2072x_config_i2spcm(cx2072x);
		cx2072x->i2spcm_changed = false;
	}

	return 0;
}
```

[`cx2072x_config_i2spcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cx2072x.c#L668) reads the cached format and selects the slot geometry. For [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) it sets no one-bit delay, which separates it from [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), where the delay is set, while the half-period pulse length is the same:

```c
/* sound/soc/codecs/cx2072x.c:725 */
	/* set format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		is_i2s = 1;
		has_one_bit_delay = 1;
		pulse_len = frame_len / 2;
		break;

	case SND_SOC_DAIFMT_RIGHT_J:
		is_i2s = 1;
		pulse_len = frame_len / 2;
		break;

	case SND_SOC_DAIFMT_LEFT_J:
		is_i2s = 1;
		pulse_len = frame_len / 2;
		break;

	default:
		dev_err(dev, "Unsupported DAI format\n");
		return -EINVAL;
	}
```

The slot placement that follows is the width dependence in code. The right-channel slot and its pause interval are computed from `frame_len / 2`, and the sample-size field is `sample_size / BITS_PER_SLOT - 1`, so a wider sample or frame moves the register values and the bit position the codec drives:

```c
/* sound/soc/codecs/cx2072x.c:777 */
	if (is_i2s) {
		i2s_right_slot = (frame_len / 2) / BITS_PER_SLOT;
		i2s_right_pause_interval = (frame_len / 2) % BITS_PER_SLOT;
		i2s_right_pause_pos = i2s_right_slot * BITS_PER_SLOT;
	}

	reg1.r.rx_ws_pol = is_frame_inv;
	reg1.r.rx_ws_wid = pulse_len - 1;

	reg1.r.rx_frm_len = frame_len / BITS_PER_SLOT - 1;
	reg1.r.rx_sa_size = (sample_size / BITS_PER_SLOT) - 1;
```

Because every term in the slot computation scales with `sample_size` and `frame_len`, the right-justified geometry is recomputed on each [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294), the concrete consequence of anchoring the sample at the right edge.

### The contrast with LEFT_J and I2S in a one-register codec

The split between [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) and [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) is clearer in a codec whose entire interface is one register word. [`wm8731_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8731.c#L406) leaves the format bits at 0 for [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28), sets bit 0 for [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), and sets bit 1 for [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), so the three protocols differ by a two-bit selector with right-justify as the zero default:

```c
/* sound/soc/codecs/wm8731.c:423 */
	/* interface format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		iface |= 0x0002;
		break;
	case SND_SOC_DAIFMT_RIGHT_J:
		break;
	case SND_SOC_DAIFMT_LEFT_J:
		iface |= 0x0001;
		break;
	case SND_SOC_DAIFMT_DSP_A:
		iface |= 0x0013;
		break;
	case SND_SOC_DAIFMT_DSP_B:
		iface |= 0x0003;
		break;
	default:
		return -EINVAL;
	}
```

The width that distinguishes one right-justified frame from another is applied separately. [`wm8731_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8731.c#L313) reads [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347) and ORs the corresponding word-length bits into the same IFACE register the format selector wrote:

```c
/* sound/soc/codecs/wm8731.c:328 */
	/* bit size */
	switch (params_width(params)) {
	case 16:
		break;
	case 20:
		iface |= 0x0004;
		break;
	case 24:
		iface |= 0x0008;
		break;
	case 32:
		iface |= 0x000c;
		break;
	}
```

[`wm8962_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748) follows the same shape, leaving the audio-interface format field at 0 for [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) and setting the word-length field from the width in [`wm8962_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2647). Not every codec opts in: [`es8326_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/es8326.c#L509) returns `-EINVAL` for [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) with the log "Codec driver does not support right justified", so a board pairing such a codec with a right-justified link sees the error surface through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194).

```
    wm8731 IFACE: format selector and word-length in one word
    ─────────────────────────────────────────────────────────
    (set_fmt writes the format bits; hw_params writes the WL bits)

    set_fmt  (fmt & FORMAT_MASK)         hw_params (params_width)
    ┌─────────────────────────────┐      ┌─────────────┐
    │ RIGHT_J  = 0      (default) │      │ 16 = 0      │
    │ LEFT_J   = 0x0001           │      │ 20 = 0x0004 │
    │ I2S      = 0x0002           │      │ 24 = 0x0008 │
    │ DSP_B    = 0x0003           │      │ 32 = 0x000c │
    │ DSP_A    = 0x0013           │      └─────────────┘
    └─────────────────────────────┘
    both fields OR into the same wm8731 IFACE register word
```

### wm8962 splits the format selector from the word length

The wm8962 audio-interface register packs the protocol and word length in one word, but the driver still writes them from two callbacks. [`wm8962_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748) selects the protocol with a small constant, leaving `aif0` at 0 for [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) so right-justify is again the zero default, distinct from the 1 and 2 written for [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) and [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27):

```c
/* sound/soc/codecs/wm8962.c:2754 */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_DSP_B:
		aif0 |= WM8962_LRCLK_INV | 3;
		fallthrough;
	case SND_SOC_DAIFMT_DSP_A:
		aif0 |= 3;
		...
		break;

	case SND_SOC_DAIFMT_RIGHT_J:
		break;
	case SND_SOC_DAIFMT_LEFT_J:
		aif0 |= 1;
		break;
	case SND_SOC_DAIFMT_I2S:
		aif0 |= 2;
		break;
	default:
		return -EINVAL;
	}
```

The width that fixes the most-significant-bit start position for that right-justified frame arrives later. [`wm8962_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2647) derives `width` from [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347) and updates the same [`WM8962_WL_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.h) field of the audio-interface register the format selector wrote:

```c
/* sound/soc/codecs/wm8962.c:2689 */
	switch (width) {
	case 16:
		break;
	case 20:
		aif0 |= 0x4;
		break;
	case 24:
		aif0 |= 0x8;
		break;
	case 32:
		aif0 |= 0xc;
		break;
	default:
		return -EINVAL;
	}

	snd_soc_component_update_bits(component, WM8962_AUDIO_INTERFACE_0,
			    WM8962_WL_MASK, aif0);
```

### es8326 rejects RIGHT_J outright

The format being per-codec opt-in is visible as an explicit refusal. [`es8326_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/es8326.c#L509) accepts [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), and the DSP modes, but its [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) case logs and returns `-EINVAL`, the error that [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) propagates when a board configures a right-justified link against this codec:

```c
/* sound/soc/codecs/es8326.c:525 */
	/* interface format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		break;
	case SND_SOC_DAIFMT_RIGHT_J:
		dev_err(component->dev, "Codec driver does not support right justified\n");
		return -EINVAL;
	case SND_SOC_DAIFMT_LEFT_J:
		iface |= ES8326_DAIFMT_LEFT_J;
		break;
	case SND_SOC_DAIFMT_DSP_A:
		iface |= ES8326_DAIFMT_DSP_A;
		break;
	case SND_SOC_DAIFMT_DSP_B:
		iface |= ES8326_DAIFMT_DSP_B;
		break;
	default:
		return -EINVAL;
	}
```
