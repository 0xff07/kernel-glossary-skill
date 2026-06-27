# ASoC clocking (sysclk, PLL, BCLK, LRCLK)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A serial audio link carries one frame of samples per audio period, and three clocks pace it, the master clock the codec or SoC runs from (MCLK, also called SYSCLK), the bit clock that shifts each data bit across the wire (BCLK), and the frame clock that marks the start of every sample frame (LRCLK, also called FSYNC or FRAME). ASoC configures this tree through a small set of DAI clocking entry points in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c), each a wrapper that tests for the matching op in [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and either calls the codec or CPU DAI implementation or falls through to a component-level fallback. The machine driver drives the whole sequence, usually from the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook of its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), where it knows the negotiated sample rate and can name the source clock, the PLL output, and the bit-clock-to-sample-rate ratio for the codec to program. [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) names the master clock and its direction, [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) configures a codec PLL to synthesize that clock from MCLK, and [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64), [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111), [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252), and [`snd_soc_dai_set_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) derive BCLK and LRCLK from it.

```
    Audio clock tree and the DAI op that programs each stage
    ────────────────────────────────────────────────────────

        crystal / PLL / CPU clock
                  │
                  ▼
    ┌──────────────────────────────┐   set_sysclk  (clk_id, freq, dir)
    │   MCLK / SYSCLK              │ ◀─ snd_soc_dai_set_sysclk()
    │   master clock, freq in Hz   │   set_pll     (synthesize from MCLK)
    └──────────────┬───────────────┘ ◀─ snd_soc_dai_set_pll()
                   │  BCLK = MCLK / x   (set_clkdiv)
                   ▼
    ┌──────────────────────────────┐   set_bclk_ratio (BCLK = LRC * ratio)
    │   BCLK   bit clock           │ ◀─ snd_soc_dai_set_bclk_ratio()
    │   shifts one data bit/edge   │   set_clkdiv  (divider from MCLK)
    └──────────────┬───────────────┘ ◀─ snd_soc_dai_set_clkdiv()
                   │  LRC = sample rate; BCLK = LRC * Channels * Word
                   ▼
    ┌──────────────────────────────┐   set_tdm_slot   (slots * slot_width)
    │   LRCLK / FSYNC / FRAME      │ ◀─ snd_soc_dai_set_tdm_slot()
    │   one pulse per sample frame │   set_channel_map (channel -> slot)
    └──────────────────────────────┘ ◀─ snd_soc_dai_set_channel_map()

    dir = SND_SOC_CLOCK_IN  (codec consumes the clock, CPU/SoC provides it)
    dir = SND_SOC_CLOCK_OUT (codec generates the clock, codec is provider)
```

## SUMMARY

Audio clocking in ASoC is the configuration of the master clock and the two derived serial clocks before a stream runs, and it flows through the DAI clocking wrappers in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c). The machine driver knows the negotiated parameters at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) time, so it calls [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) on the codec DAI to state the master clock frequency and whether the codec is the consumer or the provider of that clock, passing [`SND_SOC_CLOCK_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L145) when an external source feeds the codec and [`SND_SOC_CLOCK_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L146) when the codec generates it. When the master clock has to be synthesized from a different MCLK, the machine driver calls [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) with the input and requested output frequencies, and the codec programs its PLL. The bit clock is then derived as a divider of the master clock through [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64), or pinned to a fixed multiple of the sample rate through [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111).

The frame clock runs at exactly the sample rate, and its structure is set by [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252), which states how many time-division slots a frame holds and how wide each is, with [`snd_soc_dai_set_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) binding each DAI channel to a slot. Every wrapper follows one shape. It tests [`dai->driver->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) for the matching callback, calls it if present, and passes the result through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). The two clock wrappers that have a component-level equivalent, [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) and [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87), fall through to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) and [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) when the DAI itself supplies no op, while [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) returns `-EINVAL` and [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) returns `-ENOTSUPP` when the op is absent. A codec implements only the clocking ops its hardware exposes, and an SDCA codec reached over SoundWire programs its sample frequency through a Clock Source entity rather than a discrete sysclk op.

## SPECIFICATIONS

The clocking wrappers are Linux kernel software constructs and have no standalone hardware specification. The clock tree they configure (MCLK/SYSCLK, the BCLK bit clock, the LRCLK/FSYNC frame clock) is defined by the serial-audio interface standards the link runs, I2S, Left-Justified, Right-Justified, and the DSP/PCM TDM modes. For an SDCA codec on SoundWire the sample frequency is set through a Clock Source (CS) entity, represented in the kernel by the entity numbers and the [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) register-address macro in the SoundWire headers, and the underlying frame shape is documented in-tree by the SoundWire stream documentation.

## LINUX KERNEL

### Clocking wrappers (soc-dai.c)

- [`'\<snd_soc_dai_set_sysclk\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38): set the DAI master (MCLK) or system (SYSCLK) clock by [`clk_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), frequency, and direction; falls back to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78)
- [`'\<snd_soc_dai_set_pll\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87): configure a codec PLL to generate an output clock from an input clock; falls back to [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102)
- [`'\<snd_soc_dai_set_clkdiv\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64): set a clock divider to derive BCLK from the master clock; returns `-EINVAL` with no op
- [`'\<snd_soc_dai_set_bclk_ratio\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111): pin BCLK to a fixed multiple of the sample rate; returns `-ENOTSUPP` with no op
- [`'\<snd_soc_dai_set_tdm_slot\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252): set the per-frame slot count and slot width, computing default tx/rx masks through [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) or [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213) and recording each mask via [`snd_soc_dai_tdm_mask_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L523)
- [`'\<snd_soc_dai_set_channel_map\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) / [`'\<snd_soc_dai_get_channel_map\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L321): set and read the channel-to-slot mapping
- [`'\<snd_soc_xlate_tdm_slot_mask\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213): the built-in default that fills both masks with `(1 << slots) - 1` when the caller supplied none
- [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13): the error-annotation macro every wrapper returns through

### Component-level fallbacks (soc-component.c)

- [`'\<snd_soc_component_set_sysclk\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78): run the component [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op for codecs that expose clocking at the component rather than the DAI; returns `-ENOTSUPP` when absent
- [`'\<snd_soc_component_set_pll\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102): run the component [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; returns `-EINVAL` when absent

### Direction constants and ops type (soc-dai.h)

- [`'\<SND_SOC_CLOCK_IN\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L145): the `dir` value for [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) when an external source provides the clock and the codec consumes it (value 0)
- [`'\<SND_SOC_CLOCK_OUT\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L146): the `dir` value when the codec generates the clock and drives it out (value 1)
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct whose [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_clkdiv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_bclk_ratio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), and [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) fields the wrappers reach
- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the machine-level link callbacks, whose [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) member is the usual place clocks are set

### Negotiated-parameter accessors (pcm.h, pcm_params.h)

- [`'\<params_rate\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019): read the sample rate from the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408); LRCLK runs at this rate
- [`'\<params_width\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347): read the sample width in bits, which sets the slot width and feeds the BCLK = LRC * Channels * Word relationship

### SDCA SoundWire clock entity (codecs/rt722-sdca.c)

- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): the codec [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op that maps the sample rate to a frequency index and writes it into the SDCA Clock Source entity
- [`'rt722_sdca_ops':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246): the function pointer struct that carries no discrete clocking op, since the SoundWire bus clock is managed by the bus and the sample frequency is set inside [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)
- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): the macro that encodes a function, entity, control, and channel into the SoundWire register address the codec writes the frequency index to

### x86 ACPI machine driver clock setup (intel/boards)

- [`'\<sof_rt5682_hw_params\>':'sound/soc/intel/boards/sof_rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_rt5682.c#L259): the SOF SSP machine [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook that calls [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87), [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38), and [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) in sequence
- [`'sof_rt5682_ops':'sound/soc/intel/boards/sof_rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_rt5682.c#L405): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) that binds that hook to the DAI link
- [`'\<da7219_codec_init\>':'sound/soc/intel/boards/sof_da7219.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_da7219.c#L106): an SOF init callback that sets the codec master clock once with [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) and selects PLL bypass with [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the master clock, BCLK, and LRC terms and the three BCLK derivation formulas, with the ASoC clock APIs listed by kernel-doc
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the serial-audio interface families (AC97, I2S, PCM) whose wire clocks these ops program
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where a front-end DAI and a back-end DAI clock independently
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle and bus clock the SDCA codec joins instead of a discrete sysclk op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The clocking interface is six functions in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) plus two component-level fallbacks, and they map one to one onto the optional clocking and format ops of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269). A codec or CPU DAI fills in only the ops its hardware exposes, and an absent op is reported as success or as an error code depending on the wrapper.

| machine driver call | DAI op reached | absent-op result |
|---------------------|----------------|-------------------|
| [`snd_soc_dai_set_sysclk(dai, clk_id, freq, dir)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) | [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | component [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78), else `-ENOTSUPP` |
| [`snd_soc_dai_set_pll(dai, pll_id, source, freq_in, freq_out)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) | [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | component [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102), else `-EINVAL` |
| [`snd_soc_dai_set_clkdiv(dai, div_id, div)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) | [`set_clkdiv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | `-EINVAL` |
| [`snd_soc_dai_set_bclk_ratio(dai, ratio)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) | [`set_bclk_ratio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | `-ENOTSUPP` |
| [`snd_soc_dai_set_tdm_slot(dai, tx_mask, rx_mask, slots, slot_width)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) | [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | `-ENOTSUPP` |
| [`snd_soc_dai_set_channel_map(dai, tx_num, tx_slot, rx_num, rx_slot)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) | [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) | `-ENOTSUPP` |

### set_sysclk: name the master clock and its direction

[`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) states the master clock the codec runs from. The `clk_id` selects which of the codec's clock inputs is meant, `freq` is the frequency in Hz, and `dir` is [`SND_SOC_CLOCK_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L145) when an external source feeds the codec or [`SND_SOC_CLOCK_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L146) when the codec generates the clock. When the DAI supplies no [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op the call falls through to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78).

### set_pll: synthesize the master clock from MCLK

[`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) configures a codec PLL that takes an input clock of `freq_in` and produces `freq_out`. A machine driver calls it when the board MCLK does not directly match a frequency the codec can use for the requested sample rate, and the codec locks its PLL to bridge the two. Passing equal input and output frequencies, or a zero output, is the convention several codecs use to bypass or stop the PLL.

### set_clkdiv and set_bclk_ratio: derive BCLK

The bit clock is derived from the master clock in one of two ways. [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) sets a named divider so that BCLK = MCLK / x, and [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) instead pins BCLK to a fixed multiple of the frame clock so that BCLK = LRC * ratio. According to [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst), the bit clock can also be expressed as BCLK = LRC * Channels * Word Size, which is the form a TDM frame produces once the slot count and slot width are set.

### set_tdm_slot and set_channel_map: shape the frame

[`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) states how many time-division slots one LRCLK frame carries and how wide each is in bit-clock cycles, which fixes the bit count per frame and therefore BCLK relative to LRCLK. [`snd_soc_dai_set_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) then ties each DAI channel to a specific slot.

## DETAILS

### The wrapper shape every clocking entry point shares

The ASoC core never dereferences a clocking op directly. Each call goes through a wrapper in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) that tests for the op, calls it, and passes the result through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) is the variant that falls through to the component when the DAI has no op of its own:

```c
/* sound/soc/soc-dai.c:38 */
int snd_soc_dai_set_sysclk(struct snd_soc_dai *dai, int clk_id,
			   unsigned int freq, int dir)
{
	int ret;

	if (dai->driver->ops &&
	    dai->driver->ops->set_sysclk)
		ret = dai->driver->ops->set_sysclk(dai, clk_id, freq, dir);
	else
		ret = snd_soc_component_set_sysclk(dai->component, clk_id, 0,
						   freq, dir);

	return soc_dai_ret(dai, ret);
}
```

The `dir` argument is one of the two master clock direction constants, defined next to each other in the header:

```c
/* include/sound/soc-dai.h:142 */
/*
 * Master Clock Directions
 */
#define SND_SOC_CLOCK_IN		0
#define SND_SOC_CLOCK_OUT		1
```

[`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) has the same shape, taking the PLL identifier, a codec-specific source, and the input and output frequencies, and falling through to [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) when the DAI exposes no PLL op:

```c
/* sound/soc/soc-dai.c:87 */
int snd_soc_dai_set_pll(struct snd_soc_dai *dai, int pll_id, int source,
			unsigned int freq_in, unsigned int freq_out)
{
	int ret;

	if (dai->driver->ops &&
	    dai->driver->ops->set_pll)
		ret = dai->driver->ops->set_pll(dai, pll_id, source,
						freq_in, freq_out);
	else
		ret = snd_soc_component_set_pll(dai->component, pll_id, source,
						freq_in, freq_out);

	return soc_dai_ret(dai, ret);
}
```

The two divider wrappers have no component fallback. [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) seeds its return with `-EINVAL`, so a DAI that declares no [`set_clkdiv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op reports that error rather than silently succeeding:

```c
/* sound/soc/soc-dai.c:64 */
int snd_soc_dai_set_clkdiv(struct snd_soc_dai *dai,
			   int div_id, int div)
{
	int ret = -EINVAL;

	if (dai->driver->ops &&
	    dai->driver->ops->set_clkdiv)
		ret = dai->driver->ops->set_clkdiv(dai, div_id, div);

	return soc_dai_ret(dai, ret);
}
```

[`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) seeds `-ENOTSUPP` instead, the same not-supported convention the format wrappers use, so a machine driver can call it unconditionally and treat the not-supported return as a DAI that fixes its bit-clock ratio elsewhere:

```c
/* sound/soc/soc-dai.c:111 */
int snd_soc_dai_set_bclk_ratio(struct snd_soc_dai *dai, unsigned int ratio)
{
	int ret = -ENOTSUPP;

	if (dai->driver->ops &&
	    dai->driver->ops->set_bclk_ratio)
		ret = dai->driver->ops->set_bclk_ratio(dai, ratio);

	return soc_dai_ret(dai, ret);
}
```

### The clocking ops in the function pointer struct

Every wrapper above reaches one field of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269). The clocking fields and the format fields that pin LRCLK structure sit together near the top of the struct, and the comments state that they are optional and that the machine driver normally calls them from its hw_params:

```c
/* include/sound/soc-dai.h:269 */
struct snd_soc_dai_ops {
	...
	/*
	 * DAI clocking configuration, all optional.
	 * Called by soc_card drivers, normally in their hw_params.
	 */
	int (*set_sysclk)(struct snd_soc_dai *dai,
		int clk_id, unsigned int freq, int dir);
	int (*set_pll)(struct snd_soc_dai *dai, int pll_id, int source,
		unsigned int freq_in, unsigned int freq_out);
	int (*set_clkdiv)(struct snd_soc_dai *dai, int div_id, int div);
	int (*set_bclk_ratio)(struct snd_soc_dai *dai, unsigned int ratio);

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
	int (*set_channel_map)(struct snd_soc_dai *dai,
		unsigned int tx_num, const unsigned int *tx_slot,
		unsigned int rx_num, const unsigned int *rx_slot);
	int (*get_channel_map)(const struct snd_soc_dai *dai,
			unsigned int *tx_num, unsigned int *tx_slot,
			unsigned int *rx_num, unsigned int *rx_slot);
	...
};
```

According to the comment on the clocking block, "DAI clocking configuration, all optional. Called by soc_card drivers, normally in their hw_params", which is why the machine driver (the soc_card driver) drives the sequence while the codec only implements the ops, and why each wrapper guards against an absent op.

```
    struct snd_soc_dai_ops clocking/format fields and their wrapper
    ──────────────────────────────────────────────────────────────

    ┌─────────────────────┐
    │ snd_soc_dai_ops     │
    ├─────────────────────┤
    │ set_sysclk          │ ◀── snd_soc_dai_set_sysclk()
    │ set_pll             │ ◀── snd_soc_dai_set_pll()
    │ set_clkdiv          │ ◀── snd_soc_dai_set_clkdiv()
    │ set_bclk_ratio      │ ◀── snd_soc_dai_set_bclk_ratio()
    ├─────────────────────┤
    │ set_fmt             │ ◀── snd_soc_dai_set_fmt()
    │ xlate_tdm_slot_mask │ ◀── (used inside set_tdm_slot)
    │ set_tdm_slot        │ ◀── snd_soc_dai_set_tdm_slot()
    │ set_channel_map     │ ◀── snd_soc_dai_set_channel_map()
    │ get_channel_map     │ ◀── snd_soc_dai_get_channel_map()
    └─────────────────────┘

    all optional; an absent field makes the wrapper return its
    seeded code or fall through to the component op
```

### The component-level fallback for sysclk and PLL

A codec that exposes clocking at the component rather than the DAI level supplies a [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op on its [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) is the target of the fallback in [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38), and it seeds `-ENOTSUPP` so a component with no op reports not-supported:

```c
/* sound/soc/soc-component.c:78 */
int snd_soc_component_set_sysclk(struct snd_soc_component *component,
				 int clk_id, int source, unsigned int freq,
				 int dir)
{
	int ret = -ENOTSUPP;

	if (component->driver->set_sysclk)
		ret = component->driver->set_sysclk(component, clk_id, source,
						     freq, dir);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) is the matching fallback for [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87), and it seeds `-EINVAL`, so the absent-op result a machine driver sees depends on whether it called the sysclk or the PLL path.

### TDM slot configuration computes the default masks first

[`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) sets the frame structure that fixes BCLK relative to LRCLK. When `slots` is non-zero it first resolves the tx and rx slot masks, either through the DAI's own [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op or the built-in [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213), records each resolved mask with [`snd_soc_dai_tdm_mask_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L523), and only then calls the [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op with the slot count and slot width:

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

[`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213) is the default the wrapper uses when the caller supplied no explicit masks. It leaves any caller-provided mask untouched and otherwise marks every slot active by setting the low `slots` bits in both directions:

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

The recorded mask is stored per direction on the runtime DAI by [`snd_soc_dai_tdm_mask_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L523), which the PCM fixup path later reads back:

```c
/* include/sound/soc-dai.h:523 */
static inline void snd_soc_dai_tdm_mask_set(struct snd_soc_dai *dai, int stream,
					    unsigned int tdm_mask)
{
	dai->stream[stream].tdm_mask = tdm_mask;
}
```

### Channel-to-slot mapping

Once the frame holds N slots, [`snd_soc_dai_set_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) binds each DAI channel to one of them. The wrapper seeds `-ENOTSUPP`, so a DAI with no [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op reports not-supported and the core keeps the default identity mapping:

```c
/* sound/soc/soc-dai.c:297 */
int snd_soc_dai_set_channel_map(struct snd_soc_dai *dai,
				unsigned int tx_num, const unsigned int *tx_slot,
				unsigned int rx_num, const unsigned int *rx_slot)
{
	int ret = -ENOTSUPP;

	if (dai->driver->ops &&
	    dai->driver->ops->set_channel_map)
		ret = dai->driver->ops->set_channel_map(dai, tx_num, tx_slot,
							rx_num, rx_slot);
	return soc_dai_ret(dai, ret);
}
```

### Machine driver clock setup from hw_params: SOF on an SSP link

On an x86 ACPI system the codec sits on an SSP port driven by the SOF firmware, and the machine driver sets the clock tree from the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook of its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623). [`sof_rt5682_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_rt5682.c#L259) reads the codec DAI from the runtime, learns the topology-configured MCLK with `sof_dai_get_mclk()`, then programs the codec PLL, the system clock, and the TDM frame in that order, locking the PLL to produce `pll_out` from `pll_in`, selecting that PLL output as the codec SYSCLK with [`SND_SOC_CLOCK_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L145), and setting a two-slot frame whose slot width follows the negotiated sample width from [`params_width()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L347):

```c
/* sound/soc/intel/boards/sof_rt5682.c:378 */
		/* Configure pll for codec */
		ret = snd_soc_dai_set_pll(codec_dai, pll_id, pll_source, pll_in,
					  pll_out);
		if (ret < 0)
			dev_err(rtd->dev, "snd_soc_dai_set_pll err = %d\n", ret);
	}

	/* Configure sysclk for codec */
	ret = snd_soc_dai_set_sysclk(codec_dai, clk_id,
				     pll_out, SND_SOC_CLOCK_IN);
	if (ret < 0)
		dev_err(rtd->dev, "snd_soc_dai_set_sysclk err = %d\n", ret);

	/*
	 * slot_width should equal or large than data length, set them
	 * be the same
	 */
	ret = snd_soc_dai_set_tdm_slot(codec_dai, 0x0, 0x0, 2,
				       params_width(params));
	if (ret < 0) {
		dev_err(rtd->dev, "set TDM slot err:%d\n", ret);
		return ret;
	}

	return ret;
}
```

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook is bound to the DAI link through the machine ops struct, so the core calls it for every parameter negotiation on that link:

```c
/* sound/soc/intel/boards/sof_rt5682.c:405 */
static const struct snd_soc_ops sof_rt5682_ops = {
	.hw_params = sof_rt5682_hw_params,
};
```

The same [`SND_SOC_CLOCK_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L145)-with-MCLK pattern appears in a board that sets the clock once at link init rather than on each hw_params. [`da7219_codec_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_da7219.c#L106) reads the topology MCLK, sets the codec SYSCLK to it, and when the MCLK is one of the two frequencies the codec can use directly it puts the codec PLL in bypass by calling [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) with a zero output:

```c
/* sound/soc/intel/boards/sof_da7219.c:120 */
	ret = snd_soc_dai_set_sysclk(codec_dai, DA7219_CLKSRC_MCLK, mclk_rate,
				     SND_SOC_CLOCK_IN);
	if (ret) {
		dev_err(rtd->dev, "fail to set sysclk, ret %d\n", ret);
		return ret;
	}
	...
	if (ctx->da7219.mclk_en &&
	    (mclk_rate == 12288000 || mclk_rate == 24576000)) {
		/* PLL bypass mode */
		dev_dbg(rtd->dev, "pll bypass mode, mclk rate %d\n", mclk_rate);

		ret = snd_soc_dai_set_pll(codec_dai, 0, DA7219_SYSCLK_MCLK, 0, 0);
```

Back on the per-hw_params path, the codec DAI takes three calls in order, locking its PLL to make pll_out from MCLK, selecting that output as SYSCLK with the IN direction, then setting a two-slot frame sized to the sample width:

```
    sof_rt5682_hw_params clock-setup order on the codec DAI
    ──────────────────────────────────────────────────────

    ┌────────────────────────────────────────────────────┐
    │ snd_soc_dai_set_pll(codec_dai, pll_in, pll_out)    │
    │   lock the codec PLL: pll_out synthesized from MCLK │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │ snd_soc_dai_set_sysclk(codec_dai, pll_out, IN)     │
    │   select pll_out as SYSCLK, dir = SND_SOC_CLOCK_IN  │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │ snd_soc_dai_set_tdm_slot(codec_dai, 2, width)      │
    │   2-slot frame, slot_width = params_width(params)   │
    └────────────────────────────────────────────────────┘

    SND_SOC_CLOCK_IN ▶ codec consumes SYSCLK; the SSP/CPU is
    the bit-clock and frame provider for the link
```

### Worked example: an SDCA codec sets its sample frequency over SoundWire

A SoundWire codec does not take a discrete sysclk or PLL op, because the SoundWire bus owns the wire clock and the frame shape. The Realtek RT722 is an SDCA codec on SoundWire, and its function pointer struct carries no clocking field at all:

```c
/* sound/soc/codecs/rt722-sdca.c:1246 */
static const struct snd_soc_dai_ops rt722_sdca_ops = {
	.hw_params	= rt722_sdca_pcm_hw_params,
	.hw_free	= rt722_sdca_pcm_hw_free,
	.set_stream	= rt722_sdca_set_sdw_stream,
	.shutdown	= rt722_sdca_shutdown,
};
```

The sample-frequency configuration that on an I2S codec would be reached through a sysclk or clkdiv op is instead done inside the codec [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op. [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) reads the negotiated rate with [`params_rate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019) and maps each supported rate to an SDCA frequency index:

```c
/* sound/soc/codecs/rt722-sdca.c:1184 */
	/* sampling rate configuration */
	switch (params_rate(params)) {
	case 44100:
		sampling_rate = RT722_SDCA_RATE_44100HZ;
		break;
	case 48000:
		sampling_rate = RT722_SDCA_RATE_48000HZ;
		break;
	case 96000:
		sampling_rate = RT722_SDCA_RATE_96000HZ;
		break;
	case 192000:
		sampling_rate = RT722_SDCA_RATE_192000HZ;
		break;
	default:
		dev_err(component->dev, "%s: Rate %d is not supported\n",
			__func__, params_rate(params));
		return -EINVAL;
	}
```

It then writes that index into the Clock Source (CS) entity for the relevant audio function, selecting the entity by the DAI id and addressing it with [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), which encodes the function number, the entity, the control, and the channel into a SoundWire register address:

```c
/* sound/soc/codecs/rt722-sdca.c:1203 */
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

	return 0;
}
```

The headset function on `RT722_AIF1` carries two Clock Source entities, `RT722_SDCA_ENT_CS01` for the jack codec and `RT722_SDCA_ENT_CS11` for the second converter, so both receive the same frequency index; the speaker amplifier function on `RT722_AIF2` and the microphone-array function on `RT722_AIF3` each have one. The bit clock and frame clock themselves are produced by the SoundWire bus from the frame rate stated in the stream configuration, so the codec only needs to tell its internal clock sources which rate the bus frame will run at.

```
    rt722_sdca_pcm_hw_params: DAI id ▶ SDCA Clock Source entities
    ────────────────────────────────────────────────────────────
    (params_rate ▶ sampling_rate index, written via SDW_SDCA_CTL)

    dai->id        function              Clock Source entity
    ┌──────────┐   ┌──────────────────┐  ┌──────────────────┐
    │ RT722_   │──▶│ FUNC_NUM_JACK_   │─▶│ RT722_SDCA_ENT_  │
    │ AIF1     │   │ CODEC            │  │ CS01             │
    │          │   │                  │─▶│ CS11             │
    └──────────┘   └──────────────────┘  └──────────────────┘
    ┌──────────┐   ┌──────────────────┐  ┌──────────────────┐
    │ RT722_   │──▶│ FUNC_NUM_AMP     │─▶│ RT722_SDCA_ENT_  │
    │ AIF2     │   │                  │  │ CS31             │
    └──────────┘   └──────────────────┘  └──────────────────┘
    ┌──────────┐   ┌──────────────────┐  ┌──────────────────┐
    │ RT722_   │──▶│ FUNC_NUM_MIC_    │─▶│ RT722_SDCA_ENT_  │
    │ AIF3     │   │ ARRAY            │  │ CS1F             │
    └──────────┘   └──────────────────┘  └──────────────────┘

    each entity is addressed by SDW_SDCA_CTL(func, entity,
    SAMPLE_FREQ_INDEX, 0) and receives the same rate index
```
