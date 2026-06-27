# sof_sdw platform driver

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) is one [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) matched on the device name `"sof_sdw"` that builds a SoundWire card named `"soundwire"` for many laptops. Its [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) reads the [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) descriptor SOF passed as platform data, resolves a per-board quirk word from three sources, counts the speaker amplifiers the board carries, builds the link array, and registers the card with [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65). The quirk word [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43) is set from a DMI match through [`dmi_check_system()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmi.h#L100) over [`sof_sdw_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L58), refined from the PCI subsystem id through [`sof_sdw_check_ssid_quirk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L853), and overridable by the `quirk_override` module parameter, so one driver adapts to each machine's mic and speaker layout from data rather than per-board code. The driver runs entirely on x86 ACPI platforms, where SOF selects it and spawns its device.

```
    Board identity resolved into one quirk word (sof_sdw_quirk)
    ───────────────────────────────────────────────────────────

    DMI match      ─▶ dmi_check_system(sof_sdw_quirk_table)
                        sof_sdw_quirk_cb() sets sof_sdw_quirk
    PCI SSID       ─▶ sof_sdw_check_ssid_quirk()
                        looks up sof_sdw_ssid_quirk_table
    module param   ─▶ quirk_override  (when != -1, overrides all)

                            │
                            ▼
                     sof_sdw_quirk  (unsigned long bitmask)
                            │
                            ▼
              sof_card_dai_links_create() shapes the link array
```

## SUMMARY

The driver is registered by [`module_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L289) with a [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) whose [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1532) holds the single entry `"sof_sdw"`, so the driver core binds it to the [`platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) that [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) created for the matched descriptor. [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) allocates the board context [`struct asoc_sdw_mc_private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131) with its embedded [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), records the [`intel_mc_ctx`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.h) private pointer, sets the card name and the two card hooks, stores the context with [`snd_soc_card_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100), and resolves the quirks before it builds links.

The quirk word governs the board layout. [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) calls [`snd_soc_card_set_pci_ssid()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h) when the descriptor carries a subsystem id, then [`sof_sdw_check_ssid_quirk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L853) and [`dmi_check_system()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmi.h#L100), and applies the `quirk_override` module parameter last. After [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) builds the links, the probe sums the [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) counters that the per-amp [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callbacks incremented across [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), writes the count into the card's [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) string for userspace, and registers the card. On removal, [`mc_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1525) runs each codec DAI's exit through [`asoc_sdw_mc_dailink_exit_loop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1244).

## SPECIFICATIONS

The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) platform driver is a Linux kernel software construct and has no standalone hardware specification. It targets x86 ACPI platforms, where the board is selected by [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) matching and the codecs ride on SoundWire, handled by the kernel SoundWire core.

## LINUX KERNEL

### Platform driver and probe (boards/sof_sdw.c)

- [`'sof_sdw_driver':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1538): the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234), registered by [`module_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L289), with [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434), [`mc_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1525), and the [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c) suspend/resume hooks
- [`'mc_id_table':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1532): the [`struct platform_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L611) table with the single name `"sof_sdw"` the driver core matches
- [`'\<mc_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434): allocate the context, set up the card, resolve quirks, build links, register the card
- [`'\<mc_remove\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1525): run the per-link codec exits at teardown through [`asoc_sdw_mc_dailink_exit_loop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1244)
- [`'\<MODULE_IMPORT_NS\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1556): import the [`SND_SOC_SDW_UTILS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L831) namespace so the driver can call the utilities

### Quirk resolution (boards/sof_sdw.c)

- [`'sof_sdw_quirk':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43): the module-global bitmask describing the board layout (mic source, speaker presence, jack-detect mode)
- [`'sof_sdw_quirk_table':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L58): the [`struct dmi_system_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L632) table matching a board by vendor and SKU
- [`'\<sof_sdw_quirk_cb\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L52): the DMI callback that writes the matched entry's [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L632) into [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43)
- [`'\<sof_sdw_check_ssid_quirk\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L853): look up the PCI subsystem id in [`sof_sdw_ssid_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L832) with [`snd_pci_quirk_lookup_id()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h) and set [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43)
- [`'sof_sdw_ssid_quirk_table':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L832): the [`struct snd_pci_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h) table keyed by PCI subsystem vendor and device

### Card context and identity (boards/sof_sdw.c, sof_sdw.h)

- [`'\<struct asoc_sdw_mc_private\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131): the board context with the embedded [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), the [`codec_info_list_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131), the [`mc_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131) snapshot, and the [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131) platform pointer
- [`'\<snd_soc_card_set_pci_ssid\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h): record the PCI subsystem vendor and device on the card so the longname carries the board id
- [`'\<snd_soc_card_set_drvdata\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L100): store the board context on the card for every callback to recover
- [`'\<asoc_sdw_get_codec_info_list_count\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L833): the count [`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) loops over to sum [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) and build the components string

### Link building and teardown (boards/sof_sdw.c, sdw_utils)

- [`'\<sof_card_dai_links_create\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225): the link-array builder the probe calls after the quirks are resolved
- [`'\<asoc_sdw_mc_dailink_exit_loop\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1244): run each matched codec DAI's [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) during remove or after a failed register

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver concept this platform driver implements
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the SoundWire links the driver builds are back ends
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the built links drive
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how the board's PCI SSID and ACPI ids reach the driver

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The driver's interface to the rest of the stack is the platform-device name and the descriptor it receives as platform data. The driver core binds the device named `"sof_sdw"` to this driver, the probe reads the [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) with [`dev_get_platdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L1155), and everything else the board needs is derived from that descriptor, the DMI strings, and the PCI subsystem id.

| Source | Symbol | Drives |
|--------|--------|--------|
| platform-device name | [`mc_id_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1532) | which device binds this driver |
| platform data | [`dev_get_platdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L1155) | the matched [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) |
| DMI strings | [`sof_sdw_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L58) | per-board [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43) bits |
| PCI SSID | [`sof_sdw_check_ssid_quirk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L853) | refine [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43) |
| module param | `quirk_override` | force [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43) |
| amp counters | [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) | the card [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) string |

## DETAILS

### The probe builds one card for many boards

[`mc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434) allocates two contexts, the Intel-private [`intel_mc_ctx`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.h) and the generic [`struct asoc_sdw_mc_private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131) whose embedded [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) it fills, then records the codec table size, the card name, and the two card hooks before resolving quirks:

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
static int mc_probe(struct platform_device *pdev)
{
	struct snd_soc_acpi_mach *mach = dev_get_platdata(&pdev->dev);
	struct snd_soc_card *card;
	struct asoc_sdw_mc_private *ctx;
	struct intel_mc_ctx *intel_ctx;
	int amp_num = 0, i;
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

	if (mach->mach_params.subsystem_id_set) {
		snd_soc_card_set_pci_ssid(card,
					  mach->mach_params.subsystem_vendor,
					  mach->mach_params.subsystem_device);
		sof_sdw_check_ssid_quirk(mach);
	}

	dmi_check_system(sof_sdw_quirk_table);
	...
```

The card name is the fixed string `"soundwire"`, and the per-board identity is carried instead by the PCI subsystem id (recorded with [`snd_soc_card_set_pci_ssid()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h)) and the resolved quirk word, so the same driver presents the same card name on every machine while shaping its links differently.

```
    One probe context wraps the card and the per-board state
    ──────────────────────────────────────────────────────────

    ┌────────────────────────────────────────────────────┐
    │ struct asoc_sdw_mc_private  (ctx)                  │
    │                                                    │
    │   card                  ◀── embedded snd_soc_card  │
    │     .name = "soundwire"     (fixed on every board) │
    │     .dev  = &pdev->dev                             │
    │   codec_info_list_count                            │
    │   mc_quirk              ◀── resolved quirk word    │
    │   private  ──────┐                                 │
    └──────────────────┼─────────────────────────────────┘
                       ▼
            ┌────────────────────┐
            │ struct intel_mc_ctx│  Intel-private state
            └────────────────────┘

    snd_soc_card_set_drvdata(card, ctx) stores ctx for callbacks
    per-board identity comes from the PCI SSID + mc_quirk
```

### Three sources resolve the quirk word

The quirk word [`sof_sdw_quirk`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L43) is a module-global bitmask. The DMI path matches the board's vendor and product strings against [`sof_sdw_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L58), whose callback writes the matched entry's bits:

```c
/* sound/soc/intel/boards/sof_sdw.c:52 */
static int sof_sdw_quirk_cb(const struct dmi_system_id *id)
{
	sof_sdw_quirk = (unsigned long)id->driver_data;
	return 1;
}
```

Each table row pairs a DMI match with a quirk value, such as the PCH-DMIC bit for a CometLake reference board or the second jack-detect mode for a Dell SKU:

```c
/* sound/soc/intel/boards/sof_sdw.c:58 */
static const struct dmi_system_id sof_sdw_quirk_table[] = {
	/* CometLake devices */
	{
		.callback = sof_sdw_quirk_cb,
		.matches = {
			DMI_MATCH(DMI_SYS_VENDOR, "Intel Corporation"),
			DMI_MATCH(DMI_PRODUCT_NAME, "CometLake Client"),
		},
		.driver_data = (void *)SOC_SDW_PCH_DMIC,
	},
	{
		.callback = sof_sdw_quirk_cb,
		.matches = {
			DMI_MATCH(DMI_SYS_VENDOR, "Dell Inc"),
			DMI_EXACT_MATCH(DMI_PRODUCT_SKU, "09C6")
		},
		.driver_data = (void *)RT711_JD2,
	},
	...
};
```

The PCI-SSID path adds a second identity source. [`sof_sdw_check_ssid_quirk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L853) looks the descriptor's subsystem id up in [`sof_sdw_ssid_quirk_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L832) and overwrites the quirk word when an entry matches, so a board that ships several DMI product strings under one PCI SSID is matched by the more stable id:

```c
/* sound/soc/intel/boards/sof_sdw.c:853 */
static void sof_sdw_check_ssid_quirk(const struct snd_soc_acpi_mach *mach)
{
	const struct snd_pci_quirk *quirk_entry;

	quirk_entry = snd_pci_quirk_lookup_id(mach->mach_params.subsystem_vendor,
					      mach->mach_params.subsystem_device,
					      sof_sdw_ssid_quirk_table);

	if (quirk_entry)
		sof_sdw_quirk = quirk_entry->value;
}
```

The `quirk_override` module parameter is applied last, so a developer can force a layout from the kernel command line. After all three sources, the probe snapshots the resolved word into the context's [`mc_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L131):

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
	if (quirk_override != -1) {
		dev_info(card->dev, "Overriding quirk 0x%lx => 0x%x\n",
			 sof_sdw_quirk, quirk_override);
		sof_sdw_quirk = quirk_override;
	}

	log_quirks(card->dev);

	ctx->mc_quirk = sof_sdw_quirk;
```

The probe runs those sources in a fixed order so a later match overwrites an earlier one, the SSID lookup first, the DMI table next, and the module override last before the result is snapshotted:

```
    Three sources write sof_sdw_quirk in order, last write wins
    ────────────────────────────────────────────────────────────

    step (mc_probe order)        effect on sof_sdw_quirk
    ┌──────────────────────────┬────────────────────────────────┐
    │ sof_sdw_check_ssid_quirk │ if SSID entry: = entry->value  │
    │   (when subsystem_id_set)│ else: unchanged                │
    ├──────────────────────────┼────────────────────────────────┤
    │ dmi_check_system         │ if DMI match: = driver_data    │
    │   (sof_sdw_quirk_table)  │ else: unchanged                │
    ├──────────────────────────┼────────────────────────────────┤
    │ quirk_override           │ if != -1: = quirk_override     │
    │   (module parameter)     │ else: unchanged  (forces all)  │
    └──────────────────────────┴───────────────┬────────────────┘
                                               ▼
                                    ctx->mc_quirk = sof_sdw_quirk
                                    (snapshot of the final value)
```

### Amp counting builds the components string

After [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) builds the links, the per-amp [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callbacks have set each codec entry's [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73). The probe sums those counters over [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) and writes the total into the card's [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) string, which userspace reads to choose a UCM profile, and appends the DMIC count when the descriptor reports one:

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
	/* reset amp_num to ensure amp_num++ starts from 0 in each probe */
	for (i = 0; i < ctx->codec_info_list_count; i++)
		codec_info_list[i].amp_num = 0;

	ret = sof_card_dai_links_create(card);
	if (ret < 0)
		return ret;

	/*
	 * the default amp_num is zero for each codec and
	 * amp_num will only be increased for active amp
	 * codecs on used platform
	 */
	for (i = 0; i < ctx->codec_info_list_count; i++)
		amp_num += codec_info_list[i].amp_num;

	card->components = devm_kasprintf(card->dev, GFP_KERNEL,
					  " cfg-amp:%d", amp_num);
	if (!card->components)
		return -ENOMEM;

	if (mach->mach_params.dmic_num) {
		card->components = devm_kasprintf(card->dev, GFP_KERNEL,
						  "%s mic:dmic cfg-mics:%d",
						  card->components,
						  mach->mach_params.dmic_num);
		if (!card->components)
			return -ENOMEM;
	}
```

The `amp_num` counters are reset to zero before the link build so a re-probe counts from a clean state, since they are held in the static [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) and persist across probes.

```
    Per-codec amp_num counters sum into the components string
    ───────────────────────────────────────────────────────────

    codec_info_list[]          (reset amp_num = 0 before build)
    ┌──────────────────────┐
    │ [0] .amp_num         ├─┐
    │ [1] .amp_num         ├─┤  init callbacks bump amp_num
    │ ...                  ├─┤  for each active amp codec
    │ [n] .amp_num         ├─┘  during sof_card_dai_links_create()
    └──────────────────────┘ │
                             ▼  sum over codec_info_list_count
                      ┌─────────────┐
                      │ amp_num     │
                      └──────┬──────┘
                             ▼
       card->components = " cfg-amp:<amp_num>"
                             +
       mach_params.dmic_num ─▶ " mic:dmic cfg-mics:<dmic_num>"
```

### Registration and teardown

The probe finishes by registering the card with [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65), which arranges automatic teardown, and stores the card on the platform device. On a failed register it runs [`asoc_sdw_mc_dailink_exit_loop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1244) to undo any codec DAI setup that the link build had started:

```c
/* sound/soc/intel/boards/sof_sdw.c:1434 */
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

The driver-managed registration means [`mc_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1525) does not unregister the card itself; it only runs the same per-codec exit loop so each SoundWire codec DAI's [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) runs once more on the orderly removal path:

```c
/* sound/soc/intel/boards/sof_sdw.c:1525 */
static void mc_remove(struct platform_device *pdev)
{
	struct snd_soc_card *card = platform_get_drvdata(pdev);

	asoc_sdw_mc_dailink_exit_loop(card);
}
```

### The driver registration

The whole driver is declared with one [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) matched on `"sof_sdw"`, carrying the shared [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c) so the card suspends and resumes through the ASoC core:

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
