# sof_sdw link construction

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) builds the variable set of DAI links a SoundWire board needs by counting the endpoints of five categories (SoundWire codecs, SSP/I2S codecs, onboard PCH digital microphones, HDMI/iDisp displays, and Bluetooth), allocating one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array sized to their sum, and dispatching one builder per category. The SoundWire back ends come from [`create_sdw_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023) over [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876), the onboard microphones from [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092), and the displays from [`create_hdmi_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1122), each advancing a shared cursor through the array and assigning the next back-end id. The card's [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) hook [`sof_sdw_add_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1421) then marks an HDMI link [`ignore`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) when the board has no display codec, so the same generated table covers boards with and without HDMI.

```
    sof_card_dai_links_create(): one link array, five categories
    ─────────────────────────────────────────────────────────────

    num_links = sdw_be_num + ssp_num + dmic_num + hdmi_num + bt_num + 1

    ┌───────────────┬────────┬───────────┬───────────┬────────┐
    │ SoundWire BE  │  SSP   │   DMIC    │  iDisp    │   BT   │
    │               │ (I2S)  │  (PCH)    │  (HDMI)   │        │
    ├───────────────┼────────┼───────────┼───────────┼────────┤
    │ create_sdw_   │  ...   │ create_   │ create_   │  ...   │
    │ dailinks()    │        │ dmic_     │ hdmi_     │        │
    │               │        │ dailinks  │ dailinks  │        │
    └───────┬───────┴────────┴─────┬─────┴─────┬─────┴────────┘
            │                      │           │
            ▼                      ▼           ▼
      *dai_links advances; each builder assigns the next be_id
      via asoc_sdw_init_dai_link() / asoc_sdw_init_simple_dai_link()
```

## SUMMARY

The board's link table is generated rather than declared, because the set of codecs, amplifiers, microphones, and displays varies per machine. [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) first counts each category. The SoundWire count comes from [`asoc_sdw_count_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348) parsing the descriptor's [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210); the DMIC, HDMI, and BT counts come from the [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and the resolved quirks. It then allocates the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) and [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) arrays with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L61), points [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) and [`card->num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033) at it, and calls the per-category builders in order.

Each builder fills one or more links and advances the shared `**dai_links` cursor and `*be_id` counter, so the categories occupy contiguous regions of one array with monotonic back-end ids. The SoundWire builder [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) builds a playback and a capture back-end link per SoundWire link from the endpoint list; the microphone builder [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) builds the two PCH PDM links `dmic01` and `dmic16k`; the display builder [`create_hdmi_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1122) builds one iDisp link per HDMI port, pointing each at the HDA HDMI codec or at the dummy component when no display codec is present. All three of the simple categories delegate to [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320), and the SoundWire category delegates to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293).

## SPECIFICATIONS

The link-construction helpers are Linux kernel software constructs and have no standalone hardware specification. The SoundWire endpoints they enumerate come from the ACPI `_ADR` descriptors the platform reports, and the PCH digital-microphone and iDisp HDMI links are properties of the Intel controller, handled by the kernel SoundWire and HD-audio cores.

## LINUX KERNEL

### Top-level builder and counting (boards/sof_sdw.c, sdw_utils)

- [`'\<sof_card_dai_links_create\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225): count the five categories, allocate the link and [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) arrays, point the card at them, and dispatch the per-category builders
- [`'\<asoc_sdw_count_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348): count the SoundWire devices and links from the descriptor's [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) array
- [`'\<asoc_sdw_parse_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489): group the endpoints into the per-link [`struct asoc_sdw_dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119) records the SoundWire builder iterates

### Per-category builders (boards/sof_sdw.c)

- [`'\<create_sdw_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023): loop over each populated SoundWire link and call the per-link builder
- [`'\<create_sdw_dailink\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876): build the playback and capture back-end links for one SoundWire link, then hand off to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293)
- [`'\<create_dmic_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092): build the two PCH PDM links `dmic01` and `dmic16k`, the first passing [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) as its init
- [`'\<create_hdmi_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1122): build one iDisp link per HDMI port, the first passing [`sof_sdw_hdmi_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw_hdmi.c) as its init
- [`'\<sof_sdw_add_dai_link\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1421): the card's [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) hook that ignores an HDMI link when no iDisp codec is present

### DAI-link fillers (sdw_utils)

- [`'\<asoc_sdw_init_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293): fill one link from component arrays, used by the SoundWire builder
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): fill one link from name strings, used by the DMIC and HDMI builders
- [`'\<struct asoc_sdw_dailink\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119): the per-link grouping with [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119), [`num_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119), and the [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119) list the SoundWire builder walks

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver concept and the DAI link table
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where every generated link is a back end with [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) set
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the SoundWire back-end links drive
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the Intel controller that hosts the SoundWire, PCH DMIC, and iDisp links

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The builders share a calling convention so a single pass fills one array. Each takes the card, a pointer to the running `**dai_links` cursor, and a pointer to the `*be_id` counter, fills its links, advances the cursor past them, and returns. The counts that size the array are computed first, so the cursor never runs past the allocation.

| Category | Builder | Filler | Links produced |
|----------|---------|--------|----------------|
| SoundWire | [`create_sdw_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023) | [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) | one per direction per link |
| PCH DMIC | [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) | [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) | `dmic01`, `dmic16k` |
| HDMI | [`create_hdmi_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1122) | [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) | one per iDisp port |

## DETAILS

### The platform data drives the link array

The sof_sdw platform device carries a [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) as its platform data, whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L211) holds the codec ACPI id used for an I2S match, whose [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L215) points at the [`struct snd_soc_acpi_link_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) array of SoundWire links, and whose [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L224) carries the codec mask and the DMIC and Bluetooth counts. [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) reads that platform data, groups the SoundWire endpoints into per-link records through [`asoc_sdw_parse_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489), and runs the per-category builders that fill [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032).

```
    snd_soc_acpi_mach (platform data on the sof_sdw pdev)
    ┌────────────────────────────────────────────────────────────┐
    │  id[ACPI_ID_LEN]   (codec ACPI id, used for I2S match)     │
    │  mach_params.links ─▶ snd_soc_acpi_link_adr[] (SDW links)  │
    │  mach_params.codec_mask, dmic_num, bt_link_mask            │
    └──────────────────────────────┬─────────────────────────────┘
                                   │  sof_card_dai_links_create()
                                   ▼
        ┌───────────────────────────────────────────────────┐
        │  asoc_sdw_parse_sdw_endpoints() builds            │
        │  asoc_sdw_dailink[] from the _ADR descriptors,    │
        │  each endpoint matched to a codec_info_list entry │
        └───────┬───────────────┬──────────────────┬────────┘
                ▼               ▼                  ▼
        create_sdw_dailink  create_dmic_      create_hdmi_
        (per SDW link)      dailinks          dailinks
                │               │                  │
                └───────────────┼──────────────────┘
                                ▼
                       card->dai_link[ ]
                  (BE links: SDW, DMIC, HDMI, BT, echo-ref)
```

### Counting and sizing the array

[`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) computes the category counts, sizes the link array as their sum, allocates it from device-managed memory, and points the card at it before any builder runs. Assigning [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) and [`card->num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033) is the moment the freshly allocated array becomes the card's link set:

```c
/* sound/soc/intel/boards/sof_sdw.c:1225 */
static int sof_card_dai_links_create(struct snd_soc_card *card)
{
	struct device *dev = card->dev;
	struct snd_soc_acpi_mach *mach = dev_get_platdata(card->dev);
	int sdw_be_num = 0, ssp_num = 0, dmic_num = 0, bt_num = 0;
	...
	struct snd_soc_dai_link *dai_links;
	int num_links;
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
	card->aux_dev = sof_aux;
	card->num_aux_devs = num_aux;

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

The SoundWire region is built first by [`create_sdw_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1023), which loops over each populated [`struct asoc_sdw_dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L119) and calls [`create_sdw_dailink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L876) once per SoundWire link to fill the playback and capture back ends. Each call advances the `**dai_links` cursor, so the next category begins where the SoundWire region ends.

```
    card->dai_link[] one array, contiguous category regions
    ─────────────────────────────────────────────────────────

    num_links = sdw_be_num + ssp_num + dmic_num + hdmi_num
                + bt_num + 1

      region    builder                filler
    ┌─────────┬──────────────────────┬───────────────────────────────┐
    │ SDW BE  │ create_sdw_dailinks  │ asoc_sdw_init_dai_link        │
    ├─────────┼──────────────────────┼───────────────────────────────┤
    │ SSP     │ (I2S codec)          │ asoc_sdw_init_simple_dai_link │
    ├─────────┼──────────────────────┼───────────────────────────────┤
    │ DMIC    │ create_dmic_dailinks │ asoc_sdw_init_simple_dai_link │
    ├─────────┼──────────────────────┼───────────────────────────────┤
    │ HDMI    │ create_hdmi_dailinks │ asoc_sdw_init_simple_dai_link │
    ├─────────┼──────────────────────┼───────────────────────────────┤
    │ BT      │ (bt offload)         │ asoc_sdw_init_simple_dai_link │
    ├─────────┼──────────────────────┼───────────────────────────────┤
    │ echoref │ +1 trailing slot     │                               │
    └─────────┴──────────────────────┴───────────────────────────────┘

    one **dai_links cursor sweeps left to right;
    *be_id is assigned then post-incremented per link,
    so back-end ids increase monotonically across regions
```

### The PCH digital-microphone links

The onboard digital microphones are an Intel PCH PDM block rather than a SoundWire device, so they get their own fixed pair of links. [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) builds `dmic01` and `dmic16k`, both capture-only, both naming the generic `dmic-codec`, with only the first passing [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) so the shared microphone setup runs once:

```c
/* sound/soc/intel/boards/sof_sdw.c:1092 */
static int create_dmic_dailinks(struct snd_soc_card *card,
				struct snd_soc_dai_link **dai_links, int *be_id)
{
	struct device *dev = card->dev;
	int ret;

	ret = asoc_sdw_init_simple_dai_link(dev, *dai_links, be_id, "dmic01",
					    0, 1, // DMIC only supports capture
					    "DMIC01 Pin", "dummy",
					    "dmic-codec", "dmic-hifi", 1,
					    asoc_sdw_dmic_init, NULL);
	if (ret)
		return ret;

	(*dai_links)++;

	ret = asoc_sdw_init_simple_dai_link(dev, *dai_links, be_id, "dmic16k",
					    0, 1, // DMIC only supports capture
					    "DMIC16k Pin", "dummy",
					    "dmic-codec", "dmic-hifi", 1,
					    /* don't call asoc_sdw_dmic_init() twice */
					    NULL, NULL);
	if (ret)
		return ret;

	(*dai_links)++;

	return 0;
}
```

According to the comment "don't call asoc_sdw_dmic_init() twice", the `dmic16k` link passes a NULL init so the second link reuses the microphone setup the first installed rather than repeating it. The platform side is the dummy component because the SOF platform component is attached to these links elsewhere by the core.

```
    create_dmic_dailinks: two fixed PCH PDM links (capture only)
    ──────────────────────────────────────────────────────────

    ┌─────────┬─────────────┬────────────────────────┬────────────────────┐
    │ link    │ cpu DAI     │ codec / DAI            │ init               │
    ├─────────┼─────────────┼────────────────────────┼────────────────────┤
    │ dmic01  │ DMIC01 Pin  │ dmic-codec / dmic-hifi │ asoc_sdw_dmic_init │
    │ dmic16k │ DMIC16k Pin │ dmic-codec / dmic-hifi │ NULL  (skip 2nd)   │
    └─────────┴─────────────┴────────────────────────┴────────────────────┘

    platform = dummy on both; only dmic01 passes the init,
    so asoc_sdw_dmic_init runs once for the pair
```

### The HDMI display links

A board's HDMI outputs are presented by the on-die HDA display codec, so [`create_hdmi_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1122) builds one playback-only iDisp link per port. When the display codec was enumerated it points each link at `ehdaudio0D2` with a per-port `intel-hdmi-hifi%d` DAI, and when it was not it points at the dummy component so the link still resolves and is later ignored:

```c
/* sound/soc/intel/boards/sof_sdw.c:1122 */
static int create_hdmi_dailinks(struct snd_soc_card *card,
				struct snd_soc_dai_link **dai_links, int *be_id,
				int hdmi_num)
{
	struct device *dev = card->dev;
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	struct intel_mc_ctx *intel_ctx = (struct intel_mc_ctx *)ctx->private;
	int i, ret;

	for (i = 0; i < hdmi_num; i++) {
		char *name = devm_kasprintf(dev, GFP_KERNEL, "iDisp%d", i + 1);
		char *cpu_dai_name = devm_kasprintf(dev, GFP_KERNEL, "iDisp%d Pin", i + 1);
		...
		char *codec_name, *codec_dai_name;

		if (intel_ctx->hdmi.idisp_codec) {
			codec_name = "ehdaudio0D2";
			codec_dai_name = devm_kasprintf(dev, GFP_KERNEL,
							"intel-hdmi-hifi%d", i + 1);
		} else {
			codec_name = "snd-soc-dummy";
			codec_dai_name = "snd-soc-dummy-dai";
		}
		...
		ret = asoc_sdw_init_simple_dai_link(dev, *dai_links, be_id, name,
						    1, 0, // HDMI only supports playback
						    cpu_dai_name, "dummy",
						    codec_name, codec_dai_name, 1,
						    i == 0 ? sof_sdw_hdmi_init : NULL, NULL);
		if (ret)
			return ret;

		(*dai_links)++;
	}

	return 0;
}
```

Only the first iDisp link passes [`sof_sdw_hdmi_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw_hdmi.c) so the shared HDMI jack setup runs once, the same one-shot pattern the microphone links use.

```
    create_hdmi_dailinks: one iDisp link per port i (0..hdmi_num-1)
    ────────────────────────────────────────────────────────────

    per port i:  name        = iDisp(i+1)
                 cpu DAI     = iDisp(i+1) Pin
                 init        = (i == 0) ? sof_sdw_hdmi_init : NULL

    codec target depends on idisp_codec:
    ┌───────────────────────────────┐   ┌────────────────────────────┐
    │ idisp_codec present           │   │ idisp_codec absent         │
    │ codec  = ehdaudio0D2          │   │ codec  = snd-soc-dummy     │
    │ DAI    = intel-hdmi-hifi(i+1) │   │ DAI    = snd-soc-dummy-dai │
    └───────────────────────────────┘   └────────────────────────────┘

    absent branch links still built, then dropped by
    sof_sdw_add_dai_link (ignore = true)
```

### Ignoring HDMI when no display codec is present

When the display codec was absent and the HDMI links were built against the dummy component, the card's [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1024) hook removes them from the card. [`sof_sdw_add_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1421) runs as each runtime is created and sets [`ignore`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) on a link whose stream name contains "HDMI" when no iDisp codec exists:

```c
/* sound/soc/intel/boards/sof_sdw.c:1421 */
static int sof_sdw_add_dai_link(struct snd_soc_card *card,
				struct snd_soc_dai_link *link)
{
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	struct intel_mc_ctx *intel_ctx = (struct intel_mc_ctx *)ctx->private;

	/* Ignore the HDMI PCM link if iDisp is not present */
	if (strstr(link->stream_name, "HDMI") && !intel_ctx->hdmi.idisp_codec)
		link->ignore = true;

	return 0;
}
```

Building the link unconditionally and ignoring it at runtime keeps the count and the cursor arithmetic in [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) the same on boards with and without a display codec, so the array size does not depend on the display being present.

### Platform-data descriptor feeding the dai-link build

The [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) attached as platform data carries the codec ACPI id and the [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) SoundWire link descriptors that [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) translates (through [`asoc_sdw_parse_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489) and the per-class link builders) into the back-end entries of [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972).

```
    snd_soc_acpi_mach (platform data on the sof_sdw pdev)
    ┌───────────────────────────────────────────────────────────┐
    │  id[ACPI_ID_LEN]   (codec ACPI id, used for I2S match)    │
    │  mach_params.links ─▶ snd_soc_acpi_link_adr[] (SDW links) │
    │  mach_params.codec_mask, dmic_num, bt_link_mask           │
    └──────────────────────────────┬────────────────────────────┘
                                   │  sof_card_dai_links_create()
                                   ▼
        ┌───────────────────────────────────────────────────┐
        │  asoc_sdw_parse_sdw_endpoints() builds            │
        │  asoc_sdw_dailink[] from the _ADR descriptors,    │
        │  each endpoint matched to a codec_info_list entry │
        └───────┬───────────────┬──────────────────┬────────┘
                ▼               ▼                  ▼
        create_sdw_dailink  create_dmic_      create_hdmi_
        (per SDW link)      dailinks          dailinks
                │               │                  │
                └───────────────┴──────────────────┘
                                ▼
                       card->dai_link[ ]
                  (BE links: SDW, DMIC, HDMI, BT, echo-ref)
```
