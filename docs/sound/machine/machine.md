# ASoC machine driver

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The ASoC machine (or board) driver is the [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) driver whose probe assembles one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) from an array of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and hands it to [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65), the point at which the audio components a board carries (the CPU and platform DAIs the DSP exposes, the codecs on the bus, the DMA back end) are wired into one ALSA card. The machine driver owns the card object, the link array, the board routing in [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059), and any board kcontrols in [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050), while each codec and the platform stay separate components that register their own [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and bind to the card by name. On x86 ACPI the board is not enumerated from firmware directly; the Sound Open Firmware (SOF) probe runs [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489) to pick a [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) whose ACPI id is present and calls [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) to create the board device named by the descriptor's [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210). The Intel SOF SoundWire generic machine [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) is the worked example.

```
    ACPI namespace                         SOF probe (x86)
    ┌──────────────────────────┐           ┌──────────────────────────────┐
    │ device _HID "10508825"   │  present  │ hda_machine_select()         │
    │ (codec on SoundWire link)│ ────────▶ │   snd_soc_acpi_id_present()  │
    └──────────────────────────┘           │   pick snd_soc_acpi_mach     │
                                           │   read mach->drv_name        │
                                           │ sof_machine_register()       │
                                           └──────────────┬───────────────┘
                                                          │ platform_device
                                                          │ "sof_sdw", pdata
                                                          ▼
    machine driver  (struct platform_driver "sof_sdw")
    ┌────────────────────────────────────────────────────────────────────┐
    │ mc_probe(pdev)                                                     │
    │ mach = dev_get_platdata(&pdev->dev)                                │
    │ card = &ctx->card    card->dev = &pdev->dev                        │
    │                                                                    │
    │ struct snd_soc_card                                                │
    │   ┌─────────────────────────────────────────────────────────────┐  │
    │   │ name "soundwire"   owner   late_probe   add_dai_link        │  │
    │   │ dai_link  ──▶  struct snd_soc_dai_link [ num_links ]        │  │
    │   │                 ┌──────────────┬──────────────┬───────────┐ │  │
    │   │                 │ SDW BE link  │ DMIC BE link │ HDMI link │ │  │
    │   │                 │ cpus/codecs  │ cpus/codecs  │ ...       │ │  │
    │   │                 │ init  ops    │ init         │           │ │  │
    │   │                 └──────────────┴──────────────┴───────────┘ │  │
    │   │ codec_conf   aux_dev   controls   dapm_routes               │  │
    │   └─────────────────────────────────────────────────────────────┘  │
    │                                                                    │
    │ sof_card_dai_links_create(card)   build the link array             │
    │ devm_snd_soc_register_card(card->dev, card)  ──▶ ALSA card         │
    └────────────────────────────────────────────────────────────────────┘
```

## SUMMARY

A machine driver is a [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) driver whose probe fills one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), points [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032) at an array of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and sets [`card->num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033), then calls [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65). That helper wraps [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) with a [`devres_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L24) release, so the card is torn down when the platform device goes away, and [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) runs [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) to add the predefined links, create the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), probe every referenced component, run each link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback, add the board controls and routes, and register the sound card.

The role split is fixed. Each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) names its CPU side in [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), its codec side in [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and its DMA back end in [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), each a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that selects a component and one of its DAIs by name, so the machine driver only references components that other drivers register and never implements a codec or a DMA engine itself. The machine driver supplies the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callbacks, run by [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) and [`snd_soc_link_exit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L37), and an optional per-link [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) whose [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook programs the clock tree for a stream.

On x86 ACPI the SOF infrastructure selects the machine driver rather than a firmware node naming it. [`sof_machine_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L206) calls [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L564), which on Intel reaches [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489); the chosen [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) carries a [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) that names the board driver, and [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) creates the [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) with [`platform_device_register_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L215), passing the descriptor as platform data so the board probe reads it back with [`dev_get_platdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L1155). The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine registers one [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) named `"sof_sdw"`, and its [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) builds a card named `"soundwire"` whose links are generated by [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225), so one driver covers many boards.

## SPECIFICATIONS

The [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and the machine driver are Linux kernel software constructs and have no standalone hardware specification. The codecs the worked example wires together reach the host over SoundWire and the platform component over the DSP firmware interface, each handled by its own kernel subsystem; the firmware interface is described by the Sound Open Firmware project.

## LINUX KERNEL

### Card and link types (soc.h)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the board object the machine driver fills and registers; holds [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032), [`num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033), the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050), and the [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057)/[`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) board graph
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one PCM path; carries [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callbacks, the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer, and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) DPCM flag
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): selects one component and one of its DAIs by [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642)
- [`'\<struct snd_soc_ops\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623): the machine stream function pointer struct ([`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and the teardown duals) set on a link
- [`'\<struct snd_soc_codec_conf\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946): per-codec name-prefix configuration carried in [`card->codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<struct snd_soc_aux_dev\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960): auxiliary components (amplifiers) attached to the card without a PCM link
- [`'snd_soc_dummy_dlc':'sound/soc/soc-utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L258): the shared dummy component a link uses when one side has no real codec

### Card registration (soc-devres.c, soc-core.c)

- [`'\<devm_snd_soc_register_card\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65): device-managed card registration the machine probe calls
- [`'\<snd_soc_register_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557): validate, allocate the card DAPM context, initialise the lists and mutexes, then bind under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48)
- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): add the predefined links, create the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), probe components and DAIs, run link init, add controls and routes, register the sound card
- [`'\<snd_soc_card_set_drvdata\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100) / [`'\<snd_soc_card_get_drvdata\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L106): store and read the machine driver's private context on the card

### Per-link callbacks (soc-link.c)

- [`'\<snd_soc_link_init\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27): run a link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback when the runtime for that link is set up
- [`'\<snd_soc_link_exit\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L37): run a link's [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback during teardown

### ACPI machine selection (soc-acpi, sof)

- [`'\<struct snd_soc_acpi_mach\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210): ACPI-based board descriptor; its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is the matched codec ACPI id and its [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) names the board driver
- [`'\<snd_soc_acpi_find_machine\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34): walk a machine table and return the first whose ACPI id is present, applying [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)
- [`'\<sof_machine_check\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L206): the SOF probe step that selects a machine and records it in [`sof_pdata->machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L116)
- [`'\<hda_machine_select\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489): the Intel SOF machine selection that tries I2S/DMIC, then SoundWire, then the HDA generic fallback
- [`'\<sof_machine_register\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807): create the board [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) for [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), passing the descriptor as platform data

### sof_sdw worked example (intel/boards/sof_sdw.c)

- [`'sof_sdw_driver':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1538): the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) named `"sof_sdw"`, registered by [`module_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L289)
- [`'\<mc_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434): read the descriptor, set up the card, build the links, register the card
- [`'\<sof_card_dai_links_create\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225): allocate and fill the SDW, DMIC, HDMI, and BT back-end links from the descriptor

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver concept, the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and its DAI links
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the component model that splits the codec, platform, and machine drivers
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the routing the machine driver adds through [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059)
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where a SoundWire board's back-end links carry [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A machine driver fills the card object, builds the link array, and registers the card. The card object and the three component slots of each link are filled by the probe, and the registration call hands the result to the ASoC core.

| Element | Symbol | Role |
|---------|--------|------|
| card object | [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) | the board the driver fills and registers |
| link array | [`card->dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1032), [`card->num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1033) | the predefined PCM paths |
| one link | [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) | one path with cpus/codecs/platforms and init/ops |
| component ref | [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) | selects a component and DAI by name |
| stream ops | [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) | per-link machine hw_params/trigger hooks |
| board routing | [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) | board DAPM source-to-sink edges |
| register | [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) | bind and register the card |
| ACPI descriptor | [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) | selects the driver by [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) |
| create board device | [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) | spawn the board [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) |

## DETAILS

### The machine driver is a platform_device driver

The probe reads the matched descriptor from platform data, allocates a private context that embeds the card, fills the card and its link array, and registers the card. The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) probe shows the whole shape:

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
static int mc_probe(struct platform_device *pdev)
{
	struct snd_soc_acpi_mach *mach = dev_get_platdata(&pdev->dev);
	struct snd_soc_card *card;
	struct asoc_sdw_mc_private *ctx;
	struct intel_mc_ctx *intel_ctx;
	...
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

The card is embedded in `ctx` and reached with `card = &ctx->card`, and [`snd_soc_card_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100) stores the context back on the card so every callback recovers it with [`snd_soc_card_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L106), a one-line read of [`card->drvdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972):

```c
/* include/sound/soc-card.h:106 */
static inline void *snd_soc_card_get_drvdata(struct snd_soc_card *card)
{
	return card->drvdata;
}
```

This is how a per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) or an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook, given only a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) or a substream, reaches the machine driver's own context. It walks back to the card and reads the pointer the probe stored. The descriptor selected by ACPI arrives as platform data and is read once with [`dev_get_platdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L1155). The two card hooks set here are [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), which finishes SoundWire and HDMI bring-up after the components are up, and [`add_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), which the core calls for each link as it is added. The link array is generated by [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225), and the final [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) is the only registration call.

### devm_snd_soc_register_card binds and arranges teardown

[`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) registers the card and arranges that it is unregistered when the platform device is removed:

```c
/* sound/soc/soc-devres.c:65 */
int devm_snd_soc_register_card(struct device *dev, struct snd_soc_card *card)
{
	struct snd_soc_card **ptr;
	int ret;

	ptr = devres_alloc(devm_card_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_soc_register_card(card);
	if (ret == 0) {
		*ptr = card;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

[`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) rejects a card with no [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) or [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), allocates the card's DAPM context with [`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L168), initialises every list head and mutex, and binds the card under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) through [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163). The bind is the assembly stage. It binds the auxiliary devices, adds the predefined links as runtimes, creates the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), then probes components and runs the board hooks:

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
	/* bind aux_devs too */
	ret = soc_bind_aux_dev(card);
	if (ret < 0)
		goto probe_end;

	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;

	/* card bind complete so register a sound card */
	ret = snd_card_new(card->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
			card->owner, 0, &card->snd_card);
	if (ret < 0) {
		...
		goto probe_end;
	}
	...
```

The [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1062) step attaches the card's [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array of amplifier components, [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) turns each predefined link into a runtime, and [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) creates the underlying ALSA card. The remainder of the function probes components and runs the board hooks:

```c
/* sound/soc/soc-core.c:2163 */
	/* probe all components used by DAI links on this card */
	ret = soc_probe_link_components(card);
	...
	/* probe all DAI links on this card */
	ret = soc_probe_link_dais(card);
	...
	ret = snd_soc_add_card_controls(card, card->controls,
					card->num_controls);
	...
	ret = snd_soc_dapm_add_routes(dapm, card->dapm_routes,
				      card->num_dapm_routes);
	...
	ret = snd_soc_card_late_probe(card);
	...
	ret = snd_card_register(card->snd_card);
```

According to the comment "probe all components used by DAI links on this card", [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742) brings up the codec and platform components the links name, after which [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707) probes the DAIs and runs each link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback, then the board controls, routes, and [`late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) run before [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) makes the device nodes visible.

```
    snd_soc_bind_card() fixed assembly order
    ─────────────────────────────────────────

    ┌──────────────────────────────────────────────────────┐
    │ soc_bind_aux_dev()         bind aux_dev amplifiers   │
    ├──────────────────────────────────────────────────────┤
    │ snd_soc_add_pcm_runtimes() dai_link[] becomes rtds   │
    ├──────────────────────────────────────────────────────┤
    │ snd_card_new()             create struct snd_card    │
    ├──────────────────────────────────────────────────────┤
    │ soc_probe_link_components() codec + platform probe,  │
    │                             each adds its widgets    │
    ├──────────────────────────────────────────────────────┤
    │ soc_probe_link_dais()      probe DAIs, run link init │
    ├──────────────────────────────────────────────────────┤
    │ snd_soc_add_card_controls() add card->controls       │
    ├──────────────────────────────────────────────────────┤
    │ snd_soc_dapm_add_routes()  add card->dapm_routes     │
    ├──────────────────────────────────────────────────────┤
    │ snd_soc_card_late_probe()  board late_probe hook     │
    ├──────────────────────────────────────────────────────┤
    │ snd_card_register()        device nodes go visible   │
    └──────────────────────────────────────────────────────┘
       routes run last, so both endpoint and codec-pin widgets exist
```

### A link references components, it does not implement them

A link does not contain a codec or a DMA engine. It names them. Each side is a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) that selects a registered component by [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) and one of its DAIs by [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642):

```c
/* include/sound/soc.h:642 */
struct snd_soc_dai_link_component {
	const char *name;
	struct device_node *of_node;
	const char *dai_name;
	const struct of_phandle_args *dai_args;
	...
	unsigned int ext_fmt;
};
```

When one side of a link has no real device, the machine layer points it at the shared dummy component [`snd_soc_dummy_dlc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L258) so the link still resolves:

```c
/* sound/soc/soc-utils.c:258 */
struct snd_soc_dai_link_component snd_soc_dummy_dlc = {
	.of_node	= NULL,
	.dai_name	= "snd-soc-dummy-dai",
	.name		= "snd-soc-dummy",
};
EXPORT_SYMBOL_GPL(snd_soc_dummy_dlc);
```

The codec component and the platform component are registered by their own drivers and bind to the card by matching these names during [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742), which keeps the codec driver, the DMA/platform driver, and the machine driver as three separate components of one card.

```
    A link names three components other drivers register
    ─────────────────────────────────────────────────────

    struct snd_soc_dai_link   (machine driver fills the names)
    ┌─────────────────────────────────────────────────────┐
    │ cpus      -> dlc .name .dai_name                    │
    │ codecs    -> dlc .name .dai_name                    │
    │ platforms -> dlc .name .dai_name                    │
    └───────┬─────────────────────┬─────────────────────┬─┘
            │ match by name (soc_probe_link_components)
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │ CPU/DSP DAI   │     │ codec driver  │     │ platform/DMA  │
    │ component     │     │ component     │     │ component     │
    │ (SOF)         │     │ (rt722-sdca)  │     │ back end      │
    └───────────────┘     └───────────────┘     └───────────────┘
      a side with no real device points at snd_soc_dummy_dlc
```

### A link is a struct snd_soc_dai_link

The three component references sit inside one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the unit the machine driver fills per PCM path. The CPU, codec, and platform sides are each a counted array of [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), and the same struct carries the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callbacks, the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) pointer, and the DPCM flags:

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
	/* codec/machine specific init - e.g. add machine controls */
	int (*init)(struct snd_soc_pcm_runtime *rtd);

	/* codec/machine specific exit - dual of init() */
	void (*exit)(struct snd_soc_pcm_runtime *rtd);
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

The comment "config - must be set by machine driver" marks the contract. The board driver populates this array, and the ASoC core consumes it. The [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) flags select Dynamic PCM, where a SoundWire board marks its back-end links [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and its front-end links [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702).

Two further arrays on the card carry components that are not full PCM paths. A [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) attaches a name prefix to a codec so identically named controls on two codecs stay distinct:

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

A [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) attaches an auxiliary component, such as an amplifier, that the board uses without giving it a PCM link:

```c
/* include/sound/soc.h:960 */
struct snd_soc_aux_dev {
	/*
	 * specify multi-codec either by device name, or by
	 * DT/OF node, but not both.
	 */
	struct snd_soc_dai_link_component dlc;

	/* codec/machine specific init - e.g. add machine controls */
	int (*init)(struct snd_soc_component *component);
};
```

Both name a component through the same [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) embedded as [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946), and the card points [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) at arrays of them. The auxiliary array is bound at the start of [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) by [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1062).

```
    struct snd_soc_dai_link layout, with the two card side-arrays
    ──────────────────────────────────────────────────────────────

    struct snd_soc_dai_link
    ┌──────────────────────────────────────────────┐
    │ name  stream_name                            │
    │ cpus       *  + num_cpus       ─┐            │
    │ codecs     *  + num_codecs      ├ dlc arrays │
    │ platforms  *  + num_platforms  ─┘            │
    │ dai_fmt                                      │
    │ init()   exit()    (machine callbacks)       │
    │ ops *              (snd_soc_ops)             │
    │ no_pcm:1   dynamic:1   (DPCM flags)          │
    └──────────────────────────────────────────────┘

    card side-arrays (not PCM paths):
    ┌────────────────────────┐   ┌────────────────────────┐
    │ struct snd_soc_codec_  │   │ struct snd_soc_aux_dev │
    │   conf                 │   │   dlc  + init()        │
    │   dlc  + name_prefix   │   │   (amplifier, no PCM)  │
    └────────────────────────┘   └────────────────────────┘
       card->codec_conf[]            card->aux_dev[]
```

### The init and exit link callbacks

The machine driver attaches per-link setup to a link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback, which the core runs once the runtime for that link exists. [`snd_soc_link_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L27) is the single call site:

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

The dual is [`snd_soc_link_exit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L37), which runs the link's [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback during teardown and mirrors the init guard:

```c
/* sound/soc/soc-link.c:37 */
void snd_soc_link_exit(struct snd_soc_pcm_runtime *rtd)
{
	if (rtd->dai_link->exit)
		rtd->dai_link->exit(rtd);
}
```

An [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback receives the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) for its link and typically adds codec-specific kcontrols, sets a jack, or fixes a clock, so the board programs what is specific to that codec on that link without the codec driver knowing the board. The [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback releases whatever the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback set up, and on [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) it is the [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hooks that [`asoc_sdw_mc_dailink_exit_loop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c) drives when a failed [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) has to unwind a partially built card.

### The machine stream ops

A link may also carry a [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), set on [`dai_link->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), whose hooks run at PCM operation time:

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

The board uses the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hook to program the clock tree for a stream, for example to set the codec system clock or the bit-clock ratio once the rate and channel count are known. SoundWire back-end links generated by [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) leave [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) unset because the SoundWire bus carries clocking, while an I2S codec link sets it.

### On x86 ACPI an SOF descriptor selects the board

There is no firmware node on x86 that names a board driver, so the SOF probe discovers it. [`sof_machine_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L206) is the SOF probe step that calls [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L564) and stores the chosen descriptor in [`sof_pdata->machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L116):

```c
/* sound/soc/sof/core.c:206 */
static int sof_machine_check(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *sof_pdata = sdev->pdata;
	const struct sof_dev_desc *desc = sof_pdata->desc;
	struct snd_soc_acpi_mach *mach;
	...
		/* find machine */
		mach = snd_sof_machine_select(sdev);
		if (mach) {
			sof_pdata->machine = mach;
			...
			snd_sof_set_mach_params(mach, sdev);
			return 0;
		}
	...
nocodec:
	/* select nocodec mode */
	dev_warn(sdev->dev, "Using nocodec machine driver\n");
	mach = devm_kzalloc(sdev->dev, sizeof(*mach), GFP_KERNEL);
	if (!mach)
		return -ENOMEM;

	mach->drv_name = "sof-nocodec";
	...
	sof_pdata->machine = mach;
	snd_sof_set_mach_params(mach, sdev);

	return 0;
}
```

When no descriptor matches and the nocodec build is configured, the `nocodec` tail synthesises a fallback descriptor whose [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is `"sof-nocodec"`, so the probe always ends with a board driver name to register. On Intel [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L564) reaches [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489), which tries I2S/DMIC, then SoundWire, then the HDA generic fallback:

```c
/* sound/soc/sof/intel/hda.c:1489 */
struct snd_soc_acpi_mach *hda_machine_select(struct snd_sof_dev *sdev)
{
	u32 interface_mask = hda_get_interface_mask(sdev);
	struct snd_sof_pdata *sof_pdata = sdev->pdata;
	const struct sof_dev_desc *desc = sof_pdata->desc;
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct snd_soc_acpi_mach *mach = NULL;
	...
	/* Try I2S or DMIC if it is supported */
	if (interface_mask & (BIT(SOF_DAI_INTEL_SSP) | BIT(SOF_DAI_INTEL_DMIC))) {
		mach = snd_soc_acpi_find_machine(desc->machines);
		if (mach)
			i2s_mach_found = true;
	}

	/*
	 * If I2S fails and no external HDaudio codec is detected,
	 * try SoundWire if it is supported
	 */
	if (!mach && !HDA_EXT_CODEC(bus->codec_mask) &&
	    (interface_mask & BIT(SOF_DAI_INTEL_ALH))) {
		mach = hda_sdw_machine_select(sdev);
		if (mach)
			sdw_mach_found = true;
	}

	/*
	 * Choose HDA generic machine driver if mach is NULL.
	 * Otherwise, set certain mach params.
	 */
	hda_generic_machine_select(sdev, &mach);
	if (!mach) {
		dev_warn(sdev->dev, "warning: No matching ASoC machine driver found\n");
		return NULL;
	}
	...
	return mach;
}
```

The I2S and DMIC path matches a table entry with [`snd_soc_acpi_find_machine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34), which returns the first descriptor whose ACPI id is present:

```c
/* sound/soc/soc-acpi.c:34 */
struct snd_soc_acpi_mach *
snd_soc_acpi_find_machine(struct snd_soc_acpi_mach *machines)
{
	struct snd_soc_acpi_mach *mach;
	struct snd_soc_acpi_mach *mach_alt;

	for (mach = machines; mach->id[0] || mach->comp_ids; mach++) {
		if (snd_soc_acpi_id_present(mach)) {
			if (mach->machine_quirk) {
				mach_alt = mach->machine_quirk(mach);
				if (!mach_alt)
					continue; /* not full match, ignore */
				mach = mach_alt;
			}

			return mach;
		}
	}
	return NULL;
}
```

The presence test [`snd_soc_acpi_id_present()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L11) checks the descriptor's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and each entry of its [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) list with [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956), and the SoundWire path matches a board against the enumerated link mask through [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296).

```
    hda_machine_select() tries interfaces in order, picks one drv_name
    ──────────────────────────────────────────────────────────────────

    interface_mask has SSP/DMIC ?
    ┌───────────────────────────────────────┐ matched
    │ snd_soc_acpi_find_machine(machines)   │ ─────▶ mach (I2S/DMIC)
    └───────────────────┬───────────────────┘
                        │ no match and no external HDA codec
                        ▼
    interface_mask has ALH (SoundWire) ?
    ┌───────────────────────────────────────┐ matched
    │ hda_sdw_machine_select()              │ ─────▶ mach (SoundWire)
    └───────────────────┬───────────────────┘
                        │ still no match
                        ▼
    ┌───────────────────────────────────────┐ matched
    │ hda_generic_machine_select()          │ ─────▶ mach (HDA generic)
    └───────────────────┬───────────────────┘
                        │ none, and nocodec build configured
                        ▼
    ┌───────────────────────────────────────┐
    │ synthesised mach, drv_name            │ ─────▶ "sof-nocodec"
    └───────────────────────────────────────┘
       the chosen mach->drv_name is the platform_device name to spawn
```

### sof_machine_register creates the board platform_device

Once a [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is chosen, its [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) names the board driver, and [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) creates the matching [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23), passing the descriptor as platform data:

```c
/* sound/soc/sof/core.c:807 */
int sof_machine_register(struct snd_sof_dev *sdev, void *pdata)
{
	struct snd_sof_pdata *plat_data = pdata;
	const char *drv_name;
	const void *mach;
	int size;

	drv_name = plat_data->machine->drv_name;
	mach = plat_data->machine;
	size = sizeof(*plat_data->machine);

	/* register machine driver, pass machine info as pdata */
	plat_data->pdev_mach =
		platform_device_register_data(sdev->dev, drv_name,
					      PLATFORM_DEVID_NONE, mach, size);
	if (IS_ERR(plat_data->pdev_mach))
		return PTR_ERR(plat_data->pdev_mach);
	...
	return 0;
}
```

The [`platform_device_register_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L215) call creates a device named by [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), and the driver core then matches it to the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) of the same name and runs that driver's probe. For a SoundWire board that name is `"sof_sdw"`.

### sof_sdw registers one platform_driver for many boards

The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) module registers exactly one driver, matched on the device name `"sof_sdw"`:

```c
/* sound/soc/intel/boards/sof_sdw.c:1532 */
static const struct platform_device_id mc_id_table[] = {
	{ "sof_sdw", },
	{}
};
MODULE_DEVICE_TABLE(platform, mc_id_table);

static struct platform_driver sof_sdw_driver = {
	.driver = {
		.name = "sof_sdw",
		.pm = &snd_soc_pm_ops,
	},
	.probe = mc_probe,
	.remove = mc_remove,
	.id_table = mc_id_table,
};

module_platform_driver(sof_sdw_driver);
```

One driver serves many boards because the card is built at runtime from a descriptor table. The descriptor selected by ACPI describes the SoundWire links and codecs present, [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) runs [`dmi_check_system()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmi.h#L100) over [`sof_sdw_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L58) to adjust the layout for specific machines, and [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) turns the descriptor and quirks into the link array the card registers.
