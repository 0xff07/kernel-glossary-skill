# DAI operations (snd_soc_dai_ops)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAI operations table, [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), is the function pointer struct a codec or platform driver attaches to its [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) to handle clocking, wire-format, and PCM events on one Digital Audio Interface. Every field is optional, and the ASoC core reaches a field only through a [`snd_soc_dai_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) wrapper in [`sound/soc/soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) that tests the op for presence, invokes it, records a per-substream mark on the teardown-bearing ops, and passes the return value through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). The callbacks fall into four groups by when they run. The driver callbacks ([`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L271), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L272), [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L276), [`compress_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L274)) run once as the DAI is brought up, the clocking ([`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L283), [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L285), [`set_clkdiv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L287), [`set_bclk_ratio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L288)) and format ([`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294), [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297), [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L300), [`set_tristate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L306)) callbacks are driven by the machine driver from its hw_params hook, and the PCM callbacks ([`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L322), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324)) fire during stream operation. The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec is the worked example. Its [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246) fills only four callbacks ([`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308), [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324)) and leaves every other op NULL behind the wrapper guards.

```
    When each snd_soc_dai_ops callback fires over a substream's life
    ────────────────────────────────────────────────────────────────

    card bring-up        machine hw_params        open ─▶ run ─▶ close
    (once per DAI)       (once per stream cfg)    (per substream)
          │                     │                        │
          ▼                     ▼                        ▼
    ┌──────────────┐    ┌────────────────────┐   ┌────────────────────────┐
    │ probe        │    │ set_sysclk set_pll │   │ startup                │
    │ remove       │    │ set_clkdiv          │   │ hw_params  ──┐ push     │
    │ pcm_new      │    │ set_bclk_ratio      │   │ prepare      │ hw_params│
    │ compress_new │    │ set_fmt             │   │ trigger    ──┤ push     │
    └──────────────┘    │ set_tdm_slot        │   │ mute_stream  │ trigger  │
                        │ set_channel_map     │   │ delay        │          │
                        │ set_tristate        │   │ hw_free    ◀─┘ match    │
                        │ set_stream         │   │ shutdown   ◀── match    │
                        └────────────────────┘   └─────────────────────────┘

    every op is optional; an absent op makes its snd_soc_dai_*() wrapper
    return 0 or -ENOTSUPP, so no codec code runs.  set_sysclk and set_pll
    fall back to the component-level op when the DAI supplies none.  the
    push/match marks let an error during multi-DAI bring-up tear down only
    the DAIs whose setup op actually ran.
```

## SUMMARY

[`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) is one of the two halves of a DAI driver, the other being the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) descriptor that points at it. A driver populates only the callbacks its hardware needs and the rest stay NULL. The ASoC core treats the table as a set of optional hooks, each reached through a matching public wrapper in [`sound/soc/soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) such as [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405), [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194), or [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618).

Each wrapper follows one shape. It checks that [`dai->driver->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and the specific op pointer are present, calls the op, records the substream in a per-DAI mark ([`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438)) for the ops that have a teardown partner, and routes the result through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). The marks let the teardown wrappers ([`snd_soc_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422), [`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456)) skip a DAI whose setup op never ran during an error rollback. The clocking and format wrappers add one extra rule. [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) and [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) fall through to the component-level clock op when the DAI has no op of its own, while the rest return a defined error code for an absent op.

The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339) op is special because [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) drives every DAI of a runtime in command-order, applying the optional mute-on-trigger behavior and the rollback marks, and the comment on the field warns that the command stream may be unbalanced so the op handles each command on its own. Per-direction usage is counted by [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) and read back through [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529), which the suspend and DAPM paths consult to decide whether a DAI is carrying audio.

## SPECIFICATIONS

[`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) is a Linux kernel software construct and has no standalone hardware specification. The serial-audio wire formats its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) callback programs (I2S, DSP_A, DSP_B, Left-Justified, Right-Justified, PDM, AC97) are defined by their respective interface standards and are described on the audio-format pages.

## LINUX KERNEL

### The ops table and its descriptor (include/sound/soc-dai.h)

- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct grouping the driver, clocking, format, stream, mute, and PCM callbacks plus the [`auto_selectable_formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L356) list, the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L360)/[`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L361) fields, and the [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L364)/[`mute_unmute_on_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L365) bit fields
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the static descriptor that carries the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointer
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): the runtime instance that holds the [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438)/[`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438)/[`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) function marks the wrappers write
- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the machine-link operations struct whose hw_params hook usually calls the clocking and format wrappers

### Driver and PCM-creation callbacks (soc-dai.c)

- [`'\<snd_soc_pcm_dai_probe\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) / [`'\<snd_soc_pcm_dai_remove\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546): run the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L271)/[`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L272) ops in [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L360), toggling the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit
- [`'\<snd_soc_pcm_dai_new\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571): run the [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L276) op when the ALSA PCM is created
- [`'\<snd_soc_dai_compress_new\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L474): run the [`compress_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L274) op for an offload path

### Clocking and format wrappers (soc-dai.c)

- [`'\<snd_soc_dai_set_sysclk\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38): program the MCLK/SYSCLK; falls back to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) when the DAI has no op
- [`'\<snd_soc_dai_set_pll\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87): configure a DAI PLL; falls back to [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102)
- [`'\<snd_soc_dai_set_clkdiv\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64): set a clock divider; returns `-EINVAL` for an absent op
- [`'\<snd_soc_dai_set_bclk_ratio\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111): set the bit-clock to sample-rate ratio; returns `-ENOTSUPP` for an absent op
- [`'\<snd_soc_dai_set_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194): apply a `SND_SOC_DAIFMT_*` format word; returns `-ENOTSUPP` for an absent op
- [`'\<snd_soc_dai_set_tdm_slot\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252): set TDM masks and width, computing defaults via the optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op or [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213)
- [`'\<snd_soc_dai_set_channel_map\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) / [`'\<snd_soc_dai_get_channel_map\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L321): set and read the channel-to-slot mapping
- [`'\<snd_soc_dai_set_tristate\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L342): float the DAI pins for a shared bus
- [`'\<snd_soc_dai_get_fmt\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L155): walk the [`auto_selectable_formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L356) list to pick a format that works across a link

### Stream-handle, mute, and PCM wrappers (soc-dai.c)

- [`'\<snd_soc_dai_startup\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) / [`'\<snd_soc_dai_shutdown\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456): open and close the DAI for a substream; push and match the [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark
- [`'\<snd_soc_dai_hw_params\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) / [`'\<snd_soc_dai_hw_free\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422): apply and release hardware parameters; push and match the [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark
- [`'\<snd_soc_dai_prepare\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354): ready the DAI before the stream starts
- [`'\<snd_soc_pcm_dai_trigger\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618): drive start/stop/pause/suspend/resume across all DAIs of a runtime; per-DAI work is in [`soc_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603)
- [`'\<snd_soc_dai_digital_mute\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386): run the [`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L316) op, honoring [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L364)
- [`'\<snd_soc_pcm_dai_delay\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660): sum the [`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L346) op across the path for pointer reporting
- [`'\<snd_soc_dai_set_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559) / [`'\<snd_soc_dai_get_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L579): the inlines that call the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) and [`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310) ops with a transport stream handle

### Marks, usage count, and helpers (soc-dai.c, soc-dai.h)

- [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13) / [`soc_dai_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L25): the error-annotation and substream-mark macros every wrapper uses
- [`'\<snd_soc_dai_stream_valid\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489): test whether a DAI supports a direction by reading [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of its [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610)
- [`'\<snd_soc_dai_action\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497): add a signed delta to the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) count and the component count
- [`'\<snd_soc_dai_stream_active\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529): read one direction's usage count
- [`'\<snd_soc_dai_get_pcm_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L473): select the playback or capture capability record by direction
- [`'\<snd_soc_dai_dma_data_set\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506): store the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) pointer, reached through [`snd_soc_dai_set_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L505) and [`snd_soc_dai_get_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497)
- [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217): the iterator [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) uses to walk a runtime's CPU and codec DAIs

### rt722-sdca worked example (sound/soc/codecs/rt722-sdca.c)

- [`'rt722_sdca_ops':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246): the function pointer struct populating only [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324)
- [`'\<rt722_sdca_set_sdw_stream\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op storing the SoundWire stream handle as [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424)
- [`'\<rt722_sdca_shutdown\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1110): the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324) op clearing the stored handle
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op joining the codec to the SoundWire stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`'\<rt722_sdca_pcm_hw_free\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226): the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) op removing the codec with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)
- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries that all point [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept and the AC97, I2S, and PCM families
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): codec component guide covering the DAI driver and its ops
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK/BCLK/LRCLK relationships the clocking ops configure
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where front-end and back-end DAIs are triggered independently
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the rt722-sdca hw_params op joins

## OTHER SOURCES

- [The ALSA project home page](https://www.alsa-project.org/wiki/Main_Page)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every callback below is a field of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and is optional. A codec or platform driver fills in only the ones its hardware needs, and the matching wrapper treats an absent op as success (returning 0) or as not-supported (returning `-ENOTSUPP` or `-EINVAL`), depending on the op. The mapping from the PCM operation a userspace client requests to the DAI op the core runs and the resulting [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) state is fixed.

| PCM operation | DAI op (wrapper) | resulting PCM state |
|---------------|------------------|---------------------|
| `open()` | [`startup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) |
| `SNDRV_PCM_IOCTL_PREPARE` | [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354) | [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309) |
| `SNDRV_PCM_IOCTL_START` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) (START) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |
| `SNDRV_PCM_IOCTL_PAUSE` (push) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) (PAUSE_PUSH) | [`SNDRV_PCM_STATE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L313) |
| `SNDRV_PCM_IOCTL_DROP` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) (STOP) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| `close()` | [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) | (released) |

### probe and remove

[`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L271) runs once when the DAI's runtime is brought up, driven by [`snd_soc_pcm_dai_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) during card binding, and [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L272) runs once at teardown from [`snd_soc_pcm_dai_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546). A driver allocates per-DAI state here, the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit guards against a second probe, and the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L360)/[`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L361) fields let a DAI with a runtime dependency run before or after its peers.

### pcm_new and compress_new

[`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L276) runs from [`snd_soc_pcm_dai_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571) when the ALSA PCM device for the DAI link is created, so a DAI can add its own kcontrols or channel maps to the new PCM. [`compress_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L274), reached through [`snd_soc_dai_compress_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L474), creates a compressed-audio device instead of a PCM one for an offload path.

### set_sysclk, set_pll, set_clkdiv, set_bclk_ratio

The clocking ops are called by the machine driver, usually from its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hw_params hook, to program the DAI clock tree. [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) and [`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) fall through to the component-level clock ops ([`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78), [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102)) when the DAI itself supplies no op, while [`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) and [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) return `-EINVAL` and `-ENOTSUPP` respectively for an absent op.

### set_fmt, xlate_tdm_slot_mask, set_tdm_slot, set_channel_map, get_channel_map, set_tristate

[`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L294) receives a `SND_SOC_DAIFMT_*` word that encodes the audio protocol, the clock-provider role, and the bit-clock and frame-clock polarity, and the codec programs its serial port to match. [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) configures time-division multiplexing, with [`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) first computing default tx and rx masks through the optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op or the built-in [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213). [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L300) and [`get_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L303) tie DAI channels to TDM slots, and [`set_tristate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L306) floats the DAI pins so another device can drive a shared bus.

### set_stream and get_stream

[`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) hands the DAI a transport-specific stream handle and [`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310) reads it back. A SoundWire codec uses it to receive the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) the machine layer allocated, storing it so its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op can add itself to that stream. The inline [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559) is the wrapper that calls the op, and the SoundWire machine setup uses it to hand the codec its stream handle.

### mute_stream

[`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L316), driven by [`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386), silences the DAC to suppress pops at stream boundaries. The wrapper skips a capture-direction call when the op set [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L364), and when [`mute_unmute_on_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L365) is set the mute toggles inside [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) rather than at prepare and shutdown.

### startup and shutdown

[`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L322) runs when a substream is opened and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324) when it is closed. [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) records a successful call by storing the substream in [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), and [`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) consults that mark on a rollback so it tears down only a DAI whose startup actually ran.

### hw_params and hw_free

[`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) applies the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) (format, rate, channels) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) releases the resources it claimed. [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) sets [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) on success, and [`snd_soc_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) skips DAIs whose mark differs during an error rollback.

### prepare

[`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330) runs after parameters are applied and before the stream starts, and again after an underrun recovery, so the codec can flush FIFOs or re-arm logic. [`snd_soc_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354) returns 0 for a direction the DAI leaves unsupported, gated by [`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489).

### trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339) starts, stops, pauses, suspends, or resumes the data flow, dispatched by [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) and carried out per DAI by [`soc_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603). The op runs in atomic context for most cards. According to the comment on the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339) field, "Commands passed to the trigger function are not necessarily compatible with the current state of the dai" and "this sequence of commands is possible: START STOP STOP", so the op treats each command independently and leaves reference-counted work such as clock enable and disable to other callbacks.

### delay

[`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L346) reports the DAI's hardware FIFO latency in frames, which [`snd_soc_pcm_dai_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) sums along the audio path so the runtime pointer reflects the full delay from the application buffer to the pin.

### auto_selectable_formats and the bit fields

[`auto_selectable_formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L356) lists `SND_SOC_POSSIBLE_DAIFMT_*` values in priority order, and [`snd_soc_dai_get_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L155) consults them so the core can pick a format that works across both ends of a link. The [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L364) and [`mute_unmute_on_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L365) bit fields tune the mute behavior.

## DETAILS

### The ops table groups its callbacks by role

[`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) is one struct of optional function pointers, laid out in the header with comment banners that separate the driver callbacks, the clocking configuration, the format configuration, the stream handle, the digital mute, and the ALSA PCM operations. The full definition shows the grouping and the two warnings the comments carry:

```c
/* include/sound/soc-dai.h:269 */
struct snd_soc_dai_ops {
	/* DAI driver callbacks */
	int (*probe)(struct snd_soc_dai *dai);
	int (*remove)(struct snd_soc_dai *dai);
	/* compress dai */
	int (*compress_new)(struct snd_soc_pcm_runtime *rtd);
	/* Optional Callback used at pcm creation*/
	int (*pcm_new)(struct snd_soc_pcm_runtime *rtd,
		       struct snd_soc_dai *dai);

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
	int (*set_tristate)(struct snd_soc_dai *dai, int tristate);

	int (*set_stream)(struct snd_soc_dai *dai,
			  void *stream, int direction);
	void *(*get_stream)(struct snd_soc_dai *dai, int direction);

	/*
	 * DAI digital mute - optional.
	 * Called by soc-core to minimise any pops.
	 */
	int (*mute_stream)(struct snd_soc_dai *dai, int mute, int stream);

	/*
	 * ALSA PCM audio operations - all optional.
	 * Called by soc-core during audio PCM operations.
	 */
	int (*startup)(struct snd_pcm_substream *,
		struct snd_soc_dai *);
	void (*shutdown)(struct snd_pcm_substream *,
		struct snd_soc_dai *);
	int (*hw_params)(struct snd_pcm_substream *,
		struct snd_pcm_hw_params *, struct snd_soc_dai *);
	int (*hw_free)(struct snd_pcm_substream *,
		struct snd_soc_dai *);
	int (*prepare)(struct snd_pcm_substream *,
		struct snd_soc_dai *);
	/*
	 * NOTE: Commands passed to the trigger function are not necessarily
	 * compatible with the current state of the dai. For example this
	 * sequence of commands is possible: START STOP STOP.
	 * So do not unconditionally use refcounting functions in the trigger
	 * function, e.g. clk_enable/disable.
	 */
	int (*trigger)(struct snd_pcm_substream *, int,
		struct snd_soc_dai *);

	/*
	 * For hardware based FIFO caused delay reporting.
	 * Optional.
	 */
	snd_pcm_sframes_t (*delay)(struct snd_pcm_substream *,
		struct snd_soc_dai *);

	/*
	 * Format list for auto selection.
	 * Format will be increased if priority format was
	 * not selected.
	 * see
	 *	snd_soc_dai_get_fmt()
	 */
	const u64 *auto_selectable_formats;
	int num_auto_selectable_formats;

	/* probe ordering - for components with runtime dependencies */
	int probe_order;
	int remove_order;

	/* bit field */
	unsigned int no_capture_mute:1;
	unsigned int mute_unmute_on_trigger:1;
};
```

The descriptor points one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at one table through its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) field, and because the table is `const` it is shared across every card that instantiates the codec while the mutable per-instance state is held in the runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438).

```
    struct snd_soc_dai_ops field layout, grouped by banner
    ───────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ DAI driver callbacks (once, at bring-up)                 │
    │   probe   remove   compress_new   pcm_new                │
    ├──────────────────────────────────────────────────────────┤
    │ clocking config (machine hw_params; sysclk/pll fall      │
    │ back to the component op)                                │
    │   set_sysclk  set_pll  set_clkdiv  set_bclk_ratio        │
    ├──────────────────────────────────────────────────────────┤
    │ format config (machine hw_params)                        │
    │   set_fmt  xlate_tdm_slot_mask  set_tdm_slot             │
    │   set_channel_map  get_channel_map  set_tristate         │
    ├──────────────────────────────────────────────────────────┤
    │ stream handle                                            │
    │   set_stream   get_stream                                │
    ├──────────────────────────────────────────────────────────┤
    │ digital mute                                             │
    │   mute_stream                                            │
    ├──────────────────────────────────────────────────────────┤
    │ ALSA PCM ops (per substream)                             │
    │   startup  shutdown  hw_params  hw_free                  │
    │   prepare  trigger   delay                               │
    ├──────────────────────────────────────────────────────────┤
    │ data and tuning bits                                     │
    │   auto_selectable_formats  probe_order  remove_order     │
    │   no_capture_mute  mute_unmute_on_trigger                │
    └──────────────────────────────────────────────────────────┘
```

### The wrapper shape every entry point shares

The ASoC core reaches a DAI op only through a wrapper in [`sound/soc/soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c), and the wrappers share one shape. Two macros at the top of the file carry the boilerplate, [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13) for error annotation and [`soc_dai_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L25) for the per-substream marks:

```c
/* sound/soc/soc-dai.c:13 */
#define soc_dai_ret(dai, ret) _soc_dai_ret(dai, __func__, ret)
static inline int _soc_dai_ret(const struct snd_soc_dai *dai,
			       const char *func, int ret)
{
	return snd_soc_ret(dai->dev, ret,
			   "at %s() on %s\n", func, dai->name);
}

/*
 * We might want to check substream by using list.
 * In such case, we can update these macros.
 */
#define soc_dai_mark_push(dai, substream, tgt)	((dai)->mark_##tgt = substream)
#define soc_dai_mark_pop(dai, tgt)	((dai)->mark_##tgt = NULL)
#define soc_dai_mark_match(dai, substream, tgt)	((dai)->mark_##tgt == substream)
```

[`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) is the plain configuration variant. It returns `-ENOTSUPP` when the op is absent, so a link with a fixed format simply leaves the field NULL:

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

[`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) is the fall-back variant, where an absent DAI op routes to the component-level clock op instead of returning an error, so a codec can place its clock handling at the DAI or the component level:

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

[`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) is the PCM variant, where the wrapper records the substream in the matching mark after a successful call so the teardown path can find it:

```c
/* sound/soc/soc-dai.c:405 */
int snd_soc_dai_hw_params(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  struct snd_pcm_hw_params *params)
{
	int ret = 0;

	if (dai->driver->ops &&
	    dai->driver->ops->hw_params)
		ret = dai->driver->ops->hw_params(substream, params, dai);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_dai_mark_push(dai, substream, hw_params);

	return soc_dai_ret(dai, ret);
}
```

Those three wrappers each match one archetype in this table, which groups them by the op-absent result, a defined error code, a fall-through to the component op, or an op run that pushes a mark:

```
    Three wrapper archetypes and what each does when the op is absent
    ─────────────────────────────────────────────────────────────────

    archetype        example wrappers          op absent ▶ result
    ───────────────  ────────────────────────  ──────────────────────
    plain config     set_fmt, set_bclk_ratio   return -ENOTSUPP
                     set_clkdiv, set_tristate   return -EINVAL
    component        set_sysclk, set_pll        call the component-level
    fall-back                                   clock op instead
    PCM with mark    startup, hw_params         run op; on ret==0
                     (teardown partner)         push mark_<op>
    PCM no mark      prepare                    run op; no mark
                     (stream-valid gated)       (skip unsupported dir)

    every archetype first tests that dai->driver->ops and the op
    pointer are present, then routes the result through soc_dai_ret()
```

### Marks make error rollback exact

The marks exist so an error during multi-DAI bring-up tears down only the DAIs that ran their setup op. [`snd_soc_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) takes a `rollback` argument, and when it is set the function returns early for any DAI whose [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) differs from the substream being unwound:

```c
/* sound/soc/soc-dai.c:422 */
void snd_soc_dai_hw_free(struct snd_soc_dai *dai,
			 struct snd_pcm_substream *substream,
			 int rollback)
{
	if (rollback && !soc_dai_mark_match(dai, substream, hw_params))
		return;

	if (dai->driver->ops &&
	    dai->driver->ops->hw_free)
		dai->driver->ops->hw_free(substream, dai);

	/* remove marked substream */
	soc_dai_mark_pop(dai, hw_params);
}
```

[`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) applies the same rule to the startup mark, and it skips a direction the DAI leaves unsupported by testing [`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489) first:

```c
/* sound/soc/soc-dai.c:456 */
void snd_soc_dai_shutdown(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  int rollback)
{
	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return;

	if (rollback && !soc_dai_mark_match(dai, substream, startup))
		return;

	if (dai->driver->ops &&
	    dai->driver->ops->shutdown)
		dai->driver->ops->shutdown(substream, dai);

	/* remove marked substream */
	soc_dai_mark_pop(dai, startup);
}
```

[`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489) reads the capability record for the direction and treats a non-zero [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) as proof the DAI supports it:

```c
/* sound/soc/soc-dai.c:489 */
bool snd_soc_dai_stream_valid(const struct snd_soc_dai *dai, int dir)
{
	const struct snd_soc_pcm_stream *stream = snd_soc_dai_get_pcm_stream(dai, dir);

	/* If the codec specifies any channels at all, it supports the stream */
	return stream->channels_min;
}
```

### Mute respects direction and timing flags

[`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386) runs the [`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L316) op only for a playback direction or for a capture direction when [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L364) is clear, which keeps a capture-only amplifier from a meaningless mute call:

```c
/* sound/soc/soc-dai.c:386 */
int snd_soc_dai_digital_mute(struct snd_soc_dai *dai, int mute,
			     int direction)
{
	int ret = -ENOTSUPP;

	/*
	 * ignore if direction was CAPTURE
	 * and it had .no_capture_mute flag
	 */
	if (dai->driver->ops &&
	    dai->driver->ops->mute_stream &&
	    (direction == SNDRV_PCM_STREAM_PLAYBACK ||
	     !dai->driver->ops->no_capture_mute))
		ret = dai->driver->ops->mute_stream(dai, mute, direction);

	return soc_dai_ret(dai, ret);
}
```

The two direction-and-flag conditions in the guard become this grid, the mute running for every playback case and skipped only on a capture with no_capture_mute set:

```
    snd_soc_dai_digital_mute(): when the mute_stream op actually runs
    ─────────────────────────────────────────────────────────────────
    (the op must also be present, else the wrapper returns -ENOTSUPP)

                       no_capture_mute = 0      no_capture_mute = 1
                      ┌────────────────────┬────────────────────────┐
       PLAYBACK  ───▶ │  mute_stream runs  │  mute_stream runs      │
                      ├────────────────────┼────────────────────────┤
       CAPTURE   ───▶ │  mute_stream runs  │  skipped (-ENOTSUPP)   │
                      └────────────────────┴────────────────────────┘

    when mute_unmute_on_trigger is set the toggle moves into
    snd_soc_pcm_dai_trigger() instead of prepare/shutdown
```

### Trigger ordering and mute-on-trigger

[`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) drives every DAI of a runtime through one command, iterating with [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217). The start group (START, RESUME, PAUSE_RELEASE) runs the per-DAI op, optionally unmutes when [`mute_unmute_on_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L365) is set, and pushes the [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark, while the stop group (STOP, SUSPEND, PAUSE_PUSH) mutes first, honors the rollback mark, runs the op, and pops the mark:

```c
/* sound/soc/soc-dai.c:618 */
int snd_soc_pcm_dai_trigger(struct snd_pcm_substream *substream,
			    int cmd, int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int i, r, ret = 0;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for_each_rtd_dais(rtd, i, dai) {
			ret = soc_dai_trigger(dai, substream, cmd);
			if (ret < 0)
				break;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 0, substream->stream);

			soc_dai_mark_push(dai, substream, trigger);
		}
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		for_each_rtd_dais(rtd, i, dai) {
			if (rollback && !soc_dai_mark_match(dai, substream, trigger))
				continue;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 1, substream->stream);

			r = soc_dai_trigger(dai, substream, cmd);
			if (r < 0)
				ret = r; /* use last ret */
			soc_dai_mark_pop(dai, trigger);
		}
	}

	return ret;
}
```

The per-DAI [`soc_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603) is a thin guard around the op. According to the comment on the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339) field, "this sequence of commands is possible: START STOP STOP", so the op handles each command on its own rather than pairing it with a reference-counted call such as clock enable.

```
    snd_soc_pcm_dai_trigger(): the two command groups, per DAI
    ───────────────────────────────────────────────────────────
    (for_each_rtd_dais runs the inner steps top-to-bottom)

    start group                        stop group
    START RESUME PAUSE_RELEASE         STOP SUSPEND PAUSE_PUSH
    ┌────────────────────────────┐     ┌────────────────────────────┐
    │ soc_dai_trigger(cmd)       │     │ rollback ? skip unmarked   │
    │           │                │     │           │                │
    │           ▼                │     │           ▼                │
    │ unmute if ctrled-at-trigger│     │ mute if ctrled-at-trigger  │
    │           │                │     │           │                │
    │           ▼                │     │           ▼                │
    │ push mark_trigger          │     │ soc_dai_trigger(cmd)       │
    │                            │     │           │                │
    │                            │     │           ▼                │
    │                            │     │ pop mark_trigger           │
    └────────────────────────────┘     └────────────────────────────┘

    note: mute precedes the op on stop, unmute follows it on start
```

### Per-direction usage count

[`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) maintains the usage count. It adds a signed delta to the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) field of the [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) and to the parent component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) field in one step, so a single accounting point keeps both counts in sync:

```c
/* sound/soc/soc-dai.c:497 */
void snd_soc_dai_action(struct snd_soc_dai *dai,
			int stream, int action)
{
	/* see snd_soc_dai_stream_active() */
	dai->stream[stream].active	+= action;

	/* see snd_soc_component_active() */
	dai->component->active		+= action;
}
```

[`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) reads one direction's count, which the suspend path and DAPM use to decide whether a DAI is still carrying audio:

```c
/* include/sound/soc-dai.h:529 */
static inline unsigned int snd_soc_dai_stream_active(const struct snd_soc_dai *dai,
						     int stream)
{
	/* see snd_soc_dai_action() for setup */
	return dai->stream[stream].active;
}
```

### The driver descriptor and the machine ops struct

A codec or platform driver registers one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) per DAI. The descriptor carries the DAI name and id, the playback and capture [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) capability records, and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L412) pointer that ties it to one ops table, with a separate [`cops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L413) pointer for the compressed-audio variant:

```c
/* include/sound/soc-dai.h:403 */
struct snd_soc_dai_driver {
	/* DAI description */
	const char *name;
	unsigned int id;
	unsigned int base;
	struct snd_soc_dobj dobj;
	const struct of_phandle_args *dai_args;

	/* ops */
	const struct snd_soc_dai_ops *ops;
	const struct snd_soc_cdai_ops *cops;

	/* DAI capabilities */
	struct snd_soc_pcm_stream capture;
	struct snd_soc_pcm_stream playback;
	unsigned int symmetric_rate:1;
	unsigned int symmetric_channels:1;
	unsigned int symmetric_sample_bits:1;
};
```

The [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) is the machine-link table that sits one level above the DAI ops. A machine driver attaches it to a DAI link and its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L626) hook is the usual place where the clocking and format setters are called for each codec and CPU DAI on the link:

```c
/* include/sound/soc.h:623 */
struct snd_soc_ops {
	int (*startup)(struct snd_pcm_substream *);
	void (*shutdown)(struct snd_pcm_substream *);
	int (*hw_params)(struct snd_pcm_substream *, struct snd_pcm_hw_params *);
	int (*hw_free)(struct snd_pcm_substream *);
	int (*prepare)(struct snd_pcm_substream *);
	int (*trigger)(struct snd_pcm_substream *, int);
};
```

The machine ops shown above is the topmost of three boxes around the table, its hw_params reaching the setters, the static descriptor holding the ops and cops pointers, and the runtime instance carrying the rollback marks:

```
    Structs around the ops table (boxes are structs)
    ──────────────────────────────────────────────────

    struct snd_soc_ops                  (machine-link table, one above)
    ┌──────────────────────────┐
    │ hw_params  ──────────────┼─▶ calls the clocking and format
    │ startup shutdown trigger │    setters per CPU and codec DAI
    └──────────────────────────┘

    struct snd_soc_dai_driver           (static, const, per DAI)
    ┌──────────────────────────┐
    │ name  id  base           │
    │ playback  capture        │  snd_soc_pcm_stream capability records
    │ ops  ────────────────────┼─▶ const struct snd_soc_dai_ops
    │ cops ────────────────────┼─▶ const struct snd_soc_cdai_ops
    └──────────────────────────┘    (compressed-audio variant)

    struct snd_soc_dai                   (runtime, mutable, per instance)
    ┌──────────────────────────┐
    │ mark_startup             │  set by the wrappers; consulted on
    │ mark_hw_params           │  rollback so teardown skips a DAI
    │ mark_trigger             │  whose setup op never ran
    └──────────────────────────┘
```

### The driver and PCM-creation wrappers walk the runtime's DAIs

The driver callbacks are not reached one DAI at a time but by iterating every DAI of a runtime. [`snd_soc_pcm_dai_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) runs the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L271) op for each DAI whose [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L360) matches the order argument, sets the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit, and stops at the first failure, while [`snd_soc_pcm_dai_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546) does the mirror in [`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L361) and keeps the last error rather than stopping:

```c
/* sound/soc/soc-dai.c:520 */
int snd_soc_pcm_dai_probe(struct snd_soc_pcm_runtime *rtd, int order)
{
	struct snd_soc_dai *dai;
	int i;

	for_each_rtd_dais(rtd, i, dai) {
		if (dai->probed)
			continue;

		if (dai->driver->ops) {
			if (dai->driver->ops->probe_order != order)
				continue;

			if (dai->driver->ops->probe) {
				int ret = dai->driver->ops->probe(dai);

				if (ret < 0)
					return soc_dai_ret(dai, ret);
			}
		}
		dai->probed = 1;
	}

	return 0;
}

/* sound/soc/soc-dai.c:546 */
int snd_soc_pcm_dai_remove(struct snd_soc_pcm_runtime *rtd, int order)
{
	struct snd_soc_dai *dai;
	int i, r, ret = 0;

	for_each_rtd_dais(rtd, i, dai) {
		if (!dai->probed)
			continue;

		if (dai->driver->ops) {
			if (dai->driver->ops->remove_order != order)
				continue;

			if (dai->driver->ops->remove) {
				r = dai->driver->ops->remove(dai);
				if (r < 0)
					ret = r; /* use last error */
			}
		}
		dai->probed = 0;
	}

	return ret;
}
```

[`snd_soc_pcm_dai_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571) runs the [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L276) op when the ALSA PCM device is created, and [`snd_soc_dai_compress_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L474) is the single-DAI wrapper that runs the [`compress_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L274) op for an offload path, returning `-ENOTSUPP` when the DAI has no such op:

```c
/* sound/soc/soc-dai.c:571 */
int snd_soc_pcm_dai_new(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_dai *dai;
	int i;

	for_each_rtd_dais(rtd, i, dai) {
		if (dai->driver->ops &&
		    dai->driver->ops->pcm_new) {
			int ret = dai->driver->ops->pcm_new(rtd, dai);
			if (ret < 0)
				return soc_dai_ret(dai, ret);
		}
	}

	return 0;
}

/* sound/soc/soc-dai.c:474 */
int snd_soc_dai_compress_new(struct snd_soc_dai *dai,
			     struct snd_soc_pcm_runtime *rtd)
{
	int ret = -ENOTSUPP;
	if (dai->driver->ops &&
	    dai->driver->ops->compress_new)
		ret = dai->driver->ops->compress_new(rtd);
	return soc_dai_ret(dai, ret);
}
```

### The clocking setters wrap the DAI op

[`snd_soc_dai_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L87) follows the same fall-back shape as [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38), routing to [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) when the DAI supplies no [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L285) op, so a codec can place its PLL handling at the DAI or the component level:

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

[`snd_soc_dai_set_clkdiv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L64) and [`snd_soc_dai_set_bclk_ratio()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L111) are plain configuration wrappers with no component fall-back, differing only in the error code they return for an absent op, `-EINVAL` for the divider and `-ENOTSUPP` for the bit-clock ratio:

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

### The slot and channel-map setters

[`snd_soc_dai_set_tdm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L252) does more than the plain wrappers. When TDM is in use it first computes the default tx and rx masks through the optional [`xlate_tdm_slot_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L295) op or the built-in [`snd_soc_xlate_tdm_slot_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L213), records the per-direction mask with [`snd_soc_dai_tdm_mask_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L523), and only then runs the [`set_tdm_slot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L297) op:

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

[`snd_soc_dai_set_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L297) and its read-back partner [`snd_soc_dai_get_channel_map()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L321) are the plain wrapper shape over the [`set_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L300) and [`get_channel_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L303) ops, both returning `-ENOTSUPP` for an absent op:

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

/* sound/soc/soc-dai.c:321 */
int snd_soc_dai_get_channel_map(const struct snd_soc_dai *dai,
				unsigned int *tx_num, unsigned int *tx_slot,
				unsigned int *rx_num, unsigned int *rx_slot)
{
	int ret = -ENOTSUPP;

	if (dai->driver->ops &&
	    dai->driver->ops->get_channel_map)
		ret = dai->driver->ops->get_channel_map(dai, tx_num, tx_slot,
							rx_num, rx_slot);
	return soc_dai_ret(dai, ret);
}
```

[`snd_soc_dai_set_tristate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L342) floats the DAI pins for a shared bus through the [`set_tristate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L306) op, returning `-EINVAL` when the DAI cannot tristate:

```c
/* sound/soc/soc-dai.c:342 */
int snd_soc_dai_set_tristate(struct snd_soc_dai *dai, int tristate)
{
	int ret = -EINVAL;

	if (dai->driver->ops &&
	    dai->driver->ops->set_tristate)
		ret = dai->driver->ops->set_tristate(dai, tristate);

	return soc_dai_ret(dai, ret);
}
```

### The lifecycle and stream wrappers

[`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) opens the DAI for a substream. It returns 0 for a direction the DAI leaves unsupported, gated by [`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489), and on a successful [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L322) op it pushes the [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark that [`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) later matches on rollback:

```c
/* sound/soc/soc-dai.c:437 */
int snd_soc_dai_startup(struct snd_soc_dai *dai,
			struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return 0;

	if (dai->driver->ops &&
	    dai->driver->ops->startup)
		ret = dai->driver->ops->startup(substream, dai);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_dai_mark_push(dai, substream, startup);

	return soc_dai_ret(dai, ret);
}
```

[`snd_soc_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354) has no teardown partner so it carries no mark, but it shares the same [`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489) gate before running the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330) op:

```c
/* sound/soc/soc-dai.c:354 */
int snd_soc_dai_prepare(struct snd_soc_dai *dai,
			struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return 0;

	if (dai->driver->ops &&
	    dai->driver->ops->prepare)
		ret = dai->driver->ops->prepare(substream, dai);

	return soc_dai_ret(dai, ret);
}
```

The stream-handle accessors are header inlines rather than functions in [`sound/soc/soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c). [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559) hands the DAI a transport-specific stream handle through the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op and [`snd_soc_dai_get_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L579) reads it back through [`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310), the getter returning an `ERR_PTR(-ENOTSUPP)` so a caller can tell an unsupported op from a real handle:

```c
/* include/sound/soc-dai.h:559 */
static inline int snd_soc_dai_set_stream(struct snd_soc_dai *dai,
					 void *stream, int direction)
{
	if (dai->driver->ops->set_stream)
		return dai->driver->ops->set_stream(dai, stream, direction);
	else
		return -ENOTSUPP;
}

/* include/sound/soc-dai.h:579 */
static inline void *snd_soc_dai_get_stream(struct snd_soc_dai *dai,
					   int direction)
{
	if (dai->driver->ops->get_stream)
		return dai->driver->ops->get_stream(dai, direction);
	else
		return ERR_PTR(-ENOTSUPP);
}
```

[`snd_soc_pcm_dai_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) is the reporting wrapper for the [`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L346) op. It walks the CPU and codec DAIs separately and takes the maximum of each side rather than summing every DAI, because the figure it returns is the delay through the full transmit and receive paths:

```c
/* sound/soc/soc-dai.c:660 */
void snd_soc_pcm_dai_delay(struct snd_pcm_substream *substream,
			   snd_pcm_sframes_t *cpu_delay,
			   snd_pcm_sframes_t *codec_delay)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int i;

	/*
	 * We're looking for the delay through the full audio path so it needs to
	 * be the maximum of the DAIs doing transmit and the maximum of the DAIs
	 * doing receive (ie, all CPUs and all CODECs) rather than just the maximum
	 * of all DAIs.
	 */

	/* for CPU */
	for_each_rtd_cpu_dais(rtd, i, dai)
		if (dai->driver->ops &&
		    dai->driver->ops->delay)
			*cpu_delay = max(*cpu_delay, dai->driver->ops->delay(substream, dai));

	/* for Codec */
	for_each_rtd_codec_dais(rtd, i, dai)
		if (dai->driver->ops &&
		    dai->driver->ops->delay)
			*codec_delay = max(*codec_delay, dai->driver->ops->delay(substream, dai));
}
```

### Worked example: rt722-sdca populates four callbacks

The Realtek RT722 is an SDCA codec reached over SoundWire, registered under the [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) component driver. Its three DAIs in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) all share one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) that sets only four callbacks, which is the point of the wrapper guards. Every other op stays NULL and its wrapper returns success or a defined error with no codec code:

```c
/* sound/soc/codecs/rt722-sdca.c:1246 */
static const struct snd_soc_dai_ops rt722_sdca_ops = {
	.hw_params	= rt722_sdca_pcm_hw_params,
	.hw_free	= rt722_sdca_pcm_hw_free,
	.set_stream	= rt722_sdca_set_sdw_stream,
	.shutdown	= rt722_sdca_shutdown,
};
```

The codec exports its three DAIs as a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array, [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253), that [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) hands to [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). Each entry names a SoundWire data port, declares its playback and capture capability records, and points [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L412) at the single shared [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246) table, so the four populated callbacks serve a headphone, a speaker, and a microphone DAI alike:

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
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
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
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.ops = &rt722_sdca_ops,
	}
};
```

The [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op stores the SoundWire stream handle the machine layer passes, using [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506) to keep it in the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) slot, and the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324) op clears it:

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

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op reads that stored handle back with [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497), translates the negotiated parameters into a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907), selects the SoundWire data port from the DAI id and direction, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
static int rt722_sdca_pcm_hw_params(struct snd_pcm_substream *substream,
				struct snd_pcm_hw_params *params,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_config stream_config;
	struct sdw_port_config port_config;
	enum sdw_data_direction direction;
	struct sdw_stream_runtime *sdw_stream;
	int retval, port, num_channels;
	unsigned int sampling_rate;

	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);

	if (!sdw_stream)
		return -EINVAL;
	...
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
	...
}
```

The [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) op reverses that step, removing the codec from the SoundWire stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228):

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

The symmetry between the two ops follows the mark contract. The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) wrapper records the substream in [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) only after [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) returns success, so a later failure in the chain runs [`rt722_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226) against this codec only when it had actually been added, which prevents a double [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228).

```
    rt722 ops share one slot: the per-direction dma_data
    ──────────────────────────────────────────────────────

                  ┌─────────────────────────────────────┐
                  │ dai dma_data[direction]             │
       set_stream │   (holds struct sdw_stream_runtime) │
       ──────────▶│                                     │
       writes     └──────────────┬──────────────────────┘
       handle                    │ snd_soc_dai_get_dma_data()
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
       ┌───────────────────────┐    ┌───────────────────────┐
       │ hw_params             │    │ hw_free               │
       │ sdw_stream_add_slave  │    │ sdw_stream_remove_    │
       │                       │    │ slave                 │
       └───────────────────────┘    └───────────────────────┘

       shutdown writes NULL back into the slot, clearing the handle
```
