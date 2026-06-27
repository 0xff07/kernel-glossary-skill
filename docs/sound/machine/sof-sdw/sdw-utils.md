# SoundWire machine utilities (sdw_utils)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The SoundWire machine utilities are a shared library under [`sound/soc/sdw_utils/`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils) that hold the per-codec knowledge a SoundWire audio card needs, so the Intel SOF machine driver [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) only assembles DAI links and never encodes anything about a Realtek or Cirrus part. The core is one capability table, [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), whose entries are [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) records keyed by SoundWire part id, each carrying an array of [`struct asoc_sdw_dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) per-DAI descriptors with the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), and [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callbacks for that interface. The machine driver resolves each SoundWire device address to its table entry with [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839), builds back-end DAI links with [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293), wires every link to the shared stream operations in [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865), and lets [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) run the per-codec [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callback when the runtime is bound. Every exported symbol is in the module namespace [`SND_SOC_SDW_UTILS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L831), which the machine driver imports through [`MODULE_IMPORT_NS()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1556).

```
    codec_info_list[] : part-id ─▶ per-codec descriptor (asoc_sdw_codec_info)
    ──────────────────────────────────────────────────────────────────────

    ┌──────────┬───────────────┬──────────────────────────────────────────┐
    │ part_id  │ name_prefix   │ dais[] (asoc_sdw_dai_info per interface) │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x711    │ "rt711"       │ aif1  JACK   rtd_init=rt_sdca_jack       │
    │ (v3)     │               │                                          │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x722    │ "rt722"       │ aif1  JACK   init=rt_sdca_jack_init      │
    │ (v3)     │               │              exit=rt_sdca_jack_exit      │
    │          │               │              rtd_init=rt_sdca_jack_rtd   │
    │          │               │ aif2  AMP    init=rt_amp_init            │
    │          │               │              rtd_init=rt_mf_sdca_spk     │
    │          │               │ aif3  MIC    rtd_init=rt_dmic_rtd        │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x3556   │ "AMP"         │ sdw1  AMP    init=cs_amp_init            │
    │          │               │              rtd_init=cs_spk_rtd         │
    │          │               │ sdw1c AMP    rtd_init=cs_spk_feedback    │
    └──────────┴───────────────┴──────────────────────────────────────────┘

    machine driver (sof_sdw)             utils (sdw_utils)
    ────────────────────────             ─────────────────
    enumerate ACPI links         ──▶  asoc_sdw_find_codec_info_part(adr)
    assemble dai links           ──▶  asoc_sdw_init_dai_link(...)
    .ops = sdw_ops               ──▶  asoc_sdw_{startup,prepare,trigger,...}
    .init = asoc_sdw_rtd_init    ──▶  per-codec dais[i].rtd_init(rtd, dai)
```

## SUMMARY

A SoundWire audio card on an x86 ACPI platform is split into two pieces. The per-codec knowledge sits in the utilities library under [`sound/soc/sdw_utils/`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils), and the board topology assembly sits in the Intel SOF machine driver [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c). The single point of contact between them is [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), an exported array of [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73). Each entry pairs a SoundWire part id ([`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73)) and an optional [`version_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) with an array of [`struct asoc_sdw_dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) descriptors, one per DAI the codec exposes. Each descriptor records the direction support, the [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), a [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) of [`SOC_SDW_DAI_TYPE_JACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L41), [`SOC_SDW_DAI_TYPE_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L42), or [`SOC_SDW_DAI_TYPE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L43), the kcontrols and DAPM widgets the card should add, and three callbacks the utilities invoke at defined moments.

The lookup helpers resolve a codec to its table entry from whatever identifier is at hand. [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839) takes the 64-bit SoundWire device address and extracts the part id with [`SDW_PART_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519), [`asoc_sdw_find_codec_info_acpi()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L873) matches the ACPI hardware id from [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) against the entry's [`acpi_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), and [`asoc_sdw_find_codec_info_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L888) maps a DAI name to its entry and index. The runtime helpers [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918), [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031), [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050), and [`asoc_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1090) run when a stream is opened or driven, and the DAI-link builders [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) and [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) fill one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the assembled component lists. The per-codec glue modules ([`soc_sdw_rt_sdca_jack_common.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c), [`soc_sdw_rt_amp.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_amp.c), [`soc_sdw_cs42l43.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l43.c), [`soc_sdw_cs_amp.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c), [`soc_sdw_dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c)) each define those callbacks and are referenced by name from a [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) entry.

## SPECIFICATIONS

The [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) table is a Linux kernel software construct and has no standalone hardware specification. The part id and version id it keys on are decoded from a 64-bit SoundWire device address by the [`SDW_PART_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519) and [`SDW_VERSION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) macros in the kernel SoundWire headers.

## LINUX KERNEL

### Capability table and descriptor types (soc_sdw_utils.h, soc_sdw_utils.c)

- [`'\<struct asoc_sdw_codec_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73): the per-codec descriptor keyed by [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) and [`version_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), holding the [`acpi_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) array, the [`dai_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) count, the runtime [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) counter, and the optional [`codec_card_late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), [`count_sidecar`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), and [`add_sidecar`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) hooks
- [`'\<struct asoc_sdw_dai_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47): the per-DAI descriptor with [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) id pair, controls and widgets, the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47)/[`exit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47)/[`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callbacks, and the [`rtd_init_done`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) one-shot guard
- [`'\<struct asoc_sdw_aux_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L69): a one-field auxiliary-device descriptor used for the sidecar amplifiers an SDCA codec aggregates
- [`'codec_info_list':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74): the array of every supported codec descriptor, exported under [`SND_SOC_SDW_UTILS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L831)
- [`'\<asoc_sdw_get_codec_info_list_count\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L833): return [`ARRAY_SIZE(codec_info_list)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) so the machine driver can size its loop without seeing the array definition

### Lookup helpers (soc_sdw_utils.c)

- [`'\<asoc_sdw_find_codec_info_part\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839): decode a 64-bit SoundWire address with [`SDW_PART_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519) and [`SDW_VERSION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) and return the matching [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73)
- [`'\<asoc_sdw_find_codec_info_acpi\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L873): match the ACPI hardware id from [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) against each entry's [`acpi_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) over [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) bytes
- [`'\<asoc_sdw_find_codec_info_dai\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L888): find the entry and DAI index whose [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) matches a string
- [`'\<asoc_sdw_find_codec_info_sdw_id\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L860): match a discovered [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) by [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) and [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), used inside [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918)

### Runtime stream operations (soc_sdw_utils.c)

- [`'\<asoc_sdw_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918): the shared [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook every SoundWire DAI link uses; for each codec DAI it locates the table entry, adds the controls and widgets once, and runs the per-DAI [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47)
- [`'\<asoc_sdw_startup\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1025): a thin wrapper over [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899) for the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op
- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): read the SoundWire stream handle from the first CPU DAI and call [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_trigger\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050): map the PCM trigger command to [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) or [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707)
- [`'\<asoc_sdw_hw_params\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1090): split the channel mask across the codec DAIs of a multi-amp link by writing each [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L731) entry
- [`'\<asoc_sdw_hw_free\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133): release the stream with [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812)
- [`'\<asoc_sdw_shutdown\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1153): a wrapper over [`sdw_shutdown_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943) for the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op

### Dai-link assembly and endpoint parsing (soc_sdw_utils.c)

- [`'\<asoc_sdw_init_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293): fill one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from caller-supplied CPU, platform, and codec lists, assign and post-increment the back-end id, and store the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): allocate the three [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) slots, populate them from name strings, and forward to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293)
- [`'\<asoc_sdw_card_late_probe\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1277): walk the table and invoke each entry's [`codec_card_late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) after the card is bound
- [`'\<asoc_sdw_count_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348) / [`'\<asoc_sdw_parse_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489): count and enumerate the SoundWire endpoints the ACPI link table reports, resolving each device through [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839)

### Per-codec glue modules (soc_sdw_*.c)

- [`'\<asoc_sdw_rt_sdca_jack_init\>':'sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L194) / [`'\<asoc_sdw_rt_sdca_jack_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93): the callbacks the Realtek SDCA jack codecs (RT711, RT712, RT713, RT721, RT722) reference
- [`'\<asoc_sdw_rt_amp_init\>':'sound/soc/sdw_utils/soc_sdw_rt_amp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_amp.c#L266): the Realtek amplifier [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callback that counts amps through [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73)
- [`'\<asoc_sdw_cs42l43_spk_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_cs42l43.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l43.c#L108) / [`'\<asoc_sdw_cs_spk_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_cs_amp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38): the Cirrus CS42L43 and CS35L56 speaker callbacks
- [`'\<asoc_sdw_dmic_init\>':'sound/soc/sdw_utils/soc_sdw_dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24): the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) hook for the onboard PCH digital-microphone link, passed directly by the machine driver

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver concept, the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) the utilities populate
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end split the SoundWire DAI links use
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle that [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) and [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) drive
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus, master, and peripheral model the part id is read from

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The utilities export three families of entry points a machine driver calls. The lookup family resolves a codec to its [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) entry, the assembly family builds the DAI links, and the stream family is bound into each link as its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623). Each is declared in [`include/sound/soc_sdw_utils.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h) and exported in the [`SND_SOC_SDW_UTILS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L831) module namespace.

| Family | Entry point | Role |
|--------|-------------|------|
| lookup | [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839) | address to descriptor |
| lookup | [`asoc_sdw_find_codec_info_acpi()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L873) | ACPI HID to descriptor |
| assembly | [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) | fill one DAI link |
| assembly | [`asoc_sdw_count_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348) | size the link array |
| stream | [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) | per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) |
| stream | [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) members | PCM op table |

## DETAILS

### The capability table is keyed by part id

The table entry is a [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73). Its key fields are the [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) and optional [`version_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), its payload is the [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) array sized by [`dai_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), and its tail holds the optional card-level hooks and the [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) runtime counter that the multi-amp parts increment:

```c
/* include/sound/soc_sdw_utils.h:73 */
struct asoc_sdw_codec_info {
	const int part_id;
	const int version_id;
	const char *name_prefix;
	int amp_num;
	const u8 acpi_id[ACPI_ID_LEN];
	const bool ignore_internal_dmic;
	const struct snd_soc_ops *ops;
	struct asoc_sdw_dai_info dais[SOC_SDW_MAX_DAI_NUM];
	const int dai_num;
	struct asoc_sdw_aux_info auxs[SOC_SDW_MAX_AUX_NUM];
	const int aux_num;

	int (*codec_card_late_probe)(struct snd_soc_card *card);

	int  (*count_sidecar)(struct snd_soc_card *card,
			      int *num_dais, int *num_devs);
	int  (*add_sidecar)(struct snd_soc_card *card,
			    struct snd_soc_dai_link **dai_links,
			    struct snd_soc_codec_conf **codec_conf);
};
```

Each DAI of the codec is a [`struct asoc_sdw_dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47). It records which directions the DAI supports, its [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) and [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), the per-direction back-end ids in [`dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), the controls and widgets the card should add, the three lifecycle callbacks, and the [`rtd_init_done`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) flag that keeps [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) one-shot:

```c
/* include/sound/soc_sdw_utils.h:47 */
struct asoc_sdw_dai_info {
	const bool direction[2]; /* playback & capture support */
	const char *codec_name;
	const char *dai_name;
	const char *component_name;
	const int dai_type;
	const int dailink[2]; /* dailink id for each direction */
	const struct snd_kcontrol_new *controls;
	const int num_controls;
	const struct snd_soc_dapm_widget *widgets;
	const int num_widgets;
	int  (*init)(struct snd_soc_card *card,
		     struct snd_soc_dai_link *dai_links,
		     struct asoc_sdw_codec_info *info,
		     bool playback);
	int (*exit)(struct snd_soc_card *card, struct snd_soc_dai_link *dai_link);
	int (*rtd_init)(struct snd_soc_pcm_runtime *rtd, struct snd_soc_dai *dai);
	bool rtd_init_done; /* Indicate that the rtd_init callback is done */
	unsigned long quirk;
	bool quirk_exclude;
};
```

The Realtek RT722 entry shows the table populated for a three-interface SDCA part, naming a jack, an amp, and a microphone DAI, each with its callbacks:

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
				.exit = asoc_sdw_rt_sdca_jack_exit,
				.rtd_init = asoc_sdw_rt_sdca_jack_rtd_init,
			},
			...
		},
		.dai_num = 3,
	},
```

### Lookup resolves a SoundWire address to its entry

The machine driver enumerates SoundWire devices by their 64-bit `_ADR` and resolves each to a table entry with [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839). It decodes the part and version with the [`sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h) macros and accepts an entry whose [`version_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) is either unset (matching every version) or equal to the decoded version:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:839 */
struct asoc_sdw_codec_info *asoc_sdw_find_codec_info_part(const u64 adr)
{
	unsigned int part_id, sdw_version;
	int i;

	part_id = SDW_PART_ID(adr);
	sdw_version = SDW_VERSION(adr);
	for (i = 0; i < ARRAY_SIZE(codec_info_list); i++)
		/*
		 * A codec info is for all sdw version with the part id if
		 * version_id is not specified in the codec info.
		 */
		if (part_id == codec_info_list[i].part_id &&
		    (!codec_info_list[i].version_id ||
		     sdw_version == codec_info_list[i].version_id))
			return &codec_info_list[i];

	return NULL;
}
```

The address path is the one the bus discovery uses, but the table is also keyed two other ways. [`asoc_sdw_find_codec_info_acpi()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L873) matches the ACPI hardware id carried in [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) against each entry's [`acpi_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) over [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) bytes, the path the onboard codec on an HDA-style link takes when there is no SoundWire `_ADR` to decode:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:873 */
struct asoc_sdw_codec_info *asoc_sdw_find_codec_info_acpi(const u8 *acpi_id)
{
	int i;

	if (!acpi_id[0])
		return NULL;

	for (i = 0; i < ARRAY_SIZE(codec_info_list); i++)
		if (!memcmp(codec_info_list[i].acpi_id, acpi_id, ACPI_ID_LEN))
			return &codec_info_list[i];

	return NULL;
}
```

[`asoc_sdw_find_codec_info_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L888) takes a DAI name and walks every entry's [`dais`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) array, returning both the entry and the matched DAI index through `dai_index`, so a caller holding only a [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) string reaches the same descriptor the address lookup would:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:888 */
struct asoc_sdw_codec_info *asoc_sdw_find_codec_info_dai(const char *dai_name, int *dai_index)
{
	int i, j;

	for (i = 0; i < ARRAY_SIZE(codec_info_list); i++) {
		for (j = 0; j < codec_info_list[i].dai_num; j++) {
			if (!strcmp(codec_info_list[i].dais[j].dai_name, dai_name)) {
				*dai_index = j;
				return &codec_info_list[i];
			}
		}
	}

	return NULL;
}
```

Because [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) is local to the utilities module, the machine driver cannot take [`ARRAY_SIZE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/array_size.h#L11) of it directly; [`asoc_sdw_get_codec_info_list_count()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L833) exports that count so the driver can size a loop over every supported codec without seeing the array definition:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:833 */
int asoc_sdw_get_codec_info_list_count(void)
{
	return ARRAY_SIZE(codec_info_list);
}
```

Whichever identifier a caller holds, one of three lookups resolves it to the same record, the address keyed on part and version, the ACPI id on its bytes, and a DAI name on the entry's DAI list:

```
    Three lookup keys, one codec_info_list[] entry
    ─────────────────────────────────────────────────

    caller holds            helper resolves it          keyed on
    ┌────────────────┐
    │ u64 _ADR addr  │──▶ asoc_sdw_find_codec_info_part   part_id + version_id
    ├────────────────┤
    │ ACPI hw id     │──▶ asoc_sdw_find_codec_info_acpi   acpi_id[ACPI_ID_LEN]
    ├────────────────┤
    │ DAI name str   │──▶ asoc_sdw_find_codec_info_dai   dais[j].dai_name
    └───────┬────────┘
            │  all three converge on the same record
            ▼
    ┌────────────────────────────────┐
    │ &codec_info_list[i]            │
    │ struct asoc_sdw_codec_info     │
    │   part_id  version_id  acpi_id │
    │   dais[]   dai_num             │
    └────────────────────────────────┘
```

### The shared init runs each codec's rtd_init

Every SoundWire DAI link points its [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) at [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918), which the core runs once per runtime. It walks the link's codec DAIs, resolves each back to its table entry through [`asoc_sdw_find_codec_info_sdw_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L860), adds that DAI's controls and widgets, and runs its [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) exactly once, guarding repeats with [`rtd_init_done`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:918 */
	for_each_rtd_codec_dais(rtd, i, dai) {
		...
		codec_info = asoc_sdw_find_codec_info_sdw_id(&sdw_peripheral->id);
		if (!codec_info)
			return -EINVAL;

		dai_index = asoc_sdw_find_codec_info_dai_index(codec_info, dai->name);
		...
		if (codec_info->dais[dai_index].rtd_init_done)
			continue;
		...
		if (codec_info->dais[dai_index].rtd_init) {
			ret = codec_info->dais[dai_index].rtd_init(rtd, dai);
			if (ret)
				return ret;
		}
		codec_info->dais[dai_index].rtd_init_done = true;
	}
```

The portion the excerpt elides is the prologue that finds the SoundWire peripheral behind each DAI and the controls and widgets the first codec DAI contributes. The function resolves the peripheral with [`is_sdw_slave()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L645) and [`dev_to_sdw_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L639), adds the controls with [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1668) and the widgets with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4002) only for the first DAI, and on an [`SOC_SDW_DAI_TYPE_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L42) DAI appends the [`component_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) to the card's `spk:` component string:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:918 */
int asoc_sdw_rtd_init(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	struct asoc_sdw_codec_info *codec_info;
	struct snd_soc_dai *dai;
	struct sdw_slave *sdw_peripheral;
	const char *spk_components="";
	int dai_index;
	int ret;
	int i;

	for_each_rtd_codec_dais(rtd, i, dai) {
		if (is_sdw_slave(dai->component->dev))
			sdw_peripheral = dev_to_sdw_dev(dai->component->dev);
		else if (dai->component->dev->parent && is_sdw_slave(dai->component->dev->parent))
			sdw_peripheral = dev_to_sdw_dev(dai->component->dev->parent);
		else
			continue;
		...
		if (i > 0)
			goto skip_add_controls_widgets;

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
	return 0;
}
```

### The stream ops drive the SoundWire stream

The six members of [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) map the PCM operations onto SoundWire stream calls. [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533), [`asoc_sdw_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133) calls [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812), and [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) finds the stream stored on the first CPU DAI and maps the trigger command to enable or disable:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1050 */
int asoc_sdw_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_stream_runtime *sdw_stream;
	struct snd_soc_dai *dai;
	int ret;

	/* Find stream from first CPU DAI */
	dai = snd_soc_rtd_to_cpu(rtd, 0);

	sdw_stream = snd_soc_dai_get_stream(dai, substream->stream);
	...
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_RESUME:
		ret = sdw_enable_stream(sdw_stream);
		break;

	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		ret = sdw_disable_stream(sdw_stream);
		break;
	default:
		ret = -EINVAL;
		break;
	}
	...
	return ret;
}
```

The two endpoints of the stream lifecycle are the thinnest. [`asoc_sdw_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1025) and [`asoc_sdw_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1152) exist only to wrap [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899) and [`sdw_shutdown_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943) with the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) signatures the core expects, since those bus helpers take the substream directly:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1025 */
/* these wrappers are only needed to avoid typecast compilation errors */

int asoc_sdw_startup(struct snd_pcm_substream *substream)
{
	return sdw_startup_stream(substream);
}
```

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1152 */
void asoc_sdw_shutdown(struct snd_pcm_substream *substream)
{
	sdw_shutdown_stream(substream);
}
```

[`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) and [`asoc_sdw_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133) bracket the active part of the stream. Both read the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L981) handle from the first CPU DAI with [`snd_soc_dai_get_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L545), the same handle [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) uses, then call [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) respectively:

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

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1133 */
int asoc_sdw_hw_free(struct snd_pcm_substream *substream)
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

	return sdw_deprepare_stream(sdw_stream);
}
```

[`asoc_sdw_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1090) is the one op that does board-specific work rather than forwarding to the bus. When a link aggregates several amplifier codecs it splits the PCM channels across them by writing each [`ch_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L731) entry; playback sends the same channels to every codec, while capture divides the channels evenly and shifts the mask per codec so ASoC assigns the matching CPU-DAI channels:

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

The channel-map op shown above sits in this table beside the others, which each translate one PCM operation into a single SoundWire stream routine:

```
    sdw_ops: each PCM op forwards to one SoundWire stream call
    ────────────────────────────────────────────────────────────

    snd_soc_ops member   asoc_sdw_ wrapper      bus stream call
    ┌──────────────────┬───────────────────┬──────────────────────┐
    │ .startup         │ asoc_sdw_startup  │ sdw_startup_stream   │
    ├──────────────────┼───────────────────┼──────────────────────┤
    │ .prepare         │ asoc_sdw_prepare  │ sdw_prepare_stream   │
    ├──────────────────┼───────────────────┼──────────────────────┤
    │ .trigger START   │ asoc_sdw_trigger  │ sdw_enable_stream    │
    │ .trigger STOP    │ asoc_sdw_trigger  │ sdw_disable_stream   │
    ├──────────────────┼───────────────────┼──────────────────────┤
    │ .hw_params       │ asoc_sdw_hw_params│ (writes ch_maps)     │
    ├──────────────────┼───────────────────┼──────────────────────┤
    │ .hw_free         │ asoc_sdw_hw_free  │ sdw_deprepare_stream │
    ├──────────────────┼───────────────────┼──────────────────────┤
    │ .shutdown        │ asoc_sdw_shutdown │ sdw_shutdown_stream  │
    └──────────────────┴───────────────────┴──────────────────────┘

    trigger, prepare, hw_free read the handle from CPU DAI 0:
      sdw_stream = snd_soc_dai_get_stream(snd_soc_rtd_to_cpu(rtd, 0))
```

### The DAI-link builders fill one link from name lists

The assembly entry point [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293) writes the caller's CPU, platform, and codec component arrays into one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), assigns and post-increments the back-end id, and stores the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) the machine passes:

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

The single-codec convenience form [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) allocates the three [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) slots from device-managed memory, fills the CPU DAI name, the platform component name, and the codec name and DAI name, and forwards to [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293), so a board that needs only one codec on a link writes three strings rather than three component arrays. The DMIC and HDMI back-ends, which carry exactly one codec, are built through this form:

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

The builder leaves one link pointing at its CPU, platform, and codec component arrays, and the simple form carves those three slots from a single allocation of three components:

```
    One snd_soc_dai_link aggregates three component arrays
    ────────────────────────────────────────────────────────

    ┌────────────────────────────────────────────────┐
    │ struct snd_soc_dai_link                        │
    │   id            (*be_id)++                     │
    │   name  stream_name                            │
    │   init = init   ops = ops                      │
    │   cpus  ─▶ num_cpus                            │
    │   platforms ─▶ num_platforms                   │
    │   codecs ─▶ num_codecs                         │
    └┬────────────┬──┬────────────┬──┬────────────┬──┘
     ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │cpus[]      │  │platforms[] │  │codecs[]    │
     │DLC         │  │DLC         │  │DLC         │
     └────────────┘  └────────────┘  └────────────┘

    simple form: one devm_kcalloc(3) of snd_soc_dai_link_component
    ┌───────────────────┬───────────────────┬───────────────────┐
    │ dlc[0]            │ dlc[1]            │ dlc[2]            │
    │ .dai_name =       │ .name =           │ .name =           │
    │   cpu_dai_name    │   platform_comp   │   codec_name      │
    │                   │                   │ .dai_name =       │
    │                   │                   │   codec_dai_name  │
    └───────────────────┴───────────────────┴───────────────────┘
```

### Endpoint counting and parsing size and fill the link array

Before any link is built the machine driver walks the ACPI `_ADR` link table twice. [`asoc_sdw_count_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348) is the sizing pass; it sums the SoundWire devices, endpoints, and auxiliary devices the table reports, resolving each device through [`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839) to add its [`aux_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), so the driver can allocate the dailink and endpoint arrays exactly once:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1348 */
int asoc_sdw_count_sdw_endpoints(struct snd_soc_card *card,
				 int *num_devs, int *num_ends, int *num_aux)
{
	struct device *dev = card->dev;
	struct snd_soc_acpi_mach *mach = dev_get_platdata(dev);
	struct snd_soc_acpi_mach_params *mach_params = &mach->mach_params;
	const struct snd_soc_acpi_link_adr *adr_link;
	int i;

	for (adr_link = mach_params->links; adr_link->num_adr; adr_link++) {
		*num_devs += adr_link->num_adr;

		for (i = 0; i < adr_link->num_adr; i++) {
			const struct snd_soc_acpi_adr_device *adr_dev = &adr_link->adr_d[i];
			struct asoc_sdw_codec_info *codec_info;

			*num_ends += adr_dev->num_endpoints;

			codec_info = asoc_sdw_find_codec_info_part(adr_dev->adr);
			if (!codec_info)
				return -EINVAL;

			*num_aux += codec_info->aux_num;
		}
	}
	...
	return 0;
}
```

[`asoc_sdw_parse_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489) is the filling pass over the same table. For each device it resolves the [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73), groups endpoints that share an aggregation id into one [`struct asoc_sdw_dailink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L93), applies the codec's quirks and SDCA presence check, records the resolved codec name and [`dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) on each [`struct asoc_sdw_endpoint`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L83), and returns the total DAI-link count the driver then iterates to call [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1489 */
int asoc_sdw_parse_sdw_endpoints(struct snd_soc_card *card,
				 struct snd_soc_aux_dev *soc_aux,
				 struct asoc_sdw_dailink *soc_dais,
				 struct asoc_sdw_endpoint *soc_ends,
				 int *num_devs)
{
	...
	for (adr_link = mach_params->links; adr_link->num_adr; adr_link++) {
		...
		for (i = 0; i < adr_link->num_adr; i++) {
			const struct snd_soc_acpi_adr_device *adr_dev = &adr_link->adr_d[i];
			struct asoc_sdw_codec_info *codec_info;
			...
			codec_info = asoc_sdw_find_codec_info_part(adr_dev->adr);
			if (!codec_info)
				return -EINVAL;
			...
			for (j = 0; j < adr_dev->num_endpoints; j++) {
				...
				soc_dai = asoc_sdw_find_dailink(soc_dais, adr_end);
				...
				list_add_tail(&soc_end->list, &soc_dai->endpoints);

				codec_name = asoc_sdw_get_codec_name(dev, dai_info,
								     adr_link, i);
				...
				soc_end->codec_name = codec_name;
				soc_end->codec_info = codec_info;
				soc_end->dai_info = dai_info;
				soc_end++;
			}
		}
		...
	}

	return num_dais;
}
```

After the card binds, [`asoc_sdw_card_late_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1277) walks the whole table once more and runs each entry's optional [`codec_card_late_probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) hook, the place a codec that needs a board-wide finishing step (a shared clock, a cross-component route) does it:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1277 */
int asoc_sdw_card_late_probe(struct snd_soc_card *card)
{
	int ret = 0;
	int i;

	for (i = 0; i < ARRAY_SIZE(codec_info_list); i++) {
		if (codec_info_list[i].codec_card_late_probe) {
			ret = codec_info_list[i].codec_card_late_probe(card);
			if (ret < 0)
				return ret;
		}
	}
	return ret;
}
```

Before any link exists the driver walks that same _ADR table twice, a counting pass summing devices, endpoints, and aux devices to size the arrays and a parsing pass grouping endpoints and recording each codec name and descriptor:

```
    Two passes over the ACPI _ADR link table size then fill
    ──────────────────────────────────────────────────────────

    mach_params->links[]   (struct snd_soc_acpi_link_adr)
    ┌─────────────────────────────────────────┐
    │ adr_link        adr_d[]                 │
    │   ┌───────────────────────────────────┐ │
    │   │ adr_dev (snd_soc_acpi_adr_device) │ │
    │   │   adr            num_endpoints    │ │
    │   └───────────────────────────────────┘ │
    └─────────────────────────────────────────┘
           asoc_sdw_find_codec_info_part(adr)
                       ▼
    ┌──────────────────────────────────────────────┐
    │ struct asoc_sdw_codec_info   (aux_num, dais) │
    └──────────────────────────────────────────────┘

    pass 1  count   asoc_sdw_count_sdw_endpoints
            ──────  num_devs += num_adr
                    num_ends += adr_dev->num_endpoints
                    num_aux  += codec_info->aux_num
                       │  sizes the arrays, allocate once
                       ▼
    pass 2  parse   asoc_sdw_parse_sdw_endpoints
            ──────  group endpoints by agg id ─▶ asoc_sdw_dailink
                    fill asoc_sdw_endpoint{ codec_name,
                         codec_info, dai_info }
```

### The per-codec rtd_init callbacks add the codec's controls and routes

The generic [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) callbacks each [`struct asoc_sdw_dai_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) names are defined in the per-codec glue modules, and [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) is what reaches them. The DMIC back-end uses [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) directly as the link's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) rather than through the table; it adds the `SoC DMIC` widget and its route with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4002) and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2675):

```c
/* sound/soc/sdw_utils/soc_sdw_dmic.c:24 */
int asoc_sdw_dmic_init(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	int ret;

	ret = snd_soc_dapm_new_controls(dapm, dmic_widgets,
					ARRAY_SIZE(dmic_widgets));
	if (ret) {
		dev_err(card->dev, "DMic widget addition failed: %d\n", ret);
		/* Don't need to add routes if widget addition failed */
		return ret;
	}

	ret = snd_soc_dapm_add_routes(dapm, dmic_map,
				      ARRAY_SIZE(dmic_map));

	if (ret)
		dev_err(card->dev, "DMic map addition failed: %d\n", ret);

	return ret;
}
```

The Realtek amplifier callback [`asoc_sdw_rt_amp_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_amp.c#L266) runs as the table [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) hook rather than [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47); it counts amps through [`amp_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) on the playback link only, and when the second amp on a stereo link arrives it attaches the left/right channel device properties to both SoundWire peripherals:

```c
/* sound/soc/sdw_utils/soc_sdw_rt_amp.c:266 */
int asoc_sdw_rt_amp_init(struct snd_soc_card *card,
			 struct snd_soc_dai_link *dai_links,
			 struct asoc_sdw_codec_info *info,
			 bool playback)
{
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	struct device *sdw_dev1, *sdw_dev2;
	int ret;

	/* Count amp number and do init on playback link only. */
	if (!playback)
		return 0;

	info->amp_num++;

	if (info->amp_num == 2) {
		sdw_dev1 = bus_find_device_by_name(&sdw_bus_type, NULL, dai_links->codecs[0].name);
		...
		ret = rt_amp_add_device_props(sdw_dev1);
		...
		sdw_dev2 = bus_find_device_by_name(&sdw_bus_type, NULL, dai_links->codecs[1].name);
		...
	}

	return 0;
}
```

The Cirrus speaker callbacks run as table [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) hooks and both limit the speaker volume and add the speaker route. [`asoc_sdw_cs42l43_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l43.c#L108) sets the CS42L43 speaker component string, caps the digital volume with [`snd_soc_limit_volume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L661), and adds `cs42l43_spk_map`:

```c
/* sound/soc/sdw_utils/soc_sdw_cs42l43.c:108 */
int asoc_sdw_cs42l43_spk_rtd_init(struct snd_soc_pcm_runtime *rtd, struct snd_soc_dai *dai)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	int ret;

	if (!(ctx->mc_quirk & SOC_SDW_SIDECAR_AMPS)) {
		/* Will be set by the bridge code in this case */
		card->components = devm_kasprintf(card->dev, GFP_KERNEL,
						  "%s spk:cs42l43-spk",
						  card->components);
		if (!card->components)
			return -ENOMEM;
	}

	ret = snd_soc_limit_volume(card, "cs42l43 Speaker Digital Volume",
				   CS42L43_SPK_VOLUME_0DB);
	...
	ret = snd_soc_dapm_add_routes(dapm, cs42l43_spk_map,
				      ARRAY_SIZE(cs42l43_spk_map));
	...
	return ret;
}
```

[`asoc_sdw_cs_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38) is the CS35L56 amplifier form; it loops the codec DAIs, and for each `cs35l56` codec it builds a per-amp `SPK` widget name from the component [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), applies the volume limit, and adds a route from that widget to the `Speaker` sink:

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

### Capability table keyed by part id with per-codec descriptors and the machine-driver-to-utils call mapping

The capability table [`codec_info_list[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) maps each SoundWire part id to a [`struct asoc_sdw_codec_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73) descriptor (its per-DAI callbacks named by symbol), and the machine driver [`sof_sdw.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) reaches each utils helper ([`asoc_sdw_find_codec_info_part()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L839), [`asoc_sdw_init_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1293), [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865), and [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918)) at the matching stage of link assembly.

```
    codec_info_list[] : part-id ─▶ per-codec descriptor (asoc_sdw_codec_info)
    ──────────────────────────────────────────────────────────────────────

    ┌──────────┬───────────────┬──────────────────────────────────────────┐
    │ part_id  │ name_prefix   │ dais[] (asoc_sdw_dai_info per interface) │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x711    │ "rt711"       │ aif1  JACK   rtd_init=rt_sdca_jack       │
    │ (v3)     │               │                                          │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x722    │ "rt722"       │ aif1  JACK   init=rt_sdca_jack_init      │
    │ (v3)     │               │              exit=rt_sdca_jack_exit      │
    │          │               │              rtd_init=rt_sdca_jack_rtd   │
    │          │               │ aif2  AMP    init=rt_amp_init            │
    │          │               │              exit=rt_amp_exit            │
    │          │               │              rtd_init=rt_mf_sdca_spk     │
    │          │               │ aif3  MIC    rtd_init=rt_dmic_rtd        │
    ├──────────┼───────────────┼──────────────────────────────────────────┤
    │ 0x4243   │ "cs42l43"     │ dp5   JACK   rtd_init=cs42l43_hs_rtd     │
    │          │               │ dp1   MIC    rtd_init=cs42l43_dmic_rtd   │
    │          │               │ dp2   JACK                               │
    │          │               │ dp6   AMP    init=cs42l43_spk_init       │
    │          │               │              rtd_init=cs42l43_spk_rtd    │
    └──────────┴───────────────┴──────────────────────────────────────────┘

    machine driver (sof_sdw)             utils (sdw_utils)
    ────────────────────────             ─────────────────
    enumerate ACPI links         ──▶  asoc_sdw_find_codec_info_part(adr)
    assemble dai links           ──▶  asoc_sdw_init_dai_link(...)
    .ops = sdw_ops               ──▶  asoc_sdw_{startup,prepare,trigger,...}
    .init = asoc_sdw_rtd_init    ──▶  per-codec dais[i].rtd_init(rtd, dai)
```
