# DSP_B audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

DSP_B (PCM mode B) is a time-division-multiplexed serial-audio frame where the first data bit of the first slot aligns with the frame-sync edge, with zero bit-clock delay, and ASoC selects it by passing [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) (the constant [`SND_SOC_DAI_FORMAT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154), value 5) in the low nibble of the format word that reaches a DAI through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194). The only wire-level difference from DSP_A (PCM mode A, [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30), value 4) is the one-bit-clock data delay DSP_A inserts and DSP_B omits, which the uapi header records as the comment "L data MSB during FRM LRC" on DSP_B against "L data MSB after FRM LRC" on DSP_A. A codec's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op masks the format word with [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f) and programs its serial port's delay bit accordingly, and the slot layout is set separately through [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252). The Maxim MAX98396 is the worked example.

```
    DSP_B (PCM mode B), 4 slots, MSB first, zero BCLK delay
    ───────────────────────────────────────────────────────

    BCLK    ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
          ──┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─
            └ first data bit aligns with the frame-sync edge

    FSYNC   ┌───┐
          ──┘   └───────────────────────────────────────────
            └ one-BCLK frame-sync pulse, no leading delay

    DATA  ──◀───▶◀───▶◀───▶◀───▶◀───▶◀───▶◀───▶◀───▶──────────
            B23  B22  B21  ...  slot0 (MSB..LSB)  slot1 ...
            │
            └ MSB of slot 0 on the same BCLK as the FSYNC rise

            DSP_A would shift the DATA row one BCLK right
            (1-BCLK data delay); DSP_B has zero delay, slots packed
```

## SUMMARY

DSP_B is one of the seven serial-audio protocols an ASoC DAI can be put into, encoded in the low four bits of the `SND_SOC_DAIFMT_*` word. The seven protocol values are defined in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h) as aliases of the uapi [`SND_SOC_DAI_FORMAT_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) integers, so [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) is the integer 5 and [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) is 4. A machine driver writes the chosen value into the DAI link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field or passes it to [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), whose wrapper calls the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op when one exists and returns `-ENOTSUPP` when it does not.

The frame geometry separates the two PCM modes. Both pack their TDM slots contiguously after the frame-sync, both clock data most-significant-bit first, and both use a frame-sync that is a short pulse rather than the half-frame square wave of I2S. DSP_A delays the first data bit by one bit clock relative to the frame-sync edge, so the frame-sync rises one BCLK before the MSB of slot 0; DSP_B has no such delay, so the MSB of slot 0 is sampled on the same BCLK as the frame-sync edge. A codec that supports both reads the format nibble and sets a single code in its serial-port register to choose between them, which is the entire functional difference at the register level. Slot count, slot width, and the active-slot bitmasks are orthogonal to the protocol and are programmed through [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252). On an x86-64 Intel SOF SSP board, the shared Maxim helper [`sof_maxim_common.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c) configures two or four Maxim amplifiers on one SSP back end in DSP_B, giving each amp its own TDM slot.

## SPECIFICATIONS

DSP_B (PCM mode B) is a serial-audio framing convention rather than a single named industry standard. The kernel's seven `SND_SOC_DAIFMT_*` protocol values, including DSP_A and DSP_B, are defined in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L150) and described by codec datasheets in terms of the frame-sync-to-data delay. The TDM packing DSP_B carries is governed by the codec's own serial-port specification, and the bit-clock and frame-clock relationships are described in the ASoC clocking documentation.

## LINUX KERNEL

### Format constants (soc-dai.h, asoc.h)

- [`'\<SND_SOC_DAIFMT_DSP_B\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31): the DSP_B selector, an alias of [`SND_SOC_DAI_FORMAT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154) (integer 5, "L data MSB during FRM LRC")
- [`'\<SND_SOC_DAIFMT_DSP_A\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30): the DSP_A selector (integer 4, "L data MSB after FRM LRC"); differs from DSP_B by one BCLK of data delay
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): the 0x000f mask selecting the protocol nibble of the format word
- [`'\<SND_SOC_DAIFMT_INV_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137): the 0x0f00 mask selecting the BCLK/FSYNC inversion nibble, set independently of the protocol
- [`'\<SND_SOC_DAI_FORMAT_DSP_B\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154): the uapi integer 5 the [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) alias resolves to

### Format and TDM wrappers (soc-dai.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): apply a `SND_SOC_DAIFMT_*` word to a DAI; calls the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op or returns `-ENOTSUPP`
- [`'\<snd_soc_dai_set_tdm_slot\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252): set TDM slot count, width, and active-slot tx/rx masks, the slot layout DSP_B packs
- [`'\<snd_soc_xlate_tdm_slot_mask\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213): generate default contiguous tx/rx masks of `(1 << slots) - 1` when the caller passes zero masks

### DAI ops and link fields (soc-dai.h, soc.h)

- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct holding [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) and [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297)
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the machine-driver link descriptor whose [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field carries the format applied at init

### Codec set_fmt implementations (codecs/)

- [`'\<max98396_dai_set_fmt\>':'sound/soc/codecs/max98396.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.c#L347): the Maxim MAX98396 [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op; maps DSP_A to [`MAX98396_PCM_FORMAT_TDM_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L233) and DSP_B to [`MAX98396_PCM_FORMAT_TDM_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L232)
- [`'\<max98373_dai_set_fmt\>':'sound/soc/codecs/max98373-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98373-i2c.c#L121): the Maxim MAX98373 [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op with the same DSP_A/DSP_B branching

### x86-64 SOF SSP worked example (intel/boards/, sof/)

- [`'\<max_98373_hw_params\>':'sound/soc/intel/boards/sof_maxim_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110): the SOF two-amplifier back-end [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) callback; branches on DSP_B and assigns per-amp TDM slots
- [`'\<max_98390_hw_params\>':'sound/soc/intel/boards/sof_maxim_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L379): the SOF four-amplifier back-end [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) callback; sets a fixed 4-slot DSP_B layout
- [`'\<sof_dai_get_tdm_slots\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L1050): read the SSP TDM slot count the topology programmed, consumed by the DSP_B branch

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept and the AC97, I2S, and PCM (DSP) families
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the BCLK and frame-clock relationships a DSP_B frame is built on
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where an SSP back-end DAI is configured for DSP_B independently of its front end
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget graph the SOF amplifier back-ends attach their speaker pins to

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

DSP_B is selected by a software constant rather than by a register of its own, and each codec lands the selection in a serial-port format field. The Maxim MAX98396 keeps that field in [`MAX98396_R2041_PCM_MODE_CFG`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L45) (register 0x2041) at bits 5:3, and the named protocol encodings are defined in [`max98396.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h). The BCLK inversion bit is held in a separate register, [`MAX98396_R2042_PCM_CLK_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L46) (register 0x2042).

```
    MAX98396_R2041_PCM_MODE_CFG (0x2041), format field
    ──────────────────────────────────────────────────

    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│·│ FMT │·│L│·│
          └─┴─┴─────┴─┴─┴─┘
                 │     │
           FORMAT(5:3) │
       LRCLKEDGE ──────┘

    FORMAT (5:3) = MAX98396_PCM_MODE_CFG_FORMAT_MASK (0x7 << 3)
      I2S        = MAX98396_PCM_FORMAT_I2S       (0x0 << 3)
      LEFT_J     = MAX98396_PCM_FORMAT_LJ        (0x1 << 3)
      DSP_B      = MAX98396_PCM_FORMAT_TDM_MODE0 (0x3 << 3)
      DSP_A      = MAX98396_PCM_FORMAT_TDM_MODE1 (0x4 << 3)
    L = MAX98396_PCM_MODE_CFG_LRCLKEDGE (0x1 << 1), FSYNC polarity
    bits 7, 6, 2, 0 not set by the format/invert path
```

DSP_B is [`MAX98396_PCM_FORMAT_TDM_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L232) (the 0x3 code, TDM mode 0, the zero-delay layout) and DSP_A is [`MAX98396_PCM_FORMAT_TDM_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L233) (the 0x4 code, TDM mode 1, the one-BCLK-delay layout), so the one-bit-clock delay that distinguishes the two protocols is exactly the difference between writing TDM mode 0 and TDM mode 1 into bits 5:3 of register 0x2041.

## DETAILS

### The DSP_B constant and the format word

DSP_B is one entry in the protocol nibble of the `SND_SOC_DAIFMT_*` word. The kernel defines all seven protocol selectors in [`include/sound/soc-dai.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h) as thin aliases of the uapi integers, so the value a codec sees is a small integer index:

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

The integers and the one-line description of each protocol's framing are in the uapi header. The comments on DSP_A and DSP_B are the precise statement of the delay difference, "L data MSB after FRM LRC" against "L data MSB during FRM LRC":

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

According to the comment on [`SND_SOC_DAI_FORMAT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154), the left-channel MSB appears "during" the frame-sync (LRC) pulse, the zero-delay alignment the timing figure shows, whereas DSP_A places the MSB "after" the frame-sync, one bit clock later. Everything else about the two frames, MSB-first ordering and contiguous TDM slots after the frame-sync, is identical. The protocol nibble is isolated by [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135), and clock-polarity selection occupies a different nibble masked by [`SND_SOC_DAIFMT_INV_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L137).

```
    SND_SOC_DAIFMT_* word, DSP_B in the protocol nibble
    ───────────────────────────────────────────────────

    bit       15:12        11:8         7:4          3:0
         ┌────────────┬────────────┬────────────┬────────────┐
         │ (provider) │ INV (11:8) │   (clk)    │  FMT (3:0) │
         └────────────┴─────┬──────┴────────────┴─────┬──────┘
                            │                         │
                            │                         └─ FORMAT_MASK 0x000f
                            └─────────────────────────── INV_MASK    0x0f00

    FMT (3:0) = SND_SOC_DAIFMT_FORMAT_MASK (0x000f):
      DSP_B = 5    DSP_A = 4    (DSP_B selects this nibble)
    INV (11:8) = SND_SOC_DAIFMT_INV_MASK (0x0f00), set independently
```

### snd_soc_dai_set_fmt routes the format word to the DAI

The format word reaches a codec through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which calls the DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op with the full word or returns `-ENOTSUPP`:

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

A machine driver can either call this from a callback or set the format once in the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field and let [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) fan it out to every codec and CPU DAI of the runtime. The link descriptor records the chosen format there:

```c
/* include/sound/soc.h:749 */
	unsigned int dai_fmt;           /* format to set on init */
```

### The dai_ops struct holding set_fmt and set_tdm_slot

The [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op that decodes the DSP_B nibble is one field of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), the per-DAI function-pointer table. The two ops that matter for DSP_B framing, [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) for the protocol nibble and [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) for the slot layout DSP_B packs, sit next to each other in the format-configuration group, with the optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op between them:

```c
/* include/sound/soc-dai.h:269 */
struct snd_soc_dai_ops {
	...
	/*
	 * DAI format configuration
	 * Called by soc_card drivers, normally in their hw_params.
	 */
	int (*set_fmt)(struct snd_soc_dai *dai, unsigned int fmt);
	int (*xlate_tdm_slot_mask)(unsigned int slots,
		unsigned int *tx_mask, unsigned int *rx_mask);
	int (*set_tdm_slot)(struct snd_soc_dai *dai,
		unsigned int tx_mask, unsigned int rx_mask,
		int slots, int slot_width);
	...
	int (*hw_params)(struct snd_pcm_substream *,
		struct snd_pcm_hw_params *, struct snd_soc_dai *);
	...
};
```

The machine-driver descriptor that carries the chosen protocol into those ops is [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the per-link configuration set by the board. Its [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field holds the `SND_SOC_DAIFMT_*` word applied at init, and its `no_pcm:1` flag marks the SSP back-end link on which the multi-amplifier DSP_B example runs:

```c
/* include/sound/soc.h:702 */
struct snd_soc_dai_link {
	...
	struct snd_soc_dai_link_component *codecs;
	unsigned int num_codecs;
	...
	unsigned int dai_fmt;           /* format to set on init */
	...
	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;
	...
};
```

The board-side [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) callbacks below read [`dai_link->dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) directly and branch on its protocol nibble to decide whether to program the DSP_B TDM slots.

```
    struct snd_soc_dai_ops: format group holding the two DSP_B ops
    ─────────────────────────────────────────────────────────────

    struct snd_soc_dai_ops
    ┌────────────────────────────────────────────────┐
    │ ...                                            │
    │ set_fmt              ◀ decodes protocol nibble │
    │ xlate_tdm_slot_mask    (optional default masks)│
    │ set_tdm_slot         ◀ slot count/width/masks  │
    │ ...                                            │
    │ hw_params                                      │
    │ ...                                            │
    └────────────────────────────────────────────────┘
      set_fmt picks DSP_B; set_tdm_slot packs the slots
```

### A codec set_fmt that handles both DSP_A and DSP_B

The Maxim MAX98396 smart amplifier supports both PCM modes, and its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op shows the single-code difference. After decoding the inversion nibble, [`max98396_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.c#L347) masks the format word with [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) and selects a protocol code, mapping DSP_A and DSP_B to two adjacent encodings that differ only in the framing delay:

```c
/* sound/soc/codecs/max98396.c:382 */
	/* interface format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		format |= MAX98396_PCM_FORMAT_I2S;
		break;
	case SND_SOC_DAIFMT_LEFT_J:
		format |= MAX98396_PCM_FORMAT_LJ;
		break;
	case SND_SOC_DAIFMT_DSP_A:
		format |= MAX98396_PCM_FORMAT_TDM_MODE1;
		break;
	case SND_SOC_DAIFMT_DSP_B:
		format |= MAX98396_PCM_FORMAT_TDM_MODE0;
		break;
	default:
		dev_err(component->dev, "DAI format %d unsupported\n",
			fmt & SND_SOC_DAIFMT_FORMAT_MASK);
		return -EINVAL;
	}
```

[`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) selects [`MAX98396_PCM_FORMAT_TDM_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L232) and [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) selects [`MAX98396_PCM_FORMAT_TDM_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L233), neighbours in the format field, the 0x3 and 0x4 values of bits 5:3:

```c
/* sound/soc/codecs/max98396.h:228 */
#define MAX98396_PCM_MODE_CFG_FORMAT_MASK	(0x7 << 3)

#define MAX98396_PCM_FORMAT_I2S			(0x0 << 3)
#define MAX98396_PCM_FORMAT_LJ			(0x1 << 3)
#define MAX98396_PCM_FORMAT_TDM_MODE0		(0x3 << 3)
#define MAX98396_PCM_FORMAT_TDM_MODE1		(0x4 << 3)
```

The selected code is written back into the format register. [`max98396_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.c#L347) updates the format field of [`MAX98396_R2041_PCM_MODE_CFG`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L45) and the BCLK-edge bit of [`MAX98396_R2042_PCM_CLK_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L46):

```c
/* sound/soc/codecs/max98396.c:425 */
	regmap_update_bits(max98396->regmap,
			   MAX98396_R2041_PCM_MODE_CFG,
			   format_mask, format);

	regmap_update_bits(max98396->regmap,
			   MAX98396_R2042_PCM_CLK_SETUP,
			   MAX98396_PCM_MODE_CFG_BCLKEDGE,
			   bclk_pol);
	...
	return 0;
}
```

Choosing DSP_B over DSP_A on this codec is one numeric difference, [`MAX98396_PCM_FORMAT_TDM_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L232) instead of [`MAX98396_PCM_FORMAT_TDM_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98396.h#L233) in bits 5:3 of register 0x2041, which selects the zero-bit-clock-delay layout rather than the one-bit-clock-delay layout.

The Maxim MAX98373 implements the same mapping with the same two TDM-mode codes, confirming the pattern is not specific to one part. [`max98373_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98373-i2c.c#L121) opens by decoding the inversion nibble into a BCLK-edge bit, exactly as the MAX98396 op does, before reaching the protocol switch:

```c
/* sound/soc/codecs/max98373-i2c.c:121 */
static int max98373_dai_set_fmt(struct snd_soc_dai *codec_dai, unsigned int fmt)
{
	struct snd_soc_component *component = codec_dai->component;
	struct max98373_priv *max98373 = snd_soc_component_get_drvdata(component);
	unsigned int format = 0;
	unsigned int invert = 0;
	...
	switch (fmt & SND_SOC_DAIFMT_INV_MASK) {
	case SND_SOC_DAIFMT_NB_NF:
		break;
	case SND_SOC_DAIFMT_IB_NF:
		invert = MAX98373_PCM_MODE_CFG_PCM_BCLKEDGE;
		break;
	default:
		dev_err(component->dev, "DAI invert mode unsupported\n");
		return -EINVAL;
	}
	...
```

It then maps DSP_A and DSP_B identically to the MAX98396 and shifts the chosen code into its own format field:

```c
/* sound/soc/codecs/max98373-i2c.c:146 */
	/* interface format */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		format = MAX98373_PCM_FORMAT_I2S;
		break;
	case SND_SOC_DAIFMT_LEFT_J:
		format = MAX98373_PCM_FORMAT_LJ;
		break;
	case SND_SOC_DAIFMT_DSP_A:
		format = MAX98373_PCM_FORMAT_TDM_MODE1;
		break;
	case SND_SOC_DAIFMT_DSP_B:
		format = MAX98373_PCM_FORMAT_TDM_MODE0;
		break;
	default:
		return -EINVAL;
	}

	regmap_update_bits(max98373->regmap,
			   MAX98373_R2024_PCM_DATA_FMT_CFG,
			   MAX98373_PCM_MODE_CFG_FORMAT_MASK,
			   format << MAX98373_PCM_MODE_CFG_FORMAT_SHIFT);

	return 0;
}
```

### TDM packing is set separately from the protocol

DSP_B carries several channels in successive slots, and the slot geometry is programmed by [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252), independent of the protocol. When the caller supplies zero masks the wrapper first synthesizes default contiguous masks through the optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op or the built-in [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213), which packs every slot starting at slot 0:

```c
/* sound/soc/soc-dai.c:213 */
static int snd_soc_xlate_tdm_slot_mask(unsigned int slots,
				       unsigned int *tx_mask,
				       unsigned int *rx_mask)
{
	if (*tx_mask || *rx_mask)
		return 0;

	if (!slots)
		return -EINVAL;

	*tx_mask = (1 << slots) - 1;
	*rx_mask = (1 << slots) - 1;

	return 0;
}
```

That fully populated `(1 << slots) - 1` mask is the contiguous packing a DSP_B frame uses unless the machine driver overrides it with explicit per-slot masks, which is exactly what the multi-amplifier boards do so each amp transmits on a distinct slot.

On an Intel SOF SSP board the slot count itself is not a constant in the machine driver but a value the firmware topology programmed for the SSP back end. The DSP_B branch reads it through [`sof_dai_get_tdm_slots()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L1050), a thin wrapper that pulls the `SOF_DAI_PARAM_INTEL_SSP_TDM_SLOTS` parameter out of the runtime and returns zero when none is set:

```c
/* sound/soc/sof/sof-audio.c:1050 */
int sof_dai_get_tdm_slots(struct snd_soc_pcm_runtime *rtd)
{
	return sof_dai_get_param(rtd, SOF_DAI_PARAM_INTEL_SSP_TDM_SLOTS);
}
```

The two-amplifier board callback feeds that slot count straight into [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252), so the DSP_B frame width tracks the topology rather than being hard-coded.

```
    snd_soc_xlate_tdm_slot_mask: default packing = (1 << slots) - 1
    ──────────────────────────────────────────────────────────────
    (zero tx/rx masks ──▶ every slot from slot 0, contiguous)

    slots = 4 ──▶ (1 << 4) - 1 = 0b1111

    tx_mask bits    7   6   5   4   3   2   1   0
                  ┌───┬───┬───┬───┬───┬───┬───┬───┐
                  │ 0 │ 0 │ 0 │ 0 │ 1 │ 1 │ 1 │ 1 │
                  └───┴───┴───┴───┴───┴───┴───┴───┘

    one DSP_B frame, slots packed back to back from slot 0:
                  ┌────────┬────────┬────────┬────────┐
                  │ slot 0 │ slot 1 │ slot 2 │ slot 3 │
                  └────────┴────────┴────────┴────────┘
       a machine driver overrides with per-amp one-hot masks
```

### x86-64 ACPI worked example: Intel SOF SSP amplifiers in DSP_B

On an Intel SOF system the speaker amplifiers sit on one SSP port as a TDM back end, configured by the shared Maxim helper. The back-end link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) carries [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31), and the back-end [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) callback branches on the DSP framing and gives each amplifier its own transmit slot.

The two-amplifier variant [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110) takes [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the runtime, walks each codec DAI, and on the DSP_A or DSP_B branch reads the topology slot count through [`sof_dai_get_tdm_slots()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L1050) before assigning per-amp slots from ACPI properties:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:110 */
static int max_98373_hw_params(struct snd_pcm_substream *substream,
			       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *codec_dai;
	...
	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		...
		switch (dai_link->dai_fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
		case SND_SOC_DAIFMT_DSP_A:
		case SND_SOC_DAIFMT_DSP_B:
			/* get the tplg configured tdm slot number */
			tdm_slots = sof_dai_get_tdm_slots(rtd);
			...
			/* get the tx mask from ACPI device properties */
			tx_mask = max_98373_get_tx_mask(codec_dai->dev);
			...
			ret = snd_soc_dai_set_tdm_slot(codec_dai, tx_mask,
						       max_98373_tdm_mask[i].rx,
						       tdm_slots,
						       params_width(params));
			...
			break;
		default:
			dev_dbg(codec_dai->dev, "codec is in I2S mode\n");
			break;
		}
	}
	return 0;
}
```

The four-amplifier variant [`max_98390_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L379) has the same shape but hard-codes a 4-slot DSP_B frame, assigning each amp a distinct transmit slot and a shared two-channel receive mask:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:379 */
static int max_98390_hw_params(struct snd_pcm_substream *substream,
			       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *codec_dai;
	int i, ret;

	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		...
		switch (dai_link->dai_fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
		case SND_SOC_DAIFMT_DSP_A:
		case SND_SOC_DAIFMT_DSP_B:
			/* 4-slot TDM */
			ret = snd_soc_dai_set_tdm_slot(codec_dai,
						       max_98390_tdm_mask[i].tx,
						       max_98390_tdm_mask[i].rx,
						       4,
						       params_width(params));
			...
			break;
		default:
			dev_dbg(codec_dai->dev, "codec is in I2S mode\n");
			break;
		}
	}
	return 0;
}
```

The per-amplifier transmit masks are one-hot, each amplifier driving a single distinct slot with its IV-sense feedback while all four read the same two playback slots:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:372 */
} max_98390_tdm_mask[] = {
	{.tx = 0x01, .rx = 0x3},
	{.tx = 0x02, .rx = 0x3},
	{.tx = 0x04, .rx = 0x3},
	{.tx = 0x08, .rx = 0x3},
};
```

The full path for a DSP_B SSP TDM board is a static [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) of DSP_B applied to each amplifier through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), so each amp's [`max98373_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/max98373-i2c.c#L121) writes the TDM-mode-0 zero-delay code, followed at stream start by [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) giving each amp its distinct slot, so the protocol selection and the slot layout remain two separate calls over the one shared SSP bus.

```
    Four-amp DSP_B: one-hot tx slots on one shared SSP bus
    ──────────────────────────────────────────────────────
    (max_98390_tdm_mask[]: tx one-hot, rx = 0x3 shared)

    amp 0   tx 0x01   ┐
    amp 1   tx 0x02   ├─ each amp transmits on a distinct slot
    amp 2   tx 0x04   │  rx 0x3 = both playback slots, shared
    amp 3   tx 0x08   ┘

    one shared SSP TDM frame (4 slots, DSP_B, zero delay):
    ┌────────┬────────┬────────┬────────┐
    │ slot 0 │ slot 1 │ slot 2 │ slot 3 │
    │ amp0 IV│ amp1 IV│ amp2 IV│ amp3 IV│   tx feedback
    └────────┴────────┴────────┴────────┘
        ▲        ▲        ▲        ▲
        └ amp0   └ amp1   └ amp2   └ amp3   (one-hot tx)
```
