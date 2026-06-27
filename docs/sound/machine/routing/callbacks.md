# Machine link and card callbacks

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A machine (or board) driver supplies the glue an ASoC card adds on top of its codec and platform components, and it presents that glue as two function pointer sets, a per-link [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) (with the compressed-audio [`struct snd_soc_compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632)) attached to each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and a card-wide set of hooks held directly in [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). The ASoC core never calls a board hook directly. The PCM path reaches the link ops through the [`snd_soc_link_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c) wrappers in [`soc-link.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c), and the bind, instantiate, and power paths reach the card hooks through the [`snd_soc_card_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c) wrappers in [`soc-card.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c). Each wrapper tests for the hook, calls it, records progress on the teardown-bearing ops with a per-substream mark, and annotates any error through [`soc_link_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L11) or [`soc_card_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L14). The SoundWire machine driver [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) is the worked example, attaching one shared [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) to every back-end link and an [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) while leaving the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) card hook unset.

```
    struct snd_soc_card                       card-wide hooks
    ┌────────────────────────────────────────────────────────────┐
    │ probe / late_probe / remove                                │
    │ suspend_pre / suspend_post                                 │
    │ resume_pre / resume_post                                   │
    │ set_bias_level / set_bias_level_post                       │
    │ add_dai_link / remove_dai_link                             │
    │                                                            │
    │ dai_link ─▶ struct snd_soc_dai_link[]                      │
    │             ┌──────────────────────────────────────────┐   │
    │             │ ops      ─▶ struct snd_soc_ops           │   │
    │             │             startup  shutdown  hw_params │   │
    │             │             hw_free  prepare   trigger   │   │
    │             │ compr_ops ─▶ struct snd_soc_compr_ops    │   │
    │             │ init / exit / be_hw_params_fixup         │   │
    │             └──────────────────────────────────────────┘   │
    └────────────────────────────────────────────────────────────┘

    snd_soc_bind_card() ─▶ probe ─▶ (per link) init ─▶ late_probe
    PCM open/hw_params/start ─▶ link ops via snd_soc_link_*()
```

## SUMMARY

A machine driver writes one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), fills its [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entries, and registers the card through [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65). Each link carries an optional [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L764) pointer to a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), an optional [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L765) pointer to a [`struct snd_soc_compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632), a per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) and [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L757) pair, and an optional [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L760) rewrite hook for the back end of a Dynamic PCM path. The card itself carries the lifecycle and power hooks ([`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004), [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1007), [`suspend_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1011), [`suspend_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1012), [`resume_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1013), [`resume_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1014)), the bias hooks ([`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1017), [`set_bias_level_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1020)), and the link-mutation hooks ([`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024), [`remove_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1026)).

The two wrapper files give every board hook one calling shape. In [`soc-link.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c) the wrapper recovers the runtime from the substream with [`snd_soc_substream_to_rtd()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1200), tests [`rtd->dai_link->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L764) and the specific op, calls it, and on a teardown-bearing op records the substream with [`soc_link_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L23) so the matching teardown wrapper can skip a link whose setup never ran. In [`soc-card.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c) the wrapper tests the field on the card and calls it, with [`snd_soc_card_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140) and [`snd_soc_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) also maintaining the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) flag that [`snd_soc_card_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L193) consults. The card hooks fire from fixed points in [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) fires from [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) once the PCM runtime exists, and the link ops fire from the PCM handlers in [`soc-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c) as a userspace client opens, configures, runs, and closes a stream.

## SPECIFICATIONS

The machine link and card callbacks are Linux kernel software constructs and have no standalone hardware specification. On the x86-64 ACPI platforms the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) worked example targets, the board is selected by [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) matching and the codecs ride on SoundWire, handled by the kernel SoundWire core.

## LINUX KERNEL

### Per-link op tables and the link fields (soc.h)

- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the per-link machine stream ops, with [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623)
- [`'\<struct snd_soc_compr_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632): the per-link compressed-audio ops, with startup, shutdown, and set_params
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one CPU-to-codec link, holding the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L764) and [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L765) pointers, the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754)/[`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L757) pair, and the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L760) hook
- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the card object carrying the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array, the lifecycle and power hooks, and the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) bits

### Link op wrappers (soc-link.c)

- [`'\<snd_soc_link_init\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) / [`'\<snd_soc_link_exit\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L37): run the link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) at PCM-runtime creation and the dual [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L757) on teardown or rollback
- [`'\<snd_soc_link_be_hw_params_fixup\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43): rewrite a back-end [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) before the back-end DAIs are configured
- [`'\<snd_soc_link_startup\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54) / [`'\<snd_soc_link_shutdown\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70): open and close the link for a substream; push and pop the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark
- [`'\<snd_soc_link_hw_params\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98) / [`'\<snd_soc_link_hw_free\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L115): apply and release machine-level hardware parameters; push and pop the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark
- [`'\<snd_soc_link_prepare\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86): ready the link just before the stream starts
- [`'\<snd_soc_link_trigger\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142): start, stop, pause, suspend, or resume the link, handled per command by [`soc_link_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L130) with the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark
- [`'\<snd_soc_link_compr_startup\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L170) / [`'\<snd_soc_link_compr_set_params\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L202): the [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L765) variants for a compressed-audio stream
- [`soc_link_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L11) / [`soc_link_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L23): the error-annotation and substream-mark macros every link wrapper uses

### Card hook wrappers (soc-card.c)

- [`'\<snd_soc_card_probe\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140) / [`'\<snd_soc_card_late_probe\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163): run the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) and [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) card hooks and set the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) flag
- [`'\<snd_soc_card_remove\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L193): run [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1007) only when [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is set, then clear the flag
- [`'\<snd_soc_card_suspend_pre\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L100) / [`'\<snd_soc_card_suspend_post\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L110): run [`suspend_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1011) and [`suspend_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1012) around the component suspend work
- [`'\<snd_soc_card_resume_pre\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L120) / [`'\<snd_soc_card_resume_post\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L130): run [`resume_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1013) and [`resume_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1014) around the component resume work
- [`'\<snd_soc_card_set_bias_level\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L206) / [`'\<snd_soc_card_set_bias_level_post\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L218): run [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1017) and [`set_bias_level_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1020) as DAPM moves the card across an [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415)
- [`'\<snd_soc_card_fixup_controls\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L187): run the [`fixup_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1006) hook after the card's controls and widgets exist
- [`'\<snd_soc_card_add_dai_link\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L230): run the [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) hook as each runtime is created
- [`soc_card_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L14): the error-annotation macro every card wrapper uses

### Bind, instantiate, and PCM call sites

- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): instantiate the card, calling [`snd_soc_card_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140), then per-runtime [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512), then [`snd_soc_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) and [`snd_soc_card_fixup_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L187)
- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): call [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) first, then create the PCM, calling [`snd_soc_link_exit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L37) on the error tail
- [`'\<snd_soc_add_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175): allocate a runtime for a link and call [`snd_soc_card_add_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L230)
- [`'\<__soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854): drive [`snd_soc_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54) along with the component and DAI startups
- [`'\<dpcm_be_dai_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073): call [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) on the back end before applying its parameters
- [`'\<snd_soc_dapm_set_bias_level\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093): bracket the DAPM bias transition with [`snd_soc_card_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L206) and [`snd_soc_card_set_bias_level_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L218)

### sof_sdw worked example (x86-64 ACPI)

- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the one [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) every SoundWire back-end link shares
- [`'\<asoc_sdw_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918): the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) adding the codec's controls and widgets to the card
- [`'\<asoc_sdw_startup\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1025): the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op opening the SoundWire stream with [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899)
- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op driving [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_hw_params\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1090): the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op spreading channels across the codecs via the link [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L731)
- [`'\<sof_sdw_card_late_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1405): the [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) card hook finishing HDMI and shared-controls setup

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver concept, the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) fields, and the per-link machine ops
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): how the codec, platform, and machine layers combine into one card
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the back-end link runs its [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L760) hook
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families a link connects across its CPU and codec sides

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every hook below is a field of [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`struct snd_soc_compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632), [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), or [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and every one is optional. A machine driver fills only the hooks its board needs, and the matching wrapper treats an absent hook as success, returning 0 without touching the hardware. The link ops fire on the PCM path and the card hooks fire on the bind, instantiate, and power paths, so the order a userspace client touches a stream maps to a fixed sequence of link ops.

| userspace action | link op (wrapper) | also fires |
|------------------|-------------------|------------|
| card bind | (none) | [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140), then per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27), then [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) |
| `open()` | [`startup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54) | DAI and component startup |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98) | back-end [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) on DPCM |
| `SNDRV_PCM_IOCTL_PREPARE` | [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86) | DAPM bias, [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L206) |
| `SNDRV_PCM_IOCTL_START` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142) (START) | DAI trigger |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L115) | DAI hw_free |
| `close()` | [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70) | DAI and component shutdown |

[`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) runs when a substream is opened and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) when it is closed, with the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark deciding whether a rollback tears down a link whose startup actually ran. [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) applies the negotiated parameters at the machine level (a board can program a system clock or select a mux) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) releases what it claimed, guarded by the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark. [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) runs after parameters are applied and before the stream starts, and [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) starts, stops, pauses, suspends, or resumes the data flow, with a SoundWire board marking its links [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L777) so the trigger may sleep on the bus bank-switch completion.

The card hooks run on the bind and power paths. [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) runs before the components and links are probed and [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) after the runtimes, controls, and routes exist, while [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1007) runs at teardown only when the card had been probed. The four power hooks [`suspend_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1011), [`suspend_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1012), [`resume_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1013), and [`resume_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1014) bracket the component and DAI power work so a board can sequence external clocks or regulators around the codec transition. [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1017) and [`set_bias_level_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1020) run from the DAPM core as the card crosses a bias level, [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) fires as each runtime is created so a board can finish a link before it binds, and [`fixup_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1006) runs near the end of bind so a board can adjust or remove kcontrols the components registered.

## DETAILS

### The two op tables a link carries

A machine driver attaches its stream glue to a link through two pointers. The PCM op table is a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), whose six members are the PCM-operation hooks the core routes from userspace, each taking a [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464):

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

The compressed-audio op table is a [`struct snd_soc_compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632), the offload-path analog with three members taking a [`struct snd_compr_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/compress_driver.h#L109):

```c
/* include/sound/soc.h:632 */
struct snd_soc_compr_ops {
	int (*startup)(struct snd_compr_stream *);
	void (*shutdown)(struct snd_compr_stream *);
	int (*set_params)(struct snd_compr_stream *);
};
```

Both pointers, the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754)/[`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L757) pair, and the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L760) hook are fields of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702):

```c
/* include/sound/soc.h:754 */
	/* codec/machine specific init - e.g. add machine controls */
	int (*init)(struct snd_soc_pcm_runtime *rtd);

	/* codec/machine specific exit - dual of init() */
	void (*exit)(struct snd_soc_pcm_runtime *rtd);

	/* optional hw_params re-writing for BE and FE sync */
	int (*be_hw_params_fixup)(struct snd_soc_pcm_runtime *rtd,
			struct snd_pcm_hw_params *params);

	/* machine stream operations */
	const struct snd_soc_ops *ops;
	const struct snd_soc_compr_ops *compr_ops;
```

The card-wide hooks are a separate set held directly in [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), grouped by the moment each runs:

```c
/* include/sound/soc.h:1004 */
	int (*probe)(struct snd_soc_card *card);
	int (*late_probe)(struct snd_soc_card *card);
	void (*fixup_controls)(struct snd_soc_card *card);
	int (*remove)(struct snd_soc_card *card);

	/* the pre and post PM functions are used to do any PM work before and
	 * after the codec and DAI's do any PM work. */
	int (*suspend_pre)(struct snd_soc_card *card);
	int (*suspend_post)(struct snd_soc_card *card);
	int (*resume_pre)(struct snd_soc_card *card);
	int (*resume_post)(struct snd_soc_card *card);

	/* callbacks */
	int (*set_bias_level)(struct snd_soc_card *,
			      struct snd_soc_dapm_context *dapm,
			      enum snd_soc_bias_level level);
	int (*set_bias_level_post)(struct snd_soc_card *,
				   struct snd_soc_dapm_context *dapm,
				   enum snd_soc_bias_level level);

	int (*add_dai_link)(struct snd_soc_card *,
			    struct snd_soc_dai_link *link);
	void (*remove_dai_link)(struct snd_soc_card *,
			    struct snd_soc_dai_link *link);
```

### The wrapper shape every link op shares

The ASoC core reaches a link op only through a wrapper in [`soc-link.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c), and the wrappers share one shape. Two macro groups carry the boilerplate, [`soc_link_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L11) for error annotation through the link name and [`soc_link_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L23) for the per-substream marks stored on the runtime:

```c
/* sound/soc/soc-link.c:11 */
#define soc_link_ret(rtd, ret) _soc_link_ret(rtd, __func__, ret)
static inline int _soc_link_ret(struct snd_soc_pcm_runtime *rtd,
				const char *func, int ret)
{
	return snd_soc_ret(rtd->dev, ret,
			   "at %s() on %s\n", func, rtd->dai_link->name);
}
...
#define soc_link_mark_push(rtd, substream, tgt)		((rtd)->mark_##tgt = substream)
#define soc_link_mark_pop(rtd, tgt)		((rtd)->mark_##tgt = NULL)
#define soc_link_mark_match(rtd, substream, tgt)	((rtd)->mark_##tgt == substream)
```

[`snd_soc_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54) shows the setup variant. It recovers the runtime from the substream, tests both the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L764) pointer and the specific op so an absent table is treated as success, calls the op, and records the substream in the startup mark only when the call returned 0:

```c
/* sound/soc/soc-link.c:54 */
int snd_soc_link_startup(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret = 0;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->startup)
		ret = rtd->dai_link->ops->startup(substream);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_link_mark_push(rtd, substream, startup);

	return soc_link_ret(rtd, ret);
}
```

[`snd_soc_link_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70) is the teardown half and takes a `rollback` argument. When `rollback` is set it returns early for a link whose startup mark does not match the substream being unwound, so a failure partway through a multi-stage open undoes only the links that had opened:

```c
/* sound/soc/soc-link.c:70 */
void snd_soc_link_shutdown(struct snd_pcm_substream *substream,
			   int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);

	if (rollback && !soc_link_mark_match(rtd, substream, startup))
		return;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->shutdown)
		rtd->dai_link->ops->shutdown(substream);

	/* remove marked substream */
	soc_link_mark_pop(rtd, startup);
}
```

[`snd_soc_link_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142) splits its commands into a start group and a stop group, pushing the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark when a start succeeds and honoring it on the stop group's rollback:

```c
/* sound/soc/soc-link.c:142 */
int snd_soc_link_trigger(struct snd_pcm_substream *substream, int cmd,
			 int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret = 0;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		ret = soc_link_trigger(substream, cmd);
		if (ret < 0)
			break;
		soc_link_mark_push(rtd, substream, trigger);
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		if (rollback && !soc_link_mark_match(rtd, substream, trigger))
			break;

		ret = soc_link_trigger(substream, cmd);
		soc_link_mark_pop(rtd, startup);
	}

	return ret;
}
```

Every setup half in the path follows that shape, pushing its named mark on a ret==0 success so the matching teardown half checks the same mark and unwinds only the substream it actually opened:

```
    Per-substream marks: setup op pushes, teardown dual checks
    ────────────────────────────────────────────────────────────

    setup op (push on ret==0)      mark           teardown dual
    ──────────────────────────     ─────────      ─────────────────────
    snd_soc_link_startup       ─▶  startup    ◀─  snd_soc_link_shutdown
    snd_soc_link_hw_params     ─▶  hw_params  ◀─  snd_soc_link_hw_free
    snd_soc_link_trigger       ─▶  trigger    ◀─  snd_soc_link_trigger
      START group                                   STOP group
    snd_soc_link_compr_startup ─▶  compr_..   ◀─  compr shutdown

    push: soc_link_mark_push(rtd, substream, tgt) sets rtd->mark_<tgt>
    rollback: dual returns early unless mark_<tgt> == substream
    prepare and set_params carry no mark (no teardown dual to skip)
```

### The configure, prepare, and release link wrappers

The middle of the PCM path reuses the same shape. [`snd_soc_link_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98) applies the machine-level [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op and pushes the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) mark only on success, the same setup pattern [`snd_soc_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54) uses for its own mark:

```c
/* sound/soc/soc-link.c:98 */
int snd_soc_link_hw_params(struct snd_pcm_substream *substream,
			   struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret = 0;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->hw_params)
		ret = rtd->dai_link->ops->hw_params(substream, params);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_link_mark_push(rtd, substream, hw_params);

	return soc_link_ret(rtd, ret);
}
```

[`snd_soc_link_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L115) is the release half and honors that mark on a `rollback` unwind, so the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op runs only for a link whose [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op had succeeded, mirroring how [`snd_soc_link_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70) consults the startup mark:

```c
/* sound/soc/soc-link.c:115 */
void snd_soc_link_hw_free(struct snd_pcm_substream *substream, int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);

	if (rollback && !soc_link_mark_match(rtd, substream, hw_params))
		return;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->hw_free)
		rtd->dai_link->ops->hw_free(substream);

	/* remove marked substream */
	soc_link_mark_pop(rtd, hw_params);
}
```

[`snd_soc_link_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86) runs the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op just before the stream starts and carries no mark, since [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) has no teardown dual to skip:

```c
/* sound/soc/soc-link.c:86 */
int snd_soc_link_prepare(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret = 0;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->prepare)
		ret = rtd->dai_link->ops->prepare(substream);

	return soc_link_ret(rtd, ret);
}
```

### The compressed-audio link wrappers

The offload path reaches the [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L765) table through its own wrappers, which recover the runtime from `cstream->private_data` rather than from a substream. [`snd_soc_link_compr_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L170) calls the compressed [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632) op and pushes a `compr_startup` mark its shutdown dual pops:

```c
/* sound/soc/soc-link.c:170 */
int snd_soc_link_compr_startup(struct snd_compr_stream *cstream)
{
	struct snd_soc_pcm_runtime *rtd = cstream->private_data;
	int ret = 0;

	if (rtd->dai_link->compr_ops &&
	    rtd->dai_link->compr_ops->startup)
		ret = rtd->dai_link->compr_ops->startup(cstream);

	if (ret == 0)
		soc_link_mark_push(rtd, cstream, compr_startup);

	return soc_link_ret(rtd, ret);
}
```

[`snd_soc_link_compr_set_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L202) is the compressed analog of [`snd_soc_link_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98), running the [`set_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632) op with no mark to keep:

```c
/* sound/soc/soc-link.c:202 */
int snd_soc_link_compr_set_params(struct snd_compr_stream *cstream)
{
	struct snd_soc_pcm_runtime *rtd = cstream->private_data;
	int ret = 0;

	if (rtd->dai_link->compr_ops &&
	    rtd->dai_link->compr_ops->set_params)
		ret = rtd->dai_link->compr_ops->set_params(cstream);

	return soc_link_ret(rtd, ret);
}
```

### The PCM path fires the link ops

The PCM handlers in [`soc-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c) are the only callers of the link op wrappers. [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) opens a substream, and its first hardware action is the machine [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op, run before the component and DAI startups so the board can bring up a shared resource the codecs depend on:

```c
/* sound/soc/soc-pcm.c:854 */
static int __soc_pcm_open(struct snd_soc_pcm_runtime *rtd,
			  struct snd_pcm_substream *substream)
{
	...
	ret = soc_pcm_components_open(substream);
	if (ret < 0)
		goto err;

	ret = snd_soc_link_startup(substream);
	if (ret < 0)
		goto err;
	...
```

On a Dynamic PCM card the back end gets a chance to rewrite the negotiated parameters. [`dpcm_be_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073) runs [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) on the back-end link before it configures the back-end DAIs:

```c
/* sound/soc/soc-link.c:43 */
int snd_soc_link_be_hw_params_fixup(struct snd_soc_pcm_runtime *rtd,
				    struct snd_pcm_hw_params *params)
{
	int ret = 0;

	if (rtd->dai_link->be_hw_params_fixup)
		ret = rtd->dai_link->be_hw_params_fixup(rtd, params);

	return soc_link_ret(rtd, ret);
}
```

[`dpcm_be_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073) walks every back end of the front-end runtime, copies the front-end parameters into a local [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408), and runs the back-end link's [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L760) hook through the wrapper before that copy is applied to the back-end DAIs, so the board rewrites the rate, channel count, or format the front end negotiated:

```c
/* sound/soc/soc-pcm.c:2073 */
int dpcm_be_dai_hw_params(struct snd_soc_pcm_runtime *fe, int stream)
{
	struct snd_soc_pcm_runtime *be;
	...
	for_each_dpcm_be(fe, stream, dpcm) {
		struct snd_pcm_hw_params hw_params;
		...
		/* copy params for each dpcm */
		memcpy(&hw_params, &fe->dpcm[stream].hw_params,
				sizeof(struct snd_pcm_hw_params));

		/* perform any hw_params fixups */
		ret = snd_soc_link_be_hw_params_fixup(be, &hw_params);
		if (ret < 0)
			goto unwind;

		/* copy the fixed-up hw params for BE dai */
		memcpy(&be->dpcm[stream].hw_params, &hw_params,
		       sizeof(struct snd_pcm_hw_params));
		...
		ret = __soc_pcm_hw_params(be_substream, &hw_params);
		if (ret < 0)
			goto unwind;
		...
	}
	return 0;
	...
}
```

### The card hooks fire from snd_soc_bind_card

The card-wide hooks all originate in [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), which instantiates the card in one pass and threads the card wrappers between its build stages. Its skeleton shows the order, adding the predefined runtimes through [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269), then [`snd_soc_card_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140), the per-runtime [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512), and finally [`snd_soc_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) and [`snd_soc_card_fixup_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L187):

```c
/* sound/soc/soc-core.c:2163 */
static int snd_soc_bind_card(struct snd_soc_card *card)
{
	...
	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;
	...
	/* initialise the sound card only once */
	ret = snd_soc_card_probe(card);
	if (ret < 0)
		goto probe_end;
	...
	for_each_card_rtds(card, rtd) {
		ret = soc_init_pcm_runtime(card, rtd);
		if (ret < 0)
			goto probe_end;
	}
	...
	ret = snd_soc_card_late_probe(card);
	if (ret < 0)
		goto probe_end;

	snd_soc_dapm_new_widgets(card);
	snd_soc_card_fixup_controls(card);
	...
}
```

After the predefined links are added to the runtime list, the function runs the board's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) hook through [`snd_soc_card_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140) before any component or DAI link is probed:

```c
/* sound/soc/soc-core.c:2213 */
	/* initialise the sound card only once */
	ret = snd_soc_card_probe(card);
	if (ret < 0)
		goto probe_end;

	/* probe all components used by DAI links on this card */
	ret = soc_probe_link_components(card);
```

[`snd_soc_card_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L140) runs the hook and, when the board supplied one, sets the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) flag early. According to the comment in the function, it sets the flag here because "it needs to care about late_probe", so the flag is correct whether or not a [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) hook follows:

```c
/* sound/soc/soc-card.c:140 */
int snd_soc_card_probe(struct snd_soc_card *card)
{
	if (card->probe) {
		int ret = card->probe(card);

		if (ret < 0)
			return soc_card_ret(card, ret);

		/*
		 * It has "card->probe" and "card->late_probe" callbacks.
		 * So, set "probed" flag here, because it needs to care
		 * about "late_probe".
		 */
		card->probed = 1;
	}

	return 0;
}
```

Once the components and links are probed, [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) initializes each runtime through [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512), whose first step is the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) hook through [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27), and whose error tail runs the dual [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L757):

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
	...
err:
	snd_soc_link_exit(rtd);
	return ret;
}
```

After the runtimes, controls, and routes are in place, [`snd_soc_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) runs the [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) hook and sets the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) flag unconditionally, since by the time it runs the card is fully bound whether or not the board has an early [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) hook:

```c
/* sound/soc/soc-card.c:163 */
int snd_soc_card_late_probe(struct snd_soc_card *card)
{
	if (card->late_probe) {
		int ret = card->late_probe(card);

		if (ret < 0)
			return soc_card_ret(card, ret);
	}
	...
	card->probed = 1;

	return 0;
}
```

The teardown half pairs with the flag. [`snd_soc_card_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L193) calls the board's [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1007) hook only when [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is set, then clears it:

```c
/* sound/soc/soc-card.c:193 */
int snd_soc_card_remove(struct snd_soc_card *card)
{
	int ret = 0;

	if (card->probed &&
	    card->remove)
		ret = card->remove(card);

	card->probed = 0;

	return soc_card_ret(card, ret);
}
```

The [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) hook is the one card hook that fires per link rather than once per card. [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) is called for every link the card adds, and its first action is [`snd_soc_card_add_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L230), giving the board a last chance to finish a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) before the runtime is allocated by [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1112) and its CPU, codec, and platform components are matched and added through [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L778) and [`snd_soc_rtd_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L483):

```c
/* sound/soc/soc-core.c:1175 */
static int snd_soc_add_pcm_runtime(struct snd_soc_card *card,
				   struct snd_soc_dai_link *dai_link)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_dai_link_component *codec, *platform, *cpu;
	struct snd_soc_component *component;
	int i, id, ret;

	lockdep_assert_held(&client_mutex);

	/*
	 * Notify the machine driver for extra initialization
	 */
	ret = snd_soc_card_add_dai_link(card, dai_link);
	if (ret < 0)
		return ret;

	if (dai_link->ignore)
		return 0;

	dev_dbg(card->dev, "ASoC: binding %s\n", dai_link->name);
	...
	rtd = soc_new_pcm_runtime(card, dai_link);
	if (!rtd)
		return -ENOMEM;

	for_each_link_cpus(dai_link, i, cpu) {
		snd_soc_rtd_to_cpu(rtd, i) = snd_soc_find_dai(cpu);
		...
		snd_soc_rtd_add_component(rtd, snd_soc_rtd_to_cpu(rtd, i)->component);
	}
	...
}
```

The matching wrapper is the plainest card wrapper, testing the field and annotating any error through [`soc_card_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L14):

```c
/* sound/soc/soc-card.c:230 */
int snd_soc_card_add_dai_link(struct snd_soc_card *card,
			      struct snd_soc_dai_link *dai_link)
{
	int ret = 0;

	if (card->add_dai_link)
		ret = card->add_dai_link(card, dai_link);

	return soc_card_ret(card, ret);
}
```

Near the end of bind, [`snd_soc_card_fixup_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L187) runs the [`fixup_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1006) hook so the board can adjust or remove the kcontrols the components registered. It returns no value and keeps no flag, so it carries the lightest wrapper of the set:

```c
/* sound/soc/soc-card.c:187 */
void snd_soc_card_fixup_controls(struct snd_soc_card *card)
{
	if (card->fixup_controls)
		card->fixup_controls(card);
}
```

Bind fires these hooks in a fixed order down the timeline, the per-link add_dai_link first, then probe and the per-link init, late_probe, and this fixup_controls last, with the probed flag deciding whether remove runs at teardown:

```
    Card-hook firing order inside snd_soc_bind_card()
    ───────────────────────────────────────────────────

    time
     │  snd_soc_add_pcm_runtimes
     │     └─ per link:  add_dai_link        ◀ card hook (per link)
     │  snd_soc_card_probe                   ◀ probe      (once)
     │  soc_probe_link_components / _dais
     │  per runtime: soc_init_pcm_runtime
     │     └─ snd_soc_link_init              ◀ init       (per link)
     │  snd_soc_card_late_probe              ◀ late_probe (once)
     │  snd_soc_dapm_new_widgets
     │  snd_soc_card_fixup_controls          ◀ fixup_controls
     ▼

    teardown:  snd_soc_card_remove  fires remove only if probed==1
    probed set by probe (early) and by late_probe (unconditional)
```

### set_bias_level brackets the DAPM transition

The bias hooks run from the DAPM core rather than the bind or PCM paths. [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) brackets the per-context bias change with the card's pre and post hooks, so the board sees the transition before the components apply it and again after. [`snd_soc_card_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L206) is the pre half, taking an [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415):

```c
/* sound/soc/soc-card.c:206 */
int snd_soc_card_set_bias_level(struct snd_soc_card *card,
				struct snd_soc_dapm_context *dapm,
				enum snd_soc_bias_level level)
{
	int ret = 0;

	if (card->set_bias_level)
		ret = card->set_bias_level(card, dapm, level);

	return soc_card_ret(card, ret);
}
```

[`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) is the caller that brackets the transition. It runs the pre hook first, then moves the context across the level for any context other than the card's own, then runs the post hook, so [`snd_soc_card_set_bias_level_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L218) sees the change after the components have applied it:

```c
/* sound/soc/soc-dapm.c:1093 */
static int snd_soc_dapm_set_bias_level(struct snd_soc_dapm_context *dapm,
				       enum snd_soc_bias_level level)
{
	struct snd_soc_card *card = dapm->card;
	int ret = 0;

	trace_snd_soc_bias_level_start(dapm, level);

	ret = snd_soc_card_set_bias_level(card, dapm, level);
	if (ret != 0)
		goto out;

	if (dapm != card->dapm)
		ret = snd_soc_dapm_force_bias_level(dapm, level);

	if (ret != 0)
		goto out;

	ret = snd_soc_card_set_bias_level_post(card, dapm, level);
out:
	trace_snd_soc_bias_level_done(dapm, level);
	...
}
```

[`snd_soc_card_set_bias_level_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L218) is the post half, the same shape as the pre half but reading the [`set_bias_level_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1020) field:

```c
/* sound/soc/soc-card.c:218 */
int snd_soc_card_set_bias_level_post(struct snd_soc_card *card,
				     struct snd_soc_dapm_context *dapm,
				     enum snd_soc_bias_level level)
{
	int ret = 0;

	if (card->set_bias_level_post)
		ret = card->set_bias_level_post(card, dapm, level);

	return soc_card_ret(card, ret);
}
```

The DAPM caller wraps the level change between the two halves, running the pre hook first, letting the components move the context across the level, then this post hook once they have settled:

```
    set_bias_level brackets one DAPM bias transition
    ──────────────────────────────────────────────────

    snd_soc_dapm_set_bias_level(dapm, level):

      1  snd_soc_card_set_bias_level       ─▶ set_bias_level   (pre)
      2  if dapm != card->dapm:
            snd_soc_dapm_force_bias_level   ─▶ components apply
      3  snd_soc_card_set_bias_level_post  ─▶ set_bias_level_post (post)

    pre sees the level before the components move; post sees it after
```

### The suspend and resume card wrappers

The four power hooks share the suspend and resume paths and the same wrapper shape as the bias pre and post halves. [`snd_soc_card_suspend_pre()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L100) and [`snd_soc_card_suspend_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L110) run the [`suspend_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1011) and [`suspend_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1012) hooks around the component and DAI suspend work, so the board can sequence external clocks or regulators on either side of the codec transition:

```c
/* sound/soc/soc-card.c:100 */
int snd_soc_card_suspend_pre(struct snd_soc_card *card)
{
	int ret = 0;

	if (card->suspend_pre)
		ret = card->suspend_pre(card);

	return soc_card_ret(card, ret);
}

int snd_soc_card_suspend_post(struct snd_soc_card *card)
{
	int ret = 0;

	if (card->suspend_post)
		ret = card->suspend_post(card);

	return soc_card_ret(card, ret);
}
```

[`snd_soc_card_resume_pre()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L120) and [`snd_soc_card_resume_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L130) are the resume duals, running the [`resume_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1013) and [`resume_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1014) hooks around the component and DAI resume work:

```c
/* sound/soc/soc-card.c:120 */
int snd_soc_card_resume_pre(struct snd_soc_card *card)
{
	int ret = 0;

	if (card->resume_pre)
		ret = card->resume_pre(card);

	return soc_card_ret(card, ret);
}

int snd_soc_card_resume_post(struct snd_soc_card *card)
{
	int ret = 0;

	if (card->resume_post)
		ret = card->resume_post(card);

	return soc_card_ret(card, ret);
}
```

### Worked example: the sof_sdw SoundWire machine

The Intel SoundWire machine driver in [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) attaches one shared [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) to every back-end link, [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865), filling the PCM ops with SoundWire stream helpers:

```c
/* sound/soc/intel/boards/sof_sdw.c:865 */
static const struct snd_soc_ops sdw_ops = {
	.startup = asoc_sdw_startup,
	.prepare = asoc_sdw_prepare,
	.trigger = asoc_sdw_trigger,
	.hw_params = asoc_sdw_hw_params,
	.hw_free = asoc_sdw_hw_free,
	.shutdown = asoc_sdw_shutdown,
};
```

The link builder marks each SoundWire link [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L777) right after building it, because the SoundWire stream operations and bank switch run on [`wait_for_completion()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/completion.c#L151) and may therefore sleep inside the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op:

```c
/* sound/soc/intel/boards/sof_sdw.c:999 */
		asoc_sdw_init_dai_link(dev, *dai_links, be_id, name, playback, capture,
				       cpus, num_cpus, platform, 1, codecs, num_codecs,
				       1, asoc_sdw_rtd_init, &sdw_ops);

		/*
		 * SoundWire DAILINKs use 'stream' functions and Bank Switch operations
		 * based on wait_for_completion(), tag them as 'nonatomic'.
		 */
		(*dai_links)->nonatomic = true;
```

When the card binds, the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) runs once per runtime. [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) walks the codec DAIs of the runtime, finds the SoundWire peripheral behind each, and adds that codec's card controls and DAPM widgets through [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521) and [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:918 */
int asoc_sdw_rtd_init(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	...
	for_each_rtd_codec_dais(rtd, i, dai) {
		...
		if (codec_info->dais[dai_index].controls) {
			ret = snd_soc_add_card_controls(card, codec_info->dais[dai_index].controls,
							codec_info->dais[dai_index].num_controls);
			...
		}
		if (codec_info->dais[dai_index].widgets) {
			ret = snd_soc_dapm_new_controls(dapm,
							codec_info->dais[dai_index].widgets,
							codec_info->dais[dai_index].num_widgets);
			...
		}
		...
	}
	...
}
```

On the PCM path, the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op opens the SoundWire stream. [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) finds the SoundWire stream stored on the first CPU DAI and readies it with [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533), so by the time the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op fires START the bus is configured:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1031 */
int asoc_sdw_prepare(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_stream_runtime *sdw_stream;
	struct snd_soc_dai *dai;

	/* Find stream from first CPU DAI */
	dai = snd_soc_rtd_to_cpu(rtd, 0);

	sdw_stream = snd_soc_dai_get_stream(dai, substream->stream);
	if (IS_ERR(sdw_stream)) {
		dev_err(rtd->dev, "no stream found for DAI %s\n", dai->name);
		return PTR_ERR(sdw_stream);
	}

	return sdw_prepare_stream(sdw_stream);
}
```

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op uses the link's [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L731) to spread the stream's channels across the codecs of a multi-amp link, computing a per-codec channel mask the core applies to each CPU DAI:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1090 */
int asoc_sdw_hw_params(struct snd_pcm_substream *substream,
		       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai_link_ch_map *ch_maps;
	int ch = params_channels(params);
	unsigned int ch_mask;
	int num_codecs;
	int step;
	int i;

	if (!rtd->dai_link->ch_maps)
		return 0;

	/* Identical data will be sent to all codecs in playback */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		ch_mask = GENMASK(ch - 1, 0);
		step = 0;
	} else {
		num_codecs = rtd->dai_link->num_codecs;
		...
		ch_mask = GENMASK(ch / num_codecs - 1, 0);
		step = hweight_long(ch_mask);
	}
	...
	for_each_link_ch_maps(rtd->dai_link, i, ch_maps)
		ch_maps->ch_mask = ch_mask << (i * step);

	return 0;
}
```

On the card side, [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) leaves the early [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1004) hook unset and supplies only [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1005) and [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024), set on the card during the platform driver's probe. [`sof_sdw_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1405) then runs once the card is fully built, doing the shared-controls work and completing the HDMI setup when an iDisp codec is present:

```c
/* sound/soc/intel/boards/sof_sdw.c:1405 */
static int sof_sdw_card_late_probe(struct snd_soc_card *card)
{
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	struct intel_mc_ctx *intel_ctx = (struct intel_mc_ctx *)ctx->private;
	int ret = 0;

	ret = asoc_sdw_card_late_probe(card);
	if (ret < 0)
		return ret;

	if (intel_ctx->hdmi.idisp_codec)
		ret = sof_sdw_hdmi_card_late_probe(card);

	return ret;
}
```

Beyond those card hooks, the board fills each op slot with its concrete SoundWire op, startup and shutdown opening and closing the stream, trigger running START and STOP, and hw_params spreading the channels across ch_maps:

```
    sof_sdw dispatch: snd_soc_ops slot ─▶ concrete op
    ───────────────────────────────────────────────────

    struct snd_soc_ops sdw_ops      asoc_sdw_* implementation
    ──────────────────────────      ─────────────────────────
    .startup   ─▶ asoc_sdw_startup   open SoundWire stream
    .prepare   ─▶ asoc_sdw_prepare   sdw_prepare_stream
    .trigger   ─▶ asoc_sdw_trigger   START/STOP (nonatomic)
    .hw_params ─▶ asoc_sdw_hw_params spread ch over ch_maps
    .hw_free   ─▶ asoc_sdw_hw_free   release stream
    .shutdown  ─▶ asoc_sdw_shutdown  close stream

    card hooks:  probe unset    late_probe = sof_sdw_card_late_probe
    per-link init = asoc_sdw_rtd_init   (adds codec controls + widgets)
```
