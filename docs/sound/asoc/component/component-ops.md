# ASoC component operations (snd_soc_component_driver callbacks)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The callbacks of [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) are the per-operation hooks the ASoC core invokes on one component, and the core reaches every one of them only through a wrapper in [`soc-component.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) rather than dereferencing the pointer directly. The PCM-creation pair [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)/[`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) sets up and tears down the DMA buffers when the ALSA PCM for a link is created, the substream operations [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) through [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) carry one stream from open to close on a platform component, and the configuration callbacks [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) program the clock tree, jack detection, and power bias of a codec component. Every wrapper treats an absent callback as success (returning 0) or as not-supported (returning `-ENOTSUPP` or `-EINVAL`), so a driver fills in only the hooks its hardware needs.

```
   ALSA PCM create  ─▶ snd_soc_pcm_component_new ─▶ each component's pcm_construct
   open()           ─▶ snd_soc_component_open    ─▶ open   (mark_open pushed)
   hw_params        ─▶ snd_soc_pcm_component_hw_params ─▶ hw_params
   prepare          ─▶ snd_soc_component_prepare  ─▶ prepare
   trigger START    ─▶ soc_component_trigger      ─▶ trigger
   IRQ / pointer    ─▶ snd_soc_pcm_component_pointer ─▶ pointer
   close()          ─▶ snd_soc_component_close    ─▶ close  (mark consulted)
   PCM free         ─▶ snd_soc_pcm_component_free  ─▶ pcm_destruct

   config (on demand):
   set_sysclk / set_pll / set_jack / set_bias_level
       each wrapper: if (driver->cb) ret = driver->cb(...); else -ENOTSUPP/0
```

## SUMMARY

A component's behavior is the set of callbacks its [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) fills. They group by role. The PCM-device pair runs when the ALSA PCM for a DAI link is created and freed, where [`snd_soc_pcm_component_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033) iterates the runtime's components and calls each [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so a platform component can allocate and preallocate its DMA buffers, and [`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050) reverses it through [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). The substream operations carry one PCM stream, where [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) bracket the stream, [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) apply and release the negotiated format, [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) readies the engine, [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) starts and stops the DMA, and [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) reports the current position. The configuration callbacks run on demand, where [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) and [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) program the component-wide clock tree, [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) binds a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), and [`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134) moves the component through its [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415) power states.

The wrapper shape is uniform. A lifecycle or PCM wrapper that finds no callback returns 0, so a component without the hook is simply skipped, while a configuration wrapper that finds no callback returns `-ENOTSUPP` or `-EINVAL` so the caller can fall back or report the feature unsupported. The DAI clock helpers fall through to the component, so [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) routes to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) when the DAI itself has no clock op. The PCM substream wrappers iterate every component bound to the runtime, and the [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L165) and [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L166) order fields set the sequence a component's trigger runs in relative to its peers.

## SPECIFICATIONS

The component operation model is a Linux kernel software construct and has no standalone hardware specification. The substream operations move PCM data through the ALSA PCM layer (the [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) and its runtime), and the clocking and bias callbacks reach hardware defined by the codec's own datasheet and the serial-audio interface standards (I2S, TDM, PDM).

## LINUX KERNEL

### The descriptor (soc-component.h)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the static description carrying every callback below, plus the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) and [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L165)/[`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L166) ordering and the behavior bit flags

### PCM-device wrappers (soc-component.c)

- [`'\<snd_soc_pcm_component_new\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033): iterate the runtime's components and run each [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to allocate the DMA buffers
- [`'\<snd_soc_pcm_component_free\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050): iterate and run each [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to release them

### Substream-operation wrappers (soc-component.c)

- [`'\<snd_soc_component_open\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) / [`'\<snd_soc_component_close\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266): run the [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)/[`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callbacks, using the [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) mark for rollback
- [`'\<snd_soc_pcm_component_hw_params\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080): run each component's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), recording [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L248)
- [`'\<snd_soc_pcm_component_prepare\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063): run each component's [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback before start
- [`'\<soc_component_trigger\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1123): run the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback to start or stop the DMA
- [`'\<snd_soc_pcm_component_pointer\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884): run the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback to report the DMA position
- [`'\<snd_soc_pcm_component_new\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033): the construction iteration driven from [`soc_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c)

### Configuration wrappers (soc-component.c)

- [`'\<snd_soc_component_set_sysclk\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78): run the [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback or return `-ENOTSUPP`; the DAI clock helper falls through to this
- [`'\<snd_soc_component_set_pll\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102): run the [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback or return `-EINVAL`
- [`'\<snd_soc_component_set_jack\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190): run the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback to bind a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80)
- [`'\<snd_soc_component_get_jack_type\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L210): run the [`get_jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback or return `-ENOTSUPP`
- [`'\<snd_soc_component_set_bias_level\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134): run the [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback to move the component through its [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415) states

### DAPM-notifier callbacks (soc-component.c)

- the [`seq_notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback is called as DAPM sequences power changes, receiving the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) of the widgets in a sequence
- the [`stream_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback is called when a DAPM stream event fires so the component can react to a path powering up or down

### The error-annotation and mark macros (soc-component.c)

- [`soc_component_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L16): annotate a callback's return value with the function name and component name
- [`soc_component_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L48) / [`soc_component_mark_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) : record and test the per-substream mark that makes rollback exact

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component, where [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and the substream operations belong
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component, where the clocking, jack, and bias callbacks belong
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the bias-level and DAPM-notifier callbacks the power engine drives

## OTHER SOURCES

- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every callback below is an optional field of [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). The wrapper column names the [`soc-component.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) entry point that invokes it.

| component callback | wrapper | absent-callback result |
|--------------------|---------|------------------------|
| [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033) | skipped (0) |
| [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050) | skipped |
| [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) | 0 |
| [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266) | 0 |
| [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) | 0 |
| [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) | 0 |
| [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063) | 0 |
| [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`soc_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1123) | 0 |
| [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) | 0 |
| [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1162) | (no pointer reported) |
| [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_copy()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) | `-EINVAL` |
| [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) | (default mmap) |
| [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_pcm_component_ack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) | skipped |
| [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) | `-ENOTSUPP` |
| [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) | `-EINVAL` |
| [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) | `-ENOTSUPP` |
| [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) | [`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134) | 0 |

### pcm_construct and pcm_destruct

[`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs from [`snd_soc_pcm_component_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033) when the ALSA PCM device for a DAI link is created, so a platform component allocates its DMA buffers and preallocates pages, and [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) reverses that from [`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050). Both wrappers iterate every component bound to the runtime, so a card with separate codec and platform components calls each component's hook in turn.

### open, close, hw_params, hw_free, prepare, trigger, sync_stop

These callbacks carry one PCM substream from open to close on a platform component. [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), run by [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) and [`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266), bracket the stream and use the [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) mark so close runs only against a component whose open succeeded. [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) apply and release the negotiated format and DMA setup, [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) readies the engine just before start, [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) starts and stops the DMA, and [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) waits for an in-flight stop to settle before the next start.

### pointer, get_time_info, copy, page, mmap, ack, delay

These callbacks report and move PCM data on a platform component. [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) returns the current DMA position in frames, [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) returns a hardware timestamp paired with that position, and [`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) reports extra buffering latency. [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) moves audio between the application buffer and the DMA area for the non-mmap path, [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) returns the [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h) backing an offset for fault-based mapping, [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) maps the DMA buffer into user space directly, and [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) tells the component that the application pointer advanced.

### set_sysclk, set_pll, set_jack, get_jack_type

[`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) program the component-wide clock tree, and they double as the fall-through target for the DAI clock helpers, so [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) routes to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) when the DAI itself has no clock op. [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) binds a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) so the codec reports headphone and microphone insertion, and [`get_jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) reports the supported jack type back to the machine layer.

### set_bias_level

[`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), driven by [`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134), moves the component through the [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415) power states from [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) through [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) as DAPM powers analog blocks up and down. The [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179) flag keeps the bias at [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) while idle to avoid pops on the next stream, at the cost of standby power.

### seq_notifier and stream_event

[`seq_notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is called by DAPM as it sequences power changes, receiving the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) of the widgets in a sequence so the component can batch register writes, and [`stream_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is called when a DAPM stream event fires so the component can react to a path powering up or down.

## DETAILS

### The wrapper shape and the three return conventions

The core never calls a component callback directly. It calls a wrapper that tests for the pointer, invokes it, and annotates the result through [`soc_component_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L16). A lifecycle wrapper treats an absent callback as success. [`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303) is the shape:

```c
/* sound/soc/soc-component.c:303 */
int snd_soc_component_probe(struct snd_soc_component *component)
{
	int ret = 0;

	if (component->driver->probe)
		ret = component->driver->probe(component);

	return soc_component_ret(component, ret);
}
```

A configuration wrapper treats an absent callback as not-supported, so the caller can fall back. [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) starts its return value at `-ENOTSUPP` and only overwrites it when the callback runs:

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

[`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) follows the same `-ENOTSUPP` convention, binding the jack only when the codec supplies the callback:

```c
/* sound/soc/soc-component.c:190 */
int snd_soc_component_set_jack(struct snd_soc_component *component,
			       struct snd_soc_jack *jack, void *data)
{
	int ret = -ENOTSUPP;

	if (component->driver->set_jack)
		ret = component->driver->set_jack(component, jack, data);

	return soc_component_ret(component, ret);
}
```

A PCM substream wrapper records a mark on success so the teardown path can tell which components ran. [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) pushes [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) after a successful open:

```c
/* sound/soc/soc-component.c:251 */
int snd_soc_component_open(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (component->driver->open)
		ret = component->driver->open(component, substream);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_component_mark_push(component, substream, open);

	return soc_component_ret(component, ret);
}
```

These wrappers sort into three classes by what an absent op returns, 0 for a lifecycle or PCM hook the core treats as done, -ENOTSUPP for a clock or jack feature the caller can fall back from, and -EINVAL for a request the component reports invalid:

```
    Three return conventions when the callback pointer is absent
    ──────────────────────────────────────────────────────────────

    wrapper class        absent-callback ret   meaning to the caller
    ┌───────────────────┬─────────────────────┬─────────────────────┐
    │ lifecycle / PCM   │ 0                   │ skipped, treat done │
    │ (probe open       │                     │                     │
    │  hw_params ...)   │                     │                     │
    ├───────────────────┼─────────────────────┼─────────────────────┤
    │ config: clock,    │ -ENOTSUPP           │ feature unsupported │
    │ jack, get_type    │                     │ caller may fall back│
    │ (set_sysclk       │                     │                     │
    │  set_jack ...)    │                     │                     │
    ├───────────────────┼─────────────────────┼─────────────────────┤
    │ config: set_pll,  │ -EINVAL             │ request invalid     │
    │ copy              │                     │                     │
    └───────────────────┴─────────────────────┴─────────────────────┘
      every wrapper ends: return soc_component_ret(component, ret)
```

### pcm_construct runs over every component of a runtime

[`snd_soc_pcm_component_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033) is the construction iteration. It walks the runtime's components with [`for_each_rtd_components()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) and runs each component's [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), so a card with a codec component and a platform component gives each a turn to set up its part of the PCM:

```c
/* sound/soc/soc-component.c:1033 */
int snd_soc_pcm_component_new(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_component *component;
	int ret;
	int i;

	for_each_rtd_components(rtd, i, component) {
		if (component->driver->pcm_construct) {
			ret = component->driver->pcm_construct(component, rtd);
			if (ret < 0)
				return soc_component_ret(component, ret);
		}
	}

	return 0;
}
```

A platform component fills [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to preallocate the DMA pages for the new PCM, while a codec component that carries no DMA leaves it NULL and is skipped. The construction order across components follows the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) of each, so a platform that another component depends on can come first.

### The trigger callback and the start/stop order

[`soc_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1124) runs one component's [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to start or stop its DMA. The order in which the components of a runtime are triggered is set by the [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L165) and [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L166) fields of each descriptor, an [`enum snd_soc_trigger_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L57) that selects whether a component triggers before or after its peers, so a platform DMA can start after the codec is ready and stop before it. The trigger wrapper is the only PCM callback that runs in atomic context under the PCM stream lock, so a [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback may not sleep.

[`soc_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1123) is the per-component step, a `static` helper that calls one component's [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and treats an absent op as success. The exported [`snd_soc_pcm_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1135) loops the runtime's components and calls this helper for each, so the single-component wrapper here is the unit the fan-out repeats:

```c
/* sound/soc/soc-component.c:1123 */
static int soc_component_trigger(struct snd_soc_component *component,
				 struct snd_pcm_substream *substream,
				 int cmd)
{
	int ret = 0;

	if (component->driver->trigger)
		ret = component->driver->trigger(component, substream, cmd);

	return soc_component_ret(component, ret);
}
```

The per-descriptor order fields place each component's turn relative to its peers, the codec coming ready before the platform DMA starts on a START and the platform DMA stopping before the codec on a STOP:

```
    trigger_start / trigger_stop order the peers of one runtime
    ────────────────────────────────────────────────────────────
    (each descriptor's enum snd_soc_trigger_order field)

      START  (bring the stream up)
      ┌────────────────────┐   then   ┌────────────────────┐
      │ codec component    │  ──────▶ │ platform component │
      │ ready first        │          │ DMA starts last    │
      └────────────────────┘          └────────────────────┘

      STOP  (tear the stream down, reverse)
      ┌────────────────────┐   then   ┌────────────────────┐
      │ platform component │  ──────▶ │ codec component    │
      │ DMA stops first    │          │ powers down last   │
      └────────────────────┘          └────────────────────┘

      trigger runs in atomic context under the PCM stream lock:
      the callback may not sleep
```

### The close wrapper consults the open mark before running

[`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266) is the teardown twin of [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251). When called on the rollback path it first tests the [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) mark with [`soc_component_mark_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L48) and returns early for any component whose [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) never ran, so a failed open on one component does not provoke a stray close on it. It then runs the [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op and pops the mark:

```c
/* sound/soc/soc-component.c:266 */
int snd_soc_component_close(struct snd_soc_component *component,
			    struct snd_pcm_substream *substream,
			    int rollback)
{
	int ret = 0;

	if (rollback && !soc_component_mark_match(component, substream, open))
		return 0;

	if (component->driver->close)
		ret = component->driver->close(component, substream);

	/* remove marked substream */
	soc_component_mark_pop(component, open);

	return soc_component_ret(component, ret);
}
```

### The clock, bias, and jack-query wrappers each dispatch one op

The component-wide configuration wrappers share the single-op shape but split on the absent-callback return. [`snd_soc_component_set_pll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L102) starts at `-EINVAL`, so a component with no PLL programming reports the request invalid rather than silently succeeding:

```c
/* sound/soc/soc-component.c:102 */
int snd_soc_component_set_pll(struct snd_soc_component *component, int pll_id,
			      int source, unsigned int freq_in,
			      unsigned int freq_out)
{
	int ret = -EINVAL;

	if (component->driver->set_pll)
		ret = component->driver->set_pll(component, pll_id, source,
						  freq_in, freq_out);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134) instead starts at 0, so a component that does not stage analog bias is moved through its DAPM power states as a no-op while the core treats the transition as done:

```c
/* sound/soc/soc-component.c:134 */
int snd_soc_component_set_bias_level(struct snd_soc_component *component,
				     enum snd_soc_bias_level level)
{
	int ret = 0;

	if (component->driver->set_bias_level)
		ret = component->driver->set_bias_level(component, level);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_component_get_jack_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L210) is the read-side companion of [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), returning the [`get_jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op's reported jack type or `-ENOTSUPP` when the codec supplies no such op, so the machine layer can query what a component supports before binding a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80):

```c
/* sound/soc/soc-component.c:210 */
int snd_soc_component_get_jack_type(
	struct snd_soc_component *component)
{
	int ret = -ENOTSUPP;

	if (component->driver->get_jack_type)
		ret = component->driver->get_jack_type(component);

	return soc_component_ret(component, ret);
}
```

### The fan-out helpers iterate every component of a runtime

Where the single-op wrappers act on one component, the `snd_soc_pcm_component_*` helpers walk the runtime with [`for_each_rtd_components()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) so every component bound to a DAI link gets its turn. [`snd_soc_pcm_component_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063) runs each component's [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op just before start and stops at the first error, the iteration counterpart of the single-op pattern. This is the wrapper the core's [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) step calls, even though the core lists it under the `snd_soc_component_prepare` name:

```c
/* sound/soc/soc-component.c:1063 */
int snd_soc_pcm_component_prepare(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int i, ret;

	for_each_rtd_components(rtd, i, component) {
		if (component->driver->prepare) {
			ret = component->driver->prepare(component, substream);
			if (ret < 0)
				return soc_component_ret(component, ret);
		}
	}

	return 0;
}
```

[`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) runs each component's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op to apply the negotiated format, and pushes the [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L248) mark per component so [`snd_soc_pcm_component_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1101) can free only the components that ran, the same mark discipline the open/close pair uses:

```c
/* sound/soc/soc-component.c:1080 */
int snd_soc_pcm_component_hw_params(struct snd_pcm_substream *substream,
				    struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int i, ret;

	for_each_rtd_components(rtd, i, component) {
		if (component->driver->hw_params) {
			ret = component->driver->hw_params(component,
							   substream, params);
			if (ret < 0)
				return soc_component_ret(component, ret);
		}
		/* mark substream if succeeded */
		soc_component_mark_push(component, substream, hw_params);
	}

	return 0;
}
```

[`snd_soc_pcm_component_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884) is the exception to the run-every-component rule. It iterates but returns from the first component that supplies a [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, since only the one platform component that owns the DMA can report the stream position:

```c
/* sound/soc/soc-component.c:884 */
int snd_soc_pcm_component_pointer(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int i;

	/* FIXME: use 1st pointer */
	for_each_rtd_components(rtd, i, component)
		if (component->driver->pointer)
			return component->driver->pointer(component, substream);

	return 0;
}
```

[`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050) is the teardown counterpart of [`snd_soc_pcm_component_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1033). It guards on `rtd->pcm` so it does nothing when no ALSA PCM was created, then iterates and runs each component's [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to release the DMA buffers a platform component allocated:

```c
/* sound/soc/soc-component.c:1050 */
void snd_soc_pcm_component_free(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_component *component;
	int i;

	if (!rtd->pcm)
		return;

	for_each_rtd_components(rtd, i, component)
		if (component->driver->pcm_destruct)
			component->driver->pcm_destruct(component, rtd->pcm);
}
```

The whole family shares this loop, each helper walking the runtime's codec and platform components in turn, the setup and teardown ones running over all of them and the position read returning from the first component that owns the DMA:

```
    One PCM action runs across every component of a runtime
    ───────────────────────────────────────────────────────

                  snd_soc_pcm_component_*(substream)
                            │ for_each_rtd_components(rtd, i, component)
               ┌────────────┴────────────┐
               ▼                          ▼
        ┌──────────────────┐    ┌──────────────────┐
        │ codec component  │    │ platform comp.   │
        │ driver->op ?     │    │ driver->op ?     │
        └──────────────────┘    └──────────────────┘

      snd_soc_pcm_component_  over all     on error
      ┌──────────────────────┬────────────┬─────────────────────────┐
      │ _new                 │ yes        │ stop, return ret        │
      │ _prepare             │ yes        │ stop at first error     │
      │ _hw_params           │ yes        │ stop; mark per component│
      │ _free                │ yes        │ void, guards rtd->pcm   │
      │ _pointer             │ first match│ return that pointer     │
      └──────────────────────┴────────────┴─────────────────────────┘
        pointer differs because only the DMA-owning component reports
        position, so the first op found returns it and the walk stops
```

### Codec configuration: the rt5682 descriptor

The Realtek RT5682 codec component fills the configuration callbacks in its descriptor [`rt5682_soc_component_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3066). The clock callbacks [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) point at the codec's clock-tree programming, [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) points at its headset detection, and [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) points at its analog-bias staging:

```c
/* sound/soc/codecs/rt5682.c:3066 */
const struct snd_soc_component_driver rt5682_soc_component_dev = {
	.probe = rt5682_probe,
	.remove = rt5682_remove,
	.suspend = rt5682_suspend,
	.resume = rt5682_resume,
	.set_bias_level = rt5682_set_bias_level,
	.controls = rt5682_snd_controls,
	.num_controls = ARRAY_SIZE(rt5682_snd_controls),
	.dapm_widgets = rt5682_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt5682_dapm_widgets),
	.dapm_routes = rt5682_dapm_routes,
	.num_dapm_routes = ARRAY_SIZE(rt5682_dapm_routes),
	.set_sysclk = rt5682_set_component_sysclk,
	.set_pll = rt5682_set_component_pll,
	.set_jack = rt5682_set_jack_detect,
	.use_pmdown_time	= 1,
	.endianness		= 1,
};
```

The codec fills no [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and no substream operations, because it carries no DMA. Those belong to the platform component on the same card. When the machine driver binds a headset jack, [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) dispatches to [`rt5682_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L1014), and when DAPM powers the codec up and down [`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134) dispatches to the codec's bias staging, so the configuration callbacks and the substream operations of a card belong to different components that the core drives through the same wrappers.

```
    rt5682 config vtable: snd_soc_component_<op> ─▶ filled field ─▶ handler
    ──────────────────────────────────────────────────────────────────────

    ┌───────────────────┬─────────────────────────────────┐
    │ descriptor field  │ codec handler                   │
    ├───────────────────┼─────────────────────────────────┤
    │ .set_sysclk       │ rt5682_set_component_sysclk     │
    │ .set_pll          │ rt5682_set_component_pll        │
    │ .set_jack         │ rt5682_set_jack_detect          │
    │ .set_bias_level   │ rt5682_set_bias_level           │
    └───────────────────┴─────────────────────────────────┘
      reached via snd_soc_component_set_sysclk / _set_pll /
      _set_jack / _set_bias_level

      not filled by this codec: pcm_construct, open, hw_params,
      trigger, pointer ... (no DMA; left to the platform component)
```
