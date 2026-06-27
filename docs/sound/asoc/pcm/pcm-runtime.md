# ASoC PCM runtime (snd_soc_pcm_runtime)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The ASoC PCM runtime is the per-DAI-link object that binds one CPU DAI side to one codec DAI side and gives the pair an ALSA PCM device. The kernel represents it with [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and the core creates exactly one of these for every [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) a machine driver declares. [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) allocates the runtime and sizes its DAI pointer array from the link, [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) resolves the named CPU and codec endpoints into runtime DAIs (CPU DAIs occupying the low slots of the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array and codec DAIs the high slots), and the resolved DAIs are read back by index with [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197). Every component the path touches is recorded in the trailing [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) flexible array, and the runtime is threaded onto the card's [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). On an x86-64 ACPI system the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine driver builds its link array through [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) and hands it to the core, which turns each link into one runtime.

```
    struct snd_soc_dai_link  (machine driver declares one per path)
    ┌────────────────────────────────────────────────────────────┐
    │  name, stream_name                                         │
    │  cpus[]   num_cpus = 1     codecs[]  num_codecs = 1        │
    │  platforms[]  num_platforms = 1                            │
    └──────────────────────────────┬─────────────────────────────┘
                                   │ soc_new_pcm_runtime()
                                   ▼
    struct snd_soc_pcm_runtime  (rtd; one per dai_link)
    ┌────────────────────────────────────────────────────────────┐
    │  card ─▶ snd_soc_card        dai_link ─▶ snd_soc_dai_link  │
    │  pcm  ─▶ snd_pcm             dpcm[2]   delayed_work        │
    │                                                            │
    │  dais ─▶ ┌────────────┬────────────┐                       │
    │          │  cpu DAI 0 │ codec DAI 0│                       │
    │          └────────────┴────────────┘                       │
    │          │── num_cpus │── num_codecs │                     │
    │                                                            │
    │  components[num_components] ─▶ ┌─────────┬──────────┐      │
    │                              │ cpu comp  │codec comp│      │
    │                              └───────────┴──────────┘      │
    └────────────────────────────────────────────────────────────┘
        snd_soc_rtd_to_cpu(rtd, 0)   = dais[0]
        snd_soc_rtd_to_codec(rtd, 0) = dais[0 + num_cpus]
```

## SUMMARY

Card bind builds the runtimes in two stages. [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) first calls [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) to loop the link array, and [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) creates one runtime per link with [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498), resolves each CPU and codec entry into a [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) through [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917), and stores each through [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) or [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) while recording its owning component with [`snd_soc_rtd_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L317). A link that names a DAI no driver has registered makes the function return `-EPROBE_DEFER`, so the card retries once the missing component appears. The second stage runs [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) on each runtime after the components have probed, which creates the ALSA PCM and marks the runtime [`initialized`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143).

One runtime holds both the binding state and the runtime devices. The [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) back pointers reach the parents, the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array holds the resolved CPU-then-codec DAIs, the [`num_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) count and [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) flexible array hold every component on the path, and the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) pointer reaches the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) created in the second stage. The [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array of two [`struct snd_soc_dpcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) records carries the Dynamic PCM front-end and back-end client lists, and the [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with its [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) hook defers the power-down by [`pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) milliseconds to suppress pops. The [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) node threads the runtime onto the card, the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) is a 0-based monotonic device number, and the [`pop_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`initialized`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) bits track the pending pop timer and the second-stage setup. [`soc_free_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L458) unwinds the runtime during card cleanup.

## SPECIFICATIONS

The [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) object is a Linux kernel software construct and has no standalone hardware specification. The ALSA PCM device it owns is the userspace interface defined by the ALSA PCM core, and the audio path it binds runs over an interface standard (I2S, SoundWire, HD-Audio) defined elsewhere.

## LINUX KERNEL

### The runtime object and its accessors (soc.h)

- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the per-DAI-link runtime, holding [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array, [`num_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)/[`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), the work fields, and the state bits
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the static link a machine driver declares, naming the CPU, codec, and platform endpoints a runtime is built from
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): one named endpoint inside a link, matched to a DAI by [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917)
- [`'\<struct snd_soc_dpcm_runtime\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88): per-direction Dynamic PCM state with the [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) lists
- [`'\<snd_soc_rtd_to_cpu\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196): index the CPU half of [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) (`dais[n]`)
- [`'\<snd_soc_rtd_to_codec\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197): index the codec half of [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) (`dais[n + num_cpus]`)
- [`'\<for_each_rtd_components\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1205): walk the [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array
- [`'\<for_each_rtd_cpu_dais\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1209) / [`'\<for_each_rtd_codec_dais\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1213): walk the CPU or codec DAIs
- [`'\<for_each_rtd_dais\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217): walk all DAIs of the runtime, CPU then codec
- [`'\<for_each_card_rtds\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1109): walk every runtime on a card through the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) node

### Allocation and free (soc-core.c)

- [`'\<soc_new_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498): register the rtd device, allocate the runtime and its [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array, assign [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and link it onto [`card->rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<soc_free_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L458): unlink from the card, flush [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), free the component PCM state, and unregister the rtd device
- [`'\<soc_release_rtd_dev\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L452): the rtd-device release callback that frees the backing memory
- [`'\<close_delayed_work\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L489): the [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) handler that dispatches to [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)
- [`'\<snd_soc_close_delayed_work\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L427): the default [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), powering the path down when [`pop_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) is set

### Binding and resolution (soc-core.c)

- [`'\<snd_soc_add_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175): build one runtime from one link, resolve its DAIs, and add its components, returning `-EPROBE_DEFER` on a missing DAI
- [`'\<snd_soc_add_pcm_runtimes\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269): loop [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) over the whole link array
- [`'\<snd_soc_remove_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1147): notify the machine driver and free one runtime
- [`'\<snd_soc_find_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917): search registered components for the DAI a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) names
- [`'\<snd_soc_rtd_add_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L317): append a component to [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), skipping duplicates
- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): the card-bind sequence that creates every runtime then initializes each one

### Second-stage init and PCM creation

- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): run machine init, set the DAI format, create the PCM, and set [`initialized`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)
- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): create the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), store it in [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and install the PCM op set
- [`'\<snd_soc_pcm_dai_new\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571): run each DAI's [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op over the new PCM
- [`'\<snd_soc_pcm_component_free\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050): destruct each component's PCM during teardown

### x86-64 SoundWire machine example (sdw_utils, intel/boards)

- [`'\<asoc_sdw_init_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293): fill one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with its CPU, codec, and platform components and its [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) flag
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): allocate the three [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) entries and call [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model the runtime ties together
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and the DAI-link array each runtime is built from
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component that supplies the PCM and DMA the runtime drives
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) front-end and back-end runtimes connect
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream model the sof_sdw links route over

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

Code reaches a runtime's DAIs two ways, by index and by iteration. [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) compute one slot in the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array, while [`for_each_rtd_cpu_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1209), [`for_each_rtd_codec_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1213), [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217), and [`for_each_rtd_components()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1205) walk a whole set. A single-codec, single-CPU SoundWire link uses index 0 on both halves.

### snd_soc_rtd_to_cpu and snd_soc_rtd_to_codec

The two accessors encode the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) layout: [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) returns `dais[n]` and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) returns `dais[n + num_cpus]`, so the codec index begins past the last CPU DAI:

```c
/* include/sound/soc.h:1196 */
#define snd_soc_rtd_to_cpu(rtd, n)   (rtd)->dais[n]
#define snd_soc_rtd_to_codec(rtd, n) (rtd)->dais[n + (rtd)->dai_link->num_cpus]
```

### for_each_rtd_cpu_dais, for_each_rtd_codec_dais, for_each_rtd_components

The iterators bound the loop by the count the link carries and dereference an accessor each step. [`for_each_rtd_cpu_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1209) and [`for_each_rtd_codec_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1213) stop at [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`for_each_rtd_components()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1205) stops at [`num_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and also ends the loop on a NULL slot:

```c
/* include/sound/soc.h:1205 */
#define for_each_rtd_components(rtd, i, component)			\
	for ((i) = 0, component = NULL;					\
	     ((i) < rtd->num_components) && ((component) = rtd->components[i]);\
	     (i)++)
#define for_each_rtd_cpu_dais(rtd, i, dai)				\
	for ((i) = 0;							\
	     ((i) < rtd->dai_link->num_cpus) && ((dai) = snd_soc_rtd_to_cpu(rtd, i)); \
	     (i)++)
#define for_each_rtd_codec_dais(rtd, i, dai)				\
	for ((i) = 0;							\
	     ((i) < rtd->dai_link->num_codecs) && ((dai) = snd_soc_rtd_to_codec(rtd, i)); \
	     (i)++)
```

## DETAILS

### The runtime object

[`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) is allocated once per DAI link and carries everything the core needs to drive that link. The [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) pointers reach the parents, [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) reaches the combined CPU-then-codec DAI array, [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) reaches the ALSA device built in the second stage, and the [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) flexible array (counted by [`num_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)) reaches every component on the path:

```c
/* include/sound/soc.h:1143 */
struct snd_soc_pcm_runtime {
	struct device *dev;
	struct snd_soc_card *card;
	struct snd_soc_dai_link *dai_link;
	struct snd_pcm_ops ops;

	unsigned int c2c_params_select; /* currently selected c2c_param for dai link */

	/* Dynamic PCM BE runtime data */
	struct snd_soc_dpcm_runtime dpcm[SNDRV_PCM_STREAM_LAST + 1];
	struct snd_soc_dapm_widget *c2c_widget[SNDRV_PCM_STREAM_LAST + 1];

	long pmdown_time;

	/* runtime devices */
	struct snd_pcm *pcm;
	struct snd_compr *compr;

	/*
	 * dais = cpu_dai + codec_dai
	 * see
	 *	soc_new_pcm_runtime()
	 *	snd_soc_rtd_to_cpu()
	 *	snd_soc_rtd_to_codec()
	 */
	struct snd_soc_dai **dais;

	struct delayed_work delayed_work;
	void (*close_delayed_work_func)(struct snd_soc_pcm_runtime *rtd);
#ifdef CONFIG_DEBUG_FS
	struct dentry *debugfs_dpcm_root;
#endif

	unsigned int id; /* 0-based and monotonic increasing */
	struct list_head list; /* rtd list of the soc card */

	/* function mark */
	struct snd_pcm_substream *mark_startup;
	struct snd_pcm_substream *mark_hw_params;
	struct snd_pcm_substream *mark_trigger;
	struct snd_compr_stream  *mark_compr_startup;

	/* bit field */
	unsigned int pop_wait:1;
	unsigned int fe_compr:1; /* for Dynamic PCM */
	unsigned int initialized:1;

	/* CPU/Codec/Platform */
	int num_components;
	struct snd_soc_component *components[] __counted_by(num_components);
};
```

According to the leading comment, the struct is the "SoC machine DAI configuration, glues a codec and cpu DAI together", so one runtime joins one CPU side to one codec side. The comment on [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) records the layout as `dais = cpu_dai + codec_dai` and names [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) as the accessors that read it. The [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) fields are the per-substream rollback marks the soc-pcm teardown path checks.

The [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) member is two [`struct snd_soc_dpcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) records, one per stream direction, each carrying the front-end and back-end client lists Dynamic PCM walks to bridge a front-end runtime to its back-end runtimes:

```c
/* include/sound/soc-dpcm.h:88 */
struct snd_soc_dpcm_runtime {
	struct list_head be_clients;
	struct list_head fe_clients;

	int users;
	struct snd_pcm_hw_params hw_params;

	/* state and update */
	enum snd_soc_dpcm_update runtime_update;
	enum snd_soc_dpcm_state state;

	int trigger_pending; /* trigger cmd + 1 if pending, 0 if not */

	int be_start; /* refcount protected by BE stream pcm lock */
	int be_pause; /* refcount protected by BE stream pcm lock */
	bool fe_pause; /* used to track STOP after PAUSE */
};
```

Those two dpcm records sit inline in the runtime block, which carries the card and dai_link back pointers and points its dais field at a separately allocated CPU-then-codec array:

```
    snd_soc_pcm_runtime field layout (one block + two it points at)
    ──────────────────────────────────────────────────────────────

    struct snd_soc_pcm_runtime
    ┌───────────────────────────────────────────────────┐
    │ card ─────▶ struct snd_soc_card                   │
    │ dai_link ─▶ struct snd_soc_dai_link               │
    │ ops               (struct snd_pcm_ops)            │
    ├───────────────────────────────────────────────────┤
    │ dpcm[2]   ┌──────────────┬──────────────┐         │
    │           │ [PLAYBACK]   │ [CAPTURE]    │         │
    │           │ be_clients   │ be_clients   │         │
    │           │ fe_clients   │ fe_clients   │         │
    │           │ state        │ state        │         │
    │           └──────────────┴──────────────┘         │
    ├───────────────────────────────────────────────────┤
    │ pcm ──────▶ struct snd_pcm   (2nd stage)          │
    │ dais ─────▶ ┌────────────────┬───────────────┐    │
    │             │ cpu_dais       │ codec_dais    │    │
    │             └────────────────┴───────────────┘    │
    │             (separate devm_kcalloc array)         │
    ├───────────────────────────────────────────────────┤
    │ delayed_work  close_delayed_work_func             │
    │ id   list     mark_startup  mark_hw_params        │
    │               mark_trigger                        │
    │ pop_wait:1  fe_compr:1  initialized:1             │
    ├───────────────────────────────────────────────────┤
    │ num_components                                    │
    │ components[] ─▶ in-struct flex array, last member │
    └───────────────────────────────────────────────────┘
```

### The link the runtime is built from

A runtime is derived from one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the static description the machine driver fills. The link names its CPU, codec, and platform endpoints as arrays of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) with their counts, and those counts size the runtime's [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) arrays. The [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bits select whether the link becomes a Dynamic PCM back end or front end:

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
	...
	struct snd_soc_dai_link_component *platforms;
	unsigned int num_platforms;

	int id;	/* optional ID for machine driver link identification */
	...
	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;

	/* This DAI link can route to other DAI links at runtime (Frontend)*/
	unsigned int dynamic:1;
	...
};
```

The three endpoint counts set the length of both runtime arrays and the no_pcm and dynamic bits choose the Dynamic PCM role, the dais array spanning CPU plus codec and the components array adding the platforms:

```
    Link counts size the rtd arrays; no_pcm / dynamic pick the role
    ──────────────────────────────────────────────────────────────

    snd_soc_dai_link                  snd_soc_pcm_runtime
    ┌─────────────────────┐           ┌─────────────────────────────┐
    │ num_cpus            │           │ dais   (devm_kcalloc)       │
    │ num_codecs          │ ───────▶  │   size = num_cpus           │
    │ num_platforms       │  sizes    │        + num_codecs         │
    └─────────────────────┘  both     ├─────────────────────────────┤
                             arrays    │ components[]  (flex array)  │
                                       │   size = num_cpus           │
                                       │        + num_codecs         │
                                       │        + num_platforms      │
                                       └─────────────────────────────┘

    role bits select the Dynamic PCM kind:
      ┌──────────┬──────────┬──────────────────────────────────┐
      │ no_pcm   │ dynamic  │ link role                        │
      ├──────────┼──────────┼──────────────────────────────────┤
      │   0      │    0     │ normal PCM (own ALSA device)     │
      │   1      │    0     │ Back End  (no userspace PCM)     │
      │   0      │    1     │ Front End (routes to BEs)        │
      └──────────┴──────────┴──────────────────────────────────┘
```

### soc_new_pcm_runtime allocates the runtime

[`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) brings the runtime into existence. It registers an rtd [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) named after the link, then allocates the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) sized by [`struct_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/overflow.h) so the trailing [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array holds one slot per CPU, codec, and platform the link names. Because the allocation is bound to the rtd device, the runtime is reclaimed when that device is unregistered:

```c
/* sound/soc/soc-core.c:498 */
	dev = kzalloc_obj(struct device);
	if (!dev)
		return NULL;

	dev->parent	= card->dev;
	dev->release	= soc_release_rtd_dev;

	dev_set_name(dev, "%s", dai_link->name);

	ret = device_register(dev);
	if (ret < 0) {
		put_device(dev); /* soc_release_rtd_dev */
		return NULL;
	}

	/*
	 * for rtd
	 */
	rtd = devm_kzalloc(dev,
			   struct_size(rtd, components,
				       dai_link->num_cpus +
				       dai_link->num_codecs +
				       dai_link->num_platforms),
			   GFP_KERNEL);
	if (!rtd) {
		device_unregister(dev);
		return NULL;
	}
```

The function initializes the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) node and the two per-direction DPCM client lists, then arms the pop timer with [`INIT_DELAYED_WORK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h) pointing at [`close_delayed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L489), so the runtime owns its timer from birth even though [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) stays NULL until the PCM is created:

```c
/* sound/soc/soc-core.c:498 */
	rtd->dev = dev;
	INIT_LIST_HEAD(&rtd->list);
	for_each_pcm_streams(stream) {
		INIT_LIST_HEAD(&rtd->dpcm[stream].be_clients);
		INIT_LIST_HEAD(&rtd->dpcm[stream].fe_clients);
	}
	dev_set_drvdata(dev, rtd);
	INIT_DELAYED_WORK(&rtd->delayed_work, close_delayed_work);
```

The DAI pointer array is a second device-managed allocation sized by [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) plus [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). The accompanying comment draws the slot layout, after which the function sets the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) back pointers, assigns the monotonic [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) from [`card->num_rtd`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), seeds [`pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and links the runtime onto [`card->rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972):

```c
/* sound/soc/soc-core.c:498 */
	rtd->dais = devm_kcalloc(dev, dai_link->num_cpus + dai_link->num_codecs,
					sizeof(struct snd_soc_dai *),
					GFP_KERNEL);
	if (!rtd->dais)
		goto free_rtd;

	/*
	 * dais = [][][][][][][][][][][][][][][][][][]
	 *	  ^cpu_dais         ^codec_dais
	 *	  |--- num_cpus ---|--- num_codecs --|
	 * see
	 *	snd_soc_rtd_to_cpu()
	 *	snd_soc_rtd_to_codec()
	 */
	rtd->card	= card;
	rtd->dai_link	= dai_link;
	rtd->id		= card->num_rtd++;
	rtd->pmdown_time = pmdown_time;			/* default power off timeout */

	/* see for_each_card_rtds */
	list_add_tail(&rtd->list, &card->rtd_list);
```

### snd_soc_add_pcm_runtime resolves the link into DAIs and components

[`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) wraps the allocation and populates the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) arrays. It walks the link's CPU entries, resolving each into a runtime DAI with [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917), storing it through [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196), and adding the owning component, then does the same for the codec entries through [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197):

```c
/* sound/soc/soc-core.c:1175 */
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
```

When a named DAI has no registered match the function jumps to its `_err_defer` tail, which removes the half-built runtime and returns `-EPROBE_DEFER`, so the card driver retries once the missing component registers:

```c
/* sound/soc/soc-core.c:1175 */
_err_defer:
	snd_soc_remove_pcm_runtime(card, rtd);
	return -EPROBE_DEFER;
```

[`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) is the resolver. It walks every registered component under the [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c), and for the one matching the [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) it walks that component's DAIs and returns the one whose name matches:

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

[`snd_soc_rtd_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L317) appends to the [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array and skips a component already present, so a CPU and codec sharing one component are counted once. It bumps [`num_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) before writing the slot, which keeps the [`__counted_by()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h) annotation consistent:

```c
/* sound/soc/soc-core.c:317 */
static int snd_soc_rtd_add_component(struct snd_soc_pcm_runtime *rtd,
				     struct snd_soc_component *component)
{
	struct snd_soc_component *comp;
	int i;

	for_each_rtd_components(rtd, i, comp) {
		/* already connected */
		if (comp == component)
			return 0;
	}

	/* see for_each_rtd_components */
	rtd->num_components++; // increment flex array count at first
	rtd->components[rtd->num_components - 1] = component;

	return 0;
}
```

### Both bind stages run from snd_soc_bind_card

[`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) loops the link array, calling [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) once per link and stopping on the first error so an `-EPROBE_DEFER` propagates up. [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) is the caller and runs the two stages in order, first creating every runtime, then later, after the components and DAIs have probed, walking the runtimes with [`for_each_card_rtds()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1109) and running [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) on each:

```c
/* sound/soc/soc-core.c:2163 */
	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;
	...
	for_each_card_rtds(card, rtd) {
		ret = soc_init_pcm_runtime(card, rtd);
		if (ret < 0)
			goto probe_end;
	}
```

The two calls above become the two passes, the first allocating every runtime and resolving its DAIs and the second, after the components probe, creating each ALSA PCM and marking the runtime initialized:

```
    Two-stage rtd build inside snd_soc_bind_card (time ▼)
    ─────────────────────────────────────────────────────

    Stage 1: snd_soc_add_pcm_runtimes(card->dai_link, num_links)
    ┌─────────────────────────────────────────────────────────┐
    │ for each dai_link:  snd_soc_add_pcm_runtime             │
    │   soc_new_pcm_runtime   (alloc rtd, link onto rtd_list) │
    │   resolve cpu + codec DAIs into dais[]                  │
    │   a DAI not yet registered ─▶ -EPROBE_DEFER (retry all) │
    └─────────────────────────────────────────────────────────┘
                              │  all rtds now exist, dais[] filled
                              ▼
    ( components and their DAIs probe in between )
                              │
                              ▼
    Stage 2: for_each_card_rtds ─▶ soc_init_pcm_runtime(rtd)
    ┌─────────────────────────────────────────────────────────┐
    │ snd_soc_link_init   set DAI fmt                         │
    │ soc_new_pcm   (create struct snd_pcm, store in pcm)     │
    │ snd_soc_pcm_dai_new   (run each DAI pcm_new)            │
    │ initialized = true                                      │
    └─────────────────────────────────────────────────────────┘
```

### soc_init_pcm_runtime creates the ALSA PCM

The second stage runs the machine driver's link init, fixes the DAI format, then creates the ALSA PCM through [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909), runs each DAI's [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op through [`snd_soc_pcm_dai_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571), and sets [`initialized`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143). Its first line reads CPU DAI 0 with [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) straight out of the array the first stage filled:

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

	snd_soc_runtime_get_dai_fmt(rtd);
	ret = snd_soc_runtime_set_dai_fmt(rtd, dai_link->dai_fmt);
	if (ret)
		goto err;
	...
	/* create the pcm */
	ret = soc_new_pcm(rtd);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: can't create pcm %s :%d\n",
			dai_link->stream_name, ret);
		goto err;
	}

	ret = snd_soc_pcm_dai_new(rtd);
	if (ret < 0)
		goto err;

	rtd->initialized = true;

	return 0;
err:
	snd_soc_link_exit(rtd);
	return ret;
}
```

[`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) is what binds the runtime to an ALSA PCM. It creates the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), stores it in [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), points [`pcm->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) back at the runtime, and for a link that is not codec-to-codec installs [`snd_soc_close_delayed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L427) as the [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143):

```c
/* sound/soc/soc-pcm.c:2909 */
	if (!rtd->dai_link->c2c_params)
		rtd->close_delayed_work_func = snd_soc_close_delayed_work;

	rtd->pcm = pcm;
	pcm->nonatomic = rtd->dai_link->nonatomic;
	pcm->private_data = rtd;
	pcm->no_device_suspend = true;
```

[`snd_soc_pcm_dai_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L571) then gives each DAI on the link a chance to add controls or channel maps to the new PCM by running its [`pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, iterating the combined array with [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217):

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
```

### The delayed close work and pop suppression

The [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) defers the power-down so a gap between tracks does not cycle DAPM and produce a pop. The work handler [`close_delayed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L489) dispatches to whatever [`close_delayed_work_func`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) the runtime carries:

```c
/* sound/soc/soc-core.c:489 */
static void close_delayed_work(struct work_struct *work) {
	struct snd_soc_pcm_runtime *rtd =
			container_of(work, struct snd_soc_pcm_runtime,
				     delayed_work.work);

	if (rtd->close_delayed_work_func)
		rtd->close_delayed_work_func(rtd);
}
```

The default function [`snd_soc_close_delayed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L427) reads codec DAI 0 with [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197), and when [`pop_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) is still set it clears the bit and fires a DAPM stream-stop event, so the path powers down only after [`pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) has elapsed:

```c
/* sound/soc/soc-core.c:427 */
void snd_soc_close_delayed_work(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_dai *codec_dai = snd_soc_rtd_to_codec(rtd, 0);
	int playback = SNDRV_PCM_STREAM_PLAYBACK;

	snd_soc_dpcm_mutex_lock(rtd);
	...
	/* are we waiting on this codec DAI stream */
	if (rtd->pop_wait == 1) {
		rtd->pop_wait = 0;
		snd_soc_dapm_stream_event(rtd, playback,
					  SND_SOC_DAPM_STREAM_STOP);
	}

	snd_soc_dpcm_mutex_unlock(rtd);
}
```

### soc_free_pcm_runtime tears the runtime down

The runtime is device-managed, so most of it is reclaimed automatically, but [`soc_free_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L458) does the ordered teardown. It unlinks the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) node, flushes the pending [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) so the pop timer cannot fire after free, frees the component PCM state with [`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050), and unregisters the rtd device:

```c
/* sound/soc/soc-core.c:458 */
static void soc_free_pcm_runtime(struct snd_soc_pcm_runtime *rtd)
{
	if (!rtd)
		return;

	list_del(&rtd->list);

	flush_delayed_work(&rtd->delayed_work);
	snd_soc_pcm_component_free(rtd);

	/*
	 * we don't need to call kfree() for rtd->dev
	 * see
	 *	soc_release_rtd_dev()
	 *
	 * We don't need rtd->dev NULL check, because
	 * it is alloced *before* rtd.
	 * see
	 *	soc_new_pcm_runtime()
	 *
	 * We don't need to mind freeing for rtd,
	 * because it was created from dev (= rtd->dev)
	 * see
	 *	soc_new_pcm_runtime()
	 *
	 *		rtd = devm_kzalloc(dev, ...);
	 *		rtd->dev = dev
	 */
	device_unregister(rtd->dev);
}
```

According to the comment, the runtime needs no explicit [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slab_common.c) because it was allocated from [`rtd->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48); unregistering that device runs [`soc_release_rtd_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L452), which frees the device and releases the device-managed runtime with it. [`snd_soc_pcm_component_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1050) walks [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with [`for_each_rtd_components()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1205) and runs each component's `pcm_destruct`, so the ALSA PCM the runtime owned is released before the runtime memory goes away:

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

### Worked example: an x86-64 SoundWire DAI link

On an Intel x86-64 system the codecs are enumerated from ACPI and reached over SoundWire, and the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine driver builds its DAI-link array at probe through the shared helper [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293). The helper fills one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with its name, its CPU, platform, and codec [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) arrays and counts, and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) flag that marks a back-end link:

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

The simplest case allocates exactly the three components one SoundWire link needs. [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) allocates three [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) entries, fills slot 0 with the CPU DAI name, slot 1 with the platform component name, and slot 2 with the codec device and DAI name, then calls [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) with one of each:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1320 */
int asoc_sdw_init_simple_dai_link(struct device *dev, struct snd_soc_dai_link *dai_links,
				  int *be_id, char *name, int playback, int capture,
				  const char *cpu_dai_name, const char *platform_comp_name,
				  const char *codec_name, const char *codec_dai_name,
				  int no_pcm, int (*init)(struct snd_soc_pcm_runtime *rtd),
				  const struct snd_soc_ops *ops)
{
	struct snd_soc_dai_link_component *dlc;

	/* Allocate three DLCs one for the CPU, one for platform and one for the CODEC */
	dlc = devm_kcalloc(dev, 3, sizeof(*dlc), GFP_KERNEL);
	if (!dlc || !name || !cpu_dai_name || !platform_comp_name || !codec_name || !codec_dai_name)
		return -ENOMEM;

	dlc[0].dai_name = cpu_dai_name;
	dlc[1].name = platform_comp_name;

	dlc[2].name = codec_name;
	dlc[2].dai_name = codec_dai_name;

	asoc_sdw_init_dai_link(dev, dai_links, be_id, name, playback, capture,
			       &dlc[0], 1, &dlc[1], 1, &dlc[2], 1,
			       no_pcm, init, ops);

	return 0;
}
```

When the machine driver hands this array to the core, [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) turns each link into one [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with one CPU DAI at `dais[0]` and one codec DAI at `dais[1]`. [`snd_soc_rtd_to_cpu(rtd, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) then reaches the SoundWire CPU DAI and [`snd_soc_rtd_to_codec(rtd, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) reaches the SDCA codec DAI, with the platform component recorded alongside both in [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143). A back-end link carries [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), so [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) attaches the runtime to the substream private data without a userspace-visible PCM, while a front-end link carrying [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) gets the Dynamic PCM op set and uses the [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) client lists to bridge to its back-end runtimes.

```
    One SoundWire link: three DLCs map to one rtd's slots
    ─────────────────────────────────────────────────────

    dlc[] (asoc_sdw_init_simple_dai_link)   resolved rtd
    ┌────────────────────────────┐         ┌───────────────────────┐
    │ dlc[0] cpu_dai_name        │ ──────▶ │ dais[0] = cpu DAI     │
    │ dlc[1] platform_comp_name  │         │ dais[1] = codec DAI   │
    │ dlc[2] codec_name+dai_name │ ──────▶ ├───────────────────────┤
    └────────────────────────────┘         │ components[] =        │
       num_cpus = 1   num_codecs = 1       │   cpu comp            │
       num_platforms = 1                   │   codec comp          │
                                           │   platform comp       │
                                           └───────────────────────┘
       snd_soc_rtd_to_cpu(rtd, 0)   = dais[0]
       snd_soc_rtd_to_codec(rtd, 0) = dais[0 + num_cpus] = dais[1]
```
