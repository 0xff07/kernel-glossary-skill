# SOF PDM DMIC and NHLT

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an x86-64 ACPI Meteor Lake or Lunar Lake machine the PDM microphones wired to the PCH are decimated by the SOF DSP and surface as two capture-only back-end CPU DAIs named `"DMIC01 Pin"` and `"DMIC16k Pin"` in the SOF Intel array [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) are bound to [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) by [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) on [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) and later silicon, the DSP gateway DMA primitives come from [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) selected by [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) for a DAI whose [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) is [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79), how many PDM mics the board carries is read from the ACPI NHLT table by [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) calling [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) over the [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) endpoint descriptors, and the per-format PDM-controller blob the firmware programs into the DMIC hardware is fetched at PCM prepare by [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) and copied into the DMIC copier's [`struct sof_copier_gateway_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L215).

```
    NHLT geometry ─▶ DMIC count ─▶ topology ─▶ DMIC DAI ─▶ PDM ctrl ─▶ capture
    ────────────────────────────────────────────────────────────────────────

    ACPI NHLT table (firmware)                  Probe-time DMIC count
    ┌────────────────────────────────┐          ┌──────────────────────┐
    │ struct nhlt_acpi_table         │  geo     │ check_dmic_num()     │
    │  endpoint_count                │ ───────▶ │  intel_nhlt_get_     │
    │  desc[] (per-endpoint)         │          │   dmic_geo() ─▶ 0..4  │
    │   linktype == NHLT_LINK_DMIC   │          │  clamp + dmic_num    │
    │   nhlt_dmic_array_config       │          │  module-param        │
    │    array_type ─▶ 2CH / 4CH     │          └──────────┬───────────┘
    └────────────────────────────────┘                     │ dmic_num
                                                            ▼
                                            "...-dmic<N>ch" / "...-<N>ch" .tplg
                                                            │  topology load
                                                            ▼
    DPCM back-end CPU DAI (no_pcm)              DSP DMIC copier (topology)
    ┌────────────────────────────────┐         ┌──────────────────────────┐
    │ skl_dai[] entry                │         │ struct sof_ipc4_copier   │
    │  "DMIC01 Pin" / "DMIC16k Pin"  │ ◀─ BE ─▶ │  dai_type=SOF_DAI_INTEL_ │
    │  ops = dmic_dai_ops            │         │   DMIC, dai_index        │
    └───────────────┬────────────────┘         │  gtw_cfg.node_id |=      │
                    │ hda_dai_get_ops()         │   NODE_INDEX_INTEL_DMIC   │
                    ▼                            └──────────┬───────────────┘
        struct hda_dai_widget_dma_ops                      │ prepare
        dmic_ipc4_dma_ops                                  ▼
        get/assign/setup/trigger hext_stream    intel_nhlt_get_endpoint_blob()
                    │                            ─▶ PDM controller blob
                    ▼                                       │
        host LinkDMA stream + DSP DMIC gateway ◀────────────┘
                    │
                    ▼
              ALSA capture PCM (decimated PCM frames)
```

## SUMMARY

The PDM DMIC interface is a Dynamic-PCM back end. The SOF Intel CPU-DAI driver array [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) carries two capture-only [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries, [`'\<DMIC01 Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) and [`'\<DMIC16k Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863), each with [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of 4 and no playback. The array carries no [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at definition time. At probe [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723), reached from [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745), matches every entry whose name contains `"DMIC"` by substring and assigns [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486), but only when the chip's [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) read through [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213) is at least [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24). [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) fills the same four PCM callbacks the SSP back end uses, [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460), [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221), [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), and [`non_hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470).

Beneath the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) layer, [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) caches the per-gateway [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) returned by [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594), which returns [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) for a DAI whose [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) is [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) on [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) and later. [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) differs from the HDA and SSP gateway tables only in its [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048) ([`dmic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242), which folds an S16_LE PDM capture into a half-channel S32_LE stream) and its [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) ([`dmic_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279), which returns the DMIC extended link). The general SOF Intel HDA back-end DAI page covers the gateway-ops selection across all four families, so this page goes deeper on the NHLT geometry behind the DMIC family alone.

How many PDM mics exist is not discovered from the mics but from the NHLT table the firmware publishes. [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) reads the cached [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) from [`nhlt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L548), asks [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) for the channel geometry, applies the `dmic_num` module-parameter override [`dmic_num_override`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L477), and clamps to the 0 to 4 range the topology supports. [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) walks the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) endpoint array, skips any whose [`linktype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L66) is not [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16), and maps the DMIC endpoint's [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104) to [`MIC_ARRAY_2CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L94) or [`MIC_ARRAY_4CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L95). The count [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) returns is written into [`dmic_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L83) of the machine params at [`hda_generic_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1585) and appended to the topology file name as a `-dmic<N>ch` or `-<N>ch` suffix, so a two-mic board and a four-mic board load distinct DMIC topologies.

The DMIC blob that configures the PDM controller flows in two stages tied to the [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) that the topology allocates for the DMIC DAI widget. At topology load [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) parses the [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L341) and [`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L342) tokens and, for the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) case, folds the DMIC index into the gateway [`node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216) through [`SOF_IPC4_NODE_INDEX_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L63). At PCM prepare [`sof_ipc4_prepare_dai_copier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1966) calls [`snd_sof_get_nhlt_endpoint_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1748), which converts the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) link type into [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) and asks [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) for the [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) matching the negotiated rate, channel count, and bit depth, preferring a 32-bit blob and falling back to a 16-bit one. That blob becomes the DMIC copier's [`config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L219) and tells the DSP exactly how to drive the PDM clocks and decimation filters of the on-die DMIC controller.

## SPECIFICATIONS

PDM is the wire format of the microphone bit stream and is specified by the microphone vendors; the PDM clock and data lines carry a one-bit oversampled signal that a decimation filter converts to PCM. The NHLT (Non-HD-Audio Link Table) is an Intel-defined ACPI table located by its [`ACPI_SIG_NHLT`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L12) signature; the kernel models its layout as the packed [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) header followed by an [`endpoint_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L80)-long array of [`struct nhlt_endpoint`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L64) descriptors, each carrying a [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) capability blob and, for a DMIC endpoint, a [`struct nhlt_dmic_array_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L102) microphone-array record. The DSP DMIC gateway and the IPC4 copier blob are defined by the Intel Audio DSP IPC4 firmware interface that the Sound Open Firmware project documents.

- Intel High Definition Audio Specification: the legacy HD-Audio controller and its NHLT companion table that enumerate the on-board PDM endpoints
- ACPI Specification: the table-header format the NHLT [`header`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L79) shares with every other static ACPI table, located through [`acpi_get_table()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L12)

## LINUX KERNEL

### NHLT table model and geometry (sound/hda/core/intel-nhlt.c, intel-nhlt.h)

- [`'\<struct nhlt_acpi_table\>':'include/sound/intel-nhlt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78): the ACPI NHLT table, an [`struct acpi_table_header`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L68) plus an [`endpoint_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L80) and a variable-length [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L81) endpoint array
- [`'\<struct nhlt_endpoint\>':'include/sound/intel-nhlt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L64): one NHLT endpoint, keyed by [`linktype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L66) and self-sized by [`length`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L65), carrying a [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) capability blob
- [`'\<struct nhlt_dmic_array_config\>':'include/sound/intel-nhlt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L102): the DMIC microphone-array record at the front of a DMIC endpoint's blob, whose [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104) names the geometry
- [`'\<enum nhlt_link_type\>':'include/sound/intel-nhlt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L13): the endpoint link types; [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) is the PDM-microphone link
- [`'\<intel_nhlt_get_dmic_geo\>':'sound/hda/core/intel-nhlt.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29): walk the endpoint array, find the [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) endpoint, and return its PDM channel count from the [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104) or the format max-channel count
- [`'\<intel_nhlt_init\>':'sound/hda/core/intel-nhlt.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L7): locate the NHLT table with [`acpi_get_table()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L12) and return the mapped [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78)
- [`'\<intel_nhlt_get_endpoint_blob\>':'sound/hda/core/intel-nhlt.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290): match an endpoint by bus id, link type, direction, channel count, rate, and bit depth, and return the [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) blob the firmware loads into the DMIC controller
- [`MIC_ARRAY_2CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L94) / [`MIC_ARRAY_4CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L95): the 2 and 4 channel geometry constants [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) returns for the standard array types

### SOF DMIC count detection (sof/intel/hda.c)

- [`'\<check_dmic_num\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546): read the cached NHLT table, call [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29), apply the [`dmic_num_override`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L477) module-parameter override, and clamp the result to 0 to 4
- [`'dmic_num_override':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L477): the `dmic_num` module parameter, default -1 (use NHLT), that overrides the detected count
- [`'\<nhlt\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L548): the [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) pointer cached in [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L497) at probe by [`intel_nhlt_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L7)
- [`'\<hda_generic_machine_select\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1497): the machine-table fixup that writes [`dmic_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L83) and appends the `-dmic<N>ch` topology suffix from [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546)

### SOF DMIC back-end DAI and ops binding (sof/intel/hda-dai.c)

- [`'\<skl_dai\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788): the shared [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array of every SSP, DMIC, HDA, and codec CPU DAI, exported with `SND_SOC_SOF_INTEL_HDA_COMMON`
- [`'\<DMIC01 Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) / [`'\<DMIC16k Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863): the two capture-only DMIC back-end DAI entries, one for the 48 kHz family and one for the 16 kHz wake/voice family, each [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of 4
- [`'dmic_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486): the DMIC back-end [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), routing hw_params through [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460)
- [`'\<dmic_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723): bind [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) onto the `"DMIC"` entries when [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) is at least [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24)
- [`'\<hda_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745): the probe-time binder that delegates the DMIC entries to [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) and initialises NHLT for IPC4
- [`'\<non_hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) / [`'\<non_hda_dai_hw_params_data\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372): the DMIC and SSP hw_params, which run the shared HDA stream handling and then append the gateway DMA-config TLV
- [`'\<non_hda_dai_prepare\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470): re-run [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) against the stored [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L93) hw_params after an xrun or a restart
- [`'\<hda_dai_trigger\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) / [`'\<hda_dai_hw_free\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221): the trigger and hw_free callbacks shared with the HDA and SSP back ends, driving the DSP pipeline state and the link DMA cleanup
- [`'\<widget_to_copier\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L363): reach the [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) backing a DAI widget through its [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547)

### IPC4 DMIC gateway DMA ops and DAI type (sof/intel/hda-dai-ops.c, hda.h, sof/dai.h)

- [`'dmic_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465): the DMIC gateway [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), differing from the HDA and SSP tables only in [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048) and [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051)
- [`'\<hda_select_dai_widget_ops\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594): select the gateway by the SOF DAI [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98); return [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) for [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) on ACE 2.0 and later
- [`'\<hda_dai_get_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70): resolve and cache the per-gateway [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) in [`platform_private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L556) via [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594)
- [`'\<dmic_calc_stream_format\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242): compute the HDAudio format word for a DMIC capture, folding an S16_LE PDM stream into a half-channel S32_LE stream
- [`'\<dmic_get_hlink\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279): return the DMIC [`struct hdac_ext_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L95) through [`hdac_bus_eml_dmic_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L817)
- [`'\<struct hda_dai_widget_dma_ops\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027): the per-gateway function pointer struct with the get/assign/setup/reset hext-stream, pre/trigger/post-trigger, [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048), and [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) members
- [`'\<enum sof_ipc_dai_type\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76): the SOF DAI-type enumeration; [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) is the PCH PDM interface type, distinct from [`SOF_DAI_INTEL_SSP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L78), [`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80), and [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81)

### Topology DMIC copier and blob fetch (sof/ipc4-topology.c, ipc4-topology.h)

- [`'\<sof_ipc4_widget_setup_comp_dai\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748): allocate the DAI [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), parse [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L341)/[`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L342), and fold the DMIC index into [`node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216) for the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) case
- [`'\<sof_ipc4_prepare_dai_copier\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1966): the runtime-prepare helper that narrows the params to the DAI formats and calls [`snd_sof_get_nhlt_endpoint_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1748) to fetch the DMIC blob
- [`'\<snd_sof_get_nhlt_endpoint_data\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1748): convert [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) to [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) and call [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290), preferring a 32-bit blob and falling back to 16-bit
- [`'\<struct sof_ipc4_copier\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332): the DAI copier private data, wrapping the wire payload [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L333), the [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L341)/[`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L342), the [`copier_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L334) blob, and the [`dma_config_tlv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L343)
- [`'\<struct sof_ipc4_copier_data\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229): the wire-format copier payload, with the [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L230) input format and the [`gtw_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L233) gateway node
- [`'\<struct sof_copier_gateway_cfg\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L215): the gateway [`node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216), [`dma_buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L217), [`config_length`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L218), and trailing [`config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L219) blob the DMIC NHLT cfg is copied into
- [`SOF_IPC4_NODE_INDEX_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L63): fold the DMIC DAI index into the low 3 bits of the gateway [`node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model the DMIC back-end DAIs are the back-end side of
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface families the DMIC DAI descriptor describes
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the HDAudio extended multi-link architecture whose DMIC link the gateway programs
- [`Documentation/firmware-guide/acpi/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/index.rst): the ACPI firmware-table model the NHLT table is read from

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF Intel HDA DSP architecture](https://thesofproject.github.io/latest/architectures/firmware/intel/index.html)
- [Sound Open Firmware: IPC4 ABI and topology](https://thesofproject.github.io/latest/introduction/ipc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The objects below are the NHLT table the firmware owns, the two DMIC back-end DAI descriptors and their ops, and the DMIC copier the topology allocates. The NHLT table is mapped once at probe and shared read-only; the DAI descriptors are static for the driver lifetime and have their ops patched in place at probe; the DMIC copier is allocated at topology load and lives until the widget frees. A reader can follow a link from the NHLT geometry to the DMIC count, from the count to the topology file, and from the topology copier to the PDM-controller blob.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) (mapped) | [`intel_nhlt_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L7) at probe | cached in [`nhlt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L548) until [`intel_nhlt_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L23) |
| [`'\<DMIC01 Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) / [`'\<DMIC16k Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863) back-end DAI | static in [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) | whole driver lifetime; ops patched at probe |
| [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) binding | [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) on ACE 2.0+ | whole driver lifetime |
| [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) ([`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465)) | static; cached by [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) | [`platform_private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L556) for the DAI lifetime |
| [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) (DMIC DAI) | [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) at load | [`dai->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) until ipc_free |
| DMIC blob ([`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49)) | fetched by [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) at prepare | copied into [`config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L219) for the stream |

The DMIC back-end DAI is the CPU side of a no_pcm back-end link in Dynamic PCM. Userspace opens a front-end PCM, and the DPCM core triggers the [`'\<DMIC01 Pin\>'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) back end behind it. The DAI carries [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) as its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98), which distinguishes the PCH PDM path from the SSP, HDA, and SoundWire-over-ALH paths and selects [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) and the [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) blob lookup.

## DETAILS

### The NHLT table model

The NHLT is a static ACPI table the platform firmware publishes to describe every non-HD-Audio link on the package, including the PDM DMIC ports. The kernel models it as a packed [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78): a standard [`struct acpi_table_header`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L68), a one-byte [`endpoint_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L80), and a variable-length array of [`struct nhlt_endpoint`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L64) descriptors:

```c
/* include/sound/intel-nhlt.h:78 */
struct nhlt_acpi_table {
	struct acpi_table_header header;
	u8 endpoint_count;
	struct nhlt_endpoint desc[];
} __packed;
```

Each [`struct nhlt_endpoint`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L64) is self-sizing through its [`length`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L65) field, so the array is walked by adding [`length`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L65) bytes to advance from one descriptor to the next rather than by indexing a fixed-stride array. The [`linktype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L66) field selects which kind of link the endpoint describes, and a PDM mic endpoint carries [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16):

```c
/* include/sound/intel-nhlt.h:64 */
struct nhlt_endpoint {
	u32  length;
	u8   linktype;
	u8   instance_id;
	u16  vendor_id;
	u16  device_id;
	u16  revision_id;
	u32  subsystem_id;
	u8   device_type;
	u8   direction;
	u8   virtual_bus_id;
	struct nhlt_specific_cfg config;
} __packed;
```

```c
/* include/sound/intel-nhlt.h:13 */
enum nhlt_link_type {
	NHLT_LINK_HDA = 0,
	NHLT_LINK_DSP = 1,
	NHLT_LINK_DMIC = 2,
	NHLT_LINK_SSP = 3,
	NHLT_LINK_INVALID
};
```

The [`config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L75) member is a [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49), a [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L50)-prefixed byte blob that for a DMIC endpoint begins with a [`struct nhlt_dmic_array_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L102) and is followed by the [`struct nhlt_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L59) format list. The mic-array record names the geometry through [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104):

```c
/* include/sound/intel-nhlt.h:102 */
struct nhlt_dmic_array_config {
	struct nhlt_device_specific_config device_config;
	u8 array_type;
} __packed;
```

The table is mapped once at probe by [`intel_nhlt_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L7), which locates it by signature and returns the mapped pointer without copying:

```c
/* sound/hda/core/intel-nhlt.c:7 */
struct nhlt_acpi_table *intel_nhlt_init(struct device *dev)
{
	struct nhlt_acpi_table *nhlt;
	acpi_status status;

	status = acpi_get_table(ACPI_SIG_NHLT, 0,
				(struct acpi_table_header **)&nhlt);
	if (ACPI_FAILURE(status)) {
		dev_warn(dev, "NHLT table not found\n");
		return NULL;
	}

	return nhlt;
}
```

The SOF Intel driver caches that pointer in the [`nhlt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L548) field of [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L497), and [`intel_nhlt_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L23) returns the ACPI mapping when the driver tears down.

```
    NHLT table struct containment (DMIC endpoint shown)
    ───────────────────────────────────────────────────

    struct nhlt_acpi_table
    ┌──────────────────────────────────────────────────┐
    │ acpi_table_header header                          │
    │ u8 endpoint_count                                 │
    │ struct nhlt_endpoint desc[]  (walk by length)     │
    └───────────────────────┬──────────────────────────┘
                            │  desc[i]
                            ▼
    struct nhlt_endpoint
    ┌──────────────────────────────────────────────────┐
    │ u32 length        (stride to next desc)           │
    │ u8  linktype  == NHLT_LINK_DMIC for a PDM mic     │
    │ u8  direction                                     │
    │ struct nhlt_specific_cfg config                   │
    └───────────────────────┬──────────────────────────┘
                            │  config (size-prefixed blob)
                            ▼
    struct nhlt_specific_cfg  { u32 size; u8 caps[]; }
    ┌──────────────────────────────────────────────────┐
    │ caps[0..] begins with:                            │
    │   struct nhlt_dmic_array_config { ... array_type }│
    │ caps[size..] continues with:                      │
    │   struct nhlt_fmt  (format list)                  │
    └──────────────────────────────────────────────────┘
```

### intel_nhlt_get_dmic_geo reads the PDM geometry

[`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) is the function that turns the NHLT table into a PDM microphone count. It walks the endpoint array, skips every endpoint whose [`linktype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L66) is not [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16), and for the DMIC endpoint reads both the format list (for a maximum channel count) and the [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104) (for the array geometry). The walk advances by [`length`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L65), and the [`struct nhlt_dmic_array_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L102) and the [`struct nhlt_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L59) are reached as offsets into the endpoint's [`caps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L51) blob:

```c
/* sound/hda/core/intel-nhlt.c:47 */
	for (j = 0, epnt = nhlt->desc; j < nhlt->endpoint_count; j++,
	     epnt = (struct nhlt_endpoint *)((u8 *)epnt + epnt->length)) {

		if (epnt->linktype != NHLT_LINK_DMIC)
			continue;

		cfg = (struct nhlt_dmic_array_config  *)(epnt->config.caps);
		fmt_configs = (struct nhlt_fmt *)(epnt->config.caps + epnt->config.size);
```

When the endpoint declares a microphone array, [`array_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L104) decides the geometry. The two small/big 2-channel layouts return [`MIC_ARRAY_2CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L94), the three 4-channel layouts return [`MIC_ARRAY_4CH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L95), and a vendor-defined array reads its own [`nb_mics`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L109) count from the [`struct nhlt_vendor_dmic_array_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L107) trailer:

```c
/* sound/hda/core/intel-nhlt.c:80 */
		if (cfg->device_config.config_type != NHLT_CONFIG_TYPE_MIC_ARRAY) {
			dmic_geo = max_ch;
		} else {
			switch (cfg->array_type) {
			case NHLT_MIC_ARRAY_2CH_SMALL:
			case NHLT_MIC_ARRAY_2CH_BIG:
				dmic_geo = MIC_ARRAY_2CH;
				break;

			case NHLT_MIC_ARRAY_4CH_1ST_GEOM:
			case NHLT_MIC_ARRAY_4CH_L_SHAPED:
			case NHLT_MIC_ARRAY_4CH_2ND_GEOM:
				dmic_geo = MIC_ARRAY_4CH;
				break;
			case NHLT_MIC_ARRAY_VENDOR_DEFINED:
				cfg_vendor = (struct nhlt_vendor_dmic_array_config *)cfg;
				dmic_geo = cfg_vendor->nb_mics;
				break;
			default:
				dev_warn(dev, "%s: undefined DMIC array_type 0x%0x\n",
					 __func__, cfg->array_type);
			}
```

The function returns [`dmic_geo`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L35), the channel count of the DMIC endpoint. When the configuration is not a mic array (a plain capture endpoint with no [`NHLT_CONFIG_TYPE_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L115) record), it falls back to [`max_ch`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L36), the largest channel count any format in the [`struct nhlt_fmt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L59) list declares.

```
    array_type ─▶ dmic_geo  (cfg->array_type switch)
    ─────────────────────────────────────────────────

    cfg->array_type                          dmic_geo
    ┌──────────────────────────────────┐     ┌───────────────┐
    │ NHLT_MIC_ARRAY_2CH_SMALL         │ ──▶ │ MIC_ARRAY_2CH │
    │ NHLT_MIC_ARRAY_2CH_BIG           │     │   (2)         │
    └──────────────────────────────────┘     └───────────────┘
    ┌──────────────────────────────────┐     ┌───────────────┐
    │ NHLT_MIC_ARRAY_4CH_1ST_GEOM      │ ──▶ │ MIC_ARRAY_4CH │
    │ NHLT_MIC_ARRAY_4CH_L_SHAPED      │     │   (4)         │
    │ NHLT_MIC_ARRAY_4CH_2ND_GEOM      │     └───────────────┘
    └──────────────────────────────────┘
    ┌──────────────────────────────────┐     ┌───────────────┐
    │ NHLT_MIC_ARRAY_VENDOR_DEFINED    │ ──▶ │ cfg_vendor->  │
    │                                  │     │   nb_mics     │
    └──────────────────────────────────┘     └───────────────┘
    not NHLT_CONFIG_TYPE_MIC_ARRAY    ─▶ max_ch (from nhlt_fmt)
```

### check_dmic_num clamps and overrides the count

[`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) is the SOF Intel wrapper that turns the raw NHLT geometry into the count the topology and machine driver use. It reads the cached table, calls [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29), honours the [`dmic_num_override`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L477) module parameter when it is not -1, and clamps the result to 0 to 4:

```c
/* sound/soc/sof/intel/hda.c:546 */
static int check_dmic_num(struct snd_sof_dev *sdev)
{
	struct sof_intel_hda_dev *hdev = sdev->pdata->hw_pdata;
	struct nhlt_acpi_table *nhlt;
	int dmic_num = 0;

	nhlt = hdev->nhlt;
	if (nhlt)
		dmic_num = intel_nhlt_get_dmic_geo(sdev->dev, nhlt);

	dev_info(sdev->dev, "DMICs detected in NHLT tables: %d\n", dmic_num);

	/* allow for module parameter override */
	if (dmic_num_override != -1) {
		dev_dbg(sdev->dev,
			"overriding DMICs detected in NHLT tables %d by kernel param %d\n",
			dmic_num, dmic_num_override);
		dmic_num = dmic_num_override;
	}

	if (dmic_num < 0 || dmic_num > 4) {
		dev_dbg(sdev->dev, "invalid dmic_number %d\n", dmic_num);
		dmic_num = 0;
	}

	return dmic_num;
}
```

The [`dmic_num_override`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L477) parameter is the `dmic_num` module option, defaulting to -1 so the NHLT geometry is used unless an operator forces a count:

```c
/* sound/soc/sof/intel/hda.c:477 */
static int dmic_num_override = -1;
module_param_named(dmic_num, dmic_num_override, int, 0444);
MODULE_PARM_DESC(dmic_num, "SOF HDA DMIC number");
```

The count [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) returns is consumed by the machine-table fixup [`hda_generic_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1497), which stores it in [`dmic_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L83) of the machine params and appends it to the topology file name, picking a distinct `.tplg` per microphone count:

```c
/* sound/soc/sof/intel/hda.c:1584 */
		/* report to machine driver if any DMICs are found */
		mach->mach_params.dmic_num = check_dmic_num(sdev);

		if (sdw_mach_found || mach->tplg_quirk_mask & SND_SOC_ACPI_TPLG_INTEL_DMIC_NUMBER)
			dmic_fixup = true;

		if (tplg_fixup &&
		    dmic_fixup &&
		    mach->mach_params.dmic_num) {
			tplg_filename = devm_kasprintf(sdev->dev, GFP_KERNEL,
						       "%s%s%d%s",
						       sof_pdata->tplg_filename,
						       i2s_mach_found ? "-dmic" : "-",
						       mach->mach_params.dmic_num,
						       "ch");
			if (!tplg_filename)
				return NULL;

			sof_pdata->tplg_filename = tplg_filename;
		}
```

A two-mic board loads a `...-dmic2ch.tplg` (or `...-2ch.tplg`) topology and a four-mic board a `...-dmic4ch.tplg`, so the topology the firmware runs already matches the channel count the NHLT table reported.

### The DMIC back-end DAIs in skl_dai[]

The SOF Intel platform driver registers one CPU-DAI driver array, [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), and the two DMIC entries are capture-only with four channels and no playback record:

```c
/* sound/soc/sof/intel/hda-dai.c:855 */
{
	.name = "DMIC01 Pin",
	.capture = {
		.channels_min = 1,
		.channels_max = 4,
	},
},
{
	.name = "DMIC16k Pin",
	.capture = {
		.channels_min = 1,
		.channels_max = 4,
	},
},
```

The name `"DMIC01 Pin"` is the 48 kHz capture front for the on-board PDM array, and `"DMIC16k Pin"` is the parallel 16 kHz front used for low-power wake-word and voice capture. The entries carry no [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) here, only a name and the channel capability record, because the ops depend on the silicon generation and are bound at probe.

### dmic_set_dai_drv_ops binds dmic_dai_ops by name

At probe [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745) walks the driver array and delegates the DMIC binding to [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723), which matches each driver entry whose name contains `"DMIC"` by substring and assigns [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486), but only when the chip's [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) read through [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213) is at least [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24):

```c
/* sound/soc/sof/intel/hda-dai.c:723 */
static void dmic_set_dai_drv_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *ops)
{
	const struct sof_intel_dsp_desc *chip;
	int i;

	chip = get_chip_info(sdev->pdata);

	if (chip->hw_ip_version >= SOF_INTEL_ACE_2_0) {
		for (i = 0; i < ops->num_drv; i++) {
			if (strstr(ops->drv[i].name, "DMIC"))
				ops->drv[i].ops = &dmic_dai_ops;
		}
	}
}
```

The loop reads [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351) and the driver array [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350), which on Intel is [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), so it matches `"DMIC01 Pin"` and `"DMIC16k Pin"` by substring. The [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) gate restricts this DMIC DAI path to Lunar Lake and newer; Meteor Lake's [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) leaves the DMIC entries without these ops:

```c
/* sound/soc/sof/intel/shim.h:14 */
enum sof_intel_hw_ip_version {
	...
	SOF_INTEL_ACE_1_0,	/* MeteorLake */
	SOF_INTEL_ACE_2_0,	/* LunarLake */
	...
};
```

[`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) fills exactly four callbacks of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), the same set the SSP back end uses:

```c
/* sound/soc/sof/intel/hda-dai.c:486 */
static const struct snd_soc_dai_ops dmic_dai_ops = {
	.hw_params = non_hda_dai_hw_params,
	.hw_free = hda_dai_hw_free,
	.trigger = hda_dai_trigger,
	.prepare = non_hda_dai_prepare,
};
```

### non_hda_dai_hw_params binds the host stream and the DMA-config TLV

The DMIC [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) is [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460), which forwards to [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) with the [`SOF_DAI_CONFIG_FLAGS_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L62) flag:

```c
/* sound/soc/sof/intel/hda-dai.c:460 */
static int non_hda_dai_hw_params(struct snd_pcm_substream *substream,
				 struct snd_pcm_hw_params *params,
				 struct snd_soc_dai *cpu_dai)
{
	struct snd_sof_dai_config_data data = { 0 };
	unsigned int flags = SOF_DAI_CONFIG_FLAGS_HW_PARAMS;

	return non_hda_dai_hw_params_data(substream, params, cpu_dai, &data, flags);
}
```

[`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) first resolves the gateway ops with [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70), runs the shared HDA stream handling through [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240) to reserve a LinkDMA host stream, then writes a [`struct sof_ipc4_dma_config_tlv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L304) onto the DMIC copier so the DSP gateway learns the host stream tag:

```c
/* sound/soc/sof/intel/hda-dai.c:392 */
	ops = hda_dai_get_ops(substream, cpu_dai);
	if (!ops) {
		dev_err(cpu_dai->dev, "DAI widget ops not set\n");
		return -EINVAL;
	}

	sdev = widget_to_sdev(w);
	hext_stream = ops->get_hext_stream(sdev, cpu_dai, substream);

	/* nothing more to do if the link is already prepared */
	if (hext_stream && hext_stream->link_prepared)
		return 0;

	/* use HDaudio stream handling */
	ret = hda_dai_hw_params_data(substream, params, cpu_dai, data, flags);
```

```c
/* sound/soc/sof/intel/hda-dai.c:431 */
	/* configure TLV */
	ipc4_copier = widget_to_copier(w);

	for_each_rtd_cpu_dais(rtd, cpu_dai_id, dai) {
		if (dai == cpu_dai)
			break;
	}

	dma_config_tlv = &ipc4_copier->dma_config_tlv[cpu_dai_id];
	dma_config_tlv->type = SOF_IPC4_GTW_DMA_CONFIG_ID;
	/* dma_config_priv_size is zero */
	dma_config_tlv->length = sizeof(dma_config_tlv->dma_config);

	dma_config = &dma_config_tlv->dma_config;

	dma_config->dma_method = SOF_IPC4_DMA_METHOD_HDA;
	dma_config->pre_allocated_by_host = 1;
	dma_config->dma_channel_id = stream_id - 1;
	dma_config->stream_id = stream_id;
```

The [`copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L432) is reached through [`widget_to_copier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L363), and the per-CPU-DAI slot in [`dma_config_tlv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L343) records the host DMA stream id so the DSP DMIC gateway pulls from the same channel the host allocated. [`non_hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470) re-runs this same hw_params against the stored [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L93) hw_params so a stream restarted after an xrun reprograms its LinkDMA before it runs again, while [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) and [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) are shared with the HDA and SSP families and described on the sibling page.

### hda_select_dai_widget_ops returns dmic_ipc4_dma_ops

The per-widget DMA gateway carries the host-side stream programming and the DMIC stream-format helper. [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) caches the gateway returned by [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594), which reads the SOF DAI [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) and, for a DMIC widget on ACE 2.0 or later, returns [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465):

```c
/* sound/soc/sof/intel/hda-dai-ops.c:638 */
		switch (sdai->type) {
		case SOF_DAI_INTEL_HDA:
			if (pipeline->use_chain_dma)
				return &hda_ipc4_chain_dma_ops;

			return &hda_ipc4_dma_ops;
		case SOF_DAI_INTEL_SSP:
			if (chip->hw_ip_version < SOF_INTEL_ACE_2_0)
				return NULL;
			return &ssp_ipc4_dma_ops;
		case SOF_DAI_INTEL_DMIC:
			if (chip->hw_ip_version < SOF_INTEL_ACE_2_0)
				return NULL;
			return &dmic_ipc4_dma_ops;
```

The gateway wires the shared hext-stream assignment and trigger callbacks (identical to the HDA and SSP tables) plus a DMIC-specific [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048) and [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051):

```c
/* sound/soc/sof/intel/hda-dai-ops.c:465 */
static const struct hda_dai_widget_dma_ops dmic_ipc4_dma_ops = {
	.get_hext_stream = hda_ipc4_get_hext_stream,
	.assign_hext_stream = hda_assign_hext_stream,
	.release_hext_stream = hda_release_hext_stream,
	.setup_hext_stream = hda_setup_hext_stream,
	.reset_hext_stream = hda_reset_hext_stream,
	.pre_trigger = hda_ipc4_pre_trigger,
	.trigger = hda_trigger,
	.post_trigger = hda_ipc4_post_trigger,
	.calc_stream_format = dmic_calc_stream_format,
	.get_hlink = dmic_get_hlink,
};
```

The [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) type these tables instantiate is the per-gateway function pointer struct shared by all four back-end families, with the get/assign/setup/reset hext-stream, pre/trigger/post-trigger, format, and link members:

```c
/* sound/soc/sof/intel/hda.h:1027 */
struct hda_dai_widget_dma_ops {
	struct hdac_ext_stream *(*get_hext_stream)(struct snd_sof_dev *sdev,
						   struct snd_soc_dai *cpu_dai,
						   struct snd_pcm_substream *substream);
	struct hdac_ext_stream *(*assign_hext_stream)(struct snd_sof_dev *sdev,
						      struct snd_soc_dai *cpu_dai,
						      struct snd_pcm_substream *substream);
	void (*release_hext_stream)(struct snd_sof_dev *sdev, struct snd_soc_dai *cpu_dai,
				    struct snd_pcm_substream *substream);
	void (*setup_hext_stream)(struct snd_sof_dev *sdev, struct hdac_ext_stream *hext_stream,
				  unsigned int format_val);
	void (*reset_hext_stream)(struct snd_sof_dev *sdev, struct hdac_ext_stream *hext_sream);
	int (*pre_trigger)(struct snd_sof_dev *sdev, struct snd_soc_dai *cpu_dai,
			   struct snd_pcm_substream *substream, int cmd);
	int (*trigger)(struct snd_sof_dev *sdev, struct snd_soc_dai *cpu_dai,
		       struct snd_pcm_substream *substream, int cmd);
	int (*post_trigger)(struct snd_sof_dev *sdev, struct snd_soc_dai *cpu_dai,
			    struct snd_pcm_substream *substream, int cmd);
	void (*codec_dai_set_stream)(struct snd_sof_dev *sdev,
				     struct snd_pcm_substream *substream,
				     struct hdac_stream *hstream);
	unsigned int (*calc_stream_format)(struct snd_sof_dev *sdev,
					   struct snd_pcm_substream *substream,
					   struct snd_pcm_hw_params *params);
	struct hdac_ext_link * (*get_hlink)(struct snd_sof_dev *sdev,
					    struct snd_pcm_substream *substream);
};
```

The DMIC [`codec_dai_set_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1045) member is left NULL because there is no HDAudio codec to hand the stream tag to; only the HDA gateway fills it.

```
    hda_select_dai_widget_ops: sdai->type ─▶ gateway ops table
    ──────────────────────────────────────────────────────────
    (returns a struct hda_dai_widget_dma_ops *)

    sdai->type                     gateway ops table
    ┌─────────────────────┐        ┌───────────────────────────┐
    │ SOF_DAI_INTEL_HDA   │ ─────▶ │ hda_ipc4_chain_dma_ops    │
    │                     │        │   (if use_chain_dma) else │
    │                     │        │ hda_ipc4_dma_ops          │
    ├─────────────────────┤        ├───────────────────────────┤
    │ SOF_DAI_INTEL_SSP   │ ─────▶ │ ssp_ipc4_dma_ops          │
    │ (ACE_2_0+, else 0)  │        │                           │
    ├─────────────────────┤        ├───────────────────────────┤
    │ SOF_DAI_INTEL_DMIC  │ ─────▶ │ dmic_ipc4_dma_ops         │
    │ (ACE_2_0+, else 0)  │        │   calc_stream_format =    │
    │                     │        │     dmic_calc_stream_     │
    │                     │        │       format              │
    │                     │        │   get_hlink = dmic_get_   │
    │                     │        │     hlink                 │
    └─────────────────────┘        └───────────────────────────┘
```

### dmic_calc_stream_format folds S16_LE into half-channel S32_LE

The one DMIC-specific format step is [`dmic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242). The DMIC hardware transports a 32-bit sample over its link even when userspace requested S16_LE, so when the negotiated format is S16_LE this helper rewrites it as S32_LE, halves the channel count, and uses a 32-bit width before computing the HDAudio format word:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:242 */
static unsigned int dmic_calc_stream_format(struct snd_sof_dev *sdev,
					    struct snd_pcm_substream *substream,
					    struct snd_pcm_hw_params *params)
{
	unsigned int format_val;
	snd_pcm_format_t format;
	unsigned int channels;
	unsigned int width;
	unsigned int bits;

	channels = params_channels(params);
	format = params_format(params);
	width = params_physical_width(params);

	if (format == SNDRV_PCM_FORMAT_S16_LE) {
		format = SNDRV_PCM_FORMAT_S32_LE;
		channels /= 2;
		width = 32;
	}

	bits = snd_hdac_stream_format_bits(format, SNDRV_PCM_SUBFORMAT_STD, width);
	format_val = snd_hdac_stream_format(channels, bits, params_rate(params));
	...
	return format_val;
}
```

The [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) op [`dmic_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279) returns the DMIC extended link so the gateway can program the DMIC extended-link registers rather than the legacy HDA LOSIDV register:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:279 */
static struct hdac_ext_link *dmic_get_hlink(struct snd_sof_dev *sdev,
					    struct snd_pcm_substream *substream)
{
	struct hdac_bus *bus = sof_to_bus(sdev);

	return hdac_bus_eml_dmic_get_hlink(bus);
}
```

Alongside that link lookup, the gateway's format step folds a 16-bit capture upward, promoting S16_LE to S32_LE and halving the channel count for the 32-bit link:

```
    dmic_calc_stream_format: S16_LE fold to half-channel S32_LE
    ──────────────────────────────────────────────────────────
    (only when negotiated format == SNDRV_PCM_FORMAT_S16_LE)

    negotiated params                  link stream format
    ┌──────────────────────────┐       ┌──────────────────────────┐
    │ format   = S16_LE        │ ────▶ │ format   = S32_LE        │
    │ channels = N             │       │ channels = N / 2         │
    │ width    = 16            │       │ width    = 32            │
    └──────────────────────────┘       └────────────┬─────────────┘
                                                    │
                                                    ▼
                       snd_hdac_stream_format(channels, bits, rate)
                                                    │
                                                    ▼
                                               format_val
```

### The DMIC copier and its gateway node id

The topology binds a DSP DMIC copier behind each DMIC DAI widget, and that copier is a [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332). Its [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L341) holds the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) value, its [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L333) holds the wire payload, and its [`copier_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L334) blob is where the NHLT-derived PDM controller configuration ends up:

```c
/* sound/soc/sof/ipc4-topology.h:332 */
struct sof_ipc4_copier {
	struct sof_ipc4_copier_data data;
	u32 *copier_config;
	uint32_t ipc_config_size;
	void *ipc_config_data;
	struct sof_ipc4_available_audio_format available_fmt;
	u32 frame_fmt;
	struct sof_ipc4_msg msg;
	struct sof_ipc4_gtw_attributes *gtw_attr;
	u32 dai_type;
	int dai_index;
	struct sof_ipc4_dma_config_tlv dma_config_tlv[SOF_IPC4_DMA_DEVICE_MAX_COUNT];
};
```

The wire payload [`struct sof_ipc4_copier_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) carries the gateway record [`struct sof_copier_gateway_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L215), whose [`config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L219) trailer is the variable-length blob that names the gateway and holds the per-controller configuration:

```c
/* sound/soc/sof/ipc4-topology.h:215 */
struct sof_copier_gateway_cfg {
	uint32_t node_id;
	uint32_t dma_buffer_size;
	uint32_t config_length;
	uint32_t config_data[];
};
```

At topology load [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) parses the [`SOF_TKN_DAI_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/sof/tokens.h) and [`SOF_TKN_DAI_INDEX`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/sof/tokens.h) tokens into [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L341) and [`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L342), sets the node type, and for the DMIC case folds the DMIC index into the low bits of [`node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216) through [`SOF_IPC4_NODE_INDEX_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L63):

```c
/* sound/soc/sof/ipc4-topology.c:855 */
	case SOF_DAI_INTEL_SSP:
		/* set SSP DAI index as the node_id */
		ipc4_copier->data.gtw_cfg.node_id |=
			SOF_IPC4_NODE_INDEX_INTEL_SSP(ipc4_copier->dai_index);
		break;
	case SOF_DAI_INTEL_DMIC:
		/* set DMIC DAI index as the node_id */
		ipc4_copier->data.gtw_cfg.node_id |=
			SOF_IPC4_NODE_INDEX_INTEL_DMIC(ipc4_copier->dai_index);
		break;
```

The DMIC node index occupies the low 3 bits, separate from the SSP variant which occupies bits 4 to 7:

```c
/* sound/soc/sof/ipc4-topology.h:60 */
/* Node ID for SSP type DAI copiers */
#define SOF_IPC4_NODE_INDEX_INTEL_SSP(x) (((x) & 0xf) << 4)

/* Node ID for DMIC type DAI copiers */
#define SOF_IPC4_NODE_INDEX_INTEL_DMIC(x) ((x) & 0x7)
```

Unlike the SSP and ALH cases, the DMIC case does not allocate a default [`struct sof_ipc4_gtw_attributes`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L242) blob at load; its real gateway blob is the NHLT PDM-controller configuration fetched at prepare time.

```
    gtw_cfg.node_id: DAI index folded into the low bits
    ──────────────────────────────────────────────────────

    bit     7   6   5   4   3   2   1   0
          ┌───┬───┬───┬───┬───┬───┬───┬───┐
          │ SSP idx (7:4) │   │ DMIC(2:0) │
          └───┴───┴───┴───┴───┴───┴───┴───┘

    SOF_IPC4_NODE_INDEX_INTEL_DMIC(x) = ((x) & 0x7)        bits 2:0
    SOF_IPC4_NODE_INDEX_INTEL_SSP(x)  = (((x) & 0xf) << 4) bits 7:4
    OR-ed into gtw_cfg.node_id by sof_ipc4_widget_setup_comp_dai
```

### intel_nhlt_get_endpoint_blob configures the PDM controller

The actual PDM controller configuration is not known until the PCM negotiates a rate, channel count, and bit depth, so it is fetched at prepare. [`sof_ipc4_prepare_dai_copier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1966) narrows the params to the formats the DAI declares and calls [`snd_sof_get_nhlt_endpoint_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1748), which converts the [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) link type into [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) and reads the negotiated channel count, rate, and width, preferring a 32-bit blob when the copier supports multiple formats:

```c
/* sound/soc/sof/ipc4-topology.c:1762 */
	/* convert to NHLT type */
	switch (linktype) {
	case SOF_DAI_INTEL_DMIC:
		nhlt_type = NHLT_LINK_DMIC;
		channel_count = params_channels(params);
		sample_rate = params_rate(params);
		bit_depth = params_width(params);

		/* Prefer 32-bit blob if copier supports multiple formats */
		if (bit_depth <= 16 && !single_bitdepth) {
			dev_dbg(sdev->dev, "Looking for 32-bit blob first for DMIC\n");
			format_change = true;
			bit_depth = 32;
		}
		break;
```

It then asks [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) for the [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) matching those parameters, falling back to a 16-bit blob if the 32-bit one is absent:

```c
/* sound/soc/sof/ipc4-topology.c:1803 */
	/* find NHLT blob with matching params */
	cfg = intel_nhlt_get_endpoint_blob(sdev->dev, ipc4_data->nhlt, dai_index, nhlt_type,
					   bit_depth, bit_depth, channel_count, sample_rate,
					   dir, dev_type);

	if (!cfg) {
		bool get_new_blob = false;

		if (format_change) {
			...
			if (linktype == SOF_DAI_INTEL_DMIC) {
				bit_depth = 16;
				if (params_width(params) == 16)
					format_change = false;
			}
			...
			get_new_blob = true;
		} else if (linktype == SOF_DAI_INTEL_DMIC && !single_bitdepth) {
			bit_depth = 16;
			format_change = true;
			get_new_blob = true;
		}
		...
	}
```

[`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) matches an endpoint on bus id, link type, direction, channel count, rate, and bit depth, with a DMIC-specific allowance that the hardware supports only one 32-bit sample size (24 bits on the MSB side, the low two bits used for channel number), so it accepts either a vbps of 24 or 32 for a 32-bit DMIC blob:

```c
/* sound/hda/core/intel-nhlt.c:303 */
	if (link_type == NHLT_LINK_DMIC && bps == 32 && (vbps == 24 || vbps == 32)) {
		/*
		 * The DMIC hardware supports only one type of 32 bits sample
		 * size, which is 24 bit sampling on the MSB side and bits[1:0]
		 * are used for indicating the channel number.
		 ...
		 */
		ignore_vbps = true;
	}
	...
	epnt = (struct nhlt_endpoint *)nhlt->desc;

	for (i = 0; i < nhlt->endpoint_count; i++) {
		if (nhlt_check_ep_match(dev, epnt, bus_id, link_type, dir, dev_type)) {
			fmt = (struct nhlt_fmt *)(epnt->config.caps + epnt->config.size);

			cfg = nhlt_get_specific_cfg(dev, fmt, num_ch, rate,
						    vbps, bps, ignore_vbps);
			if (cfg)
				return cfg;
		}

		epnt = (struct nhlt_endpoint *)((u8 *)epnt + epnt->length);
	}
```

The returned [`struct nhlt_specific_cfg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L49) blob is the opaque PDM-controller configuration the firmware writes into the on-die DMIC hardware, holding the clock dividers, the decimation-filter coefficients, and the channel routing for this rate and width. [`snd_sof_get_nhlt_endpoint_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1748) reports its length in dwords through the [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L50) field shifted right by two, and [`sof_ipc4_prepare_dai_copier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1966) records it as the DMIC copier's gateway [`config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L219). When the DSP creates the DMIC gateway from that copier, it programs the PDM controller from this blob and begins streaming decimated PCM into the host LinkDMA buffer the back-end DAI reserved.

### From NHLT to a capture PCM

The full chain on a Meteor Lake or Lunar Lake machine starts in firmware and ends at userspace. The ACPI NHLT table declares the DMIC endpoint geometry, [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29) and [`check_dmic_num()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L546) turn that into a 0 to 4 count, the count picks the `-dmic<N>ch` topology, the topology binds a [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) copier behind each of `"DMIC01 Pin"` and `"DMIC16k Pin"`, and at PCM prepare [`intel_nhlt_get_endpoint_blob()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L290) supplies the PDM controller blob for the negotiated format. A userspace client opens an ALSA capture PCM on the front end and reads decimated PCM frames; it never sees the PDM stream, the NHLT geometry, or the controller blob, all of which are confined to the path the SOF DSP drove to fill the buffer on Lunar Lake silicon.
