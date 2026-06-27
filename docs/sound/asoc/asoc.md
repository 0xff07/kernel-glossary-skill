# ASoC (ALSA System on Chip) overview

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ASoC is the ALSA layer that builds one playable [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) out of several independently written drivers, so a codec vendor, an SoC audio-DSP vendor, and a machine integrator each ship a separate piece and the core stitches them together at runtime. The machine integrator describes the board as a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) carrying an array of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entries, registers it with [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), and [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) resolves each link into a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) (the rtd) that binds a CPU [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) to a CODEC [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) through the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) instances that own those DAIs. A codec or platform driver does not allocate any of these runtime objects. It registers a static [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) plus an array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), and the machine's per-link stream hooks are held separately in a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hung off the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). The worked example is an Intel SOF SoundWire system, where the Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec is the codec component, the SOF DSP supplies the platform/CPU component, and [`sof_sdw.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) is the machine driver that assembles the card.

```
    snd_soc_card  (machine description, one per board)
    ┌───────────────────────────────────────────────────────────────┐
    │  dai_link[]   ─▶ snd_soc_dai_link { cpus, codecs, ops }       │
    │  snd_card     ─▶ struct snd_card  (the ALSA device)           │
    │  rtd_list                                                     │
    └─────────────────────────────────┬─────────────────────────────┘
                                      │ snd_soc_bind_card()
                ┌─────────────────────┼───────────────────┐
                ▼                     ▼                   ▼
        snd_soc_pcm_runtime   snd_soc_pcm_runtime   snd_soc_pcm_runtime
        (rtd, one per link)   (rtd)                 (rtd)
        ┌──────────────────────────────────────────┐
        │  dais[] = cpu_dai ... codec_dai          │
        └───────┬──────────────────────────┬───────┘
                ▼                          ▼
          snd_soc_dai (CPU)         snd_soc_dai (CODEC)
                │                          │
                ▼                          ▼
          snd_soc_component         snd_soc_component
          (SOF platform)            (rt722-sdca codec)
                └──────────── DAPM graph over both ───────┘
```

## SUMMARY

A complete ASoC sound device is assembled from three classes of driver that never share a compilation unit. The codec component is a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) plus an array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) that a codec driver registers with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). The platform (or CPU) component is the same pair of structures registered by the SoC audio controller or DSP driver, describing the DMA engine and the CPU-side serial ports. The machine (or card) driver is a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) that names the board, lists the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) connections between the CPU and codec DAIs, and registers the whole assembly with [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557).

The object model rests on the difference between a `*_driver` struct and a `*_ops` struct. A [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) are the static, const description a codec or platform driver registers once, owned by that driver and shared across every card that instantiates it. A [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) fills a different role. It is the machine-level stream hook set, attached to one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) through its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field, so the board integrator runs code at stream open, hw_params, and trigger without modifying either vendor driver. The function pointer struct on the link belongs to the board; the function pointer struct on the component or DAI driver belongs to the device vendor.

Registration is a two-stage rendezvous through [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48). A codec or platform driver calls [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932), which allocates a [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), runs [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850), and through [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) and [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) creates one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) per driver entry, then links the component onto the global [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49). The machine driver separately calls [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), which hands off to [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163). For each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) creates a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and resolves the link's named CPU and codec DAIs against the registered components. [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) then calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) exactly once to allocate the underlying [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), probes the components, builds the PCM devices, and constructs the DAPM graph that ties the widgets of every component into one routing topology.

## SPECIFICATIONS

The ASoC object model is a Linux kernel software construct and has no standalone hardware specification. The serial-audio interfaces the DAIs drive (I2S, TDM, PDM) and the control and data transports the components sit behind (SoundWire, SLIMbus, HDA) are defined by their own bus and interface standards. For the SOF SoundWire worked example, the SoundWire stream model the codec component joins is documented in-tree, and the audio DSP firmware interface is defined by the Sound Open Firmware project.

## LINUX KERNEL

### Card and machine description (soc.h)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the machine description; carries the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array, the [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), the DAPM widget and route tables, and a pointer to the allocated [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one CPU-to-codec connection; names its [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) endpoints and points at the machine [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): one endpoint reference on a link, by [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), used to look up a registered DAI
- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the machine stream hooks ([`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623)) attached to a link, owned by the board not the device driver
- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the runtime instance of one link (the rtd); holds the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array and the [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) flex array that back this stream

### Component and DAI objects (soc-component.h, soc-dai.h)

- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the runtime instance of a registered codec or platform driver; owns a [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and a back pointer to its [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and parent [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207)
- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the static description a codec/platform driver registers; the function pointer struct of [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), PCM, and register-access callbacks plus the DAPM widget and route tables
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): the runtime instance of one DAI; back-points to its [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and parent [`component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and holds the per-direction stream state
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the static description of one DAI a codec/platform driver registers; carries the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capability records and the DAI ops pointer

### The underlying ALSA card and DAPM (core.h, soc-dapm.c)

- [`'\<struct snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80): the ALSA soundcard object; one is created per ASoC card and holds the control, PCM, and proc devices userspace opens
- [`'\<struct snd_soc_dapm_context\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44): the DAPM (Dynamic Audio Power Management) context attached to the card and to each component, holding the bias level and the widget/path lists

### Card registration and binding (soc-core.c, soc-devres.c)

- [`'\<snd_soc_register_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557): validate the card, allocate its DAPM context, initialise its lists and mutexes, and hand off to the binder under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48)
- [`'\<devm_snd_soc_register_card\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65): the device-managed wrapper a machine driver's probe uses, unregistering the card automatically at device teardown
- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): the binder; adds the runtimes, calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), probes components and DAIs, builds the PCMs, and links the DAPM graph
- [`'\<snd_soc_add_pcm_runtimes\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269): loop over the link array, creating and resolving one runtime per link
- [`'\<snd_soc_add_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175): resolve one link, allocating the rtd and binding its CPU, codec, and platform endpoints to registered components
- [`'\<soc_new_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498): allocate the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and its [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array and add it to the card's [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): run the link init, set the DAI format, and create the ALSA PCM for one bound runtime
- [`'\<snd_card_new\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171): allocate and initialise the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) that ASoC publishes to userspace

### Component and DAI registration (soc-core.c, soc-devres.c)

- [`'\<snd_soc_register_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932): allocate a [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), initialise it, and add it with its DAIs
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): the device-managed wrapper a codec/platform driver uses to register one component plus its DAI driver array
- [`'\<snd_soc_component_initialize\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850): allocate the component DAPM context, init its lists, name it, and store the [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) back pointer
- [`'\<snd_soc_add_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885): register the DAIs, set up the regmap, add the component to [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49), and rebind any deferred card
- [`'\<snd_soc_register_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773): loop over the DAI driver array, registering each entry and rolling back on failure
- [`'\<snd_soc_register_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706): allocate one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and add it to the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207)

### DAPM graph construction (soc-dapm.c)

- [`'\<snd_soc_dapm_link_dai_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407): join each DAI widget to the stream widgets of the same name so a stream becomes one connected path across components

### Runtime accessors (soc.h, soc-card.h)

- [`'\<snd_soc_rtd_to_cpu\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196): index the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array for the CPU DAI of a runtime
- [`'\<snd_soc_rtd_to_codec\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197): index past the CPU DAIs to the codec DAI of a runtime
- [`'\<snd_soc_card_to_dapm\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1137): read the card's generic DAPM context
- [`'\<snd_soc_card_set_drvdata\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100) / [`'\<snd_soc_card_get_drvdata\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L106): store and read the machine driver's private context on the card

### rt722-sdca and SOF SoundWire worked example

- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the codec [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) the rt722-sdca DAIs register under
- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries the codec exposes over SoundWire
- [`'\<rt722_sdca_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299): the codec driver entry point that calls [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'\<mc_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434): the SOF SoundWire machine driver probe that fills a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), builds its DAI links, and calls [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65)
- [`'\<sof_sdw_card_late_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1405): the machine [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) callback that finalises the card after its components are bound

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC design rationale and the codec, platform, and machine split
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and its DAI link array, the subject of the card description
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform (CPU/DMA) component the SOF DSP supplies
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide covering the component and DAI driver structures
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the routing graph built across all components at bind time
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where front-end and back-end runtimes are bound and triggered independently
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream model the rt722-sdca codec component joins

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The interface between the three driver classes is small. A codec or platform driver presents itself with two functions and two structs, while a machine driver presents itself with one struct and one registration call.

| Driver class | Registers | With | Owns the function pointer struct |
|--------------|-----------|------|----------------------------------|
| Codec component | [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) + [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array | `devm_snd_soc_register_component` | `snd_soc_dai_ops`, component PCM ops |
| Platform/CPU component | [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) + [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array | `devm_snd_soc_register_component` | `pcm_construct`, `pointer`, DMA ops |
| Machine/card | [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) + [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array | `devm_snd_soc_register_card` | `snd_soc_ops` per link |

### snd_soc_register_component, devm_snd_soc_register_component

A codec or platform driver calls [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) with its const [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), the array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries, and the entry count. The devm wrapper records a release action and forwards to [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932), which allocates the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and registers the DAIs.

### snd_soc_register_card, devm_snd_soc_register_card

A machine driver calls [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) with a fully filled [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). The card must already carry a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), a [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and a [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array, and [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) rejects a card missing the name or device before it does anything else.

### snd_soc_ops on a dai_link

The machine driver attaches a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) to a link through the link's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) field. Its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) callback is where a board programs the clock tree of the codec and CPU DAIs for the negotiated rate, distinct from the codec driver's own [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) which programs the codec's serial port.

## DETAILS

### The static description versus the runtime instance

ASoC keeps a strict split between the const description a driver registers and the runtime object the core allocates from it, and the split repeats at three levels. A component, a DAI, and a card each have a `*_driver` or description struct supplied by a driver, and a matching runtime struct ([`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)) that the core creates and links into its lists.

The codec driver writes a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) holding its probe, PCM, register-access, and DAPM description. The struct is const and shared by every card that instantiates the codec, so it carries only immutable description and function pointers:

```c
/* include/sound/soc-component.h:67 */
struct snd_soc_component_driver {
	const char *name;

	/* Default control and setup, added after probe() is run */
	const struct snd_kcontrol_new *controls;
	unsigned int num_controls;
	const struct snd_soc_dapm_widget *dapm_widgets;
	unsigned int num_dapm_widgets;
	const struct snd_soc_dapm_route *dapm_routes;
	unsigned int num_dapm_routes;

	int (*probe)(struct snd_soc_component *component);
	void (*remove)(struct snd_soc_component *component);
	int (*suspend)(struct snd_soc_component *component);
	int (*resume)(struct snd_soc_component *component);

	unsigned int (*read)(struct snd_soc_component *component,
			     unsigned int reg);
	int (*write)(struct snd_soc_component *component,
		     unsigned int reg, unsigned int val);

	/* pcm creation and destruction */
	int (*pcm_construct)(struct snd_soc_component *component,
			     struct snd_soc_pcm_runtime *rtd);
	void (*pcm_destruct)(struct snd_soc_component *component,
			     struct snd_pcm *pcm);
	...
};
```

The runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) is the per-instance object. It back-points at its [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and parent [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), owns the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) of runtime DAIs it created, and holds the mutable [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) count and the function marks:

```c
/* include/sound/soc-component.h:207 */
struct snd_soc_component {
	const char *name;
	const char *name_prefix;
	struct device *dev;
	struct snd_soc_card *card;

	unsigned int active;

	unsigned int suspended:1; /* is in suspend PM state */

	struct list_head list;
	struct list_head card_aux_list; /* for auxiliary bound components */
	struct list_head card_list;

	const struct snd_soc_component_driver *driver;

	struct list_head dai_list;
	int num_dai;

	struct regmap *regmap;
	int val_bytes;
	...
};
```

This pairing of a registered description with a core-allocated instance repeats down the levels, the component and DAI driver records each yielding a runtime object and the machine-owned link yielding its runtime (the rtd):

```
    static description (driver-owned, const)  runtime instance (core-alloc)
    ────────────────────────────────────────  ───────────────────────────────
    snd_soc_component_driver              ─▶  snd_soc_component
    snd_soc_dai_driver                    ─▶  snd_soc_dai
    snd_soc_dai_link  (machine-owned)     ─▶  snd_soc_pcm_runtime  (rtd)
    snd_soc_ops       (on the link)           (called via the rtd's ops)
```

### The card description and its DAI links

The machine driver writes the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). The card names the board, points at the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array that describes the connections, carries the card-wide DAPM widget and route tables, and after binding holds the pointer to the allocated [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and the [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) of runtimes:

```c
/* include/sound/soc.h:972 */
struct snd_soc_card {
	const char *name;
	const char *long_name;
	const char *driver_name;
	const char *components;
	...
	struct device *dev;
	struct snd_card *snd_card;
	struct module *owner;
	...
	/* CPU <--> Codec DAI links  */
	struct snd_soc_dai_link *dai_link;  /* predefined links only */
	int num_links;  /* predefined links only */

	struct list_head rtd_list;
	int num_rtd;
	...
};
```

Each entry in that array is a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). It names its CPU side, its codec side, and its platform side as arrays of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), and it carries the machine [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and the DPCM flags. The endpoint arrays and the machine ops are the load-bearing fields for binding:

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
	unsigned int dai_fmt;           /* format to set on init */
	...
	/* machine stream operations */
	const struct snd_soc_ops *ops;
	const struct snd_soc_compr_ops *compr_ops;
	...
	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;

	/* This DAI link can route to other DAI links at runtime (Frontend)*/
	unsigned int dynamic:1;
	...
};
```

The machine hooks themselves are a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and the contrast with [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) above is the object model's central distinction. The component driver describes a device the vendor ships, while this struct describes per-stream behaviour the board integrator adds on top, attached to one link rather than to any component:

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

Those board hooks hang off each link the card points at, one card holding num_links links whose CPU, codec, and platform endpoints each resolve by name to a registered DAI:

```
    The static card description: one card, num_links dai_link[]
    ──────────────────────────────────────────────────────────

    struct snd_soc_card  (machine-owned, one per board)
    ┌────────────────────────────────────────────────────────┐
    │  name                                                  │
    │  dai_link  ─▶ struct snd_soc_dai_link[ num_links ]     │
    │  num_links                                             │
    └────────────────────────────┬───────────────────────────┘
                                 │ one element per CPU↔codec link
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
     dai_link[0]           dai_link[1]    ...   dai_link[N-1]
     ┌──────────────────────────────────────────────────────┐
     │ struct snd_soc_dai_link                              │
     │   cpus      ─▶ snd_soc_dai_link_component[num_cpus]  │
     │   codecs    ─▶ snd_soc_dai_link_component[num_codecs]│
     │   platforms ─▶ snd_soc_dai_link_component[num_plat]  │
     │   ops       ─▶ struct snd_soc_ops  (board hooks)     │
     │   dynamic / no_pcm  (DPCM front-end / back-end)      │
     └──────────────────────────────────────────────────────┘

    Each *_link_component names an endpoint by name + dai_name;
    binding resolves each name to a registered snd_soc_dai.
```

### Component registration creates the runtime component and its DAIs

A codec driver registers through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), which records a devres release action and calls [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932):

```c
/* sound/soc/soc-devres.c:29 */
int devm_snd_soc_register_component(struct device *dev,
			 const struct snd_soc_component_driver *cmpnt_drv,
			 struct snd_soc_dai_driver *dai_drv, int num_dai)
{
	const struct snd_soc_component_driver **ptr;
	int ret;

	ptr = devres_alloc(devm_component_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_soc_register_component(dev, cmpnt_drv, dai_drv, num_dai);
	if (ret == 0) {
		*ptr = cmpnt_drv;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

[`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) allocates the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h), initialises it, and adds it together with its DAIs:

```c
/* sound/soc/soc-core.c:2932 */
int snd_soc_register_component(struct device *dev,
			const struct snd_soc_component_driver *component_driver,
			struct snd_soc_dai_driver *dai_drv,
			int num_dai)
{
	struct snd_soc_component *component;
	int ret;

	component = devm_kzalloc(dev, sizeof(*component), GFP_KERNEL);
	if (!component)
		return -ENOMEM;

	ret = snd_soc_component_initialize(component, component_driver, dev);
	if (ret < 0)
		return ret;

	return snd_soc_add_component(component, dai_drv, num_dai);
}
```

[`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), calls [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) to turn each [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) into a runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), adds the component to the global [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49), and then retries any card that had deferred for want of this component:

```c
/* sound/soc/soc-core.c:2885 */
int snd_soc_add_component(struct snd_soc_component *component,
			  struct snd_soc_dai_driver *dai_drv,
			  int num_dai)
{
	struct snd_soc_card *card, *c;
	int ret;
	int i;

	mutex_lock(&client_mutex);
	...
	ret = snd_soc_register_dais(component, dai_drv, num_dai);
	if (ret < 0) {
		dev_err(component->dev, "ASoC: Failed to register DAIs: %d\n",
			ret);
		goto err_cleanup;
	}
	...
	/* see for_each_component */
	list_add(&component->list, &component_list);

	list_for_each_entry_safe(card, c, &unbind_card_list, list)
		snd_soc_rebind_card(card);

err_cleanup:
	if (ret < 0)
		snd_soc_del_component_unlocked(component);

	mutex_unlock(&client_mutex);
	return ret;
}
```

The DAI registration loop itself is the work of [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773), which iterates the array and calls [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) for each entry, allocating one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and linking it onto [`component->dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207).

```
    One component, num_dai runtime DAIs on its dai_list
    ───────────────────────────────────────────────────

    static (driver-owned)              runtime (core-allocated)

    snd_soc_dai_driver[ num_dai ]      struct snd_soc_component
    ┌────────────────────────────┐     ┌───────────────────────┐
    │ [0] playback / capture caps│     │ driver  ─▶ the driver │
    │ [1] ...                    │     │ dai_list (head)       │
    │ ...                        │     │ num_dai               │
    │ [num_dai-1]                │     └───────────┬───────────┘
    └─────────────┬──────────────┘                 │ list_add per DAI
                  │ snd_soc_register_dais():        ▼
                  │  one snd_soc_dai per entry   component->dai_list
                  │              ┌───────────┬───────────┬─────┬───────────┐
                  └────────────▶ │  dai[0]   │  dai[1]   │ ... │ dai[N-1]  │
                                 └───────────┴───────────┴─────┴───────────┘
                                 (runtime snd_soc_dai nodes)

    Each runtime snd_soc_dai back-points at its snd_soc_dai_driver entry
    and at the parent snd_soc_component.
```

### Card registration hands off to the binder

A machine driver registers its card with [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), which rejects a card with no name or device, allocates the card's DAPM context, initialises the card's lists and mutexes, and then under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) calls [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163):

```c
/* sound/soc/soc-core.c:2557 */
int snd_soc_register_card(struct snd_soc_card *card)
{
	int ret;

	if (!card->name || !card->dev)
		return -EINVAL;

	card->dapm = snd_soc_dapm_alloc(card->dev);
	if (!card->dapm)
		return -ENOMEM;

	dev_set_drvdata(card->dev, card);

	INIT_LIST_HEAD(&card->widgets);
	INIT_LIST_HEAD(&card->paths);
	INIT_LIST_HEAD(&card->dapm_list);
	INIT_LIST_HEAD(&card->aux_comp_list);
	INIT_LIST_HEAD(&card->component_dev_list);
	INIT_LIST_HEAD(&card->list);
	INIT_LIST_HEAD(&card->rtd_list);
	INIT_LIST_HEAD(&card->dapm_dirty);
	INIT_LIST_HEAD(&card->dobj_list);

	card->instantiated = 0;
	mutex_init(&card->mutex);
	mutex_init(&card->dapm_mutex);
	mutex_init(&card->pcm_mutex);

	mutex_lock(&client_mutex);

	if (card->devres_dev) {
		ret = devm_snd_soc_bind_card(card->devres_dev, card);
		if (ret == -EPROBE_DEFER) {
			list_add(&card->list, &unbind_card_list);
			ret = 0;
		}
	} else {
		ret = snd_soc_bind_card(card);
	}

	mutex_unlock(&client_mutex);

	return ret;
}
```

### snd_soc_bind_card creates the one snd_card

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) is the assembly point. It first adds a runtime per link with [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269), then calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) exactly once to create the underlying ALSA [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) and stores it in [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972):

```c
/* sound/soc/soc-core.c:2163 */
static int snd_soc_bind_card(struct snd_soc_card *card)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_component *component;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	int ret;

	snd_soc_card_mutex_lock_root(card);
	snd_soc_fill_dummy_dai(card);

	snd_soc_dapm_init(dapm, card, NULL);
	...
	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;

	/* card bind complete so register a sound card */
	ret = snd_card_new(card->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
			card->owner, 0, &card->snd_card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: can't create sound card for card %s: %d\n",
			card->name, ret);
		goto probe_end;
	}
	...
```

According to the comment "card bind complete so register a sound card", the order is fixed. The runtimes are added and their DAIs resolved first, and only then does the single ALSA card come into existence. After that, [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) probes the components used by the links with [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742), probes the DAIs with [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707), and runs [`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) over each runtime to create the ALSA PCM devices:

```c
/* sound/soc/soc-core.c:2163 (continued) */
	/* probe all components used by DAI links on this card */
	ret = soc_probe_link_components(card);
	...
	/* probe all DAI links on this card */
	ret = soc_probe_link_dais(card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: failed to instantiate card %d\n", ret);
		goto probe_end;
	}

	for_each_card_rtds(card, rtd) {
		ret = soc_init_pcm_runtime(card, rtd);
		if (ret < 0)
			goto probe_end;
	}

	snd_soc_dapm_link_dai_widgets(card);
	snd_soc_dapm_connect_dai_link_widgets(card);
	...
	ret = snd_card_register(card->snd_card);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: failed to register soundcard %d\n",
				ret);
		goto probe_end;
	}

	card->instantiated = 1;
```

The DAPM graph is built across every component at this point by [`snd_soc_dapm_link_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407), which joins each DAI widget to the stream widgets of the same name so a playback or capture stream becomes one connected path from the CPU DMA widget through the codec output. The card is then published to userspace with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) and marked [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972).

```
    snd_soc_bind_card() fixed order (top to bottom)
    ───────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ snd_soc_add_pcm_runtimes()                               │
    │   one rtd per dai_link; resolve CPU + CODEC DAIs         │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼  (rtds exist, DAIs resolved)
    ┌──────────────────────────────────────────────────────────┐
    │ snd_card_new()        ← exactly once: the one snd_card   │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ soc_probe_link_components()   then  soc_probe_link_dais()│
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ soc_init_pcm_runtime()  per rtd → create the ALSA PCM    │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_link_dai_widgets()  → one DAPM graph        │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ snd_card_register()  → publish;  instantiated = 1        │
    └──────────────────────────────────────────────────────────┘
```

### An rtd binds one CPU DAI to one CODEC DAI

The runtime that links a CPU DAI to a codec DAI is the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143). Its definition carries a [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) pointer (the CPU DAIs followed by the codec DAIs) and a [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) flex array of the components backing the stream, and according to its own comment it "glues a codec and cpu DAI together":

```c
/* include/sound/soc.h:1143 */
struct snd_soc_pcm_runtime {
	struct device *dev;
	struct snd_soc_card *card;
	struct snd_soc_dai_link *dai_link;
	struct snd_pcm_ops ops;
	...
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
	...
	/* CPU/Codec/Platform */
	int num_components;
	struct snd_soc_component *components[] __counted_by(num_components);
};
```

[`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) allocates the rtd sized for the link's CPU, codec, and platform endpoints, allocates the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array for the CPU plus codec DAIs, and links the rtd onto the card's [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). The comment in the function spells out the layout of the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array:

```c
/* sound/soc/soc-core.c:498 */
	/*
	 * for rtd->dais
	 */
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
```

The two accessor macros read that layout. [`snd_soc_rtd_to_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) indexes from the front for a CPU DAI and [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) indexes past the CPU DAIs for a codec DAI:

```c
/* include/sound/soc.h:1196 */
#define snd_soc_rtd_to_cpu(rtd, n)   (rtd)->dais[n]
#define snd_soc_rtd_to_codec(rtd, n) (rtd)->dais[n + (rtd)->dai_link->num_cpus]
```

The binding itself happens in [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175), which [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) calls per link. After [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) returns the empty rtd, the function walks the link's CPU and codec endpoint arrays, resolves each named DAI to a registered runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) with [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917), writes it into the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) slot through the accessor, and records the owning component on the rtd:

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

When a named DAI is not yet registered, the function jumps to `_err_defer` and returns `-EPROBE_DEFER`, which propagates back so the whole card defers until the missing component appears. This is the path [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) later retries through [`snd_soc_rebind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2347) when the codec finally registers.

```
    rtd->dais[] memory layout: CPU DAIs then CODEC DAIs
    ───────────────────────────────────────────────────

    index   0          num_cpus-1  num_cpus              end
            ┌──────┬──────┬─────┬──────┬──────┬──────┬─────┬──────┐
    dais[]  │ cpu0 │ cpu1 │ ... │ cpuC │ cod0 │ cod1 │ ... │ codK │
            └──────┴──────┴─────┴──────┴──────┴──────┴─────┴──────┘
            ├──────── num_cpus ────────┼─────── num_codecs ───────┤
            (C = num_cpus-1)            (K = num_codecs-1)

    snd_soc_rtd_to_cpu(rtd, n)   = dais[n]
    snd_soc_rtd_to_codec(rtd, n) = dais[n + rtd->dai_link->num_cpus]

    allocated by soc_new_pcm_runtime() with
      num_cpus + num_codecs slots.
```

### Worked example: the SOF SoundWire card and the rt722-sdca codec

The three driver classes are visible in one Intel SOF SoundWire system. The codec component is the rt722-sdca codec, whose [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) registers a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) named [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) together with its three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries:

```c
/* sound/soc/codecs/rt722-sdca.c:1090 */
static const struct snd_soc_component_driver soc_sdca_dev_rt722 = {
	.probe = rt722_sdca_probe,
	.controls = rt722_sdca_controls,
	.num_controls = ARRAY_SIZE(rt722_sdca_controls),
	.dapm_widgets = rt722_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt722_sdca_dapm_widgets),
	.dapm_routes = rt722_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt722_sdca_audio_map),
	.set_jack = rt722_sdca_set_jack_detect,
	.endianness = 1,
};
```

[`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) ends by calling [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) with that component driver and the DAI driver array, which is the codec-component entry into the registration path above:

```c
/* sound/soc/codecs/rt722-sdca.c:1299 */
	return devm_snd_soc_register_component(dev,
			&soc_sdca_dev_rt722, rt722_sdca_dai, ARRAY_SIZE(rt722_sdca_dai));
```

The platform/CPU component is the SOF audio DSP, registered separately by the SOF core as its own [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) describing the DSP-side DMA and the SoundWire DAIs. The machine component is [`sof_sdw.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c), whose [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) fills a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) from the ACPI machine match data, builds the DAI links with [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225), and registers the card with [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65):

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
static int mc_probe(struct platform_device *pdev)
{
	struct snd_soc_acpi_mach *mach = dev_get_platdata(&pdev->dev);
	struct snd_soc_card *card;
	struct asoc_sdw_mc_private *ctx;
	struct intel_mc_ctx *intel_ctx;
	int amp_num = 0, i;
	int ret;
	...
	ctx->private = intel_ctx;
	ctx->codec_info_list_count = asoc_sdw_get_codec_info_list_count();
	card = &ctx->card;
	card->dev = &pdev->dev;
	card->name = "soundwire";
	card->owner = THIS_MODULE;
	card->late_probe = sof_sdw_card_late_probe;
	card->add_dai_link = sof_sdw_add_dai_link;

	snd_soc_card_set_drvdata(card, ctx);
	...
	ret = sof_card_dai_links_create(card);
	if (ret < 0)
		return ret;
	...
	/* Register the card */
	ret = devm_snd_soc_register_card(card->dev, card);
	if (ret) {
		dev_err_probe(card->dev, ret, "snd_soc_register_card failed %d\n", ret);
		asoc_sdw_mc_dailink_exit_loop(card);
		return ret;
	}

	platform_set_drvdata(pdev, card);

	return ret;
}
```

The machine driver stores its private context on the card with [`snd_soc_card_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100) and reads it back from card callbacks with [`snd_soc_card_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L106). The card carries no DAI ops of its own here. The board names its DSP platform and rt722-sdca codec in the link endpoints, and binding resolves those names into the rtd's [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) slots. The card's [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) hook, [`sof_sdw_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1405), runs from [`snd_soc_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L163) near the end of [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), after every component is bound and the single [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) exists, so the board can attach the HDMI display-audio codecs that depend on the bound topology.

### The card resolved into per-link runtimes, DAIs, and components

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) turns the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) machine description and its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array into one [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) plus a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) per link, each binding a CPU and CODEC [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) through the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) instances that own them.

```
    snd_soc_card  (machine description, one per board)
    ┌───────────────────────────────────────────────────────────────┐
    │  dai_link[]   ─▶ snd_soc_dai_link { cpus, codecs, ops }       │
    │  snd_card     ─▶ struct snd_card  (the ALSA device)           │
    │  rtd_list                                                     │
    └───────────────────────────────┬───────────────────────────────┘
                                    │ snd_soc_bind_card()
                ┌───────────────────┼─────────────────────┐
                ▼                   ▼                     ▼
        snd_soc_pcm_runtime   snd_soc_pcm_runtime   snd_soc_pcm_runtime
        (rtd, one per link)   (rtd)                 (rtd)
        ┌──────────────────────────────────────────┐
        │  dais[] = cpu_dai ... codec_dai          │
        └───────┬──────────────────────────┬───────┘
                ▼                          ▼
          snd_soc_dai (CPU)         snd_soc_dai (CODEC)
                │                          │
                ▼                          ▼
          snd_soc_component         snd_soc_component
          (SOF platform)            (rt722-sdca codec)
                └──────────── DAPM graph over both ───────┘
```
