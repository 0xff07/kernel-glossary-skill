# ASoC DAI link (snd_soc_dai_link)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAI link is the static description that binds one audio path together, naming the CPU-side DAI or DAIs, the codec-side DAI or DAIs, and the platform or PCM/DMA component that carries the data, and the kernel represents it as [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). A machine driver fills in an array of these and hands it to the card, and each end is itself a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that names a component plus a DAI within it through its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) fields. The [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) arrays may each hold more than one entry, and a [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array of [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) pairs each CPU DAI to the codec DAI it feeds. The link also carries machine-level behavior, the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) serial format word, an [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback pair, a [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook for Dynamic PCM back-ends, an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer to a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) function pointer struct for the machine's own PCM callbacks, a [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer for compressed paths, and a row of config bit-fields. The card walks the array through [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269), and [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) resolves every component name in one link into a runtime [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) by looking each DAI up with [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917). The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine builds its links at probe time rather than statically, with [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) populating each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the SoundWire topology it discovered.

```
    struct snd_soc_dai_link
    ┌────────────────────────────────────────────────────────────────────┐
    │  name, stream_name, id, dai_fmt                                    │
    │  init() / exit() / be_hw_params_fixup()                            │
    │  ops ─▶ snd_soc_ops      compr_ops ─▶ snd_soc_compr_ops            │
    │  config bits: nonatomic, no_pcm, dynamic, ignore_suspend, ...      │
    │                                                                    │
    │  cpus ──────────┐   codecs ────────┐   platforms ──────┐           │
    │  num_cpus = C   │   num_codecs = K │   num_platforms=P │           │
    │  ch_maps ───────┼──────────┐       │                   │           │
    └─────────────────┼──────────┼───────┼───────────────────┼───────────┘
                      │          │       │                   │
                      ▼          │       ▼                   ▼
    cpus[0..C-1]                 │  codecs[0..K-1]       platforms[0..P-1]
    ┌──────────────┐             │  ┌──────────────┐     ┌──────────────┐
    │ name         │             │  │ name         │     │ name         │
    │ dai_name     │             │  │ dai_name     │     │ dai_name     │
    │ ext_fmt      │             │  │ ext_fmt      │     │ ext_fmt      │
    └──────────────┘             │  └──────────────┘     └──────────────┘
      struct snd_soc_dai_link_component  (one per array slot)
                                 │
                                 ▼  ch_maps[m] = { cpu, codec, ch_mask }
                      ch_maps[0..max(C,K)-1]
                      ┌──────────────────────────────────┐
                      │ .cpu = i   .codec = j   .ch_mask │
                      └──────────────────────────────────┘
                        pairs cpus[i] with codecs[j]
```

## SUMMARY

A machine driver describes each audio path as one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and places the links in an array on its [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). Every link names its endpoints by string. The [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer addresses an array of [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) CPU [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) records, the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer addresses [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) codec records, and the [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer addresses [`num_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) platform records. Each record carries a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that selects a registered component and a [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that selects the DAI within it. The [`SND_SOC_DAILINK_DEFS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L928) macro and the [`COMP_CPU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L935), [`COMP_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L936), [`COMP_PLATFORM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L937), and [`DAILINK_COMP_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L933) helpers exist to write those arrays without boilerplate, and [`SND_SOC_DAILINK_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L922) wires the three arrays and their sizes into the link in one line.

The card converts the static array into runtime state. [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) iterates the array and calls [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) for each link, which runs [`soc_dai_link_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949), allocates one [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498), and resolves each [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) into a [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) through [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917). The resolved CPU and codec DAIs are stored in the runtime's [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) pointer array, reached afterward through [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197). Once resolved the link continues to govern the runtime, the [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field is applied through [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459), the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback runs from [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27), and the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook runs from [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) every time a Dynamic PCM back-end negotiates parameters.

## SPECIFICATIONS

The [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) object is a Linux kernel software construct and has no standalone hardware specification. The serial-audio format that its [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field encodes (I2S, DSP_A, DSP_B, Left-Justified, Right-Justified) is defined by the relevant interface standard. The SoundWire transport the worked example binds is described in-tree by the kernel SoundWire stream documentation.

## LINUX KERNEL

### Link and component types (soc.h)

- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the static description of one audio path; holds the CPU/codec/platform component arrays, the channel maps, the format word, the callbacks, the ops pointers, and the config bit-fields
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): one endpoint of a link, naming a component by [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and a DAI within it by [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), with an optional [`ext_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) clock-provider extension
- [`'\<struct snd_soc_dai_link_ch_map\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696): pairs one CPU DAI index to one codec DAI index, with a [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) for the channels carried between them
- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the machine-level PCM function pointer struct (`startup`, `hw_params`, `prepare`, `trigger`, `hw_free`, `shutdown`) the link points at through [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<struct snd_soc_compr_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L632): the compressed-audio variant of the machine ops, reached through [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the runtime object one link resolves into; keeps the back pointer to its [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and the resolved [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array
- [`'\<enum snd_soc_dpcm_trigger\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58): the per-link DPCM trigger order ([`SND_SOC_DPCM_TRIGGER_PRE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58), [`SND_SOC_DPCM_TRIGGER_POST`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58)) held in the link's [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array
- [`'\<enum snd_soc_trigger_order\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601): the link-versus-component-versus-DAI trigger sequence held in [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)

### Declaration macros (soc.h)

- [`'\<SND_SOC_DAILINK_DEFS\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L928): declare the three `name##_cpus`, `name##_codecs`, `name##_platforms` component arrays at once
- [`'\<SND_SOC_DAILINK_DEF\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L925): declare a single named [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) array
- [`'\<COMP_CPU\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L935): one CPU endpoint initializer setting only `.dai_name`
- [`'\<COMP_CODEC\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L936): one codec endpoint initializer setting `.name` and `.dai_name`
- [`'\<COMP_PLATFORM\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L937): one platform endpoint initializer setting `.name`
- [`'\<DAILINK_COMP_ARRAY\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L933): pass-through wrapper that lets a `COMP_*` list become an array initializer
- [`'\<SND_SOC_DAILINK_REG\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L922): set [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`num_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the declared arrays in one line, filling the platform slot with [`null_dailink_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L59) when omitted

### Array iterators and accessors (soc.h)

- [`'\<for_each_link_cpus\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L847) / [`'\<for_each_link_codecs\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L835) / [`'\<for_each_link_platforms\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L841): iterate one component array, calling the matching accessor for each index
- [`'\<for_each_link_ch_maps\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L853): iterate the [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array
- [`'\<snd_soc_link_to_cpu\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L821) / [`'\<snd_soc_link_to_codec\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L825) / [`'\<snd_soc_link_to_platform\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L830): return the nth entry of the matching array
- [`'\<snd_soc_rtd_to_cpu\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) / [`'\<snd_soc_rtd_to_codec\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197): index the resolved [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array of the runtime, codecs offset past the CPU DAIs

### Resolution and lifecycle (soc-core.c)

- [`'\<snd_soc_add_pcm_runtimes\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269): loop over the link array, resolving each into a runtime
- [`'\<snd_soc_add_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175): resolve one link, allocate the runtime, and fill its [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array from the component arrays
- [`'\<soc_dai_link_sanity_check\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949): validate each [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), returning `-EPROBE_DEFER` when a named component is not yet registered
- [`'\<soc_new_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498): allocate the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) sized for `num_cpus + num_codecs + num_platforms` components and link it to its [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)
- [`'\<snd_soc_find_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917): walk all registered components and return the [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) names
- [`'\<snd_soc_is_matching_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273): test whether a DAI's name matches the [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) in a component record
- [`'\<snd_soc_runtime_set_dai_fmt\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459): push the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) onto every CPU and codec DAI of the runtime, flipping the clock-provider role for the CPU end

### Link operation wrappers (soc-link.c)

- [`'\<snd_soc_link_init\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27): run the link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback if present
- [`'\<snd_soc_link_be_hw_params_fixup\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43): run the link's [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback if present, called from the DPCM back-end hw_params path

### sof_sdw worked example (intel/boards/sof_sdw.c, sdw_utils/soc_sdw_utils.c)

- [`'\<create_sdw_dailink\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876): build the CPU/codec/platform arrays and the channel maps for one SoundWire link from the discovered endpoints
- [`'\<asoc_sdw_init_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293): populate one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the arrays, setting [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`playback_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`capture_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) the SoundWire links share for their machine-level startup/shutdown
- [`'\<asoc_sdw_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918): the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback the links use, which adds the codec controls and widgets once per resolved codec DAI
- [`'\<sof_pcm_dai_link_fixup\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719): the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) the SOF platform installs on every back-end link, matching the negotiated parameters to the loaded topology

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface families a link binds at each end
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver guide, where the DAI link array is declared and registered on the card
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) front-end and [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) back-end link flags split a path
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model the link ties together
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the sof_sdw links drive

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A DAI link is data, so its interface is the field set a machine driver fills in and the small set of core functions that read those fields. A machine driver writes the static fields and the core never writes them back. The callbacks ([`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)) and the ops pointers ([`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`compr_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)) are optional and run only when set, each behind a wrapper in [`soc-link.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c) that treats an absent callback as success. The config bit-fields are read at bind and at stream time to decide how the path is built and driven.

| Field | Type | Read by | Effect |
|-------|------|---------|--------|
| `cpus` / `num_cpus` | component array | [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) | resolve the CPU-side DAIs |
| `codecs` / `num_codecs` | component array | [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) | resolve the codec-side DAIs |
| `platforms` / `num_platforms` | component array | [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) | attach the PCM/DMA component |
| `ch_maps` | ch_map array | [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) and DPCM | pair each CPU DAI with its codec DAI |
| `dai_fmt` | format word | [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459) | program the serial format on both ends |
| `init` / `exit` | callback | [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) | machine-specific setup and teardown |
| `be_hw_params_fixup` | callback | [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) | rewrite back-end params for FE/BE sync |
| `ops` | `struct snd_soc_ops *` | the PCM core | machine PCM callbacks |
| `compr_ops` | `struct snd_soc_compr_ops *` | the compress core | machine compressed-audio callbacks |
| `nonatomic` | bit-field | the PCM core | run ops in process context |
| `no_pcm` | bit-field | the PCM core | this link is a DPCM back-end |
| `dynamic` | bit-field | the PCM core | this link is a DPCM front-end |
| `playback_only` / `capture_only` | bit-field | the PCM core | restrict to one direction |
| `ignore_suspend` | bit-field | the suspend path | keep the DAI active over suspend |
| `ignore` | bit-field | [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) | skip binding this link |
| `symmetric_rate` / `symmetric_channels` / `symmetric_sample_bits` | bit-field | the PCM core | force later streams to match the first |
| `dpcm_merged_format` / `dpcm_merged_chan` / `dpcm_merged_rate` | bit-field | the DPCM core | merge FE and BE constraints |

## DETAILS

### The link binds three component arrays

A DAI link names everything by string and is meant to be filled in by a machine driver. The CPU, codec, and platform ends are three separate arrays of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), each paired with a count, and the [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array pairs entries of the first two:

```c
/* include/sound/soc.h:702 */
struct snd_soc_dai_link {
	/* config - must be set by machine driver */
	const char *name;			/* Codec name */
	const char *stream_name;		/* Stream name */
	...
	struct snd_soc_dai_link_component *cpus;
	unsigned int num_cpus;
	...
	struct snd_soc_dai_link_component *codecs;
	unsigned int num_codecs;

	/* num_ch_maps = max(num_cpu, num_codecs) */
	struct snd_soc_dai_link_ch_map *ch_maps;
	...
	struct snd_soc_dai_link_component *platforms;
	unsigned int num_platforms;

	int id;	/* optional ID for machine driver link identification */
	...
	unsigned int dai_fmt;           /* format to set on init */

	enum snd_soc_dpcm_trigger trigger[2]; /* trigger type for DPCM */

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
	...
	/* Mark this pcm with non atomic ops */
	unsigned int nonatomic:1;

	/* For unidirectional dai links */
	unsigned int playback_only:1;
	unsigned int capture_only:1;

	/* Keep DAI active over suspend */
	unsigned int ignore_suspend:1;

	/* Symmetry requirements */
	unsigned int symmetric_rate:1;
	unsigned int symmetric_channels:1;
	unsigned int symmetric_sample_bits:1;

	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;

	/* This DAI link can route to other DAI links at runtime (Frontend)*/
	unsigned int dynamic:1;

	/* DPCM used FE & BE merged format */
	unsigned int dpcm_merged_format:1;
	/* DPCM used FE & BE merged channel */
	unsigned int dpcm_merged_chan:1;
	/* DPCM used FE & BE merged rate */
	unsigned int dpcm_merged_rate:1;

	/* pmdown_time is ignored at stop */
	unsigned int ignore_pmdown_time:1;

	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int ignore:1;
	...
};
```

Each endpoint is a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642). On an x86-64 ACPI system a component is selected by the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) strings, and [`ext_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) carries an optional per-end clock-provider extension applied alongside the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702):

```c
/* include/sound/soc.h:642 */
struct snd_soc_dai_link_component {
	const char *name;
	struct device_node *of_node;
	const char *dai_name;
	const struct of_phandle_args *dai_args;

	/*
	 * Extra format = SND_SOC_DAIFMT_Bx_Fx
	 *
	 * [Note] it is Bx_Fx base, not CBx_CFx
	 *
	 * It will be used with dai_link->dai_fmt
	 * see
	 *	snd_soc_runtime_set_dai_fmt()
	 */
	unsigned int ext_fmt;
};
```

The [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array exists because a link with several CPU DAIs and several codec DAIs has to record which CPU feeds which codec. Each [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) is one such pairing:

```c
/* include/sound/soc.h:696 */
struct snd_soc_dai_link_ch_map {
	unsigned int cpu;
	unsigned int codec;
	unsigned int ch_mask;
};
```

### Declaration macros remove the array boilerplate

Writing the three component arrays by hand is repetitive, so the header supplies a macro family. [`SND_SOC_DAILINK_DEF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L925) declares one named array of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), [`SND_SOC_DAILINK_DEFS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L928) declares the three at once with `_cpus`, `_codecs`, and `_platforms` suffixes, and [`DAILINK_COMP_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L933) passes a `COMP_*` list through as the array body:

```c
/* include/sound/soc.h:925 */
#define SND_SOC_DAILINK_DEF(name, def...)		\
	static struct snd_soc_dai_link_component name[]	= { def }

#define SND_SOC_DAILINK_DEFS(name, cpu, codec, platform...)	\
	SND_SOC_DAILINK_DEF(name##_cpus, cpu);			\
	SND_SOC_DAILINK_DEF(name##_codecs, codec);		\
	SND_SOC_DAILINK_DEF(name##_platforms, platform)

#define DAILINK_COMP_ARRAY(param...)	param
#define COMP_EMPTY()			{ }
#define COMP_CPU(_dai)			{ .dai_name = _dai, }
#define COMP_CODEC(_name, _dai)		{ .name = _name, .dai_name = _dai, }
#define COMP_PLATFORM(_name)		{ .name = _name }
```

[`COMP_CPU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L935) sets only [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) because a CPU DAI is matched by DAI name alone on most systems, while [`COMP_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L936) sets both [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) because a codec must name its component. Once the arrays exist, [`SND_SOC_DAILINK_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L922) wires them into the link, counting each with `ARRAY_SIZE` and substituting the empty [`null_dailink_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L59) when a link omits its platform:

```c
/* include/sound/soc.h:912 */
#define SND_SOC_DAILINK_REG1(name)	 SND_SOC_DAILINK_REG3(name##_cpus, name##_codecs, name##_platforms)
#define SND_SOC_DAILINK_REG2(cpu, codec) SND_SOC_DAILINK_REG3(cpu, codec, null_dailink_component)
#define SND_SOC_DAILINK_REG3(cpu, codec, platform)	\
	.cpus		= cpu,				\
	.num_cpus	= ARRAY_SIZE(cpu),		\
	.codecs		= codec,			\
	.num_codecs	= ARRAY_SIZE(codec),		\
	.platforms	= platform,			\
	.num_platforms	= ARRAY_SIZE(platform)

#define SND_SOC_DAILINK_REG(...) \
	CONCATENATE(SND_SOC_DAILINK_REG, COUNT_ARGS(__VA_ARGS__))(__VA_ARGS__)
```

The worked sample in the header writes a single CPU/codec/platform link by declaring the arrays with [`SND_SOC_DAILINK_DEFS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L928) and then placing [`SND_SOC_DAILINK_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L922) inside the link initializer:

```c
/* include/sound/soc.h:859 (sample from the header comment) */
 * SND_SOC_DAILINK_DEFS(test,
 *	DAILINK_COMP_ARRAY(COMP_CPU("cpu_dai")),
 *	DAILINK_COMP_ARRAY(COMP_CODEC("codec", "codec_dai")),
 *	DAILINK_COMP_ARRAY(COMP_PLATFORM("platform")));
 *
 * struct snd_soc_dai_link link = {
 *	...
 *	SND_SOC_DAILINK_REG(test),
 * };
```

### Resolution turns one link into one runtime

The card processes the link array through [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269), which calls [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) once per link after compensating the channel map:

```c
/* sound/soc/soc-core.c:1269 */
int snd_soc_add_pcm_runtimes(struct snd_soc_card *card,
			     struct snd_soc_dai_link *dai_link,
			     int num_dai_link)
{
	for (int i = 0; i < num_dai_link; i++) {
		int ret;

		ret = snd_soc_compensate_channel_connection_map(card, dai_link + i);
		if (ret < 0)
			return ret;

		ret = snd_soc_add_pcm_runtime(card, dai_link + i);
		if (ret < 0)
			return ret;
	}

	return 0;
}
```

[`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) is where a link becomes a runtime. It honors the [`ignore`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) flag, runs [`soc_dai_link_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949), allocates the runtime with [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498), then walks each component array with the [`for_each_link_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L847), [`for_each_link_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L835), and [`for_each_link_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L841) iterators, storing each resolved DAI through [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197):

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
	...
	if (dai_link->ignore)
		return 0;

	dev_dbg(card->dev, "ASoC: binding %s\n", dai_link->name);

	ret = soc_dai_link_sanity_check(card, dai_link);
	if (ret < 0)
		return ret;

	rtd = soc_new_pcm_runtime(card, dai_link);
	if (!rtd)
		return -ENOMEM;

	for_each_link_cpus(dai_link, i, cpu) {
		snd_soc_rtd_to_cpu(rtd, i) = snd_soc_find_dai(cpu);
		if (!snd_soc_rtd_to_cpu(rtd, i)) {
			dev_info(card->dev, "ASoC: CPU DAI %s not registered\n",
				 cpu->dai_name);
			goto _err_defer;
		}
		snd_soc_rtd_add_component(rtd, snd_soc_rtd_to_cpu(rtd, i)->component);
	}

	/* Find CODEC from registered CODECs */
	for_each_link_codecs(dai_link, i, codec) {
		snd_soc_rtd_to_codec(rtd, i) = snd_soc_find_dai(codec);
		if (!snd_soc_rtd_to_codec(rtd, i)) {
			dev_info(card->dev, "ASoC: CODEC DAI %s not registered\n",
				 codec->dai_name);
			goto _err_defer;
		}

		snd_soc_rtd_add_component(rtd, snd_soc_rtd_to_codec(rtd, i)->component);
	}

	/* Find PLATFORM from registered PLATFORMs */
	for_each_link_platforms(dai_link, i, platform) {
		for_each_component(component) {
			if (!snd_soc_is_matching_component(platform, component))
				continue;
			...
			snd_soc_rtd_add_component(rtd, component);
		}
	}
	...
_err_defer:
	snd_soc_remove_pcm_runtime(card, rtd);
	return -EPROBE_DEFER;
}
```

The CPU and codec slots are looked up by exact DAI, the platform slot matches every registered component whose name fits the platform record, and a missing CPU or codec DAI returns `-EPROBE_DEFER` so the bind retries once the providing driver loads. The runtime that holds the result keeps a back pointer to the link and a flat [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) pointer array laid out as the CPU DAIs followed by the codec DAIs, which is why [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) offsets its index past the CPU DAIs while [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) does not:

```c
/* include/sound/soc.h:1196 */
#define snd_soc_rtd_to_cpu(rtd, n)   (rtd)->dais[n]
#define snd_soc_rtd_to_codec(rtd, n) (rtd)->dais[n + (rtd)->dai_link->num_cpus]
```

That offset falls out of the layout the binder builds, resolving the link's cpus and codecs name arrays through one lookup into a single dais[] that runs the CPU DAIs first and starts the codec DAIs at index num_cpus:

```
    Resolution: link arrays become one flat dais[] (CPUs then codecs)
    ────────────────────────────────────────────────────────────────

    struct snd_soc_dai_link        snd_soc_find_dai() resolves each entry
    ┌─────────────────────────┐
    │ cpus[0 .. num_cpus-1]   │ ──────────────┐
    │ codecs[0 .. num_codecs-1│ ──────┐       │
    └─────────────────────────┘       │       │
                                      ▼       ▼
    struct snd_soc_pcm_runtime    dais[]  (num_cpus + num_codecs slots)
    ┌──────────────────────┐      ┌────────┬────────┬────────┬────────┐
    │ dai_link  (back ptr) │      │ dais[0]│  ...   │ dais[k]│  ...   │
    │ dais ────────────────┼────▶ │ CPU DAI│ CPU DAI│ codec  │ codec  │
    └──────────────────────┘      └────────┴────────┴────────┴────────┘
                                   k = num_cpus (first codec slot)

    snd_soc_rtd_to_cpu(rtd, n)   = dais[n]
    snd_soc_rtd_to_codec(rtd, n) = dais[n + num_cpus]
```

### The component arrays are reached through to_cpu, to_codec, and to_platform accessors

The iterators the resolution path uses are built on three one-line accessors. [`snd_soc_link_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L821), [`snd_soc_link_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L825), and [`snd_soc_link_to_platform()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L830) each return the address of the nth entry of the matching [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) array on the link, the same [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointers a machine driver filled in:

```c
/* include/sound/soc.h:820 */
static inline struct snd_soc_dai_link_component*
snd_soc_link_to_cpu(struct snd_soc_dai_link *link, int n) {
	return &(link)->cpus[n];
}

static inline struct snd_soc_dai_link_component*
snd_soc_link_to_codec(struct snd_soc_dai_link *link, int n) {
	return &(link)->codecs[n];
}

static inline struct snd_soc_dai_link_component*
snd_soc_link_to_platform(struct snd_soc_dai_link *link, int n) {
	return &(link)->platforms[n];
}
```

The [`for_each_link_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L847), [`for_each_link_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L835), and [`for_each_link_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L841) iterators just call the matching accessor for each index up to the array's count. The channel maps have their own iterator, [`for_each_link_ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L853), which walks the [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array directly and bounds the loop with [`snd_soc_link_num_ch_map()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L815), the `max(num_cpus, num_codecs)` count the link's comment names as `num_ch_maps`:

```c
/* include/sound/soc.h:853 */
#define for_each_link_ch_maps(link, i, ch_map)			\
	for ((i) = 0;						\
	     ((i) < snd_soc_link_num_ch_map(link) &&		\
		      ((ch_map) = link->ch_maps + i));		\
	     (i)++)
```

### Each component name resolves through snd_soc_find_dai

The per-entry lookup is [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917). It walks every registered component, and for one whose name fits the record it walks that component's DAIs and returns the first whose name matches:

```c
/* sound/soc/soc-core.c:917 */
struct snd_soc_dai *snd_soc_find_dai(
	const struct snd_soc_dai_link_component *dlc)
{
	struct snd_soc_component *component;
	struct snd_soc_dai *dai;

	lockdep_assert_held(&client_mutex);

	/* Find CPU DAI from registered DAIs */
	for_each_component(component)
		if (snd_soc_is_matching_component(dlc, component))
			for_each_component_dais(component, dai)
				if (snd_soc_is_matching_dai(dlc, dai))
					return dai;

	return NULL;
}
```

[`snd_soc_is_matching_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273) compares the record's [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) against the DAI driver name, the runtime DAI name, and the component name in turn, and treats a record with no [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) as a wildcard match so a single-DAI component binds without naming its DAI:

```c
/* sound/soc/soc-core.c:273 */
static int snd_soc_is_matching_dai(const struct snd_soc_dai_link_component *dlc,
				   struct snd_soc_dai *dai)
{
	if (!dlc)
		return 0;

	if (dlc->dai_args)
		return snd_soc_is_match_dai_args(dai->driver->dai_args, dlc->dai_args);

	if (!dlc->dai_name)
		return 1;

	/* see snd_soc_dai_name_get() */

	if (dai->driver->name &&
	    strcmp(dlc->dai_name, dai->driver->name) == 0)
		return 1;

	if (strcmp(dlc->dai_name, dai->name) == 0)
		return 1;

	if (dai->component->name &&
	    strcmp(dlc->dai_name, dai->component->name) == 0)
		return 1;

	return 0;
}
```

### Sanity check defers until every named component exists

Before allocating anything, [`soc_dai_link_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949) validates each [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) of the link. A codec must name a component and a DAI, a CPU may name a DAI alone, and any named-but-not-yet-registered component returns `-EPROBE_DEFER` so card registration retries later:

```c
/* sound/soc/soc-core.c:949 */
static int soc_dai_link_sanity_check(struct snd_soc_card *card,
				     struct snd_soc_dai_link *link)
{
	int i;
	struct snd_soc_dai_link_component *dlc;

	/* Codec check */
	for_each_link_codecs(link, i, dlc) {
		...
		/* Codec DAI name must be specified */
		if (snd_soc_dlc_dai_is_empty(dlc))
			goto dai_empty;

		/*
		 * Defer card registration if codec component is not added to
		 * component list.
		 */
		if (!soc_find_component(dlc))
			goto component_not_found;
	}
	...
component_not_found:
	dev_dbg(card->dev, "ASoC: Component %s not found for link %s\n", dlc->name, link->name);
	return -EPROBE_DEFER;
	...
}
```

### dai_fmt applies to both ends from the link

After resolution the link's [`dai_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is pushed onto every DAI of the runtime by [`snd_soc_runtime_set_dai_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1459). It calls [`snd_soc_dai_set_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) for each codec DAI with the format ORed with that codec record's [`ext_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), then flips the clock-provider role and applies the result to each CPU DAI, because the link states the format from the codec's point of view:

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

One format word reaches both ends, each side ORing its own ext_fmt, the codec DAIs taking it as written and the CPU DAIs taking it with the clock-provider role flipped because the link spells it from the codec's side:

```
    snd_soc_runtime_set_dai_fmt: one word, two ends, CPU flipped
    ───────────────────────────────────────────────────────────
    (the link states dai_fmt from the codec's point of view)

                          dai_link.dai_fmt
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
    each codec DAI                   each CPU DAI
    ┌──────────────────────────┐     ┌──────────────────────────┐
    │set_fmt( dai_fmt          │     │set_fmt( flipped(dai_fmt) │
    │         OR               │     │         OR               │
    │         codecs[i].       │     │         cpus[i].         │
    │         ext_fmt )        │     │         ext_fmt )        │
    └──────────────────────────┘     └──────────────────────────┘
      format word as written         clock-provider role flipped by
                                     clock_provider_flipped()
```

### Link callbacks run behind thin wrappers

The link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback runs once when the runtime is brought up, reached through [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27), which calls the op only if the machine set one and passes the result through [`soc_link_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L13):

```c
/* sound/soc/soc-link.c:27 */
int snd_soc_link_init(struct snd_soc_pcm_runtime *rtd)
{
	int ret = 0;

	if (rtd->dai_link->init)
		ret = rtd->dai_link->init(rtd);

	return soc_link_ret(rtd, ret);
}
```

The [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback follows the same shape in [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43). The DPCM back-end hw_params path calls it so a back-end link can rewrite the negotiated parameters to whatever its hardware or topology fixes them at. The wrapper reads the optional [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field off the link, calls it only when the machine set one, and passes the result through [`soc_link_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L13) exactly as [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) does:

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

The machine-level [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer is a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), the machine's own copy of the PCM callback set the core also keeps on the DAI and the component, run in addition to those at stream time:

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

### The DPCM bit-fields split a path into front-end and back-end

Dynamic PCM is selected by two of the link bit-fields. A front-end link sets [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and according to its comment "This DAI link can route to other DAI links at runtime (Frontend)", so it carries the user-visible PCM and routes to back-ends chosen at runtime through DAPM. A back-end link sets [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), whose comment reads "Do not create a PCM for this DAI link (Backend link)", so it has no PCM device of its own and is driven by whichever front-end routes to it. The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array of [`enum snd_soc_dpcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58) values sets whether each back-end triggers before or after the front-end, and the [`dpcm_merged_format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`dpcm_merged_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`dpcm_merged_rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bits decide whether the front-end inherits the back-end's constraints during parameter negotiation. The [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit moves the PCM ops out of atomic context, which a transport whose operations sleep must request.

```
    Two link bits select the DPCM role of a path
    ─────────────────────────────────────────────

    dynamic  no_pcm   role of this dai_link
    ───────  ──────   ─────────────────────────────────────────────
       0       0      normal link (its own PCM, fixed CPU↔codec path)
       1       0      Front-End: owns the user PCM, routes to BEs
                      chosen at runtime through DAPM
       0       1      Back-End: no PCM device, driven by whichever
                      Front-End routes to it
    ───────────────────────────────────────────────────────────────

       userspace PCM
            │
            ▼
    ┌────────────────┐   DAPM route   ┌────────────────┐
    │ Front-End link │ ─────────────▶ │ Back-End link  │
    │ dynamic = 1    │  (runtime)     │ no_pcm = 1     │
    └────────────────┘                └───────┬────────┘
                                              ▼
                                       codec / transport DAI
```

### The trigger-order enum sequences link, component, and DAI

The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array of [`enum snd_soc_dpcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58) decides whether a back-end fires before or after its front-end, but a separate pair of fields, [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), decides the order in which the three layers of one link are triggered. They hold an [`enum snd_soc_trigger_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601), whose comment column spells out the start and stop sequences each value selects:

```c
/* include/sound/soc.h:601 */
enum snd_soc_trigger_order {
					/* start			stop		     */
	SND_SOC_TRIGGER_ORDER_DEFAULT	= 0,	/* Link->Component->DAI		DAI->Component->Link */
	SND_SOC_TRIGGER_ORDER_LDC,		/* Link->DAI->Component		Component->DAI->Link */

	SND_SOC_TRIGGER_ORDER_MAX,
};
```

[`SND_SOC_TRIGGER_ORDER_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L603) triggers the link first, then the component, then the DAI on start and unwinds in reverse on stop, the order almost every machine wants. [`SND_SOC_TRIGGER_ORDER_LDC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L604) moves the DAI ahead of the component, which a machine sets on its link only when its hardware needs the DAI started before the component that feeds it.

```
    enum snd_soc_trigger_order: layer sequence per link
    ───────────────────────────────────────────────────
    (stop unwinds the start order in reverse)

    SND_SOC_TRIGGER_ORDER_DEFAULT
       start:  Link ─▶ Component ─▶ DAI
       stop:    DAI ─▶ Component ─▶ Link        (exact reverse)

    SND_SOC_TRIGGER_ORDER_LDC      (DAI ahead of Component)
       start:  Link ─▶ DAI ─▶ Component
       stop:    Component ─▶ DAI ─▶ Link        (exact reverse)

    held in dai_link.trigger_start / dai_link.trigger_stop
```

### Worked example: dynamically created links in sof_sdw

The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine driver does not declare a static link array. It discovers the SoundWire topology at probe and builds one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) per stream direction in [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876). It takes a `**dai_links` write cursor and loops over the playback and capture streams, and for each direction it sizes the arrays from the discovered endpoints, the CPU count from the populated SoundWire link bits and the codec count from the number of devices on that stream:

```c
/* sound/soc/intel/boards/sof_sdw.c:876 */
static int create_sdw_dailink(struct snd_soc_card *card,
			      struct asoc_sdw_dailink *sof_dai,
			      struct snd_soc_dai_link **dai_links,
			      int *be_id, struct snd_soc_codec_conf **codec_conf)
{
	...
	for_each_pcm_streams(stream) {
		...
		struct snd_soc_dai_link_ch_map *codec_maps;
		struct snd_soc_dai_link_component *codecs;
		struct snd_soc_dai_link_component *cpus;
		struct snd_soc_dai_link_component *platform;
		int num_cpus = hweight32(sof_dai->link_mask[stream]);
		int num_codecs = sof_dai->num_devs[stream];
		...
		cpus = devm_kcalloc(dev, num_cpus, sizeof(*cpus), GFP_KERNEL);
		...
		codecs = devm_kcalloc(dev, num_codecs, sizeof(*codecs), GFP_KERNEL);
		...
		platform = devm_kzalloc(dev, sizeof(*platform), GFP_KERNEL);
		...
		codec_maps = devm_kcalloc(dev, num_codecs, sizeof(*codec_maps), GFP_KERNEL);
		...
	}

	return 0;
}
```

For each direction it allocates the CPU, codec, and platform [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) arrays and a [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) array sized from the discovered endpoints, fills each codec entry and channel-map pairing from the endpoint list, then calls [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293):

```c
/* sound/soc/intel/boards/sof_sdw.c:963 */
		list_for_each_entry(sof_end, &sof_dai->endpoints, list) {
			if (!sof_end->dai_info->direction[stream])
				continue;

			if (cur_link != sof_end->link_mask) {
				int link_num = ffs(sof_end->link_mask) - 1;
				int pin_num = intel_ctx->sdw_pin_index[link_num]++;

				cur_link = sof_end->link_mask;

				cpus[i].dai_name = devm_kasprintf(dev, GFP_KERNEL,
								  "SDW%d Pin%d",
								  link_num, pin_num);
				if (!cpus[i].dai_name)
					return -ENOMEM;
				i++;
			}

			codec_maps[j].cpu = i - 1;
			codec_maps[j].codec = j;

			codecs[j].name = sof_end->codec_name;
			codecs[j].dai_name = sof_end->dai_info->dai_name;
			...
			j++;
		}

		WARN_ON(i != num_cpus || j != num_codecs);

		playback = (stream == SNDRV_PCM_STREAM_PLAYBACK);
		capture = (stream == SNDRV_PCM_STREAM_CAPTURE);

		asoc_sdw_init_dai_link(dev, *dai_links, be_id, name, playback, capture,
				       cpus, num_cpus, platform, 1, codecs, num_codecs,
				       1, asoc_sdw_rtd_init, &sdw_ops);

		/*
		 * SoundWire DAILINKs use 'stream' functions and Bank Switch operations
		 * based on wait_for_completion(), tag them as 'nonatomic'.
		 */
		(*dai_links)->nonatomic = true;
		(*dai_links)->ch_maps = codec_maps;
```

The CPU [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) is a generated `"SDW<n> Pin<m>"` string naming the SoundWire master DAI, each codec entry takes the codec component name and DAI name straight from the discovered endpoint, and each [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) pairs the codec index with the CPU index it shares a SoundWire link with. The last two statements set [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) on the link, because SoundWire bank switching waits on a completion and cannot run atomic, and attach the built [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array.

[`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) writes the fields the resolution path and the PCM core read. It sets the name and stream name, the component-array pointers and counts, the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) back-end flag, the [`playback_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`capture_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) direction flags derived from the stream, the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback, and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1293 */
void asoc_sdw_init_dai_link(struct device *dev, struct snd_soc_dai_link *dai_links,
			    int *be_id, char *name, int playback, int capture,
			    struct snd_soc_dai_link_component *cpus, int cpus_num,
			    struct snd_soc_dai_link_component *platform_component,
			    int num_platforms, struct snd_soc_dai_link_component *codecs,
			    int codecs_num, int no_pcm,
			    int (*init)(struct snd_soc_pcm_runtime *rtd),
			    const struct snd_soc_ops *ops)
{
	dev_dbg(dev, "create dai link %s, id %d\n", name, *be_id);
	dai_links->id = (*be_id)++;
	dai_links->name = name;
	dai_links->stream_name = name;
	dai_links->platforms = platform_component;
	dai_links->num_platforms = num_platforms;
	dai_links->no_pcm = no_pcm;
	dai_links->cpus = cpus;
	dai_links->num_cpus = cpus_num;
	dai_links->codecs = codecs;
	dai_links->num_codecs = codecs_num;
	dai_links->playback_only =  playback && !capture;
	dai_links->capture_only  = !playback &&  capture;
	dai_links->init = init;
	dai_links->ops = ops;
}
```

Every SoundWire link is a Dynamic PCM back-end ([`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is passed as 1), so it has no PCM device of its own and is fed by a SOF front-end. The [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback the links share is [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918), which runs once the link is resolved and walks the runtime's codec DAIs to add each codec's controls and DAPM widgets to the card. The shared [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865), the machine-level [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) the SoundWire links use for their startup and shutdown.

Because these are back-end links, the parameter rewrite is provided by the SOF platform rather than the machine. The SOF PCM driver installs [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) as the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) of every back-end, and [`snd_soc_link_be_hw_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L43) calls it whenever the back-end negotiates parameters, matching the stream to the loaded topology and falling back to 48 kHz stereo S16_LE when no topology entry exists:

```c
/* sound/soc/sof/pcm.c:719 */
int sof_pcm_dai_link_fixup(struct snd_soc_pcm_runtime *rtd, struct snd_pcm_hw_params *params)
{
	struct snd_interval *rate = hw_param_interval(params,
			SNDRV_PCM_HW_PARAM_RATE);
	struct snd_interval *channels = hw_param_interval(params,
						SNDRV_PCM_HW_PARAM_CHANNELS);
	struct snd_mask *fmt = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
	struct snd_soc_component *component =
		snd_soc_rtdcom_lookup(rtd, SOF_AUDIO_PCM_DRV_NAME);
	struct snd_sof_dai *dai =
		snd_sof_find_dai(component, (char *)rtd->dai_link->name);
	...
	/* no topology exists for this BE, try a common configuration */
	if (!dai) {
		dev_warn(component->dev,
			 "warning: no topology found for BE DAI %s config\n",
			 rtd->dai_link->name);

		/*  set 48k, stereo, 16bits by default */
		rate->min = 48000;
		rate->max = 48000;

		channels->min = 2;
		channels->max = 2;

		snd_mask_none(fmt);
		snd_mask_set_format(fmt, SNDRV_PCM_FORMAT_S16_LE);

		return 0;
	}

	if (pcm_ops && pcm_ops->dai_link_fixup)
		return pcm_ops->dai_link_fixup(rtd, params);

	return 0;
}
```

The fixup reaches its SOF DAI by name, looking it up with the link's own [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field. The same string the machine driver wrote into the back-end link is the lookup key the platform uses to find that link's topology configuration at stream time.
