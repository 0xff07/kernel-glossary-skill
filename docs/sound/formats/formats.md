# DAI audio formats (SND_SOC_DAIFMT)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The serial-audio wire format of an ASoC link is carried in a single `unsigned int` named `fmt`, a packed 16-bit word a machine driver hands to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which forwards it to the codec or CPU DAI through the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) function pointer of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269). The word is divided into four nibble-wide field groups. These are the protocol field under [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) in bits 3:0, the clock-gating field under [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136) in bits 7:4, the bit-clock and frame-clock inversion field under [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137) in bits 11:8, and the clock-provider field under [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138) in bits 15:12. The protocol values [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30), and the rest each name one serial-audio protocol, the inversion values [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96) and its siblings set the clock edges, and the provider values [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) and [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) state, from the codec's point of view, which end drives the bit clock (BCLK) and the frame clock (LRCLK/FSYNC).

```
    fmt word passed to set_fmt (16-bit packed field)
    ─────────────────────────────────────────────────

    bit    1 1 1 1 1 1
           5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  prov │  inv  │  gate │  fmt  │
          │ 15:12 │  11:8 │  7:4  │  3:0  │
          └───────┴───────┴───────┴───────┘

    fmt       (3:0)   = SND_SOC_DAIFMT_FORMAT_MASK   (0x000f)
                        1 I2S, 2 RIGHT_J, 3 LEFT_J, 4 DSP_A,
                        5 DSP_B, 6 AC97, 7 PDM
    gate      (7:4)   = SND_SOC_DAIFMT_CLOCK_MASK     (0x00f0)
                        CONT (1<<4) continuous, GATED (0<<4) gated
    inv       (11:8)  = SND_SOC_DAIFMT_INV_MASK       (0x0f00)
                        NB_NF (0<<8), NB_IF (2<<8),
                        IB_NF (3<<8), IB_IF (4<<8)
    prov      (15:12) = SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK (0xf000)
                        CBP_CFP (1<<12), CBC_CFP (2<<12),
                        CBP_CFC (3<<12), CBC_CFC (4<<12)
    (B = BCLK provider, F = FSYNC/LRCLK provider; C from codec view)
```

## SUMMARY

A machine driver picks one serial-audio protocol, one clock-gating policy, one clock-edge polarity, and one clock-provider assignment, packs them into a single [`fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) word from the [`SND_SOC_DAIFMT_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) constants, and applies it either by storing it in the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) or by calling [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) from a [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) hook. The four field groups occupy four nibbles, the protocol in bits 3:0 under [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), the gating in bits 7:4 under [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136), the inversion in bits 11:8 under [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137), and the provider in bits 15:12 under [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138).

The protocol nibble takes one of [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28), [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30), [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31), [`SND_SOC_DAIFMT_AC97`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L32), or [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33), each defined as one of the [`SND_SOC_DAI_FORMAT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) family of small integers 1 through 7. The inversion nibble takes [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96), [`SND_SOC_DAIFMT_NB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L97), [`SND_SOC_DAIFMT_IB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L98), or [`SND_SOC_DAIFMT_IB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L99), and the provider nibble takes [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116), [`SND_SOC_DAIFMT_CBC_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L117), [`SND_SOC_DAIFMT_CBP_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L118), or [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119), whose CBx_CFx names replaced the older CBM/CBS spelling and read as codec-bit-clock-provider/consumer and codec-frame-clock-provider/consumer. The same word is applied to both ends of a link by [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which sends [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) unchanged to each codec DAI and runs the provider nibble through [`snd_soc_daifmt_clock_provider_flipped()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306) before sending it to each CPU DAI, so a codec marked clock provider leaves the CPU marked clock consumer. The individual protocols are detailed on their own pages.

## SPECIFICATIONS

The [`fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) word and its [`SND_SOC_DAIFMT_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) constants are a Linux kernel software encoding and have no standalone hardware specification. The wire protocols the protocol nibble names are defined by their own public interface standards. These are the I2S bus specification for [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27), [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29), and [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28); a codec or DSP vendor's PCM/TDM timing for [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) and [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31); the AC97 component specification for [`SND_SOC_DAIFMT_AC97`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L32); and the PDM microphone interface for [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33).

## LINUX KERNEL

### The fmt word and its four masks (soc-dai.h)

- [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): bits 3:0, the protocol nibble (0x000f)
- [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136): bits 7:4, the clock-gating nibble (0x00f0)
- [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137): bits 11:8, the BCLK/FSYNC inversion nibble (0x0f00)
- [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138): bits 15:12, the clock-provider nibble (0xf000)
- [`SND_SOC_DAIFMT_MASTER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L140): legacy alias of [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138), still used by many codec set_fmt switches

### Protocol values (soc-dai.h, over the uapi enum)

- [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27): I2S mode, [`SND_SOC_DAI_FORMAT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) (1)
- [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28): right-justified, [`SND_SOC_DAI_FORMAT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L151) (2), aliased as [`SND_SOC_DAIFMT_LSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L37)
- [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29): left-justified, [`SND_SOC_DAI_FORMAT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L152) (3), aliased as [`SND_SOC_DAIFMT_MSB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L36)
- [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30): DSP/PCM mode A, [`SND_SOC_DAI_FORMAT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L153) (4), L data MSB one BCLK after FSYNC
- [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31): DSP/PCM mode B, [`SND_SOC_DAI_FORMAT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154) (5), L data MSB on the FSYNC edge
- [`SND_SOC_DAIFMT_AC97`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L32): AC97 mode, [`SND_SOC_DAI_FORMAT_AC97`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L155) (6)
- [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33): pulse-density modulation, [`SND_SOC_DAI_FORMAT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L156) (7)

### Clock-gating values (soc-dai.h)

- [`SND_SOC_DAIFMT_CONT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L61): continuous clock, BCLK runs between frames (1<<4)
- [`SND_SOC_DAIFMT_GATED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L62): gated clock, BCLK stops when no PCM data is moving (0<<4)

### Inversion values (soc-dai.h)

- [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96): normal BCLK, normal FSYNC (0<<8)
- [`SND_SOC_DAIFMT_NB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L97): normal BCLK, inverted FSYNC (2<<8)
- [`SND_SOC_DAIFMT_IB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L98): inverted BCLK, normal FSYNC (3<<8)
- [`SND_SOC_DAIFMT_IB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L99): inverted BCLK, inverted FSYNC (4<<8)

### Clock-provider values (soc-dai.h)

- [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116): codec is BCLK provider and FSYNC provider (1<<12); the older name was CBM_CFM
- [`SND_SOC_DAIFMT_CBC_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L117): codec is BCLK consumer and FSYNC provider (2<<12)
- [`SND_SOC_DAIFMT_CBP_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L118): codec is BCLK provider and FSYNC consumer (3<<12)
- [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119): codec is BCLK consumer and FSYNC consumer (4<<12); the older name was CBS_CFS
- [`SND_SOC_DAIFMT_BP_FP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L122): provider-perspective alias of [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116), used when set_fmt is called on a DAI directly
- [`SND_SOC_DAIFMT_BC_FC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L125): provider-perspective alias of [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119)

### Set-fmt entry points and the op (soc-dai.c, soc-dai.h, soc-core.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): wrapper that calls the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, returning `-ENOTSUPP` when absent
- [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) callback a codec or platform DAI fills to decode the word and program its serial port
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): apply the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) to codec DAIs, then to CPU DAIs with the provider nibble flipped
- [`'\<snd_soc_daifmt_clock_provider_flipped\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306): swap each CBx_CFx value for its complement so the CPU end mirrors the codec end
- [`'\<snd_soc_dai_get_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L155): collect the [`auto_selectable_formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L356) up to a priority for automatic format selection

### The link and its format fields (soc.h)

- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one machine-described link; its [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field is the format applied at init
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): one codec or CPU entry; its [`ext_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L657) carries the per-component provider nibble in the new scheme

### rt5682 codec worked example (codecs/rt5682.c)

- [`'\<rt5682_set_dai_fmt\>':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221): the Realtek RT5682 [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, three switches decoding the provider, inversion, and protocol nibbles into I2S and TDM register fields
- [`'rt5682_aif1_dai_ops':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3051): the function pointer struct installing [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) as its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept and the I2S, AC97, and PCM/TDM families the protocol nibble names
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK/SYSCLK, BCLK, and LRCLK relationships the gating, inversion, and provider nibbles describe
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the power management that gates the BCLK domain when [`SND_SOC_DAIFMT_GATED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L62) is in effect
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec driver guide covering the DAI driver and its set_fmt op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [I2S bus specification (NXP/Philips)](https://www.nxp.com/docs/en/user-manual/UM11732.pdf)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The argument to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) is not a hardware register; it is a software encoding the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op decodes into whatever physical register bits its serial port exposes. The encoding partitions a 16-bit word into four nibble-wide groups, one mask per group.

| Bits | Field | Mask macro | Values |
|------|-------|------------|--------|
| 3:0 | protocol | [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f) | [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) (1) through [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33) (7) |
| 7:4 | clock gating | [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136) (0x00f0) | [`SND_SOC_DAIFMT_GATED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L62) (0<<4), [`SND_SOC_DAIFMT_CONT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L61) (1<<4) |
| 11:8 | BCLK/FSYNC inversion | [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137) (0x0f00) | [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96) (0), [`SND_SOC_DAIFMT_NB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L97) (2<<8), [`SND_SOC_DAIFMT_IB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L98) (3<<8), [`SND_SOC_DAIFMT_IB_IF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L99) (4<<8) |
| 15:12 | clock provider | [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138) (0xf000) | [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) (1<<12) through [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) (4<<12) |

A codec set_fmt op typically reads the word three times, masking off one group each time with [`SND_SOC_DAIFMT_MASTER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L140) (the provider alias), [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137), and [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), and ignores the gating nibble when its hardware has no separate gated-clock control, as shown in DETAILS.

## DETAILS

### The four nibbles and their constants

The four field groups are four blocks of `#define` in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h), each followed by its mask. The protocol nibble is an alias layer over the uapi integers so the same numbers serve topology and the `SND_SOC_POSSIBLE_DAIFMT_*` bitmaps:

```c
/* include/sound/soc-dai.h:27 */
#define SND_SOC_DAIFMT_I2S		SND_SOC_DAI_FORMAT_I2S
#define SND_SOC_DAIFMT_RIGHT_J		SND_SOC_DAI_FORMAT_RIGHT_J
#define SND_SOC_DAIFMT_LEFT_J		SND_SOC_DAI_FORMAT_LEFT_J
#define SND_SOC_DAIFMT_DSP_A		SND_SOC_DAI_FORMAT_DSP_A
#define SND_SOC_DAIFMT_DSP_B		SND_SOC_DAI_FORMAT_DSP_B
#define SND_SOC_DAIFMT_AC97		SND_SOC_DAI_FORMAT_AC97
#define SND_SOC_DAIFMT_PDM		SND_SOC_DAI_FORMAT_PDM
```

The underlying numbers are small integers 1 through 7 from the uapi header that fit the bottom nibble, so the protocol field is the raw value with nothing shifted:

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

The clock-gating nibble sits in bits 7:4, where [`SND_SOC_DAIFMT_GATED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L62) lets the BCLK stop between frames and [`SND_SOC_DAIFMT_CONT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L61) keeps it running:

```c
/* include/sound/soc-dai.h:61 */
#define SND_SOC_DAIFMT_CONT		(1 << 4) /* continuous clock */
#define SND_SOC_DAIFMT_GATED		(0 << 4) /* clock is gated */
```

The inversion nibble in bits 11:8 names the active edges, the four values covering the combinations of normal or inverted bit clock and normal or inverted frame clock:

```c
/* include/sound/soc-dai.h:96 */
#define SND_SOC_DAIFMT_NB_NF		(0 << 8) /* normal bit clock + frame */
#define SND_SOC_DAIFMT_NB_IF		(2 << 8) /* normal BCLK + inv FRM */
#define SND_SOC_DAIFMT_IB_NF		(3 << 8) /* invert BCLK + nor FRM */
#define SND_SOC_DAIFMT_IB_IF		(4 << 8) /* invert BCLK + FRM */
```

The provider nibble in bits 15:12 states which end drives the two clocks. According to the block comment the values are written from the codec's point of view, "the inverse is true for the interface", so the four CBx_CFx values name the codec's role for the bit clock (CBP provider, CBC consumer) and the frame clock (CFP provider, CFC consumer), replacing the older CBM_CFM and CBS_CFS spelling:

```c
/* include/sound/soc-dai.h:116 */
#define SND_SOC_DAIFMT_CBP_CFP		(1 << 12) /* codec clk provider & frame provider */
#define SND_SOC_DAIFMT_CBC_CFP		(2 << 12) /* codec clk consumer & frame provider */
#define SND_SOC_DAIFMT_CBP_CFC		(3 << 12) /* codec clk provider & frame consumer */
#define SND_SOC_DAIFMT_CBC_CFC		(4 << 12) /* codec clk consumer & frame consumer */
```

The four masks are contiguous nibbles, so a decode is one mask-and-compare per group:

```c
/* include/sound/soc-dai.h:135 */
#define SND_SOC_DAIFMT_FORMAT_MASK		0x000f
#define SND_SOC_DAIFMT_CLOCK_MASK		0x00f0
#define SND_SOC_DAIFMT_INV_MASK			0x0f00
#define SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK	0xf000
```

### snd_soc_dai_set_fmt forwards the word to the op

The whole word is opaque to the core. [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) checks that the DAI has a [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, hands it the word verbatim, and reports `-ENOTSUPP` when the DAI does not implement format programming:

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

According to the comment above the op, format configuration is "Called by soc_card drivers, normally in their hw_params", which is why the machine layer rather than the PCM core drives it:

```c
/* include/sound/soc-dai.h:290 */
	/*
	 * DAI format configuration
	 * Called by soc_card drivers, normally in their hw_params.
	 */
	int (*set_fmt)(struct snd_soc_dai *dai, unsigned int fmt);
```

### snd_soc_runtime_set_dai_fmt applies the link format to both ends

Most machine drivers set [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) once in the link and let the core apply it. During card bring-up [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) passes that field to [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which sends the word to every codec DAI first, then flips the provider nibble and sends it to every CPU DAI. According to the comment in the function, the provider field "is set from Codec perspective in dai_fmt. So it will be flipped when this function calls set_fmt() for CPU (CBx_CFx -> Bx_Cx)":

```c
/* sound/soc/soc-core.c:1490 */
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

The per-component [`ext_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L657) OR-ed into each call lets the provider nibble be set per codec or per CPU instead of one value for the whole link. The flip is a switch over the four provider values, each mapped to its mirror so provider becomes consumer on the opposite end:

```c
/* sound/soc/soc-core.c:3306 */
unsigned int snd_soc_daifmt_clock_provider_flipped(unsigned int dai_fmt)
{
	unsigned int inv_dai_fmt = dai_fmt & ~SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK;

	switch (dai_fmt & SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK) {
	case SND_SOC_DAIFMT_CBP_CFP:
		inv_dai_fmt |= SND_SOC_DAIFMT_CBC_CFC;
		break;
	case SND_SOC_DAIFMT_CBP_CFC:
		inv_dai_fmt |= SND_SOC_DAIFMT_CBC_CFP;
		break;
	case SND_SOC_DAIFMT_CBC_CFP:
		inv_dai_fmt |= SND_SOC_DAIFMT_CBP_CFC;
		break;
	case SND_SOC_DAIFMT_CBC_CFC:
		inv_dai_fmt |= SND_SOC_DAIFMT_CBP_CFP;
		break;
	}

	return inv_dai_fmt;
}
```

The function clears the provider nibble with `~SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK` and OR-s in the mirror, so [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) on the codec becomes [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) on the CPU, and the protocol, gating, and inversion nibbles pass through untouched.

```
    snd_soc_runtime_set_dai_fmt: codecs first, then CPUs flipped
    ────────────────────────────────────────────────────────────

    dai_fmt (codec view)
         │
         ├─▶ every codec DAI ── set_fmt(dai_fmt) ──┐  (1st)
         │                                         ▼
         │   snd_soc_daifmt_clock_provider_flipped(dai_fmt)
         │                                         │
         └─▶ every CPU DAI ── set_fmt(flipped) ────┘  (2nd)

    PROVIDER nibble flip (only this nibble changes):
         CBP_CFP ◀───────────────────────────────▶ CBC_CFC
         CBP_CFC ◀───────────────────────────────▶ CBC_CFP
    FMT / CLOCK / INV nibbles pass to both ends unchanged.
    (each call also ORs in the per-component ext_fmt)
```

### A codec set_fmt op: the modern Realtek RT5682

The Realtek [`rt5682`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c) headset codec is wired to the SSP serial ports of modern Intel x86-64 ACPI SOF platforms such as Alder Lake and Meteor Lake laptops, over I2C for control and a TDM/I2S link for audio. It installs [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) as the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) of its AIF1 function pointer struct:

```c
/* sound/soc/codecs/rt5682.c:3051 */
const struct snd_soc_dai_ops rt5682_aif1_dai_ops = {
	.hw_params = rt5682_hw_params,
	.set_fmt = rt5682_set_dai_fmt,
	.set_tdm_slot = rt5682_set_tdm_slot,
	.set_bclk_ratio = rt5682_set_bclk1_ratio,
};
```

The op masks the word once per group. The first switch reads the clock-provider nibble through [`SND_SOC_DAIFMT_MASTER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L140), accepting only the two symmetric values: [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) records a 1 in the per-AIF [`master[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L1461) array, [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) records a 0, and the two mixed roles fall to `default` and return `-EINVAL` because this codec cannot split bit-clock and frame-clock ownership:

```c
/* sound/soc/codecs/rt5682.c:2221 */
static int rt5682_set_dai_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
	struct snd_soc_component *component = dai->component;
	struct rt5682_priv *rt5682 = snd_soc_component_get_drvdata(component);
	unsigned int reg_val = 0, tdm_ctrl = 0;

	switch (fmt & SND_SOC_DAIFMT_MASTER_MASK) {
	case SND_SOC_DAIFMT_CBP_CFP:
		rt5682->master[dai->id] = 1;
		break;
	case SND_SOC_DAIFMT_CBC_CFC:
		rt5682->master[dai->id] = 0;
		break;
	default:
		return -EINVAL;
	}
```

The second switch reads the inversion nibble through [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137), where [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96) touches no register bit and the inverting values OR the relevant inversion bits into the I2S and TDM accumulators:

```c
/* sound/soc/codecs/rt5682.c:2238 */
	switch (fmt & SND_SOC_DAIFMT_INV_MASK) {
	case SND_SOC_DAIFMT_NB_NF:
		break;
	case SND_SOC_DAIFMT_IB_NF:
		reg_val |= RT5682_I2S_BP_INV;
		tdm_ctrl |= RT5682_TDM_S_BP_INV;
		break;
	...
	default:
		return -EINVAL;
	}
```

The third switch reads the protocol nibble through [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), where [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) leaves the data-format register at its default and the other supported protocols OR their data-format bits into both accumulators:

```c
/* sound/soc/codecs/rt5682.c:2262 */
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

After the three switches the op writes the accumulated `reg_val` and `tdm_ctrl` into the codec's I2S and TDM registers. It never inspects the gating nibble, because its serial port has no separate continuous-versus-gated control, so the [`SND_SOC_DAIFMT_GATED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L62) bit has no effect for this codec. The values that fall to a `default` ([`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28), [`SND_SOC_DAIFMT_AC97`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L32), [`SND_SOC_DAIFMT_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L33), and the mixed provider roles) return `-EINVAL`, which is how a codec advertises that it does not implement part of the encoding.

```
    rt5682_set_dai_fmt: three masked switches feed two accumulators
    ──────────────────────────────────────────────────────────────

    fmt word
       │
       ├─ & MASTER_MASK ─▶ switch ─▶ master[dai->id]  (1 or 0; else -EINVAL)
       │                              CBP_CFP=1   CBC_CFC=0
       │
       ├─ & INV_MASK ────▶ switch ─┬─▶ reg_val   (I2S regs)
       │                           └─▶ tdm_ctrl  (TDM regs)
       │                              NB_NF none; IB_NF sets BP_INV
       │
       └─ & FORMAT_MASK ─▶ switch ─┬─▶ reg_val   gets DF code
                                   └─▶ tdm_ctrl  gets DF code
                                      I2S none; LEFT_J/DSP_A/DSP_B set DF

    reg_val ──▶ RT5682 I2S1_SDP        tdm_ctrl ──▶ RT5682 TDM regs
    gating nibble is never read (no gated-clock control on this port).
```

### The two ends of one link carry complementary provider roles

On a modern Intel x86-64 ACPI SOF platform the codec end of the link runs the word through [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) while the CPU end is an Intel SSP serial port. When the SOF machine driver marks its link [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) with [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119), the RT5682 takes the consumer branch and records a 0 in [`master[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L1461), and [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) flips that nibble through [`snd_soc_daifmt_clock_provider_flipped()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306) before it reaches the SSP, so the SSP is programmed [`SND_SOC_DAIFMT_CBP_CFP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116) and drives both clocks. The protocol, gating, and inversion nibbles pass to both ends unchanged, so the SSP and the RT5682 agree on framing and clock edges while disagreeing only on who is the provider.

```
    One link, two ends: complementary PROVIDER, shared everything else
    ─────────────────────────────────────────────────────────────────

      codec end (RT5682)                       CPU end (Intel SSP)
    ┌──────────────────────────┐             ┌──────────────────────────┐
    │ PROVIDER  CBC_CFC        │ ──flip──▶   │ PROVIDER  CBP_CFP        │
    │   consumer, master[]=0   │             │   provider, drives BCLK  │
    │                          │             │   and FSYNC              │
    │ FMT   (e.g. I2S / DSP_A) │ ══same══▶   │ FMT   (e.g. I2S / DSP_A) │
    │ INV   (e.g. NB_NF)       │ ══same══▶   │ INV   (e.g. NB_NF)       │
    │ CLOCK (gating)           │ ══same══▶   │ CLOCK (gating)           │
    └──────────────────────────┘             └──────────────────────────┘

    Only the PROVIDER nibble differs; the codec is consumer because the
    machine set dai_fmt CBC_CFC and the flip made the SSP the provider.
```

### Automatic format selection

When neither end has a fixed format, [`snd_soc_dai_get_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L155) reads a DAI's [`auto_selectable_formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L356) array, a list of `SND_SOC_POSSIBLE_DAIFMT_*` bitmaps in priority order, and OR-s the entries up to a requested priority so the core can intersect both ends and choose a format both implement:

```c
/* sound/soc/soc-dai.c:155 */
u64 snd_soc_dai_get_fmt(const struct snd_soc_dai *dai, int priority)
{
	const struct snd_soc_dai_ops *ops = dai->driver->ops;
	u64 fmt = 0;
	int i, max = 0, until = priority;
	...
	if (ops)
		max = ops->num_auto_selectable_formats;

	if (max < until)
		until = max;

	if (ops && ops->auto_selectable_formats)
		for (i = 0; i < until; i++)
			fmt |= ops->auto_selectable_formats[i];

	return fmt;
}
```

According to the comment on [`snd_soc_dai_get_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L155), a DAI "should return only formats implemented with high quality", so a device that cannot use both LRCLK edges in an I2S-style frame lists only its DSP modes here even though its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op would accept more. The result feeds the negotiation that builds the final [`fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) word the two DAIs are programmed with.
