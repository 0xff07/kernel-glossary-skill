# Left-justified audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Left-justified (also called MSB-justified) is a serial-audio wire format on the same three-wire clock pair as I2S, a bit clock and a frame clock, where the high-order bit (MSB) of each sample is driven onto the data line on the same edge the frame clock changes level, with no delay. The kernel names the format [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), which expands to [`SND_SOC_DAI_FORMAT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L152) with value 3, and the machine layer selects it by passing it in the low nibble of the format word to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which calls the codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op so the codec programs the data-format field of its serial-port register. On an x86-64 ACPI system the codec is enumerated by ACPI HID over I2C and carries audio over a Sound Open Firmware SSP link, and the Realtek RT5682 is the worked example, with [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) handling I2S, left-justified, and both DSP modes in one switch that differs only by the value written to the [`RT5682_I2S_DF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737) field.

```
    Left-justified frame (data MSB aligned to LRCLK edge, no delay)
    ──────────────────────────────────────────────────────────────

    BCLK  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
        ──┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └──

    LRCLK ────────────────────────────┐                           ┌
              left channel            └───────right channel───────┘

    SD    ◀M◀ ◀ ◀ ◀ ◀L◀     ◀ ◀ ◀ ◀ ◀M◀ ◀ ◀ ◀ ◀L◀     ◀ ◀ ◀ ◀ ◀M
           S               S           S               S         S
           B               B           B               B         B
          left MSB on the same edge          right MSB on the same edge
          LRCLK rises, no BCLK delay         LRCLK falls, no BCLK delay

    I2S, for contrast (1-BCLK delay after the LRCLK edge)
    ─────────────────────────────────────────────────────

    LRCLK ──┐                                 ┌──────────────────────
            └───────────left channel──────────┘     right channel

    SD      ░◀M◀ ◀ ◀ ◀ ◀L◀       ░◀M◀ ◀ ◀ ◀ ◀L◀       ░◀M◀ ◀ ◀ ◀ ◀L
             S               S     S               S     S
             B               B     B               B     B
            ░ = one BCLK of delay before the MSB; left channel is LRCLK low

    M = MSB cell   L = LSB cell   ◀ = one data bit, MSB first
    left-justified: MSB cell starts on the LRCLK transition
    I2S: MSB cell starts one BCLK after the LRCLK transition
```

## SUMMARY

Left-justified is one value of the format nibble that [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) decodes. The format word packs four independent fields, the audio protocol in [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f), the clock gating in [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136) (0x00f0), the clock and frame polarity in [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137) (0x0f00), and the clock-provider role in [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138) (0xf000). The protocol field takes one of seven enumerators from [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150), and [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) is value 3. Because the value is also reachable through the alias [`SND_SOC_DAIFMT_MSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36), the kernel treats "left-justified" and "MSB-justified" as the same wire format.

A machine driver selects the format by writing the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), which the core applies once at runtime init through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), or by calling that function from a [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook when the format is dynamic. Either path ends in [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) being called once per DAI on the link, codec DAIs first and then the CPU DAI with the clock-provider bits flipped by [`snd_soc_daifmt_clock_provider_flipped()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306). The codec op masks the format nibble, switches on it, and writes the data-format field of its serial-port register, the single field that distinguishes left-justified (MSB on the frame edge) from I2S (MSB one bit clock later) and from right-justified (LSB aligned to the trailing frame edge).

## SPECIFICATIONS

The left-justified format is a serial-audio wire convention defined outside Linux, and the kernel header tracks its timing in a comment rather than a formal specification reference. According to the comment in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L88), for "Left/Right Justified: frame consists of left then right channel data. Left channel starts with rising FSYNC edge, right channel starts with falling FSYNC edge." The phrase "left and right justified also known as MSB and LSB respectively" at [`SND_SOC_DAIFMT_MSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36) records the alternate naming. According to [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst), for Left Justified the "MSB is transmitted on transition of LRC", which contrasts with the I2S line where the "MSB is transmitted on the falling edge of the first BCLK after LRC transition", and with Right Justified, where the "MSB is transmitted sample size BCLKs before LRC transition".

## LINUX KERNEL

### Format value and field masks (soc-dai.h, asoc.h)

- [`'\<SND_SOC_DAIFMT_LEFT_J\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29): the format selector, an alias for [`SND_SOC_DAI_FORMAT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L152) (value 3)
- [`'\<SND_SOC_DAIFMT_MSB\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36): a second name for the same value, "MSB-justified"
- [`'\<SND_SOC_DAI_FORMAT_LEFT_J\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L152): the underlying enumerator, value 3, comment "Left Justified mode"
- [`'\<SND_SOC_DAIFMT_I2S\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27): the I2S value 1, one bit clock of delay before the MSB
- [`'\<SND_SOC_DAIFMT_RIGHT_J\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28): the right-justified value 2, LSB aligned to the trailing frame edge
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): 0x000f, isolates the protocol nibble a codec switches on
- [`'\<SND_SOC_DAIFMT_INV_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137): 0x0f00, the bit-clock and frame-clock polarity field
- [`'\<SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138): 0xf000, who drives BCLK and the frame clock

### Format-application path (soc-dai.c, soc-core.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): call the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op with the `SND_SOC_DAIFMT_*` word; returns `-ENOTSUPP` when the op is absent
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): apply one [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) to every DAI on a link, codecs then CPU
- [`'\<snd_soc_daifmt_clock_provider_flipped\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306): invert the clock-provider field so the CPU end takes the opposite role from the codec
- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): the runtime-init caller that applies the static [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749)

### Link descriptor field (soc.h)

- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the machine-driver link descriptor; [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) is the format-on-init field

### Codec set_fmt examples (codecs/)

- [`'\<rt5682_set_dai_fmt\>':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221): the RT5682 op; handles left-justified in the same switch as I2S and the DSP modes, writing [`RT5682_I2S_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L740) into [`RT5682_I2S1_SDP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L79)
- [`'rt5682_dai':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L78): the two [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries (rt5682-aif1, rt5682-aif2) for the I2C/SSP-attached part
- [`'rt5682_acpi_match':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L320): the ACPI HID table (10EC5682) that enumerates the codec on an x86-64 platform
- [`'\<wm8962_set_dai_fmt\>':'sound/soc/codecs/wm8962.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748): a platform-agnostic op where left-justified, right-justified, and I2S differ only by the value of the two-bit [`WM8962_FMT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.h#L1370) field
- [`'\<cs4271_set_dai_fmt\>':'sound/soc/codecs/cs4271.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L205): a codec whose switch supports only left-justified and I2S, choosing between [`CS4271_MODE1_DAC_DIF_LJ`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L62) and [`CS4271_MODE1_DAC_DIF_I2S`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L63)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the I2S, Left Justified, Right Justified, and PCM mode timing definitions
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK, BCLK, and LRCLK relationships a format runs over
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec DAI driver and its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and the DAI link where [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) is set

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [I2S bus specification (NXP/Philips)](https://www.nxp.com/docs/en/user-manual/UM11732.pdf)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The format nibble a codec switches on is the protocol field of the word passed to [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294), and [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f) isolates it. The seven protocol values share bits 3:0 of the format word with three other fields the other masks isolate, so a codec masks the word down to the nibble before its switch.

```
    DAI format word (passed to set_fmt)
    ───────────────────────────────────

    bit   15        12 11         8 7          4 3          0
         ┌────────────┬────────────┬────────────┬────────────┐
    DW0  │ clk prov   │  inv mask  │ clk gating │  protocol  │
         │ (15:12)    │  (11:8)    │  (7:4)     │   (3:0)    │
         └────────────┴────────────┴────────────┴────────────┘
            0xf000        0x0f00       0x00f0       0x000f

    protocol nibble (bits 3:0), values from include/uapi/sound/asoc.h
    ─────────────────────────────────────────────────────────────────
      1  I2S       MSB one BCLK after the LRCLK edge
      2  RIGHT_J   LSB aligned to the trailing LRCLK edge
      3  LEFT_J    MSB on the LRCLK edge, no delay   ◀── this page
      4  DSP_A     MSB one BCLK after the frame pulse (single FSYNC)
      5  DSP_B     MSB on the frame pulse (single FSYNC)
      6  AC97      AC-link slotted frame
      7  PDM       pulse-density modulation
```

A codec maps the chosen protocol value onto its own data-format register field. For the RT5682 the field is [`RT5682_I2S_DF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737) (0x7) at the low end of [`RT5682_I2S1_SDP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L79) (0x0070), and [`RT5682_I2S_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L740) (0x1) selects left-justified, sitting alongside [`RT5682_I2S_DF_I2S`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L739) (0x0) and [`RT5682_I2S_DF_PCM_A`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L741) (0x2) in the same field.

```
    RT5682 I2S1_SDP data-format field (register 0x0070)
    ───────────────────────────────────────────────────

    bit    2 1 0
          ┌─┬─┬─┐
    DW0   │ DF  │   I2S_DF (2:0), RT5682_I2S_DF_MASK = 0x7
          └─┴─┴─┘
           value selects the wire format:
             0x0  RT5682_I2S_DF_I2S    (1-BCLK delay)
             0x1  RT5682_I2S_DF_LEFT   (left-justified, no delay)
             0x2  RT5682_I2S_DF_PCM_A  (DSP_A)
             0x3  RT5682_I2S_DF_PCM_B  (DSP_B)
```

## DETAILS

### The format word and the position of LEFT_J in it

The single argument [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) receives packs four fields into one `unsigned int`. The protocol occupies bits 3:0, and the seven enumerators are defined in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) with left-justified as 3:

```c
/* include/uapi/sound/asoc.h:147 */
/* DAI physical PCM data formats.
 * Add new formats to the end of the list.
 */
#define SND_SOC_DAI_FORMAT_I2S          1 /* I2S mode */
#define SND_SOC_DAI_FORMAT_RIGHT_J      2 /* Right Justified mode */
#define SND_SOC_DAI_FORMAT_LEFT_J       3 /* Left Justified mode */
#define SND_SOC_DAI_FORMAT_DSP_A        4 /* L data MSB after FRM LRC */
#define SND_SOC_DAI_FORMAT_DSP_B        5 /* L data MSB during FRM LRC */
#define SND_SOC_DAI_FORMAT_AC97         6 /* AC97 */
#define SND_SOC_DAI_FORMAT_PDM          7 /* Pulse density modulation */

/* left and right justified also known as MSB and LSB respectively */
#define SND_SOC_DAI_FORMAT_MSB          SND_SOC_DAI_FORMAT_LEFT_J
#define SND_SOC_DAI_FORMAT_LSB          SND_SOC_DAI_FORMAT_RIGHT_J
```

[`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) re-exports each of these under the [`SND_SOC_DAIFMT_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) name codecs and machine drivers use, and adds the [`SND_SOC_DAIFMT_MSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36) alias so the format can be named after its alignment:

```c
/* include/sound/soc-dai.h:36 */
/* left and right justified also known as MSB and LSB respectively */
#define SND_SOC_DAIFMT_MSB		SND_SOC_DAIFMT_LEFT_J
#define SND_SOC_DAIFMT_LSB		SND_SOC_DAIFMT_RIGHT_J
```

A codec uses [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f) to isolate the protocol nibble before switching on it, leaving the other three nibbles for gating, polarity, and provider role:

```c
/* include/sound/soc-dai.h:135 */
#define SND_SOC_DAIFMT_FORMAT_MASK		0x000f
#define SND_SOC_DAIFMT_CLOCK_MASK		0x00f0
#define SND_SOC_DAIFMT_INV_MASK			0x0f00
#define SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK	0xf000
```

### Left-justification and the single-bit offset from I2S

Left-justified and I2S share the same bit clock and the same frame clock that names the left and right channels, and they differ only in where the MSB of each sample sits relative to the frame-clock edge. In left-justified the MSB cell begins on the same edge the frame clock transitions, so the sample is justified to the left (early) end of the frame, MSB first. In I2S the MSB cell begins one bit clock after that edge, the one-bit delay the I2S standard requires. According to the comment in [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst), in I2S the "MSB is transmitted on the falling edge of the first BCLK after LRC transition", while for Left Justified the "MSB is transmitted on transition of LRC". The difference at the wire is one bit clock of offset, and inside a codec it is the difference between two adjacent values of one register field.

Right-justified inverts the reference. Instead of pinning the MSB to the leading frame edge, it pins the LSB to the trailing frame edge, so the sample is justified to the right (late) end of the frame and the position of the MSB depends on the sample width. According to the same documentation, for Right Justified the "MSB is transmitted sample size BCLKs before LRC transition". A codec that supports all three needs only one register field to select among them, because the three are alternatives within the protocol nibble.

For the channel-to-edge association, the header comment in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L75) records that under left-justified framing the "Left channel starts with rising FSYNC edge, right channel starts with falling FSYNC edge", which is the reverse of the I2S convention where the left channel opens on the falling edge. Each channel occupies one level of the frame clock for the whole of its sample, with the MSB landing on the level transition.

```
    LEFT_J vs RIGHT_J: where the sample word sits in one channel slot
    ────────────────────────────────────────────────────────────────
    (▼ = leading LRCLK edge, ▽ = trailing edge; slot = one channel)

                  ▼ leading edge          ▽ trailing edge
                  │                       │
    LEFT_J        ├────────────────┬──────┤   MSB pinned to the
    (MSB-just)    │ MSB ······ LSB │ idle │   leading edge, no delay
                  ├────────────────┴──────┤

    RIGHT_J       ├──────┬────────────────┤   LSB pinned to the
    (LSB-just)    │ idle │ MSB ······ LSB │   trailing edge; MSB is
                  ├──────┴────────────────┤   sample-width BCLKs early

    I2S delays LEFT_J by one BCLK; RIGHT_J packs to the far end.
```

### snd_soc_dai_set_fmt reaches the codec op

The core never writes a codec register itself. It calls the codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op through one wrapper, and the wrapper returns the not-supported result when a DAI has no op:

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

Most machine drivers set the static [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of the link, and the core applies it once at runtime init through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which walks the codec DAIs first, then flips the clock-provider bits and walks the CPU DAIs, so one value programs both ends consistently:

```c
/* sound/soc/soc-core.c:1493 */
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
```

The `-ENOTSUPP` return from a DAI that does not implement [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) is tolerated by the `ret != -ENOTSUPP` test, so a DAI on a fixed wire format that needs no programming is skipped silently while the other end is still configured.

### The link descriptor carries the format on its dai_fmt field

The static format a machine driver chooses is held in one field of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the descriptor the machine driver fills in for each CPU-to-codec connection. The [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) member holds the full `SND_SOC_DAIFMT_*` word, including the protocol nibble that selects left-justified, and its comment names it the format to set on init:

```c
/* include/sound/soc.h:702 */
struct snd_soc_dai_link {
	/* config - must be set by machine driver */
	const char *name;			/* Codec name */
	const char *stream_name;		/* Stream name */
	...
	unsigned int dai_fmt;           /* format to set on init */
	...
};
```

A SOF SSP codec link that wants left-justified framing stores [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) in the protocol nibble of this field, alongside the polarity and clock-provider bits, and never calls the codec op itself. The core reads the field once at runtime init.

### soc_init_pcm_runtime applies the static format once per link

Runtime init is the single point where the static [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) takes effect. [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) runs once per link as the card is brought up, reads the field from the link descriptor, and hands it to [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459):

```c
/* sound/soc/soc-core.c:1512 */
static int soc_init_pcm_runtime(struct snd_soc_card *card,
				struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *cpu_dai = snd_soc_rtd_to_cpu(rtd, 0);
	int ret;
	...
	snd_soc_runtime_get_dai_fmt(rtd);
	ret = snd_soc_runtime_set_dai_fmt(rtd, dai_link->dai_fmt);
	if (ret)
		goto err;
	...
}
```

Because the format is applied here rather than per-stream, a link with a fixed left-justified format programs both DAIs once, and no [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook is needed unless the format changes with the stream.

### snd_soc_runtime_set_dai_fmt walks both ends of the link

The function the init path calls takes the format word and applies it across every DAI on the runtime. [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) returns early on a zero format, then runs the codec-then-CPU loop shown above, so one [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) value carrying [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) reaches both the codec op and the CPU op:

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
}
```

The zero-format guard means a link that leaves [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) unset is left untouched, while a link that sets it to a left-justified word drives the codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op through the loop body already shown, where the protocol nibble selects left-justified framing.

### A generic codec set_fmt: the format nibble selects one field value

The cleanest illustration that left-justified, right-justified, and I2S are three values of one field is [`wm8962_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748). It masks the format nibble and accumulates the two-bit [`WM8962_FMT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.h#L1370) value into a local, where right-justified contributes 0, left-justified contributes 1, and I2S contributes 2:

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

The accumulated value is written in one update at the end of the op into the [`WM8962_AUDIO_INTERFACE_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.h#L37) register (0x07), masked by [`WM8962_FMT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.h#L1370) (0x0003) together with the clock-inversion and master bits:

```c
/* sound/soc/codecs/wm8962.c:2810 */
	snd_soc_component_update_bits(component, WM8962_AUDIO_INTERFACE_0,
			    WM8962_FMT_MASK | WM8962_BCLK_INV | WM8962_MSTR |
			    WM8962_LRCLK_INV, aif0);
```

Because the right-justified case adds nothing (the field stays 0), the three wire formats correspond to the field encodings 0, 1, and 2, and the choice of one over another is the choice of which `case` label runs. A second example, [`cs4271_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L205), supports only left-justified and I2S and selects between [`CS4271_MODE1_DAC_DIF_LJ`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L62) and [`CS4271_MODE1_DAC_DIF_I2S`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L63) for both the DAC and the ADC paths:

```c
/* sound/soc/codecs/cs4271.c:226 */
	switch (format & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_LEFT_J:
		val |= CS4271_MODE1_DAC_DIF_LJ;
		ret = regmap_update_bits(cs4271->regmap, CS4271_ADCCTL,
			CS4271_ADCCTL_ADC_DIF_MASK, CS4271_ADCCTL_ADC_DIF_LJ);
		if (ret < 0)
			return ret;
		break;
	case SND_SOC_DAIFMT_I2S:
		val |= CS4271_MODE1_DAC_DIF_I2S;
		ret = regmap_update_bits(cs4271->regmap, CS4271_ADCCTL,
			CS4271_ADCCTL_ADC_DIF_MASK, CS4271_ADCCTL_ADC_DIF_I2S);
		if (ret < 0)
			return ret;
		break;
	default:
		dev_err(component->dev, "Invalid DAI format\n");
		return -EINVAL;
	}
```

Set side by side, the two codecs map the same format nibble onto their own field encodings, left-justified picking the value 1 on one and the LJ data-interface code on the other:

```
    Format nibble ──▶ one register-field value (per codec)
    ──────────────────────────────────────────────────────

    fmt & SND_SOC_DAIFMT_FORMAT_MASK    wm8962        cs4271
    ────────────────────────────────    ──────        ──────
    SND_SOC_DAIFMT_RIGHT_J              FMT = 0       (unsupported)
    SND_SOC_DAIFMT_LEFT_J     ◀──page   FMT = 1       DAC_DIF_LJ
    SND_SOC_DAIFMT_I2S                  FMT = 2       DAC_DIF_I2S

    wm8962 field = WM8962_FMT_MASK (0x0003) in WM8962_AUDIO_INTERFACE_0
    cs4271 field = CS4271_MODE1_DAC_DIF_* in MODE1, ADC mirror in ADCCTL
```

### The codec set_fmt entry points share one signature

Every codec op the format word reaches has the same two-argument shape, a [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) pointer and the `unsigned int` format word, and each pulls its private data off the component before decoding the nibbles. [`cs4271_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs4271.c#L205) opens by reading the clock-provider role and only then runs the left-justified-or-I2S switch shown above:

```c
/* sound/soc/codecs/cs4271.c:205 */
static int cs4271_set_dai_fmt(struct snd_soc_dai *codec_dai,
			      unsigned int format)
{
	struct snd_soc_component *component = codec_dai->component;
	struct cs4271_private *cs4271 = snd_soc_component_get_drvdata(component);
	unsigned int val = 0;
	int ret;
	...
}
```

[`wm8962_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/wm8962.c#L2748) has the same prologue and accumulates its bits into the local `aif0` that the format switch shown above contributes to before the single register update:

```c
/* sound/soc/codecs/wm8962.c:2748 */
static int wm8962_set_dai_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
	struct snd_soc_component *component = dai->component;
	struct wm8962_priv *wm8962 = snd_soc_component_get_drvdata(component);
	int aif0 = 0;
	...
}
```

[`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) follows the same form, keeping two accumulators, one for the non-TDM serial port and one for the TDM path, that the format switch and the per-DAI commit shown in the worked example below fill in:

```c
/* sound/soc/codecs/rt5682.c:2221 */
static int rt5682_set_dai_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
	struct snd_soc_component *component = dai->component;
	struct rt5682_priv *rt5682 = snd_soc_component_get_drvdata(component);
	unsigned int reg_val = 0, tdm_ctrl = 0;
	...
}
```

Because the entry signature is fixed by the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op type, [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) hands the same left-justified word to any of these three the same way, and the only per-codec difference is which register field the body writes.

```
    One set_fmt op type, three codec bodies writing different fields
    ───────────────────────────────────────────────────────────────

    snd_soc_dai_set_fmt() ──▶ set_fmt(dai, fmt)   (one signature)
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     rt5682_set_dai_fmt   wm8962_set_dai_fmt   cs4271_set_dai_fmt
              ▼                    ▼                    ▼
     RT5682_I2S_DF_MASK     WM8962_FMT_MASK   CS4271_MODE1_DAC_DIF
              ▼                    ▼                    ▼
     in RT5682_I2S1_SDP  in AUDIO_INTERFACE_0  in MODE1 (+ ADCCTL)
```

### Worked example: RT5682 on an x86-64 ACPI SOF SSP board

On an x86-64 ACPI platform the codec is enumerated by an ACPI HID and controlled over I2C, while its audio samples travel over an Intel SSP port driven by Sound Open Firmware. The RT5682 I2C front end matches the ACPI identifier 10EC5682, and the codec exposes the DAIs `rt5682-aif1` and `rt5682-aif2`, each pointing at a function pointer struct whose [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) is [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221):

```c
/* sound/soc/codecs/rt5682-i2c.c:78 */
static struct snd_soc_dai_driver rt5682_dai[] = {
	{
		.name = "rt5682-aif1",
		.id = RT5682_AIF1,
		.playback = {
			.stream_name = "AIF1 Playback",
			...
		},
		.capture = {
			.stream_name = "AIF1 Capture",
			...
		},
		.ops = &rt5682_aif1_dai_ops,
	},
	...
};
```

When a SOF machine driver sets its codec link to left-justified, the format word reaching this op carries [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) in bits 3:0. The op decodes the clock-provider and polarity fields first, then switches on the format nibble. The left-justified case sets [`RT5682_I2S_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L740) (0x1) in the serial-port value and [`RT5682_TDM_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L836) in the TDM-control value, the two register fields that carry the wire format for the non-TDM and TDM paths, while the I2S case sets nothing and leaves the field at [`RT5682_I2S_DF_I2S`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L739) (0x0):

```c
/* sound/soc/codecs/rt5682.c:2263 */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		break;
	case SND_SOC_DAIFMT_LEFT_J:
		reg_val |= RT5682_I2S_DF_LEFT;
		tdm_ctrl |= RT5682_TDM_DF_LEFT;
		break;
	case SND_SOC_DAIFMT_DSP_A:
		reg_val |= RT5682_I2S_DF_PCM_A;
		tdm_ctrl |= RT5682_TDM_DF_PCM_A;
		break;
	case SND_SOC_DAIFMT_DSP_B:
		reg_val |= RT5682_I2S_DF_PCM_B;
		tdm_ctrl |= RT5682_TDM_DF_PCM_B;
		break;
	default:
		return -EINVAL;
	}
```

The accumulated value is committed per DAI id, with `RT5682_AIF1` writing the serial-port register [`RT5682_I2S1_SDP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L79) under [`RT5682_I2S_DF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737), so the only difference between selecting I2S and selecting left-justified on this codec is whether the field holds 0x0 or 0x1, the in-register form of the one-bit-clock offset the figure shows on the wire:

```c
/* sound/soc/codecs/rt5682.c:2287 */
	switch (dai->id) {
	case RT5682_AIF1:
		snd_soc_component_update_bits(component, RT5682_I2S1_SDP,
			RT5682_I2S_DF_MASK, reg_val);
		...
		break;
```

The machine link supplies the rest of the format word. A SOF SSP codec link sets [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) to the protocol value with normal clock polarity [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96) and the codec as clock consumer [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119), and swapping the protocol field to [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) drives the RT5682 to program left-justified framing. [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) then flips [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) to [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) for the SSP CPU DAI, so the SSP drives BCLK and the frame clock while the codec consumes them, both ends carrying the same left-justified protocol value in bits 3:0.

```
    RT5682 LEFT_J: two accumulators feed two register fields
    ────────────────────────────────────────────────────────

    LEFT_J case sets   RT5682_I2S_DF_LEFT  into reg_val   (serial port)
                       RT5682_TDM_DF_LEFT  into tdm_ctrl  (TDM path)

         reg_val                    tdm_ctrl
            │                          │
            ▼                          ▼
    ┌────────────────────┐    ┌────────────────────┐
    │ RT5682_I2S1_SDP    │    │ RT5682 TDM ctrl reg│
    │  RT5682_I2S_DF_MASK│    │  RT5682_TDM_DF_*   │
    │  LEFT = 0x1        │    │  LEFT framing      │
    └────────────────────┘    └────────────────────┘
       per dai->id commit; I2S leaves both fields at 0x0
```

### Protocol nibble values within the format word

The format word a codec [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op decodes splits into four fields isolated by [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137), and [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138), with the low protocol nibble holding one of seven values where [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) is 3.

```
    DAI format word (passed to set_fmt)
    ───────────────────────────────────

    bit   15        12 11         8 7          4 3          0
         ┌────────────┬────────────┬────────────┬────────────┐
    DW0  │ clk prov   │  inv mask  │ clk gating │  protocol  │
         │ (15:12)    │  (11:8)    │  (7:4)     │   (3:0)    │
         └────────────┴────────────┴────────────┴────────────┘
            0xf000        0x0f00       0x00f0       0x000f

    protocol nibble (bits 3:0), values from include/uapi/sound/asoc.h
    ─────────────────────────────────────────────────────────────────
      1  I2S       MSB one BCLK after the LRCLK edge
      2  RIGHT_J   LSB aligned to the trailing LRCLK edge
      3  LEFT_J    MSB on the LRCLK edge, no delay   ◀── this page
      4  DSP_A     MSB one BCLK after the frame pulse (single FSYNC)
      5  DSP_B     MSB on the frame pulse (single FSYNC)
      6  AC97      AC-link slotted frame
      7  PDM       pulse-density modulation

    FORMAT_MASK = SND_SOC_DAIFMT_FORMAT_MASK (0x000f)
    INV_MASK = SND_SOC_DAIFMT_INV_MASK (0x0f00)
    clk prov = SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK (0xf000)
```
