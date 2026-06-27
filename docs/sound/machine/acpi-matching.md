# ACPI machine matching (snd_soc_acpi_mach)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an x86-64 platform the ASoC machine driver for a board is chosen at runtime by matching the firmware-described audio hardware against a per-SoC table of [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) descriptors, and Sound Open Firmware (SOF) performs that match from its DSP probe. A descriptor keys the match in one of two ways. An I2C-attached codec is named by the ACPI Hardware ID in the descriptor's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) field, an [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) byte string compared against the ACPI namespace; a SoundWire peripheral is named by a [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) array of [`struct snd_soc_acpi_link_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) descriptors that carry each device's 64-bit `_ADR` and the link it sits on. The HID path runs through [`snd_soc_acpi_find_machine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34), which calls [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956) through [`snd_soc_acpi_id_present()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L11); the SoundWire path runs through [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296), which checks each link's `_ADR` list against the enumerated peripherals with [`snd_soc_acpi_sdw_link_slaves_found()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L132). Whichever descriptor wins, its [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) names the platform driver SOF instantiates and its [`sof_tplg_filename`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) names the topology the DSP loads.

```
    ACPI machine match (one snd_soc_acpi_mach entry)
    ────────────────────────────────────────────────

    Platform A: plain ACPI HID (I2C codec)
    ┌──────────────────────────────────────────────────────────┐
    │ snd_soc_acpi_mach                                        │
    │   id = "10134242"   (CS42L42 HID, found via _HID)        │
    │   drv_name         = "mtl_cs42l42_def"                   │
    │   sof_tplg_filename = "sof-mtl" (+ runtime suffix)       │
    └──────────────────────────────────────────────────────────┘

    Platform B: SoundWire _ADR links
    ┌──────────────────────────────────────────────────────────┐
    │ snd_soc_acpi_mach                                        │
    │   link_mask = BIT(0)                                     │
    │   links ─▶ snd_soc_acpi_link_adr[]                       │
    │              mask = BIT(0)  (SoundWire link 0)           │
    │              adr_d ─▶ adr = 0x000030025D071201           │
    │                       (mfg 025D, part 0712, ver 3)       │
    │   drv_name         = "sof_sdw"                           │
    │   sof_tplg_filename = "sof-mtl-rt712-l0.tplg"            │
    └──────────────────────────────────────────────────────────┘
```

## SUMMARY

A per-SoC table is an array of [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) entries terminated by an empty one, and SOF holds two such tables per platform in its [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), a HID-keyed [`machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L14) table for I2S, I2C, and PDM codecs and a SoundWire-keyed [`alt_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L14) table. For Meteor Lake those tables are [`snd_soc_acpi_intel_mtl_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L33) and [`snd_soc_acpi_intel_mtl_sdw_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L1191), both built in [`soc-acpi-intel-mtl-match.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c), and Lunar Lake has the analogous tables in [`soc-acpi-intel-lnl-match.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-lnl-match.c).

SOF reaches the match from its core probe. [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L191) calls [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L563), which dispatches into the platform op [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489). That function tries the HID table with [`snd_soc_acpi_find_machine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34) when an SSP or DMIC interface is available, and only when no codec HID is present and no HDAudio codec is on the link does it fall through to [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296) for the SoundWire table. The selected descriptor is recorded in [`sof_pdata->machine`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L40), and [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) fills the [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) embedded in the descriptor with the controller-side facts the board driver needs. Later, [`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) creates the board platform device by passing [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and the whole descriptor as platform data to [`platform_device_register_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L833).

The two match kinds differ in what the firmware exposes. A HID match works when an I2C codec such as CS42L42 (HID "10134242") appears as an ACPI device with a `_HID`, so [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956) finds it by string. A SoundWire match works when the codecs are enumerated on a SoundWire bus, where each peripheral is named by a 64-bit `_ADR` carried in [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) of [`struct snd_soc_acpi_adr_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116), and the match compares the manufacturer, part, version, and link fields decoded out of that `_ADR` against the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) instances the SoundWire controller already discovered.

## SPECIFICATIONS

- ACPI Specification: the `_HID` (Hardware ID) and `_ADR` (Address) namespace objects identify a device on its parent bus. An I2C codec carries a `_HID`; a SoundWire peripheral carries an `_ADR`.
- The 64-bit `_ADR` value encodes a SoundWire Device ID (version, manufacturer ID, part ID, class ID) along with the link ID and a unique ID. The field layout is given by the mask macros in [`include/linux/soundwire/sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h), beginning with [`SDW_DISCO_LINK_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L508).

## LINUX KERNEL

### Machine descriptor and parameter types (soc-acpi.h)

- [`'\<struct snd_soc_acpi_mach\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210): one machine-match entry; holds the ACPI [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) HID, the [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) alternate-HID list, the SoundWire [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), the [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), the [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)/[`quirk_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) pair, the embedded [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), and the [`sof_tplg_filename`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)
- [`'\<struct snd_soc_acpi_mach_params\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78): the controller-to-board area filled at match time, carrying [`platform`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), [`dmic_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), the SoundWire [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) and [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), and the [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) array
- [`'\<struct snd_soc_acpi_link_adr\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133): one SoundWire link's required device list; [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) selects the link, [`num_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) counts the devices, [`adr_d`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) is the device array
- [`'\<struct snd_soc_acpi_adr_device\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116): one `_ADR`-enumerated peripheral; [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) is the 64-bit `_ADR`, [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) the function list, [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) the control-name prefix
- [`'\<struct snd_soc_acpi_endpoint\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102): one function of a multi-function device; carries [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102) and the [`aggregated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102)/[`group_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102)/[`group_position`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102) fields that group amplifiers spread across links
- [`'\<struct snd_soc_acpi_codecs\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L244): a list of up to [`SND_SOC_ACPI_MAX_CODECS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L233) ACPI HIDs, used both as [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and as [`quirk_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)

### Generic match helpers (soc-acpi.c)

- [`'\<snd_soc_acpi_find_machine\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34): walk a HID table, return the first entry whose codec is present, applying [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) if set
- [`'\<snd_soc_acpi_id_present\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L11): test [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and then each [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) entry with [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956), copying a matched alternate HID back into [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)
- [`'\<snd_soc_acpi_codec_list\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L109): a [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) callback that confirms every HID in the [`quirk_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) list is also present before accepting the entry
- [`'\<snd_soc_acpi_sdw_link_slaves_found\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L132): for one [`struct snd_soc_acpi_link_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133), decode each device's `_ADR` and check that a matching [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) was enumerated on the same link

### SoundWire _ADR field macros (sdw.h)

- [`'\<SDW_MFG_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518): extract manufacturer ID (bits 39:24) via [`SDW_MFG_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L511)
- [`'\<SDW_PART_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519): extract part ID (bits 23:8) via [`SDW_PART_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L512)
- [`'\<SDW_VERSION\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516): extract SoundWire version (bits 47:44) via [`SDW_VERSION_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L509)
- [`'\<SDW_DISCO_LINK_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515): extract the link ID (bits 51:48) via [`SDW_DISCO_LINK_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L508)
- [`'\<SDW_UNIQUE_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L517): extract the unique ID (bits 43:40) via [`SDW_UNIQUE_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L510), used to disambiguate identical parts on one link
- [`'\<SDW_CODEC_ADR_MASK\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L128): mask an `_ADR` to its link, version, manufacturer, and part fields so two devices compare ignoring the unique ID

### Intel per-SoC match tables (intel/common)

- [`'\<snd_soc_acpi_intel_mtl_machines\>':'sound/soc/intel/common/soc-acpi-intel-mtl-match.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L33): the Meteor Lake HID-keyed table for I2S and PDM codecs
- [`'\<snd_soc_acpi_intel_mtl_sdw_machines\>':'sound/soc/intel/common/soc-acpi-intel-mtl-match.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L1191): the Meteor Lake SoundWire-keyed table, each entry with [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) `"sof_sdw"` and a [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) array
- [`'mtl_712_l0':'sound/soc/intel/common/soc-acpi-intel-mtl-match.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L391): a one-link, one-device descriptor naming RT712 on SoundWire link 0
- [`'rt712_0_single_adr':'sound/soc/intel/common/soc-acpi-intel-mtl-match.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L209): the [`struct snd_soc_acpi_adr_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) array carrying `_ADR` 0x000030025D071201

### SOF match and board-device creation (sof/)

- [`'\<snd_sof_machine_select\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L563): dispatch to the platform [`machine_select`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L341) op, called from [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L191)
- [`'\<hda_machine_select\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489): the Intel implementation; tries HID, then SoundWire, then HDAudio-generic
- [`'\<hda_sdw_machine_select\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296): walk [`alt_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L14), match each [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) entry with [`snd_soc_acpi_sdw_link_slaves_found()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L132), set [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)
- [`'\<hda_set_mach_params\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438): fill [`platform`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), and [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) in the selected descriptor's [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)
- [`'\<sof_machine_register\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807): create the board platform device from [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) via [`platform_device_register_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L833), passing the descriptor as platform data

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver concept and how it binds CPU and codec DAIs into a card
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the SoundWire bus and peripheral model that produces the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) instances the `_ADR` match checks against
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how ACPI `_HID` and `_ADR` enumerate I2C and other bus devices on x86

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The match-time interface between the SOF controller side and the board driver is the embedded [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78). Until the match the descriptor is the static table entry; once a descriptor is chosen, [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) and [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296) write the controller-side facts into [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), and the board driver named by [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) reads them back from the platform-data copy.

| Field of [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | Written by | Read by the board driver to |
|---|---|---|
| [`platform`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) | name the PCM platform component the card binds to |
| [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) / [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) | find the CPU DAI drivers in nocodec and generic paths |
| [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296) | know which SoundWire links to bring up |
| [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296) | build one DAI link per `_ADR` device |
| [`dmic_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) | [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489) | add the SoC PDM DMIC back end |

## DETAILS

### The machine descriptor

A board is described by one [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210). The first group of fields keys the match (the ACPI [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) HID, the [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) list, or the SoundWire [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)), the second names the driver and firmware ([`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), [`fw_filename`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), [`sof_tplg_filename`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)), the third refines the match at runtime ([`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) with [`quirk_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), and [`machine_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210)), and [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is the writable area filled once the entry wins.

```c
/* include/sound/soc-acpi.h:210 */
struct snd_soc_acpi_mach {
	u8 id[ACPI_ID_LEN];
	const char *uid;
	const struct snd_soc_acpi_codecs *comp_ids;
	const u32 link_mask;
	const struct snd_soc_acpi_link_adr *links;
	const char *drv_name;
	const char *fw_filename;
	const char *tplg_filename;
	const char *board;
	struct snd_soc_acpi_mach * (*machine_quirk)(void *arg);
	const void *quirk_data;
	bool (*machine_check)(void *arg);
	void *pdata;
	struct snd_soc_acpi_mach_params mach_params;
	const char *sof_tplg_filename;
	const u32 tplg_quirk_mask;
	int (*get_function_tplg_files)(struct snd_soc_card *card,
				       const struct snd_soc_acpi_mach *mach,
				       const char *prefix, const char ***tplg_files,
				       bool best_effort);
};
```

According to the comment on the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) field, it is the "ACPI ID (usually the codec's) used to find a matching machine driver", and according to the comment on [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), it is the "array of link _ADR descriptors, null terminated". A given entry sets one or the other. The HID tables set [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) or [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and leave [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) NULL; the SoundWire tables set [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and leave [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) empty.

The writable [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) carries the controller-to-board handoff:

```c
/* include/sound/soc-acpi.h:78 */
struct snd_soc_acpi_mach_params {
	u32 acpi_ipc_irq_index;
	const char *platform;
	u32 codec_mask;
	u32 dmic_num;
	u32 link_mask;
	const struct snd_soc_acpi_link_adr *links;
	u32 i2s_link_mask;
	u32 num_dai_drivers;
	struct snd_soc_dai_driver *dai_drivers;
	unsigned short subsystem_vendor;
	unsigned short subsystem_device;
	unsigned short subsystem_rev;
	bool subsystem_id_set;
	u32 bt_link_mask;
};
```

That writable area sits at the bottom of four zones the entry groups by purpose, the match keys keying the lookup, a names zone giving the driver and firmware, a runtime refine narrowing the hit, and mach_params carrying the handoff:

```
    struct snd_soc_acpi_mach: four field zones (one entry)
    ───────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────┐
    │ MATCH KEYS  (one kind set per entry)                 │
    │   id[ACPI_ID_LEN]      HID string  (I2C codec)       │
    │   comp_ids             alternate-HID list            │
    │   link_mask  +  links  SoundWire _ADR descriptors    │
    ├──────────────────────────────────────────────────────┤
    │ NAMES the driver and firmware                        │
    │   drv_name             board platform driver         │
    │   fw_filename  tplg_filename  sof_tplg_filename      │
    ├──────────────────────────────────────────────────────┤
    │ REFINES at runtime                                   │
    │   machine_quirk  +  quirk_data    machine_check      │
    ├──────────────────────────────────────────────────────┤
    │ WRITABLE handoff  (filled once the entry wins)       │
    │   mach_params ─▶ struct snd_soc_acpi_mach_params     │
    └──────────────────────────────────────────────────────┘

    HID table entry:  set id or comp_ids,  leave links empty
    SDW table entry:  set link_mask + links,  leave id empty
```

### The SoundWire link and device descriptors

A SoundWire board is described by an array of [`struct snd_soc_acpi_link_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133), one element per active link, terminated by an empty element. Each element selects the link with a single-bit [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) and points at an array of [`struct snd_soc_acpi_adr_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) through [`adr_d`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133):

```c
/* include/sound/soc-acpi.h:133 */
struct snd_soc_acpi_link_adr {
	u32 mask;
	u32 num_adr;
	const struct snd_soc_acpi_adr_device *adr_d;
};
```

Each device carries its 64-bit `_ADR` in [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116), a count and array of [`struct snd_soc_acpi_endpoint`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102) for its functions, and a [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) the codec driver prepends to its controls:

```c
/* include/sound/soc-acpi.h:116 */
struct snd_soc_acpi_adr_device {
	u64 adr;
	u8 num_endpoints;
	const struct snd_soc_acpi_endpoint *endpoints;
	const char *name_prefix;
};
```

The endpoint descriptor exists so a single physical device that exposes several functions, or several amplifiers that combine into one logical speaker, can be grouped:

```c
/* include/sound/soc-acpi.h:102 */
struct snd_soc_acpi_endpoint {
	u8 num;
	u8 aggregated;
	u8 group_position;
	u8 group_id;
};
```

According to the comment on [`aggregated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102), the value is "0 (independent) or 1 (logically grouped)", and the [`group_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102) and [`group_position`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L102) fields order the members of a group, which is how two physically separate amplifiers on different links become the left and right halves of one stereo speaker.

```
    SoundWire board description: nested _ADR descriptors
    ──────────────────────────────────────────────────────

    struct snd_soc_acpi_link_adr [ ]   (one per link, end {})
    ┌────────────────────────────────┐
    │ mask      = BIT(n)  one link   │
    │ num_adr   = count              │
    │ adr_d ─────────────────────┐   │
    └────────────────────────────┼───┘
                                 ▼
    struct snd_soc_acpi_adr_device [ ]   (one per peripheral)
    ┌────────────────────────────────┐
    │ adr        64-bit _ADR         │
    │ name_prefix                    │
    │ num_endpoints                  │
    │ endpoints ─────────────────┐   │
    └────────────────────────────┼───┘
                                 ▼
    struct snd_soc_acpi_endpoint [ ]   (one per function)
    ┌────────────────────────────────┐
    │ num                            │
    │ aggregated  0 indep / 1 group  │
    │ group_id    group_position     │
    └────────────────────────────────┘
```

### The 64-bit _ADR encodes manufacturer, part, version, and link

The `_ADR` value is the SoundWire Device ID. The high nibbles carry the link ID, version, and unique ID, the middle bytes carry the 16-bit manufacturer ID and 16-bit part ID, and the low byte carries the class ID. The field masks and accessors are defined together in [`sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h):

```c
/* include/linux/soundwire/sdw.h:508 */
#define SDW_DISCO_LINK_ID_MASK	GENMASK_ULL(51, 48)
#define SDW_VERSION_MASK	GENMASK_ULL(47, 44)
#define SDW_UNIQUE_ID_MASK	GENMASK_ULL(43, 40)
#define SDW_MFG_ID_MASK		GENMASK_ULL(39, 24)
#define SDW_PART_ID_MASK	GENMASK_ULL(23, 8)
#define SDW_CLASS_ID_MASK	GENMASK_ULL(7, 0)

#define SDW_DISCO_LINK_ID(addr)	FIELD_GET(SDW_DISCO_LINK_ID_MASK, addr)
#define SDW_VERSION(addr)	FIELD_GET(SDW_VERSION_MASK, addr)
#define SDW_UNIQUE_ID(addr)	FIELD_GET(SDW_UNIQUE_ID_MASK, addr)
#define SDW_MFG_ID(addr)	FIELD_GET(SDW_MFG_ID_MASK, addr)
#define SDW_PART_ID(addr)	FIELD_GET(SDW_PART_ID_MASK, addr)
#define SDW_CLASS_ID(addr)	FIELD_GET(SDW_CLASS_ID_MASK, addr)
```

For the RT712 descriptor, the `_ADR` is 0x000030025D071201. Reading the fields off the masks gives [`SDW_DISCO_LINK_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515) (bits 51:48) 0 for link 0, [`SDW_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) (bits 47:44) 3, [`SDW_UNIQUE_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L517) (bits 43:40) 0, [`SDW_MFG_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518) (bits 39:24) 0x025D for Realtek, [`SDW_PART_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519) (bits 23:8) 0x0712, and [`SDW_CLASS_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L520) (bits 7:0) 0x01.

```
    _ADR = 0x000030025D071201  (RT712 on link 0)
    ──────────────────────────────────────────────

     63        52 51 48 47 44 43 40 39          24 23          8 7      0
    ┌────────────┬─────┬─────┬─────┬──────────────┬─────────────┬───────┐
    │  reserved  │ lnk │ ver │ uid │   mfg_id     │   part_id   │ class │
    │   (63:52)  │51:48│47:44│43:40│   (39:24)    │   (23:8)    │ (7:0) │
    │     0      │  0  │  3  │  0  │   0x025D     │   0x0712    │ 0x01  │
    └────────────┴─────┴─────┴─────┴──────────────┴─────────────┴───────┘

    lnk = SDW_DISCO_LINK_ID  (SoundWire link the device sits on)
    ver = SDW_VERSION        uid = SDW_UNIQUE_ID
    mfg_id = SDW_MFG_ID (0x025D = Realtek)   part_id = SDW_PART_ID
    class = SDW_CLASS_ID
```

### A real MTL SoundWire match entry

The Meteor Lake SoundWire table holds an entry for an RT712 on link 0. The device is described once as an [`struct snd_soc_acpi_adr_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L116) array, [`rt712_0_single_adr`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L209):

```c
/* sound/soc/intel/common/soc-acpi-intel-mtl-match.c:209 */
static const struct snd_soc_acpi_adr_device rt712_0_single_adr[] = {
	{
		.adr = 0x000030025D071201ull,
		.num_endpoints = ARRAY_SIZE(rt712_endpoints),
		.endpoints = rt712_endpoints,
		.name_prefix = "rt712"
	}
};
```

That device array is wrapped by a one-link [`struct snd_soc_acpi_link_adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) array, [`mtl_712_l0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L391), whose [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L133) of `BIT(0)` ties it to SoundWire link 0:

```c
/* sound/soc/intel/common/soc-acpi-intel-mtl-match.c:391 */
static const struct snd_soc_acpi_link_adr mtl_712_l0[] = {
	{
		.mask = BIT(0),
		.num_adr = ARRAY_SIZE(rt712_0_single_adr),
		.adr_d = rt712_0_single_adr,
	},
	{}
};
```

That link array is the [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) field of one entry in [`snd_soc_acpi_intel_mtl_sdw_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L1191), which names the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1538) board driver and the RT712 topology file:

```c
/* sound/soc/intel/common/soc-acpi-intel-mtl-match.c:1191 */
struct snd_soc_acpi_mach snd_soc_acpi_intel_mtl_sdw_machines[] = {
	...
	{
		.link_mask = BIT(0),
		.links = mtl_712_l0,
		.drv_name = "sof_sdw",
		.sof_tplg_filename = "sof-mtl-rt712-l0.tplg",
		.get_function_tplg_files = sof_sdw_get_tplg_files,
	},
	...
};
EXPORT_SYMBOL_GPL(snd_soc_acpi_intel_mtl_sdw_machines);
```

The plain-HID entries of the same SoC sit in the separate [`snd_soc_acpi_intel_mtl_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/common/soc-acpi-intel-mtl-match.c#L33) table and set [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) to a codec HID string instead of any [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210). The CS42L42 entry is one such, an I2C codec named by HID "10134242":

```c
/* sound/soc/intel/common/soc-acpi-intel-mtl-match.c:59 */
	{
		.id = CS42L42_ACPI_HID,
		.drv_name = "mtl_cs42l42_def",
		.sof_tplg_filename = "sof-mtl", /* the tplg suffix is added at run time */
		.tplg_quirk_mask = SND_SOC_ACPI_TPLG_INTEL_AMP_NAME |
					SND_SOC_ACPI_TPLG_INTEL_CODEC_NAME,
	},
```

[`CS42L42_ACPI_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi-intel-ssp-common.h#L11) expands to "10134242", and the same string appears in the codec's own I2C ACPI match table in [`cs42l42-i2c.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42-i2c.c#L75), which is how the firmware enumerates the part as an I2C device with that `_HID`.

### The HID match: snd_soc_acpi_find_machine

When SOF detects an SSP or DMIC interface, [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489) tries the HID table first with [`snd_soc_acpi_find_machine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34). That function iterates the table until the terminating empty entry, an entry with neither [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) nor [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), and returns the first entry whose codec is present after applying [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) if the entry sets one:

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

The presence test is [`snd_soc_acpi_id_present()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L11). It calls [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956) on the primary [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), then on each HID in the [`comp_ids`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) list, and copies a matched alternate HID back into [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) with [`strscpy()`](https://elixir.bootlin.com/linux/v7.0/source/lib/string.c) so the rest of the path sees the concrete codec found:

```c
/* sound/soc/soc-acpi.c:11 */
static bool snd_soc_acpi_id_present(struct snd_soc_acpi_mach *machine)
{
	const struct snd_soc_acpi_codecs *comp_ids = machine->comp_ids;
	int i;

	if (machine->id[0]) {
		if (acpi_dev_present(machine->id, NULL, -1))
			return true;
	}

	if (comp_ids) {
		for (i = 0; i < comp_ids->num_codecs; i++) {
			if (acpi_dev_present(comp_ids->codecs[i], NULL, -1)) {
				strscpy(machine->id, comp_ids->codecs[i], ACPI_ID_LEN);
				return true;
			}
		}
	}

	return false;
}
```

When an entry needs more than one codec present, it sets [`machine_quirk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) to [`snd_soc_acpi_codec_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L109) and lists the extra HIDs in [`quirk_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210). The callback walks that [`struct snd_soc_acpi_codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L244) and returns the entry only when every listed HID is present, otherwise NULL so [`snd_soc_acpi_find_machine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L34) skips to the next row:

```c
/* sound/soc/soc-acpi.c:109 */
struct snd_soc_acpi_mach *snd_soc_acpi_codec_list(void *arg)
{
	struct snd_soc_acpi_mach *mach = arg;
	struct snd_soc_acpi_codecs *codec_list =
		(struct snd_soc_acpi_codecs *) mach->quirk_data;
	int i;

	if (mach->quirk_data == NULL)
		return mach;

	for (i = 0; i < codec_list->num_codecs; i++) {
		if (!acpi_dev_present(codec_list->codecs[i], NULL, -1))
			return NULL;
	}

	return mach;
}
```

The matcher walks the table entry by entry, the presence test accepting an entry whose id is present and copying a comp_ids hit back into id, then this quirk gate winning on all listed HIDs present and skipping the row on any absent:

```
    HID match: per-entry presence test, first hit wins
    ────────────────────────────────────────────────────

    for each entry until id[0]==0 and comp_ids==NULL:

      step  test (snd_soc_acpi_id_present)        on present
      ────  ──────────────────────────────────    ──────────
      1     acpi_dev_present(id)                   accept id
      2     acpi_dev_present(comp_ids[i]) for i    copy hit ─▶ id
            (none present)                         next entry

    if entry sets machine_quirk:
      machine_quirk(mach) = snd_soc_acpi_codec_list
        every quirk_data HID present   ─▶ return mach  (win)
        any one absent                 ─▶ return NULL  (skip)
```

### The SoundWire match: hda_sdw_machine_select

When the HID match returns NULL and there is no HDAudio codec on the link, [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489) calls [`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296):

```c
/* sound/soc/sof/intel/hda.c:1503 */
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
```

[`hda_sdw_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1296) walks the [`alt_machines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L14) table. For each entry it first checks that the entry's [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is a subset of the links the hardware enabled, then walks the entry's [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) array and requires every link's device list to be found among the enumerated peripherals with [`snd_soc_acpi_sdw_link_slaves_found()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L132):

```c
/* sound/soc/sof/intel/hda.c:1322 */
	for (mach = pdata->desc->alt_machines;
	     mach && mach->link_mask; mach++) {
		/*
		 * On some platforms such as Up Extreme all links
		 * are enabled but only one link can be used by
		 * external codec. Instead of exact match of two masks,
		 * first check whether link_mask of mach is subset of
		 * link_mask supported by hw and then go on searching
		 * link_adr
		 */
		if (~hdev->info.link_mask & mach->link_mask)
			continue;

		/* No need to match adr if there is no links defined */
		if (!mach->links)
			break;

		link = mach->links;
		for (i = 0; i < hdev->info.count && link->num_adr;
		     i++, link++) {
			/*
			 * Try next machine if any expected Slaves
			 * are not found on this link.
			 */
			if (!snd_soc_acpi_sdw_link_slaves_found(sdev->dev, link,
								hdev->sdw->peripherals))
				break;
		}
		/* Found if all Slaves are checked */
		if (i == hdev->info.count || !link->num_adr)
			if (!mach->machine_check || mach->machine_check(hdev->sdw))
				break;
	}
```

Once an entry wins, the function copies the entry's [`links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) into its [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) and records the DSP device name in [`platform`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), which the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1538) board driver later reads to build one DAI link per `_ADR` device:

```c
/* sound/soc/sof/intel/hda.c:1370 */
	if (mach && mach->link_mask) {
		mach->mach_params.links = mach->links;
		mach->mach_params.link_mask = mach->link_mask;
		mach->mach_params.platform = dev_name(sdev->dev);

		return mach;
	}
```

### snd_soc_acpi_sdw_link_slaves_found compares decoded _ADR fields

The link-level test decodes each expected device's `_ADR` with the [`SDW_MFG_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518), [`SDW_PART_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519), [`SDW_DISCO_LINK_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515), and [`SDW_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) accessors and looks for a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) on the same link whose id fields match:

```c
/* sound/soc/soc-acpi.c:132 */
bool snd_soc_acpi_sdw_link_slaves_found(struct device *dev,
					const struct snd_soc_acpi_link_adr *link,
					struct sdw_peripherals *peripherals)
{
	unsigned int part_id, link_id, unique_id, mfg_id, version;
	int i, j, k;

	for (i = 0; i < link->num_adr; i++) {
		u64 adr = link->adr_d[i].adr;
		int reported_part_count = 0;

		mfg_id = SDW_MFG_ID(adr);
		part_id = SDW_PART_ID(adr);
		link_id = SDW_DISCO_LINK_ID(adr);
		version = SDW_VERSION(adr);
		...
```

When more than one identical part sits on one link, the count of reported parts is compared to the count of expected parts using [`SDW_CODEC_ADR_MASK()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L128), and the per-device [`SDW_UNIQUE_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L517) disambiguates them, so a board with two of the same amplifier on one link matches only when each expected unique ID is present:

```c
/* sound/soc/soc-acpi.c:128 */
#define SDW_CODEC_ADR_MASK(_adr) ((_adr) & (SDW_DISCO_LINK_ID_MASK | SDW_VERSION_MASK | \
				  SDW_MFG_ID_MASK | SDW_PART_ID_MASK))
```

The test lines the expected device's decoded _ADR up against each enumerated peer on the same link, comparing mfg_id, part_id, and version, with that mask folding duplicate parts together so every expected unique_id still has to turn up:

```
    Link slaves found: expected _ADR fields vs enumerated peer
    ────────────────────────────────────────────────────────────

      expected device                       enumerated peripheral
    link->adr_d[i].adr  (u64)               struct sdw_slave .id
    decoded by SDW_* accessors              (struct sdw_slave_id)
    ┌──────────────────────────┐            ┌──────────────────────┐
    │ mfg_id  = SDW_MFG_ID     │◀──compare─▶│ mfg_id               │
    │ part_id = SDW_PART_ID    │◀──compare─▶│ part_id              │
    │ link_id = SDW_DISCO_LINK │◀──compare─▶│ (same link)          │
    │ version = SDW_VERSION    │◀──compare─▶│ sdw_version          │
    │ unique  = SDW_UNIQUE_ID  │◀──compare─▶│ unique_id            │
    └──────────────────────────┘            └──────────────────────┘
      dup parts on one link are counted via SDW_CODEC_ADR_MASK,
      then each expected unique_id must be present
```

### From the matched descriptor to the board platform device

[`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489) is invoked through the platform op wrapper [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L563), which [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L191) calls and whose result it stores in [`sof_pdata->machine`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.h#L40). For both match kinds, [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) records the DSP device name and the DAI driver array in the selected descriptor's [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), so the board driver finds the platform component and the CPU DAIs:

```c
/* sound/soc/sof/intel/hda.c:1438 */
void hda_set_mach_params(struct snd_soc_acpi_mach *mach,
			 struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *pdata = sdev->pdata;
	const struct sof_dev_desc *desc = pdata->desc;
	struct snd_soc_acpi_mach_params *mach_params;

	mach_params = &mach->mach_params;
	mach_params->platform = dev_name(sdev->dev);
	if (IS_ENABLED(CONFIG_SND_SOC_SOF_NOCODEC_DEBUG_SUPPORT) &&
	    sof_debug_check_flag(SOF_DBG_FORCE_NOCODEC))
		mach_params->num_dai_drivers = SOF_SKL_NUM_DAIS_NOCODEC;
	else
		mach_params->num_dai_drivers = desc->ops->num_drv;
	mach_params->dai_drivers = desc->ops->drv;
}
```

[`sof_machine_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L807) then instantiates the board. It reads [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) out of the descriptor as the platform driver name and passes the whole descriptor as platform data to [`platform_device_register_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L833), so the board driver that probes against that name receives the descriptor with its now-populated [`mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210):

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

For the RT712 example, [`drv_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) is "sof_sdw", so the [`sof_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1538) platform driver binds, reads [`mach_params.links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) and [`mach_params.link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78), and builds one DAI link per `_ADR` device before [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) brings the card up, and SOF then loads the topology named by [`sof_tplg_filename`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210), "sof-mtl-rt712-l0.tplg".
