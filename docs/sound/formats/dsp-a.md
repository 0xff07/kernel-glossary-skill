# DSP_A audio format

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

DSP_A (also called DSP mode A or PCM mode A) is the time-division-multiplexed serial-audio framing ASoC selects with the [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) format word, defined as [`SND_SOC_DAI_FORMAT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L153) with value 4 and the in-tree comment "L data MSB after FRM LRC". A single short frame-sync pulse marks the start of a frame, the first data bit is presented one BCLK after the frame-sync edge, and the channel slots are packed back to back most-significant-bit first, which is the framing the kernel uses to drive several codecs or amplifiers sharing one bit clock and one data line. A machine or platform driver requests this framing through [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), which hands the word to each DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback, and it pairs the framing with a slot map programmed through [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252). On an x86-64 Intel SOF platform the Maxim multi-amp helper [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110) is the worked example, programming a per-amp TDM slot on a shared SSP bus once the link format is [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30).

```
    DSP_A (PCM mode A): 1-BCLK data delay, slots packed, MSB first
    ──────────────────────────────────────────────────────────────

             ┌─┐                                         ┌─┐
    FSYNC  ──┘ └─────────────────────────────────────────┘ └────
             one short pulse marks the frame start

           ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌
    BCLK ──┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘
            ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲
            │ 1-BCLK delay after FSYNC, then data
            │
    DATA  ──┼───◀slot0  msb..lsb▶◀slot1  msb..lsb▶◀slot2 ..▶──────
            │   ◀──── 1 ────▶◀──── 2 ────▶◀──── 3 ────▶
          FSYNC edge   (each slot = slot_width BCLKs, packed back to back)

    Mode A: MSB on the first BCLK after FRAME/SYNC (data delayed 1 bit).
    Mode B (DSP_B): MSB on the rising edge of FRAME/SYNC (no delay).
    slot0, slot1, slot2 ... carry one channel each (mono/TDM, no L/R phase).
```

## SUMMARY

DSP_A is one of the serial-audio framings encoded in the low four bits selected by [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f). The macro [`SND_SOC_DAIFMT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30) expands to [`SND_SOC_DAI_FORMAT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L153), the constant 4, one value below [`SND_SOC_DAIFMT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31) (value 5). A machine driver sets the link format either statically through the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field of its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) or at runtime through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), and either path ends in [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) per DAI, which invokes the codec or CPU DAI's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback.

The framing has a single short frame-sync pulse, a one-BCLK data delay after the frame-sync edge, and channel slots packed contiguously most-significant-bit first. There is no left/right channel phase as in I2S, so each slot is one independent channel, which lets several devices read distinct slots off one shared bus. That arrangement is the common way to wire multiple smart amplifiers, and it pairs with [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) to tell each device which slots to transmit and receive. The codec side is shown by [`tas2764_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.c#L376), where the DSP_A case sets the receive start slot to 1, encoding the one-BCLK delay, while DSP_B and Left-Justified set it to 0. The platform side is shown by [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110) on an Intel SOF SSP TDM board, which reads the slot count from the SOF topology with [`sof_dai_get_tdm_slots()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L1050) and assigns each MAX98373 amplifier its own transmit slot for IV-sense feedback.

## SPECIFICATIONS

DSP_A is the ASoC name for what [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst) calls PCM mode A, a four-wire PCM framing (BCLK, SYNC, Tx, Rx) that supports Time Division Multiplexing so several devices use the bus at once. According to that document, in Mode A "MSB is transmitted on falling edge of first BCLK after FRAME/SYNC", and in Mode B "MSB is transmitted on rising edge of FRAME/SYNC". The framing follows the conventions of the codec and host serial-port datasheets (the TI TAS2764 ASI, the Maxim MAX98373 PCM interface, and the Intel SSP) rather than a single industry standard.

## LINUX KERNEL

### Format word macros (soc-dai.h, asoc.h)

- [`'\<SND_SOC_DAIFMT_DSP_A\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L30): the DSP_A format macro, expands to [`SND_SOC_DAI_FORMAT_DSP_A`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L153)
- [`'\<SND_SOC_DAIFMT_DSP_B\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L31): the DSP_B format macro, the zero-delay sibling, expands to [`SND_SOC_DAI_FORMAT_DSP_B`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L154)
- [`'\<SND_SOC_DAI_FORMAT_DSP_A\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L153): the underlying value 4, commented "L data MSB after FRM LRC"
- [`'\<SND_SOC_DAIFMT_FORMAT_MASK\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135): the value 0x000f selecting the framing field within the format word

### Format and slot wrappers (soc-dai.c, soc-core.c)

- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): apply a `SND_SOC_DAIFMT_*` word to one DAI by calling its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, returning `-ENOTSUPP` if absent
- [`'\<snd_soc_dai_set_tdm_slot\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252): set the active TX/RX slot masks, slot count, and slot width that DSP_A framing carries
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): apply one link format to every CPU and codec DAI on a runtime, flipping the clock-provider role for the CPU end
- [`'\<snd_soc_xlate_tdm_slot_mask\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213): the default mask builder used by [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) when a DAI supplies no [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op

### Format and slot callback fields (soc-dai.h)

- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the DAI function pointer struct whose [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) and [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) members a codec fills in
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the link descriptor carrying the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) field a machine driver sets to DSP_A

### TI TAS2764 codec (codecs/tas2764.c)

- [`'\<tas2764_set_fmt\>':'sound/soc/codecs/tas2764.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.c#L376): the [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op; the DSP_A case sets the RX start slot to 1, encoding the one-BCLK data delay
- [`'\<tas2764_set_dai_tdm_slot\>':'sound/soc/codecs/tas2764.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.c#L444): the [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) op that picks the output slots and the IV-sense slots
- [`'tas2764_dai_ops':'sound/soc/codecs/tas2764.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.c#L512): the function pointer struct wiring both callbacks

### Intel SOF SSP multi-amp board (boards/sof_maxim_common.c, sof-audio.c)

- [`'\<max_98373_hw_params\>':'sound/soc/intel/boards/sof_maxim_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110): the machine [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook that programs a per-amp TDM slot when the link format is DSP_A or DSP_B
- [`'\<max_98373_get_tx_mask\>':'sound/soc/intel/boards/sof_maxim_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L94): build one amp's TX slot mask from its ACPI `maxim,vmon-slot-no` and `maxim,imon-slot-no` properties
- [`'max_98373_ops':'sound/soc/intel/boards/sof_maxim_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L233): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) binding [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110)
- [`'\<sof_dai_get_tdm_slots\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L1050): read the SSP TDM slot count the topology configured for the runtime

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the AC97, I2S, and PCM DAI families, including PCM mode A and mode B and the note that PCM supports Time Division Multiplexing
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the BCLK and frame-sync clock relationships the format word's polarity bits configure
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide covering the DAI driver and its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end/back-end split an Intel SOF SSP back end uses to reach the amplifiers

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

DSP_A is a wire framing rather than a kernel register block, so the registers it touches are codec-internal serial-port registers a [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op programs. On the TI TAS2764 the framing maps onto two fields, the frame-start polarity in `TAS2764_TDM_CFG0` and the RX start-slot offset in `TAS2764_TDM_CFG1`, the second of which carries the one-BCLK delay that distinguishes DSP_A from DSP_B. The slot geometry is programmed separately in `TAS2764_TDM_CFG2` (slot width), `TAS2764_TDM_CFG3` (the output slots), and `TAS2764_TDM_CFG5`/`TAS2764_TDM_CFG6` (the voltage- and current-sense slots), set by [`tas2764_set_dai_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.c#L444).

```
    TAS2764 ASI fields that DSP_A framing programs
    ──────────────────────────────────────────────

    set_fmt (framing)            set_tdm_slot (slot geometry)
    ┌──────────────────────┐     ┌──────────────────────────────┐
    │ TAS2764_TDM_CFG0     │     │ TAS2764_TDM_CFG2  slot width │
    │   FRAME_START pol    │     │ TAS2764_TDM_CFG3  L/R slots  │
    │ TAS2764_TDM_CFG1     │     │ TAS2764_TDM_CFG5  V-sense    │
    │   RX start slot:     │     │ TAS2764_TDM_CFG6  I-sense    │
    │   1 = DSP_A (delay)  │     └──────────────────────────────┘
    │   0 = DSP_B / LEFT_J │
    └──────────────────────┘
```

The register names above are TI TAS2764 datasheet field names. Their macro values are private to [`sound/soc/codecs/tas2764.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2764.h); the framing decision is carried by the C control flow rather than by a single register value.

## DETAILS

### The format word and where DSP_A sits in it

A DAI format word is an `unsigned int` whose low four bits hold the framing, selected by [`SND_SOC_DAIFMT_FORMAT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L135) (0x000f), with the clock divider, inversion, and clock-provider fields stacked above it:

```c
/* include/sound/soc-dai.h:135 */
#define SND_SOC_DAIFMT_FORMAT_MASK		0x000f
#define SND_SOC_DAIFMT_CLOCK_MASK		0x00f0
#define SND_SOC_DAIFMT_INV_MASK			0x0f00
#define SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK	0xf000
```

The framing values are an enumeration in the userspace topology ABI so a topology file and the kernel agree on the numbers. DSP_A is 4 and DSP_B is 5, and the comments record the timing difference they share:

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

The comment "L data MSB after FRM LRC" on DSP_A versus "L data MSB during FRM LRC" on DSP_B records the one-bit difference. In DSP_A the first data bit comes one BCLK after the frame edge, and in DSP_B it coincides with the frame edge. The dai.rst PCM section states the same rule in clock-edge terms, mode A putting the MSB on the falling edge of the first BCLK after FRAME/SYNC while mode B puts it on the rising edge of FRAME/SYNC.

```
    Format word nibbles, with DSP_A in the low FMT field
    ────────────────────────────────────────────────────

    bit   15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
         ┌──────────────┬──────────────┬──────────────┬─────┐
         │   PROVIDER   │     INV      │    CLOCK     │ FMT │
         │   (15:12)    │   (11:8)     │    (7:4)     │(3:0)│
         └────┬─────────┴────┬─────────┴────┬─────────┴──┬──┘
              │              │              │            │
              │              │              │            └─ FORMAT_MASK 0x000f
              │              │              └────────────── CLOCK_MASK  0x00f0
              │              └───────────────────────────── INV_MASK    0x0f00
              └──────────────────────────────────────────── PROVIDER    0xf000

    FMT (3:0) = SND_SOC_DAIFMT_FORMAT_MASK (0x000f):
      DSP_A = 4    DSP_B = 5    (DSP_A sits in this nibble)
```

### snd_soc_dai_set_fmt hands DSP_A to the codec

[`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) applies a format word to one DAI, calling its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op when present and returning `-ENOTSUPP` for a DAI with no format op:

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

The [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) member it dereferences is grouped with the slot callbacks in the DAI function pointer struct:

```c
/* include/sound/soc-dai.h:290 */
	int (*set_fmt)(struct snd_soc_dai *dai, unsigned int fmt);
	int (*xlate_tdm_slot_mask)(unsigned int slots,
		unsigned int *tx_mask, unsigned int *rx_mask);
	int (*set_tdm_slot)(struct snd_soc_dai *dai,
		unsigned int tx_mask, unsigned int rx_mask,
		int slots, int slot_width);
```

A machine driver rarely calls the per-DAI setter itself; it sets one link-wide [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) of DSP_A and lets [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) fan it out to every codec and CPU DAI, flipping only the clock-provider field for the CPU end. The `-ENOTSUPP` tolerance in that loop lets a codec that supports DSP_A sit on a link with a CPU DAI that has no [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op, the codec programming the framing and the CPU skipping it.

### tas2764_set_fmt encodes the one-BCLK delay

The TI TAS2764 is a smart amplifier with current and voltage sense, common on x86-64 laptops driven by Intel SOF. Its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op maps the framing field to the receive start slot. The DSP_A and I2S cases share a start-slot value of 1, with I2S first toggling the frame-start polarity and falling through, while DSP_B and Left-Justified use 0:

```c
/* sound/soc/codecs/tas2764.c:412 */
	switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
	case SND_SOC_DAIFMT_I2S:
		asi_cfg_0 ^= TAS2764_TDM_CFG0_FRAME_START;
		fallthrough;
	case SND_SOC_DAIFMT_DSP_A:
		tdm_rx_start_slot = 1;
		break;
	case SND_SOC_DAIFMT_DSP_B:
	case SND_SOC_DAIFMT_LEFT_J:
		tdm_rx_start_slot = 0;
		break;
	default:
		dev_err(tas2764->dev,
			"DAI Format is not found, fmt=0x%x\n", fmt);
		return -EINVAL;
	}
```

The `tdm_rx_start_slot` value is written into the start-slot field, delaying the first received bit by one BCLK when the value is 1:

```c
/* sound/soc/codecs/tas2764.c:436 */
	ret = snd_soc_component_update_bits(component, TAS2764_TDM_CFG1,
					    TAS2764_TDM_CFG1_MASK,
					    (tdm_rx_start_slot << TAS2764_TDM_CFG1_51_SHIFT));
	if (ret < 0)
		return ret;

	return 0;
```

This is the contrast with DSP_B in hardware terms: DSP_A sets `tdm_rx_start_slot = 1` so the amplifier begins sampling one BCLK after the frame-sync edge, while DSP_B (and Left-Justified) set it to 0 so the amplifier begins sampling on the frame-sync edge itself. The codec wires both callbacks through its function pointer struct, so the same DAI accepts the framing and the slot map:

```c
/* sound/soc/codecs/tas2764.c:512 */
static const struct snd_soc_dai_ops tas2764_dai_ops = {
	.mute_stream = tas2764_mute,
	.hw_params  = tas2764_hw_params,
	.set_fmt    = tas2764_set_fmt,
	.set_tdm_slot = tas2764_set_dai_tdm_slot,
	.no_capture_mute = 1,
};
```

The format callback in that struct maps the framing onto the receive start slot, a value of 1 lifting the slot-0 MSB one BCLK clear of the FSYNC edge and a value of 0 leaving it on the edge:

```
    tas2764_set_fmt: tdm_rx_start_slot sets where the slot-0 MSB lands
    ─────────────────────────────────────────────────────────────────
    (▼ = the FSYNC edge that opens the frame; each cell is one BCLK)

                   ▼
    FSYNC ─────────┐
                   └────────────────────────────

    DSP_A               ┌────┬────┬────┐   start_slot = 1: MSB one BCLK
    SD         ·········│MSB │ b14│ b13│   after the FSYNC edge

    DSP_B          ┌────┬────┬────┐        start_slot = 0: MSB on the
    SD             │MSB │ b14│ b13│        FSYNC edge (no delay)
                   └────┘
                   one BCLK (DSP_A delay)
```

### set_tdm_slot pairs the framing with a slot map

DSP_A carries no channel-phase information, so the channel-to-slot assignment comes from [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252). It computes default masks (through the DAI's optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op or the built-in [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213)), records them, then calls the DAI's [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) op:

```c
/* sound/soc/soc-dai.c:252 */
int snd_soc_dai_set_tdm_slot(struct snd_soc_dai *dai,
			     unsigned int tx_mask, unsigned int rx_mask,
			     int slots, int slot_width)
{
	int ret = -ENOTSUPP;
	int stream;
	unsigned int *tdm_mask[] = {
		&tx_mask,
		&rx_mask,
	};

	if (slots) {
		if (dai->driver->ops &&
		    dai->driver->ops->xlate_tdm_slot_mask)
			ret = dai->driver->ops->xlate_tdm_slot_mask(slots, &tx_mask, &rx_mask);
		else
			ret = snd_soc_xlate_tdm_slot_mask(slots, &tx_mask, &rx_mask);
		if (ret)
			goto err;
	}

	for_each_pcm_streams(stream)
		snd_soc_dai_tdm_mask_set(dai, stream, *tdm_mask[stream]);

	if (dai->driver->ops &&
	    dai->driver->ops->set_tdm_slot)
		ret = dai->driver->ops->set_tdm_slot(dai, tx_mask, rx_mask,
						      slots, slot_width);
err:
	return soc_dai_ret(dai, ret);
}
```

On the TAS2764 the [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) op derives the two output slots from the TX mask with `__ffs`, validates them against the slot count, and writes them with the slot width:

```c
/* sound/soc/codecs/tas2764.c:444 */
static int tas2764_set_dai_tdm_slot(struct snd_soc_dai *dai,
				unsigned int tx_mask,
				unsigned int rx_mask,
				int slots, int slot_width)
{
	struct snd_soc_component *component = dai->component;
	int left_slot, right_slot;
	int slots_cfg;
	int ret;

	if (tx_mask == 0 || rx_mask != 0)
		return -EINVAL;

	left_slot = __ffs(tx_mask);
	tx_mask &= ~(1 << left_slot);
	if (tx_mask == 0) {
		right_slot = left_slot;
	} else {
		right_slot = __ffs(tx_mask);
		tx_mask &= ~(1 << right_slot);
	}

	if (tx_mask != 0 || left_slot >= slots || right_slot >= slots)
		return -EINVAL;

	slots_cfg = (right_slot << TAS2764_TDM_CFG3_RXS_SHIFT) | left_slot;

	ret = snd_soc_component_write(component, TAS2764_TDM_CFG3, slots_cfg);
	if (ret)
		return ret;
	...
}
```

Because each amplifier on the bus is given a distinct slot, several TAS2764 or MAX98373 parts share the same BCLK and data line while each reads only its assigned slots, which is the reason DSP_A is the usual framing for multi-amp boards.

```
    tas2764_set_dai_tdm_slot: TX mask picks two slots into TDM_CFG3
    ──────────────────────────────────────────────────────────────

    tx_mask bits    7   6   5   4   3   2   1   0
                  ┌───┬───┬───┬───┬───┬───┬───┬───┐
                  │ 0 │ 0 │ 0 │ 0 │ 0 │ 0 │ 1 │ 1 │ set bits mark two slots
                  └───┴───┴───┴───┴───┴───┴─┬─┴─┬─┘
                                            │   └── __ffs lowest set ▶ left_slot
                                            └── __ffs next set ▶ right_slot

    these two slot numbers pack into TAS2764_TDM_CFG3:
                      ┌────────────────────┬──────────────┐
                      │ right_slot         │ left_slot    │
                      │ (<< RXS_SHIFT)     │ (low field)  │
                      └────────────────────┴──────────────┘
```

### Worked example: Intel SOF SSP TDM multi-amp board

On an x86-64 Intel SOF platform the speaker amplifiers hang off an SSP port programmed for TDM and the link format is DSP_A. The machine helper [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110) runs once per stream and walks every codec DAI. When the link format field is DSP_A or DSP_B it reads the slot count the SOF topology configured, builds each amp's TX mask from its ACPI properties, validates the masks against an accumulator, and calls [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) for that amp:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:110 */
static int max_98373_hw_params(struct snd_pcm_substream *substream,
			       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *codec_dai;
	int i;
	int tdm_slots;
	unsigned int tx_mask;
	unsigned int tx_mask_used = 0x0;
	int ret = 0;

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
			if (!tx_mask)
				return -EINVAL;

			if (tx_mask & tx_mask_used) {
				dev_err(codec_dai->dev, "invalid tx mask 0x%x, used 0x%x\n",
					tx_mask, tx_mask_used);
				return -EINVAL;
			}

			tx_mask_used |= tx_mask;
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

The `default` arm makes the DSP_A path opt-in, since the helper programs slots only when the static link format selects DSP_A or DSP_B and any other format leaves the amps in plain I2S. The `tx_mask_used` accumulator rejects two amps that claim the same TX slot, which is the failure DSP_A multi-amp wiring has to avoid because both amps drive the one shared data line during their feedback slots.

The per-amp TX mask is computed from ACPI `_DSD` device properties, so the firmware describes which slot each amplifier reports its IV-sense data on:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:94 */
static unsigned int max_98373_get_tx_mask(struct device *dev)
{
	int vmon_slot;
	int imon_slot;

	if (device_property_read_u32(dev, "maxim,vmon-slot-no", &vmon_slot))
		vmon_slot = 0;

	if (device_property_read_u32(dev, "maxim,imon-slot-no", &imon_slot))
		imon_slot = 1;

	dev_dbg(dev, "vmon_slot %d imon_slot %d\n", vmon_slot, imon_slot);

	return (0x1 << vmon_slot) | (0x1 << imon_slot);
}
```

The helper is bound to the link through the machine ops struct, so the SSP back end runs it at hardware-parameter time:

```c
/* sound/soc/intel/boards/sof_maxim_common.c:233 */
static const struct snd_soc_ops max_98373_ops = {
	.hw_params = max_98373_hw_params,
	.trigger = max_98373_trigger,
};
```

The full path for a DSP_A SSP TDM board is a static [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L749) of DSP_A on the amplifier link, applied to each amp's [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) op through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) so each amp programs the one-BCLK-delayed framing, followed at stream start by [`max_98373_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_maxim_common.c#L110) calling [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) so each amp transmits its feedback on a distinct slot of the shared SSP bus.

```
    Multi-amp DSP_A: each amp owns distinct slots on one shared SSP bus
    ──────────────────────────────────────────────────────────────────
    (tx_mask = set bits at vmon_slot, imon_slot; default vmon 0, imon 1)

      ACPI _DSD per amp
      ┌──────────────────────┐
      │ amp 0  vmon 0  imon 1│ ──▶  tx_mask 0 = 0b0011   (slots 0, 1)
      │ amp 1  vmon 2  imon 3│ ──▶  tx_mask 1 = 0b1100   (slots 2, 3)
      └──────────────────────┘
                            tx_mask_used OR-accumulates each amp;
                            a reused slot bit ──▶ -EINVAL

      one shared SSP TDM frame (slots packed back to back, DSP_A):
      ┌────────┬────────┬────────┬────────┐
      │ slot 0 │ slot 1 │ slot 2 │ slot 3 │
      │ amp0 V │ amp0 I │ amp1 V │ amp1 I │
      └────────┴────────┴────────┴────────┘
        ◀── amp 0 reads ──▶ ◀── amp 1 reads ──▶
```
