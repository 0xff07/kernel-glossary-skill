# I2S audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

I2S (Inter-IC Sound) is the three-wire serial format ASoC selects with the [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) protocol code (value 1, defined as [`SND_SOC_DAI_FORMAT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150)), passed to a DAI when the machine layer hands that code through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) to the codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback. The wire carries three signals, the bit clock BCLK that strobes one data bit per edge, the word-select LRCLK (also called WS or frame clock) that is low for the left channel and high for the right, and the serial data SD line that presents each sample most-significant-bit first. What distinguishes I2S from the left-justified format that shares the same three wires is one timing detail, the MSB of each channel appears one BCLK period after the LRCLK transition rather than on the same edge, so the data slot is delayed by exactly one bit relative to the word-select change. The codec programs that framing from the protocol nibble [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f), the clock-inversion bits under [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137) (0x0f00), and the clock-provider role under [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138) (0xf000). The Realtek RT5682 is the worked example.

```
    One I2S frame (left then right slot), data MSB-first
    ─────────────────────────────────────────────────────
    (the SD MSB lags the WS edge by one BCLK; left = WS low)

           ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
    BCLK ──┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─

    WS   ──┐                       ┌───────────────────────
    (LR)   └───────────────────────┘
           │      left slot        │      right slot
           │  (WS low)             │  (WS high)

    SD     ◀──▶◀──┬──┬──┬──┬──┬──┐ ◀───┬──┬──┬──┬──┬──┬──┐
    (data) ░░░░░░░│M │  │  │  │L │░░░░░│M │  │  │  │  │L │░░
                  │SB│        │SB│     │SB│           │SB│
           └─1bit─┘ left sample      ▲ right sample
            delay                    │
                              MSB lags WS edge by one BCLK
```

## SUMMARY

The kernel does not model I2S as a struct; it is one value in the format word a DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op decodes. The macro [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) expands to [`SND_SOC_DAI_FORMAT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150), which is 1, and sits in the low four bits that [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) selects alongside [`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29) (3), [`SND_SOC_DAIFMT_RIGHT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28) (2), [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) (4), and [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) (5). A machine driver builds a full format word by ORing the protocol code with a polarity selector such as [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96) (normal bit clock, normal frame) and a clock-provider selector such as [`SND_SOC_DAIFMT_CBC_CFC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119) (codec is bit-clock and frame consumer), then hands it to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194).

When a board sets one format for the whole link, it stores the word in the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and the core applies it through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), which sends the word to every codec DAI and then to every CPU DAI after flipping the clock-provider role with [`snd_soc_daifmt_clock_provider_flipped()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306). On the codec side a platform-agnostic part such as the Realtek RT5682 implements [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221), which reads the masks and writes the serial-data-format field of its I2S port register, leaving the register bits at 0 for the I2S case because I2S is the part's reset default. I2S is inherently a two-slot frame (one left and one right sample per LRCLK period), so it is the degenerate case of TDM where the slot count is 2; a codec that supports more slots routes the wider case through its [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op instead.

## SPECIFICATIONS

I2S is defined by the Philips (NXP) I2S bus specification, which fixes the three-wire serial protocol, the MSB-first data ordering, and the one-bit delay between the word-select edge and the first data bit. The kernel constants in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h) and [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h) encode the protocol family but carry no electrical timing of their own, since the codec register programmed by [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) determines the wire behavior. According to the polarity comment block in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L85), "I2S: frame consists of left then right channel data. Left channel starts with falling FSYNC edge, right channel starts with rising FSYNC edge."

## LINUX KERNEL

### Protocol format codes (soc-dai.h, asoc.h)

- [`'\<SND_SOC_DAIFMT_I2S\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27): the I2S protocol selector, expands to [`SND_SOC_DAI_FORMAT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) (value 1)
- [`'\<SND_SOC_DAIFMT_LEFT_J\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29): left-justified (MSB) selector, value 3; same three wires as I2S but with no one-bit delay
- [`'\<SND_SOC_DAIFMT_RIGHT_J\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L28): right-justified (LSB) selector, value 2
- [`'\<SND_SOC_DAIFMT_DSP_A\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) / [`'\<SND_SOC_DAIFMT_DSP_B\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31): the single-frame-sync TDM/PCM modes, values 4 and 5
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): 0x000f, the low nibble that holds the protocol code
- [`'\<SND_SOC_DAI_FORMAT_I2S\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150): the underlying uapi constant, "I2S mode", value 1

### Polarity and clock-provider selectors (soc-dai.h)

- [`'\<SND_SOC_DAIFMT_NB_NF\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96): normal bit clock, normal frame (0<<8), the usual I2S polarity
- [`'\<SND_SOC_DAIFMT_IB_NF\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L98): inverted BCLK, normal frame (3<<8)
- [`'\<SND_SOC_DAIFMT_INV_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137): 0x0f00, the polarity field
- [`'\<SND_SOC_DAIFMT_CBP_CFP\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L116): codec is bit-clock and frame provider (1<<12); the codec drives BCLK and LRCLK
- [`'\<SND_SOC_DAIFMT_CBC_CFC\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L119): codec is bit-clock and frame consumer (4<<12); the SSP/CPU drives the clocks
- [`'\<SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138): 0xf000, the provider field, aliased by [`SND_SOC_DAIFMT_MASTER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L140)

### Format dispatch and link application (soc-dai.c, soc-core.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): the wrapper that calls the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op with the format word, or returns -ENOTSUPP
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): apply one link format to every codec DAI then every CPU DAI, flipping the provider role for the CPU end
- [`'\<dai_fmt\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749): the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field a board sets for a static link format

### Codec set_fmt worked example (codecs/rt5682.c, rt5682.h, rt5682-i2c.c)

- [`'\<rt5682_set_dai_fmt\>':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221): the RT5682 [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op decoding provider, polarity, and protocol into the I2S port register
- [`'rt5682_aif1_dai_ops':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3051): the function pointer struct that wires [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) into the set_fmt slot
- [`'\<RT5682_I2S1_SDP\>':'sound/soc/codecs/rt5682.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L79): the AIF1 serial-data-port register (0x0070) the op programs
- [`'\<RT5682_I2S_DF_MASK\>':'sound/soc/codecs/rt5682.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737): 0x7, the data-format field; I2S writes 0, left-justified writes [`RT5682_I2S_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L740) (0x1)
- [`'rt5682_dai':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L78): the I2C/ACPI [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) table whose "rt5682-aif1" entry sets its ops to [`rt5682_aif1_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3051) for an I2S-attached part on x86 ACPI

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families, with an I2S section describing the BCLK, LRC, Tx, and Rx wires and the master/slave clocking options
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK/BCLK/LRCLK relationships an I2S link depends on
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide covering the DAI driver and its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [I2S bus specification (NXP/Philips)](https://www.nxp.com/docs/en/user-manual/UM11732.pdf)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The protocol value is one nibble of the software [`fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) word held in memory, and the codec [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op maps it onto a real device register. On the RT5682 that register is the AIF1 serial-data port [`RT5682_I2S1_SDP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L79) (0x0070), whose data-format field [`RT5682_I2S_DF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737) (0x7) reads 0 for I2S and the BCLK-polarity bit [`RT5682_I2S_BP_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L725) (bit 8) reflects the inversion nibble.

```
    RT5682_I2S1_SDP serial-data-port format field (low bits)
    ────────────────────────────────────────────────────────

    bit    8 ...        3   2   1   0
         ┌───┬─────────┬───┬───┬───┬───┐
         │BP │   ...   │ - │   DF (2:0)│
         └───┴─────────┴───┴───┴───┴───┘
           │                     │
           │                     └─ RT5682_I2S_DF_MASK (0x7)
           └─────────────────────── RT5682_I2S_BP_MASK (0x1 << 8)

    DF = 0          I2S            (RT5682 reset default)
    DF = 1          LEFT_J         (RT5682_I2S_DF_LEFT)
    DF = 2          PCM_A / DSP_A  (RT5682_I2S_DF_PCM_A)
    DF = 3          PCM_B / DSP_B  (RT5682_I2S_DF_PCM_B)
    BP = 1          BCLK inverted  (RT5682_I2S_BP_INV)
```

## DETAILS

### SND_SOC_DAIFMT_I2S is the protocol nibble

I2S is selected by the low four bits of the format word. [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) is one of a family of protocol codes, all defined as aliases of the uapi constants so the same numbering is shared with the topology binary interface:

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

The numbers come from [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150), whose comments distinguish I2S from its relatives by exactly the timing point this page is about, where the left-channel MSB sits relative to the frame-clock (LRC) edge:

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

The table restates these codes by their timing, pairing each value in the nibble with where its left-channel MSB falls against the LRC (FSYNC) edge:

```
    Protocol codes in the format nibble (FORMAT_MASK 0x000f)
    ─────────────────────────────────────────────────────────

    SND_SOC_DAIFMT_*  value   left-channel MSB vs FSYNC (LRC) edge
    ────────────────  ─────   ────────────────────────────────────
    I2S                 1     after falling edge, lagged one BCLK
    RIGHT_J             2     right-justified in the slot
    LEFT_J              3     on the rising edge, no delay
    DSP_A               4     after FRM (rising) edge
    DSP_B               5     during FRM (rising) edge
```

### The one-BCLK delay distinguishes I2S from left-justified

I2S and left-justified ([`SND_SOC_DAIFMT_LEFT_J`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L29)) drive the identical three wires and both present each sample MSB-first; the only difference is where the MSB lands. In I2S the MSB of the left sample appears one BCLK period after LRCLK (the frame clock, FSYNC) falls, and the MSB of the right sample one BCLK period after it rises, so the data is shifted by a single bit relative to the word-select transition. In left-justified the MSB is aligned to the LRCLK edge with no delay. The polarity comment in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L85) records the frame convention, and the I2S and Left/Right-Justified entries differ in which FSYNC edge opens the left channel:

```c
/* include/sound/soc-dai.h:85 */
 * FSYNC "normal" polarity depends on the frame format:
 * - I2S: frame consists of left then right channel data. Left channel starts
 *      with falling FSYNC edge, right channel starts with rising FSYNC edge.
 * - Left/Right Justified: frame consists of left then right channel data.
 *      Left channel starts with rising FSYNC edge, right channel starts with
 *      falling FSYNC edge.
 * - DSP A/B: Frame starts with rising FSYNC edge.
 * - AC97: Frame starts with rising FSYNC edge.
```

For ordinary I2S a board passes [`SND_SOC_DAIFMT_NB_NF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L96), normal bit clock and normal frame, so the data line is sampled on the rising BCLK edge and the left slot opens on the falling LRCLK edge. According to the same comment block, "normal" BCLK polarity means the signal is available at the rising edge of BCLK and "inverted" means the falling edge:

```c
/* include/sound/soc-dai.h:96 */
#define SND_SOC_DAIFMT_NB_NF		(0 << 8) /* normal bit clock + frame */
#define SND_SOC_DAIFMT_NB_IF		(2 << 8) /* normal BCLK + inv FRM */
#define SND_SOC_DAIFMT_IB_NF		(3 << 8) /* invert BCLK + nor FRM */
#define SND_SOC_DAIFMT_IB_IF		(4 << 8) /* invert BCLK + FRM */
```

Holding that normal polarity fixed, the figure lines up the two formats on one WS edge, the I2S MSB sitting one BCLK in and the left-justified MSB landing right on the edge:

```
    I2S vs left-justified: where the left-channel MSB sits
    ────────────────────────────────────────────────────────
    (▼ = tick 0, the WS falling edge that opens the left slot;
     each data cell is one BCLK period)

                  ▼
    WS    ────────┐
                  └────────────────────────────────

    I2S   ─────────────┌────┬────┬────┬────┐    MSB starts one
    SD            ·····│MSB │ b14│ b13│ b12│    BCLK after the edge

    LEFT  ────────┌────┬────┬────┬────┐          MSB starts on
    SD            │MSB │ b14│ b13│ b12│          the edge (no delay)
```

### snd_soc_dai_set_fmt dispatches the word to the DAI op

The format word reaches a DAI through one wrapper. [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) checks that the DAI registered a [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, calls it with the whole word, and reports -ENOTSUPP when none is registered, which the link-level caller tolerates:

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

A board that sets the format once for the whole link places the word in [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) and lets [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) apply it, sending the word unchanged to each codec DAI and then flipping the provider nibble with [`snd_soc_daifmt_clock_provider_flipped()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L3306) before each CPU DAI, so a codec-consumer I2S link makes the CPU the clock provider while both ends agree on I2S framing.

```
    snd_soc_runtime_set_dai_fmt(): one link fmt, two destinations
    ───────────────────────────────────────────────────────────────
    (codec DAIs get the word as-is; CPU DAIs get the provider nibble
     flipped first, so both ends agree on framing but swap clock role)

                       dai_link.dai_fmt
                              │
              ┌───────────────┴───────────────┐
              ▼ (1) as-is                     ▼ (2) provider flipped
        ┌───────────┐                    ┌───────────────┐
        │ codec DAI │  ... each codec    │ flip provider │
        │  set_fmt  │      DAI first     │     nibble    │
        └───────────┘                    └───────┬───────┘
                                                 ▼
                                          ┌───────────┐
                                          │  CPU DAI  │  ... each
                                          │  set_fmt  │  CPU DAI
                                          └───────────┘

    flip via snd_soc_daifmt_clock_provider_flipped(); each set_fmt
    reached through snd_soc_dai_set_fmt()
```

### A codec set_fmt programs its serial port for I2S

The receiving end of the dispatch is the codec [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op. The Realtek RT5682 is a platform-agnostic codec on x86 ACPI SOF systems, and its [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) decodes the format word one nibble at a time, recording the provider role and accumulating any inversion bits before it reaches the protocol switch:

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
	...
```

The protocol nibble is read through [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135). The [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) case does nothing, leaving the accumulated [`reg_val`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) data-format field at 0, because I2S is the RT5682 reset state of [`RT5682_I2S_DF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L737); only the non-I2S protocols write a non-zero code such as [`RT5682_I2S_DF_LEFT`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L740) or [`RT5682_I2S_DF_PCM_A`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L741):

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

The op writes the accumulated [`reg_val`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) into the AIF1 serial-data-port register, masking the data-format field, so for an I2S, normal-polarity, codec-consumer link the data-format field is cleared to 0 and the port runs standard I2S with the one-BCLK delay:

```c
/* sound/soc/codecs/rt5682.c:2281 */
	switch (dai->id) {
	case RT5682_AIF1:
		snd_soc_component_update_bits(component, RT5682_I2S1_SDP,
			RT5682_I2S_DF_MASK, reg_val);
		...
```

The op is registered in the AIF1 function pointer struct, so [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) reaches it through the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) slot:

```c
/* sound/soc/codecs/rt5682.c:3051 */
const struct snd_soc_dai_ops rt5682_aif1_dai_ops = {
	.hw_params = rt5682_hw_params,
	.set_fmt = rt5682_set_dai_fmt,
	.set_tdm_slot = rt5682_set_tdm_slot,
	.set_bclk_ratio = rt5682_set_bclk1_ratio,
};
EXPORT_SYMBOL_GPL(rt5682_aif1_dai_ops);
```

The contrast with the single-FSYNC modes is direct. Both [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) and [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) write a non-zero data-format code so the port switches to a PCM frame opening on a rising FSYNC edge, while [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) is the only protocol that reaches the register write with its data-format field still cleared, which is why a board that wants plain I2S passes [`SND_SOC_DAIFMT_I2S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L27) and relies on the reset default.

```
    fmt FORMAT nibble case → reg_val / tdm_ctrl accumulators
    ──────────────────────────────────────────────────────────
    (the I2S case adds nothing, so reg_val keeps its cleared 0)

    fmt & FORMAT_MASK   adds to reg_val      adds to tdm_ctrl
    ─────────────────   ─────────────────    ─────────────────
    I2S                 nothing (stays 0)    nothing
    LEFT_J              RT5682_I2S_DF_LEFT   RT5682_TDM_DF_LEFT
    DSP_A               RT5682_I2S_DF_PCM_A  RT5682_TDM_DF_PCM_A
    DSP_B               RT5682_I2S_DF_PCM_B  RT5682_TDM_DF_PCM_B
                              │
                              ▼
    snd_soc_component_update_bits(RT5682_I2S1_SDP,
                                  RT5682_I2S_DF_MASK, reg_val)
```

### I2S is the two-slot case of TDM

I2S carries exactly two samples per frame, one in the LRCLK-low (left) slot and one in the LRCLK-high (right) slot, so it is the two-slot degenerate case of time-division multiplexing. A codec that supports wider TDM exposes both paths. The [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op selects the I2S protocol, and a separate [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op widens the frame and assigns slot masks when more than two slots are used. In [`rt5682_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) the I2S decode and the TDM-control decode share the same switch, accumulating into [`reg_val`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) for the plain serial port and into [`tdm_ctrl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2221) for the TDM control register, which is why the I2S case leaves both at their cleared default and a plain left-plus-right frame needs no [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) call.

```
    I2S frame = the two-slot case of TDM
    ──────────────────────────────────────
    (one sample per slot; set_fmt picks I2S, set_tdm_slot widens it)

    One WS (LRCLK) period:
    ┌───────────────────────┬───────────────────────┐
    │       left slot       │       right slot      │
    │       (WS low)        │       (WS high)       │   I2S = 2 slots
    └───────────────────────┴───────────────────────┘

    Same wires, a wider TDM frame (one FSYNC period, N slots):
    ┌──────┬──────┬──────┬──────┬──────┬─────┬───────┐
    │slot 0│slot 1│slot 2│slot 3│slot 4│ ... │slotN-1│
    └──────┴──────┴──────┴──────┴──────┴─────┴───────┘
       set_tdm_slot assigns each codec channel a slot mask (N > 2)
```

### Format word nibble layout

The format word that [`snd_soc_dai_set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) carries packs four nibbles, the protocol under [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), the clock gating under [`SND_SOC_DAIFMT_CLOCK_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L136), the BCLK and frame polarity under [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137), and the codec clock-provider role under [`SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L138).

```
    snd_soc_dai_set_fmt() format word (packed nibbles)
    ──────────────────────────────────────────────────

    bit   15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
         ┌──────────────┬──────────────┬─────┬─────┬─────┐
         │   PROVIDER   │     INV      │ CLK │  0  │ FMT │
         │   (15:12)    │   (11:8)     │(7:4)│     │(3:0)│
         └────┬─────────┴────┬─────────┴──┬──┴─────┴──┬──┘
              │              │            │           │
              │              │            │           └─ FMT mask
              │              │            └───────────── CLK mask
              │              └────────────────────────── INV mask
              └───────────────────────────────────────── PROVIDER mask

    FMT      (3:0)  = SND_SOC_DAIFMT_FORMAT_MASK (0x000f)
      I2S    = 1    LEFT_J = 3    RIGHT_J = 2    DSP_A = 4    DSP_B = 5
    CLK      (7:4)  = SND_SOC_DAIFMT_CLOCK_MASK (0x00f0)
      GATED  = 0 << 4    CONT = 1 << 4
    INV      (11:8) = SND_SOC_DAIFMT_INV_MASK (0x0f00)
      NB_NF  = 0 << 8    NB_IF = 2 << 8    IB_NF = 3 << 8    IB_IF = 4 << 8
    PROVIDER (15:12) = SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK (0xf000)
      CBP_CFP = 1 << 12    CBC_CFC = 4 << 12
```
