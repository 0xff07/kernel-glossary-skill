# DAI link binding

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) describes one audio path on a card by naming a CPU side, a codec side, and an optional platform side, each through a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that identifies a component and one of its DAIs by string name. The ASoC core resolves those names into runtime DAI pointers when the card binds, allocating one [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) per link with [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) and calling [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) for each component entry, which matches a registered DAI by component identity through [`snd_soc_is_matching_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856) and by DAI name through [`snd_soc_is_matching_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273). On an Intel SoundWire laptop the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine generates the link table at probe rather than declaring it, building each link through [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) and [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293), pointing each link's [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) at a SOF DSP back-end DAI such as `"SDW0 Pin0"`, its [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) at an SDCA codec DAI such as `"rt722-sdca-aif1"` on the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec, and its [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) at the SOF PCI audio controller named by its bus address.

```
    one struct snd_soc_dai_link (a SoundWire back-end link)
    ───────────────────────────────────────────────────────

        cpus[0]                platforms[0]           codecs[0]
    ┌──────────────┐        ┌──────────────┐        ┌──────────────────┐
    │ name  = NULL │        │ name  =      │        │ name  = "sdw:..."│
    │ dai_name =   │        │  "0000:00:   │        │ dai_name =       │
    │  "SDW0 Pin0" │        │   1f.3"      │        │  "rt722-sdca-    │
    │              │        │ dai_name=NULL│        │   aif1"          │
    └──────┬───────┘        └──────┬───────┘        └────────┬─────────┘
           ▼                       ▼                         ▼
     SOF DSP BE DAI         SOF PCI component         SDCA codec DAI
     (registered by         (the platform that        (registered by
      the SOF driver)        provides the PCM)         the SoundWire codec)

    snd_soc_find_dai() resolves each entry to a struct snd_soc_dai and
    stores it in rtd->dais[]: CPU DAIs first, codec DAIs after num_cpus.
```

## SUMMARY

The machine driver owns one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) whose [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) array and [`num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033) count describe every audio path. Each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) carries three arrays of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and the [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with [`num_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and each entry identifies a DAI by a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) (the component device name) and a [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) (the DAI within that component). When the card binds, [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175) creates one [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) per link, then walks the three arrays and calls [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) for each, storing the resolved [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) pointers in the runtime's [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array with the CPU DAIs first and the codec DAIs after.

On the Intel SoundWire board the link table is generated rather than declared. [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) counts the SoundWire endpoints, allocates the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) array, and drives [`create_sdw_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023), which calls [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) once per SoundWire link. That builder fills the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) with a `"SDW%d Pin%d"` string naming a SOF DSP back-end DAI, fills each [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry's [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) from the matched [`struct asoc_sdw_dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) record in [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), and hands the assembled arrays to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293), which writes them into the link and marks it a DPCM back end through its [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) argument.

## SPECIFICATIONS

The [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) object is a Linux kernel software construct and has no standalone hardware specification. The SoundWire bus the linked codecs and amplifiers ride on is handled by the kernel SoundWire core, and the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec is programmed through the kernel's SDCA helper layer and regmap.

## LINUX KERNEL

### Link and component types (soc.h)

- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one audio path; holds the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) component arrays, their counts, and the link flags [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): one endpoint identifier, by component [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and DAI [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642)
- [`'\<struct snd_soc_dai_link_ch_map\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696): maps each CPU DAI to a codec DAI on a multi-codec link
- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the runtime object the core builds per link, holding the resolved [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array and a back pointer to [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): the registered DAI a link entry resolves to

### Resolution path (soc-core.c)

- [`'\<snd_soc_add_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175): per link, run [`soc_dai_link_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949), allocate the runtime, and resolve every CPU, codec, and platform component
- [`'\<soc_new_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498): allocate the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) sized for [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) plus [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) DAIs and link it onto the card
- [`'\<snd_soc_find_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917): walk every registered component and its DAIs, returning the first whose component and DAI name both match the [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642)
- [`'\<snd_soc_is_matching_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856): compare the component [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), the bus-address string for the SOF platform
- [`'\<snd_soc_is_matching_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273): compare the [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) against the DAI driver name, the runtime DAI name, or the component name
- [`'\<soc_dai_link_sanity_check\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949): reject a link whose component is over- or under-specified, or defer when a component is not yet registered

### Resolution-path macros (soc.h)

- [`'\<for_each_link_cpus\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L847) / [`'\<for_each_link_codecs\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L835): iterate the CPU and codec component arrays of one link
- [`'\<snd_soc_rtd_to_cpu\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1196) / [`'\<snd_soc_rtd_to_codec\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197): index the runtime [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array, codecs sitting after the CPUs

### Intel SoundWire board builder (boards/sof_sdw.c)

- [`'\<sof_card_dai_links_create\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225): count endpoints, allocate the link and [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) arrays, and dispatch the SoundWire, SSP, DMIC, HDMI, and BT builders
- [`'\<create_sdw_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023): loop over each populated [`struct asoc_sdw_dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119) and call the per-link builder
- [`'\<create_sdw_dailink\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876): build the playback and capture back-end links for one SoundWire link, filling [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) attached to every SoundWire link

### SoundWire utils helpers (sdw_utils/soc_sdw_utils.c)

- [`'\<asoc_sdw_init_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293): assign the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), counts, [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) of one link
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): allocate the three single-element component arrays and delegate to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293)
- [`'codec_info_list':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74): the per-part table mapping a SoundWire part id to its codec DAIs, back-end ids, controls, widgets, and callbacks
- [`'\<struct asoc_sdw_dai_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47): one codec DAI's [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), per-direction back-end ids, and callbacks

### SDCA codec DAIs (codecs)

- [`'rt722_sdca_dai':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec's three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries named `"rt722-sdca-aif1"`, `"rt722-sdca-aif2"`, `"rt722-sdca-aif3"`

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver concept and the DAI link table that glues CPU and codec DAIs
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where a front-end link with [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) set routes to back-end links with [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) set
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the split between codec, platform, and machine drivers
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the linked codec DAIs join

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The interface a machine driver fills in is the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and the three pointer-plus-count pairs at its head are the contract with the core. A reader of one link learns the whole path from those fields, which CPU DAI carries the data ([`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)), which codec or codecs terminate it ([`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)), and which platform component provides the PCM and DMA back end ([`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`num_platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)). Each of those arrays is a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), and only two of its fields drive matching on an x86-64 ACPI system, the component [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and the [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642).

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

The [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) head holds the three arrays and their counts, followed by the flags a SoundWire back-end link sets, [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) so no front-facing PCM device is created for the link, and [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) so the link's trigger may sleep.

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
	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;

	/* This DAI link can route to other DAI links at runtime (Frontend)*/
	unsigned int dynamic:1;
	...
};
```

## DETAILS

### One link names three component sides

A [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is the unit a machine driver writes per audio path, and the three component arrays at its head are independent. The [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the DAIs the DSP exposes, the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the DAIs on the external chips, and the [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the component that owns the PCM and DMA back end. On an Intel SoundWire laptop all three resolve to components the firmware and bus enumeration registered, the CPU side to a SOF DSP back-end DAI, the platform side to the SOF PCI audio controller whose component [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) is its PCI bus address such as `"0000:00:1f.3"`, and the codec side to a SoundWire peripheral DAI such as one of the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) interfaces. The codec DAIs come from the codec driver, which registers [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries whose [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) fields are exactly the strings the machine driver places in [`codecs[].dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642):

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
	...
};
```

### Resolution turns names into DAI pointers

When the card binds, [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) adds one runtime per link through [`snd_soc_add_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1175). That function first runs [`soc_dai_link_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L949), then allocates the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) with [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498), and finally walks the CPU and codec arrays, calling [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) for each entry and recording the result into the runtime [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array. A component that is not yet registered makes the function return `-EPROBE_DEFER` so the card is retried later:

```c
/* sound/soc/soc-core.c:1175 */
static int snd_soc_add_pcm_runtime(struct snd_soc_card *card,
				   struct snd_soc_dai_link *dai_link)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_dai_link_component *codec, *platform, *cpu;
	...
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
	...
_err_defer:
	snd_soc_remove_pcm_runtime(card, rtd);
	return -EPROBE_DEFER;
}
```

[`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) is the lookup itself. It walks every registered component, keeps those whose identity matches the link component through [`snd_soc_is_matching_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856), and within each match walks the component's DAIs, returning the first whose name matches through [`snd_soc_is_matching_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273):

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

[`snd_soc_is_matching_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856) on an x86-64 ACPI card reduces to a string compare of the component [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), since firmware enumeration sets no firmware-node pointer on the component, so the platform entry matches because its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) equals the SOF controller's bus-address component name:

```c
/* sound/soc/soc-core.c:856 */
static int snd_soc_is_matching_component(
	const struct snd_soc_dai_link_component *dlc,
	struct snd_soc_component *component)
{
	struct device_node *component_of_node;

	if (!dlc)
		return 0;
	...
	component_of_node = soc_component_to_node(component);

	if (dlc->of_node && component_of_node != dlc->of_node)
		return 0;
	if (dlc->name && strcmp(component->name, dlc->name))
		return 0;

	return 1;
}
```

[`snd_soc_is_matching_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L273) then compares [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642). A NULL [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) matches the sole DAI of a single-DAI component; otherwise the string must equal the DAI driver name, the runtime DAI name, or the component name, which is how `"rt722-sdca-aif1"` selects exactly one of the three [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) interfaces:

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

The runtime that [`soc_new_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L498) allocates lays its [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) array out with the CPU DAIs first and the codec DAIs after, which is why [`snd_soc_rtd_to_codec()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1197) offsets by [`num_cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702):

```c
/* include/sound/soc.h:1196 */
#define snd_soc_rtd_to_cpu(rtd, n)   (rtd)->dais[n]
#define snd_soc_rtd_to_codec(rtd, n) (rtd)->dais[n + (rtd)->dai_link->num_cpus]
```

Filling each slot of that array runs the name test, a NULL dlc.dai_name taking the sole DAI of the component and any other value selecting the one whose driver, runtime, or component name it equals:

```
    snd_soc_is_matching_dai: dlc.dai_name selects one DAI
    ──────────────────────────────────────────────────────

       link component                       a registered snd_soc_dai
    ┌────────────────────┐               ┌──────────────────────────┐
    │ dlc.dai_name       │               │ dai->driver->name        │
    │                    │  compared to  │ dai->name                │
    │                    │               │ dai->component->name     │
    └─────────┬──────────┘               └──────────────────────────┘
              ▼
    ┌────────────────────────┬────────────────────────────────────┐
    │ dlc.dai_name           │ result                             │
    ├────────────────────────┼────────────────────────────────────┤
    │ NULL                   │ match (sole DAI of the component)  │
    │ == driver->name        │ match                              │
    │ == dai->name           │ match                              │
    │ == component->name     │ match                              │
    │ none of the above      │ no match                           │
    └────────────────────────┴────────────────────────────────────┘

    "rt722-sdca-aif1" equals one rt722_sdca_dai[] driver name,
    so it selects exactly one of the three rt722-sdca interfaces.
```

### The SoundWire board builds links from a codec table

On the Intel SoundWire board the link table is generated at probe rather than written by hand, because the set of codecs and amplifiers varies per machine. [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) counts the endpoints the ACPI machine description reports, sizes and allocates the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) array, points [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) at it, and dispatches the per-class builders:

```c
/* sound/soc/intel/boards/sof_sdw.c:1225 */
static int sof_card_dai_links_create(struct snd_soc_card *card)
{
	...
	num_links = sdw_be_num + ssp_num + dmic_num + hdmi_num + bt_num + 1;
	dai_links = devm_kcalloc(dev, num_links, sizeof(*dai_links), GFP_KERNEL);
	if (!dai_links) {
		ret = -ENOMEM;
		goto err_end;
	}

	card->codec_conf = codec_conf;
	card->num_configs = num_confs;
	card->dai_link = dai_links;
	card->num_links = num_links;
	...
	/* SDW */
	if (sdw_be_num) {
		ret = create_sdw_dailinks(card, &dai_links, &be_id,
					  sof_dais, &codec_conf);
		if (ret)
			goto err_end;
	}
	...
}
```

[`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) is where the component arrays are filled. For each PCM direction it allocates the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) arrays sized to the endpoint counts, builds the CPU [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) as a `"SDW%d Pin%d"` string keyed by the link and pin index, and copies each endpoint's codec name and codec DAI name out of its [`dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107) into the codec component entry:

```c
/* sound/soc/intel/boards/sof_sdw.c:876 */
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
```

The codec name and DAI name in each endpoint trace back to [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), the per-part table keyed by SoundWire [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73). The [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) entry declares its three DAIs, one [`SOC_SDW_DAI_TYPE_JACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L41) headset interface, one [`SOC_SDW_DAI_TYPE_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L42) speaker interface, and one [`SOC_SDW_DAI_TYPE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L43) microphone interface, each with the per-direction back-end id it should claim:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:468 */
	{
		.part_id = 0x722,
		.name_prefix = "rt722",
		.version_id = 3,
		.dais = {
			{
				.direction = {true, true},
				.dai_name = "rt722-sdca-aif1",
				.dai_type = SOC_SDW_DAI_TYPE_JACK,
				.dailink = {SOC_SDW_JACK_OUT_DAI_ID, SOC_SDW_JACK_IN_DAI_ID},
				.init = asoc_sdw_rt_sdca_jack_init,
				...
			},
			...
		},
		.dai_num = 3,
	},
```

[`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) is the helper that writes the assembled arrays into the link, sets the matching counts, marks the link a back end through its [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) argument, and attaches the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702):

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

The single-codec form is [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320), which allocates one [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) each for the CPU, platform, and codec, fills the three names, and delegates to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293):

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

A link assembled this way names a SoundWire CPU DAI such as `"SDW0 Pin0"`, the codec DAI on the matched SoundWire device, and the SOF platform component, and sets [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) because a SoundWire link is a DPCM back end. The same resolution path that matches a statically declared link then matches the generated one, because by bind time both are ordinary [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) records with the same three component arrays.

```
    A codec name flows from the part table into codecs[]
    ──────────────────────────────────────────────────────

    codec_info_list[]  (keyed by SoundWire part_id)
    ┌────────────────────────────────────┐
    │ .part_id     = 0x722               │
    │ .name_prefix = "rt722"             │
    │ .dais[] ───────────────┐           │
    └────────────────────────┼───────────┘
                             ▼
    struct asoc_sdw_dai_info  (one codec DAI)
    ┌────────────────────────────────────┐
    │ .dai_name = "rt722-sdca-aif1"      │
    │ .dai_type = SOC_SDW_DAI_TYPE_JACK  │
    │ .dailink  = { out_id, in_id }      │
    └────────────────────┬───────────────┘
                         ▼  copied per endpoint by create_sdw_dailink()
    one codecs[] entry (struct snd_soc_dai_link_component)
    ┌────────────────────────────────────┐
    │ .name     = sof_end->codec_name    │
    │ .dai_name = dai_info->dai_name     │
    └────────────────────────────────────┘
```

### Three component sides of one back-end link

One [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) names a CPU side, a platform side, and a codec side through [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) entries that [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) resolves to the SOF DSP back-end DAI, the SOF PCI component, and the SDCA codec DAI.

```
    one struct snd_soc_dai_link (a SoundWire back-end link)
    ───────────────────────────────────────────────────────

        cpus[0]                platforms[0]           codecs[0]
    ┌──────────────┐        ┌──────────────┐        ┌──────────────────┐
    │ name  = NULL │        │ name  =      │        │ name  = "sdw:..."│
    │ dai_name =   │        │  "0000:00:   │        │ dai_name =       │
    │  "SDW0 Pin0" │        │   1f.3"      │        │  "rt722-sdca-    │
    │              │        │ dai_name=NULL│        │   aif1"          │
    └──────┬───────┘        └──────┬───────┘        └────────┬─────────┘
           ▼                       ▼                         ▼
     SOF DSP BE DAI         SOF PCI component         SDCA codec DAI
     (registered by         (the platform that        (registered by
      the SOF driver)        provides the PCM)         the SoundWire codec)
```
