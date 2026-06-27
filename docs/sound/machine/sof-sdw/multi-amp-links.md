# Multi-amplifier DAI links

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A speaker amplifier joins a card either as its own [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) whose single [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry names the amp DAI, or as several codecs on one link when more than one amp shares a SoundWire link. The shared-link case sets [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) greater than one, writes one [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) per amp with the same [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) but a distinct device [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), assigns each amp its channel with a [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696), and gives each amp a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) name prefix so the two amps' kcontrols and DAPM widgets stay distinct. Each amp's analog output is wired to the board speaker by a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) that the per-DAI [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callback adds with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272). The Cirrus [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) amplifier is the worked example.

```
    Two amplifiers on one SoundWire link
    ─────────────────────────────────────

    struct snd_soc_dai_link "SDW1-Playback"   (num_codecs = 2)
    ┌────────────────────────────────────────────────────────────┐
    │ cpus[0]   dai_name "SDW1 Pin2"      (num_cpus = 1)         │
    │ codecs[0] name "sdw:...:01" dai_name "cs35l56-sdw1"        │
    │ codecs[1] name "sdw:...:02" dai_name "cs35l56-sdw1"        │
    │ ch_maps[0] cpu=0 codec=0    ch_maps[1] cpu=0 codec=1       │
    └───────────────────────────────┬────────────────────────────┘
                                    │
        codec_conf[]                │  per-amp name prefix
        ┌────────────────────────┐  │
        │ dlc.name "sdw:...:01"  │ ─┼▶ widgets "AMP1 ..."
        │ name_prefix "AMP1"     │   │
        ├────────────────────────┤  │
        │ dlc.name "sdw:...:02"  │ ─┼▶ widgets "AMP2 ..."
        │ name_prefix "AMP2"     │   │
        └────────────────────────┘  │
                                    ▼
        dapm_routes added per amp by rtd_init:
          { "Speaker", NULL, "AMP1 SPK" }
          { "Speaker", NULL, "AMP2 SPK" }
```

## SUMMARY

An amplifier on its own SoundWire link is an ordinary [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with one [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry, built by the same [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) path that builds a jack codec link; the part is described in [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) by its SoundWire [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), and the [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) entry declares a playback amp DAI `"cs35l56-sdw1"` and a feedback-capture DAI `"cs35l56-sdw1c"` for its current and voltage monitor.

When two amplifiers share one SoundWire link they become a single [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) of two. [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) sizes the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array to the endpoint count, writes one component entry per amp with the same DAI name and a distinct device name, fills a [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) so each amp is fed the correct channel, and, for any endpoint that carries a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107), writes a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) entry. The core prepends that prefix to the amp's kcontrols and DAPM widgets, so two amps with the same DAI driver expose distinct `"AMP1 ..."` and `"AMP2 ..."` names. The path from each amp's analog output to the board speaker is a DAPM graph, and the per-DAI [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callback adds one route per amp with the matching prefix through [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272).

## SPECIFICATIONS

The [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) and the multi-codec link are Linux kernel software constructs and have no standalone hardware specification. The amplifiers ride the SoundWire bus handled by the kernel SoundWire core, and the [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) amplifier is programmed through its codec driver and regmap.

## LINUX KERNEL

### Multi-codec link types (soc.h)

- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one path; a multi-amp link sets [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) greater than one and points [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) at a per-codec channel map
- [`'\<struct snd_soc_dai_link_ch_map\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696): one entry per codec DAI, tying a [`cpu`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) index to a [`codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) index and a channel mask
- [`'\<struct snd_soc_codec_conf\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946): maps a codec component (its embedded [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946)) to a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) for control and widget naming
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) connecting two widget pins

### Builder and codec table (boards/sof_sdw.c, sdw_utils)

- [`'\<create_sdw_dailink\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876): build the link, size the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array to the endpoint count, fill [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and write the per-amp [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) prefixes
- [`'codec_info_list':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74): the per-part table whose [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) entry at part id 0x3556 declares the amp DAIs, controls, widgets, and routing callbacks
- [`'\<struct asoc_sdw_endpoint\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107): one DAI on one codec on one link, carrying the [`codec_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107) and the [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107) that becomes a [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) entry

### Per-amp routing (sdw_utils)

- [`'\<asoc_sdw_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918): the link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback that runs each codec DAI's widgets, controls, and [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) once
- [`'asoc_sdw_cs_spk_rtd_init':'sound/soc/sdw_utils/soc_sdw_cs_amp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38): the [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) speaker [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) that builds a `"<prefix> SPK"` route per amp
- [`'asoc_sdw_cs42l43_spk_rtd_init':'sound/soc/sdw_utils/soc_sdw_cs42l43.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l43.c#L108): the [`cs42l43`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l43.c) speaker [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) that adds the static [`cs42l43_spk_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l43.c#L32)
- [`'generic_spk_widgets':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L30): the single [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78) board "Speaker" widget the route map targets
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): add a batch of routes under the DAPM mutex

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver concept and the DAI link table
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget graph that the per-amp routes extend from each amp output to the board speaker
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where each amp link is a back end with [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) set
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the amp DAIs join

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A multi-amp link differs from a single-codec link only in the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array length, the [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array, and a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) per amp on the card. The codec_conf names a codec component through its embedded [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) and gives it a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) the core prepends to that component's controls and widgets.

```c
/* include/sound/soc.h:946 */
struct snd_soc_codec_conf {
	/*
	 * specify device either by device name, or by
	 * DT/OF node, but not both.
	 */
	struct snd_soc_dai_link_component dlc;

	/*
	 * optional map of kcontrol, widget and path name prefixes that are
	 * associated per device
	 */
	const char *name_prefix;
};
```

## DETAILS

### An amplifier is added as its own codec link

A speaker amplifier on its own SoundWire link is just another [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) whose [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry names the amp DAI. The [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) amplifier appears in [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) under part id 0x3556 with two DAIs, the playback amp DAI `"cs35l56-sdw1"` typed [`SOC_SDW_DAI_TYPE_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L42) and a separate feedback-capture DAI `"cs35l56-sdw1c"` for the current and voltage monitor, each claiming a different back-end id:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:573 */
	{
		.part_id = 0x3556,
		.name_prefix = "AMP",
		.dais = {
			{
				.direction = {true, false},
				.dai_name = "cs35l56-sdw1",
				.component_name = "cs35l56",
				.dai_type = SOC_SDW_DAI_TYPE_AMP,
				.dailink = {SOC_SDW_AMP_OUT_DAI_ID, SOC_SDW_UNUSED_DAI_ID},
				.init = asoc_sdw_cs_amp_init,
				.rtd_init = asoc_sdw_cs_spk_rtd_init,
				.controls = generic_spk_controls,
				.num_controls = ARRAY_SIZE(generic_spk_controls),
				.widgets = generic_spk_widgets,
				.num_widgets = ARRAY_SIZE(generic_spk_widgets),
			},
			{
				.direction = {false, true},
				.dai_name = "cs35l56-sdw1c",
				.dai_type = SOC_SDW_DAI_TYPE_AMP,
				.dailink = {SOC_SDW_UNUSED_DAI_ID, SOC_SDW_AMP_IN_DAI_ID},
				.rtd_init = asoc_sdw_cs_spk_feedback_rtd_init,
			},
		},
		.dai_num = 2,
	},
```

The same builder path that wired a jack codec wires the amp, because both reach [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) through the per-link loop. The difference is only in the data, the amp endpoint's [`dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107) carries `"cs35l56-sdw1"` as its [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) and a different back-end id, so it lands on its own [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) separate from the headset link.

```
    cs35l56 part (0x3556): two DAIs, opposite directions
    ──────────────────────────────────────────────────────

    codec_info_list[] entry .part_id = 0x3556  (.dais[], dai_num = 2)
    ┌──────────────────────────────┬──────────────────────────────┐
    │ .dais[0]                     │ .dais[1]                     │
    ├──────────────────────────────┼──────────────────────────────┤
    │ .dai_name "cs35l56-sdw1"     │ .dai_name "cs35l56-sdw1c"    │
    │ .direction {true,  false}    │ .direction {false, true}     │
    │   (playback amp)             │   (feedback capture)         │
    │ .dai_type AMP                │ .dai_type AMP                │
    └───────────────┬──────────────┴───────────────┬──────────────┘
                    ▼                               ▼
    .dailink = { AMP_OUT_DAI_ID,    .dailink = { UNUSED,
                 UNUSED }                        AMP_IN_DAI_ID }
    playback back-end link          capture back-end link
```

### Two amps on one link use num_codecs and codec_conf

When two amplifiers share a single SoundWire link they become one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) whose [`num_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is two. [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) sizes the [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array to the endpoint count and writes one [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) per amp, each with the same [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) but a distinct device [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), and fills a [`struct snd_soc_dai_link_ch_map`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L696) so each codec is fed the right channel:

```c
/* sound/soc/intel/boards/sof_sdw.c:876 */
		codec_maps[j].cpu = i - 1;
		codec_maps[j].codec = j;

		codecs[j].name = sof_end->codec_name;
		codecs[j].dai_name = sof_end->dai_info->dai_name;
		...
		j++;
```

Two amps with the same DAI driver would collide on control and widget names, so each amp endpoint that carries a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L107) gets a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) entry written at the top of the same builder loop:

```c
/* sound/soc/intel/boards/sof_sdw.c:876 */
	list_for_each_entry(sof_end, &sof_dai->endpoints, list) {
		if (sof_end->name_prefix) {
			(*codec_conf)->dlc.name = sof_end->codec_name;
			(*codec_conf)->name_prefix = sof_end->name_prefix;
			(*codec_conf)++;
		}
		...
	}
```

Each [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) names a codec component through its embedded [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) and supplies a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) the core prepends to that component's kcontrols and DAPM widgets, so the two amps expose distinct `"AMP1 ..."` and `"AMP2 ..."` widget names that the per-amp routes can reference.

### The board routing connects amp pins to the speaker

The codec and amp DAIs only carry the PCM stream onto the chip. The path from the chip's analog output to the board's speaker is a DAPM graph, and the machine layer extends that graph with [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) entries added through [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272). Each route is a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), an optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and a [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473):

```c
/* include/sound/soc-dapm.h:473 */
struct snd_soc_dapm_route {
	const char *sink;
	const char *control;
	const char *source;

	/* Note: currently only supported for links where source is a supply */
	int (*connected)(struct snd_soc_dapm_widget *source,
			 struct snd_soc_dapm_widget *sink);

	struct snd_soc_dobj dobj;
};
```

A codec with a fixed pin layout uses a static route array. The [`cs42l43`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l43.c) speaker map ties the board "Speaker" widget to the four analog amp output pins the codec exposes:

```c
/* sound/soc/sdw_utils/soc_sdw_cs42l43.c:32 */
static const struct snd_soc_dapm_route cs42l43_spk_map[] = {
	{ "Speaker", NULL, "cs42l43 AMP1_OUT_P", },
	{ "Speaker", NULL, "cs42l43 AMP1_OUT_N", },
	{ "Speaker", NULL, "cs42l43 AMP2_OUT_P", },
	{ "Speaker", NULL, "cs42l43 AMP2_OUT_N", },
};
```

The [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) amplifier builds its route at runtime instead, because the source widget name depends on the per-amp [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) that the [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) assigned. [`asoc_sdw_cs_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38) walks the codec DAIs of the link, composes the `"<prefix> SPK"` widget name, and adds one route from that widget to the board "Speaker", so a two-amp link yields one route per amp with the correct prefix on each:

```c
/* sound/soc/sdw_utils/soc_sdw_cs_amp.c:38 */
int asoc_sdw_cs_spk_rtd_init(struct snd_soc_pcm_runtime *rtd, struct snd_soc_dai *dai)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	char widget_name[16];
	struct snd_soc_dapm_route route = { "Speaker", NULL, widget_name };
	struct snd_soc_dai *codec_dai;
	int i, ret;

	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		if (!strstr(codec_dai->name, "cs35l56"))
			continue;

		snprintf(widget_name, sizeof(widget_name), "%s SPK",
			 codec_dai->component->name_prefix);

		ret = asoc_sdw_cs35l56_volume_limit(card, codec_dai->component->name_prefix);
		if (ret)
			return ret;

		ret = snd_soc_dapm_add_routes(dapm, &route, 1);
		if (ret)
			return ret;
	}

	return 0;
}
```

The "Speaker" sink is a board widget the codec info supplies through [`generic_spk_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L30), a single [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78) entry added before the per-DAI [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) runs:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:30 */
static const struct snd_soc_dapm_widget generic_spk_widgets[] = {
	SND_SOC_DAPM_SPK("Speaker", NULL),
};
```

That single Speaker widget is the sink the static map drives, each of the codec's four amp output pins wired to it by one fixed route:

```
    cs42l43_spk_map: four codec pins converge on one Speaker
    ──────────────────────────────────────────────────────────

    codec output pins (source)            board endpoint (sink)
    ┌──────────────────────┐
    │ "cs42l43 AMP1_OUT_P" │ ───┐
    └──────────────────────┘    │
    ┌──────────────────────┐    │
    │ "cs42l43 AMP1_OUT_N" │ ───┤
    └──────────────────────┘    │         ┌─────────────┐
    ┌──────────────────────┐    ├───────▶ │ "Speaker"   │
    │ "cs42l43 AMP2_OUT_P" │ ───┤         └─────────────┘
    └──────────────────────┘    │
    ┌──────────────────────┐    │
    │ "cs42l43 AMP2_OUT_N" │ ───┘
    └──────────────────────┘

    each row is one { "Speaker", NULL, "<pin>" } dapm_route,
    control = NULL is a fixed board wire
```

### The rtd_init callback runs once per codec DAI

The per-amp routes are added from the link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918), which the core invokes once per [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) after the DAIs are resolved. It walks the link's codec DAIs, adds each DAI's controls and widgets, and runs its [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) once, guarding repeats with a per-DAI flag:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:918 */
	for_each_rtd_codec_dais(rtd, i, dai) {
		...
		if (codec_info->dais[dai_index].rtd_init_done)
			continue;
		...
		if (codec_info->dais[dai_index].widgets) {
			ret = snd_soc_dapm_new_controls(dapm,
							codec_info->dais[dai_index].widgets,
							codec_info->dais[dai_index].num_widgets);
			if (ret)
				return ret;
		}

skip_add_controls_widgets:
		if (codec_info->dais[dai_index].rtd_init) {
			ret = codec_info->dais[dai_index].rtd_init(rtd, dai);
			if (ret)
				return ret;
		}
		...
		codec_info->dais[dai_index].rtd_init_done = true;
	}
```

For a two-amp link this loop visits each amp's codec DAI, so [`asoc_sdw_cs_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38) runs once and its inner [`for_each_rtd_codec_dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1455) loop composes a prefixed route for each amp, and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) installs each under the DAPM mutex:

```c
/* sound/soc/soc-dapm.c:3272 */
int snd_soc_dapm_add_routes(struct snd_soc_dapm_context *dapm,
			    const struct snd_soc_dapm_route *route, int num)
{
	int i, ret = 0;

	snd_soc_dapm_mutex_lock(dapm);
	for (i = 0; i < num; i++) {
		int r = snd_soc_dapm_add_route(dapm, route);
		if (r < 0)
			ret = r;
		route++;
	}
	snd_soc_dapm_mutex_unlock(dapm);

	return ret;
}
```
