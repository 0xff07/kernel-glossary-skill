# SOF Intel HDA back-end DAIs

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Sound Open Firmware Intel driver registers one CPU DAI per physical audio link of an Intel x86 ACPI audio controller from the shared array [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), every entry of which is a no_pcm back-end in the DPCM graph whose job is to take the host DMA stream the front-end allocated and bind it to a DSP copier gateway, where [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745), [`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708), and [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) install [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479), and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) onto the matching entries by name, and a second function pointer struct [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) selected by [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) supplies the per-gateway DMA primitives for the four gateway families (HDA, SSP, DMIC, and SoundWire) through the variants [`hda_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L438) and [`sdw_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478) so the same [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273), [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), [`hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346), and [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) flow drives every link on an Intel MeteorLake or LunarLake DSP.

```
    DPCM back-end CPU DAI (no_pcm) selecting its gateway DMA ops
    ───────────────────────────────────────────────────────────

    host PCM stream (FE)                         DSP copier gateway
    ┌────────────────────┐                    ┌────────────────────┐
    │ hdac_ext_stream    │   programmed by    │ sof_ipc4_copier    │
    │ stream_tag, LinkDMA│ ◀───── BE DAI ───▶ │ dma_config_tlv[]   │
    └────────────────────┘                    └────────────────────┘
              ▲                                          ▲
              │   snd_soc_dai_ops (hw_params/trigger)    │
              │                                          │
        ┌─────┴──────────────────────────────────────────┴─────┐
        │   one skl_dai[] entry  (struct snd_soc_dai_driver)   │
        │   ops ─▶ hda_dai_ops / ssp_dai_ops / dmic_dai_ops    │
        └───────────────────────────┬──────────────────────────┘
                                    │  hda_select_dai_widget_ops()
              ┌──────────┬──────────┼──────────┬──────────┐
              ▼          ▼          ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
         │HDA gw  │ │SSP gw  │ │DMIC gw │ │SDW gw  │ │chain-DMA │
         │hda_ipc4│ │ssp_ipc4│ │dmic_ip4│ │sdw_ipc4│ │ *_chain  │
         └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
             └──────────┴──────────┴──────────┴───────────┘
              struct hda_dai_widget_dma_ops variants
                          │
                          ▼
              get/assign/setup/trigger hdac_ext_stream  ─▶  DSP gateway
```

## SUMMARY

The SOF Intel driver presents its CPU DAIs from one shared array, [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), which the common DSP ops table exports as its [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L87) member, and [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) hands that array and its count to the machine layer by writing [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L86) and [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L87) of the [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78). Every entry is a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) naming one link, with the names grouped by back-end family. The SSP entries run from `"SSP0 Pin"` through `"SSP5 Pin"`, the DMIC entries are `"DMIC01 Pin"` and `"DMIC16k Pin"`, the HDA display entries run from `"iDisp1 Pin"` through `"iDisp4 Pin"`, and the HDA analog and codec entries are `"Analog CPU DAI"`, `"Digital CPU DAI"`, and `"Alt Analog CPU DAI"`. The array carries no [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at definition time, and [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745) installs them at probe by matching the name against `"iDisp"`, `"Analog"`, or `"Digital"` to set [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), then deferring the SSP and DMIC binding to [`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) and [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723), which bind [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) only on Intel ACE 2.0 and later silicon read through [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191).

Each [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) fills only the four PCM callbacks the back-end needs, [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330), and the three families differ only in which hw_params function runs. The HDA family uses [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273), which reserves and programs a HDAudio link DMA stream directly, while the SSP and DMIC families use [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460), which adds a DMA-config TLV onto the copier so the DSP gateway learns the host stream tag. All three share [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) and [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287). Beneath the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) layer, [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) calls [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) to choose one [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) per back-end, and that struct abstracts whether the stream is fetched, assigned, set up, reset, and triggered the HDA way, the SSP way, the DMIC way, or the SoundWire way. The SoundWire back-end is entered from the SoundWire core through [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493), [`sdw_hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L615), and [`sdw_hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L644), which wrap the shared flow and additionally program the per-sublink channel map through [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847). The [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) the gateway ops fetch and assign comes from the bus stream pool owned by the sibling resource-management code, which the gateway ops reach by name.

## SPECIFICATIONS

The [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) DAIs and the [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) abstraction are Linux kernel software constructs with no standalone hardware specification. The HDA link, the LinkDMA stream registers, and the LOSIDV stream-id register they program are defined by the Intel High Definition Audio Specification. The SoundWire links the ALH back-end drives are defined by the MIPI SoundWire Specification, and the PCMSyCM channel-map register [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) writes is part of the HDAudio extended-multi-link shim. The DSP copier gateways and the IPC4 DMA configuration are defined by the Intel Audio DSP IPC4 firmware interface that the Sound Open Firmware project documents.

## LINUX KERNEL

### Back-end DAI driver array and ops binding (hda-dai.c)

- [`'\<skl_dai\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788): the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array of every SSP, DMIC, HDA, and codec CPU DAI, exported with `SND_SOC_SOF_INTEL_HDA_COMMON`
- [`'\<hda_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745): bind [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) onto the `"iDisp"`/`"Analog"`/`"Digital"` entries, then call the SSP and DMIC binders, then init NHLT for IPC4
- [`'\<ssp_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) / [`'\<dmic_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723): bind [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) / [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) onto the matching entries when [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) is at least [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24)
- [`'hda_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354): the HDA back-end [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) ([`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273), [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221), [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), [`hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346))
- [`'ssp_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) / [`'dmic_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486): the SSP and DMIC [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), both routing hw_params through [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460)

### Shared hw_params / hw_free / trigger flow (hda-dai.c)

- [`'\<hda_dai_get_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70): resolve and cache the per-gateway [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) in [`platform_private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L556) via [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594)
- [`'\<hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) / [`'\<hda_dai_hw_params_data\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240): reserve the LinkDMA stream through [`hda_link_dma_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L166), then send the topology DAI config with [`hda_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L32)
- [`'\<hda_link_dma_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L166): get or assign the [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47), set the link stream id, then reset, format, and set up the stream through the gateway ops
- [`'\<non_hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) / [`'\<non_hda_dai_hw_params_data\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372): run the shared HDA hw_params, then write a [`struct sof_ipc4_dma_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L285) TLV onto the [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) so the DSP gateway uses the host stream tag
- [`'\<hda_dai_hw_free\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) / [`'\<hda_link_dma_cleanup\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117): release the link stream id and, when releasing, call the gateway [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034) op
- [`'\<hda_dai_trigger\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287): run the gateway [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1039), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1041), and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1043) ops, then clean up the link DMA on STOP and SUSPEND
- [`'\<hda_dai_prepare\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346) / [`'\<non_hda_dai_prepare\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470): re-run the family's hw_params against the stored [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L93) hw_params after an xrun or a restart
- [`'\<widget_to_copier\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L363): reach the [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) backing a DAI widget through its [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547)
- [`'\<hda_dai_config\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L32): invoke the IPC topology [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) op to push the DAI config to firmware at each lifecycle stage
- [`'\<hda_dsp_dais_suspend\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L943): force a DAI release for streams left paused across a system suspend

### SoundWire-over-HDA entry points (hda-dai.c, hda-mlink.c)

- [`'\<sdw_hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493): the ALH back-end hw_params reached from the SoundWire core, building the SoundWire DAI index and node id, running [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372), and programming the per-sublink channel map
- [`'\<sdw_hda_dai_hw_free\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L615): release the link stream through [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) and reset the PCMSyCM registers
- [`'\<sdw_hda_dai_trigger\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L644): forward to the shared [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287)
- [`'\<hdac_bus_eml_sdw_map_stream_ch\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847): write the SoundWire PCMSyCM channel-and-stream map register for one sublink

### Per-gateway DMA op tables (hda-dai-ops.c, hda.h)

- [`'\<struct hda_dai_widget_dma_ops\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027): the per-gateway function pointer struct with [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028), [`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031), [`setup_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1036), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1041), [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048), and [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051)
- [`'\<hda_select_dai_widget_ops\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594): select one variant from the DAI [`type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), the IPC version, [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L162), and [`dspless_mode_selected`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L560)
- [`'hda_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L438): the HDA gateway variant for IPC4, using [`hda_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L190) and [`hda_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L215)
- [`'ssp_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L452): the SSP gateway variant, using [`generic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) and [`ssp_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L271)
- [`'dmic_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465): the DMIC gateway variant, using [`dmic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242) and [`dmic_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279)
- [`'sdw_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478): the SoundWire (ALH) gateway variant, using [`generic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) and [`sdw_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287)
- [`'hda_ipc4_chain_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L491) / [`'sdw_ipc4_chain_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L503): the chained-DMA variants used when [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L162) is set, omitting the pipeline pre/post-trigger ops
- [`'hda_ipc3_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L542): the HDA gateway variant for the older IPC3 firmware, using [`hda_ipc3_post_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L514)
- [`'hda_dspless_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L576) / [`'sdw_dspless_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L584): the variants used when the DSP is bypassed, fetching the stream through [`hda_dspless_get_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L555) from the front-end runtime

### Gateway op implementations (hda-dai-ops.c)

- [`'\<hda_get_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L117) / [`'\<hda_ipc4_get_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L124): read the saved [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) from the DAI [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L430); the IPC4 form also flags the pipeline to skip the FE trigger
- [`'\<hda_assign_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L144) / [`'\<hda_link_stream_assign\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L45): allocate a free link stream, decouple host and link DMA, and store it in [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L430)
- [`'\<hda_release_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L159): clear the [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L430) pointer and return the link stream to the bus
- [`'\<hda_setup_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L168) / [`'\<hda_reset_hext_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L174): write the computed format to the link stream and reset it
- [`'\<hda_trigger\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L338): start or clear the link DMA stream with [`snd_hdac_ext_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L174) and [`snd_hdac_ext_stream_clear()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L185)
- [`'\<hda_ipc4_pre_trigger\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L295) / [`'\<hda_ipc4_post_trigger\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L372): move the DSP pipeline through [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) and [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) around the link DMA change
- [`'\<hda_calc_stream_format\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L190) / [`'\<generic_calc_stream_format\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) / [`'\<dmic_calc_stream_format\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242): compute the HDAudio format word, the HDA variant reading the codec [`sig_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L619)
- [`'\<hda_codec_dai_set_stream\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L179): hand the host stream tag to the HDAudio codec DAI through [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559)
- [`'\<hda_get_hlink\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L215) / [`'\<ssp_get_hlink\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L271) / [`'\<dmic_get_hlink\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279) / [`'\<sdw_get_hlink\>':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287): return the [`struct hdac_ext_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L95) for the back-end's physical link

### DAI type, chip descriptor, and machine handoff

- [`'\<enum sof_ipc_dai_type\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76): the DAI type [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) keys on, with [`SOF_DAI_INTEL_SSP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L78), [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79), [`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80), and [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81)
- [`'\<enum sof_intel_hw_ip_version\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14): the silicon generation, with [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) for MeteorLake and [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) for LunarLake
- [`'\<struct sof_intel_dsp_desc\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173): the per-chip descriptor whose [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) gates the SSP, DMIC, and ALH ops; read by [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213)
- [`'mtl_chip_info':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) / [`'lnl_chip_info':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164): the MeteorLake (ACE 1.0) and LunarLake (ACE 2.0) descriptors
- [`'\<struct snd_soc_acpi_mach_params\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78): the per-machine parameters whose [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L87) and [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L86) point the machine driver at [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788)
- [`'\<hda_set_mach_params\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438): write [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L87) from the DSP ops [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L87) member
- [`'sdw_ace2x_callback':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L131): the [`struct sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L223) whose [`params_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L132) member is [`sdw_ace2x_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L108), the bridge that calls [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493); selected for ACE 2.0 and later in [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159)

### Common DAI link types and accessors (soc-dai.h, soc.h)

- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the static DAI descriptor each [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry is
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the ASoC PCM-callback function pointer struct that [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479), and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) instantiate
- [`'\<snd_soc_dai_get_widget\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482): return the DAPM widget the DAI feeds in a direction, the anchor every gateway op resolves from
- [`'\<snd_soc_dai_set_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559): hand the HDAudio stream to the codec DAI, used by [`hda_codec_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L179)
- [`'\<snd_soc_dai_dma_data_set\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506) / [`'\<snd_soc_dai_dma_data_get\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L498): store and read the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L430) where the link stream pointer lives, reached through the [`snd_soc_dai_set_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L505) and [`snd_soc_dai_get_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497) macros
- [`'\<no_pcm\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792): the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit that marks a back-end link in DPCM, set on every link that uses an [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) DAI

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model these CPU DAIs are the back-end side of
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface families (AC97, I2S, PCM) the DAI descriptor describes
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component side that registers CPU DAIs and DMA
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the HDAudio extended multi-link architecture the SSP, DMIC, and SoundWire back-ends program
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the ALH back-end joins

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF Intel HDA DSP architecture](https://thesofproject.github.io/latest/architectures/firmware/intel/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Each back-end family supplies one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) with four PCM callbacks, and underneath those it supplies one [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) whose members the ASoC callbacks invoke. The two layers run in a fixed order. The ASoC core calls the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) callback for the PCM operation, that callback resolves the gateway ops with [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70), and then it dispatches through the [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) members to act on the host stream and the DSP gateway. The first table maps the PCM operation to the DAI ops callback and the gateway ops it drives; the second names the gateway-ops family selected for each DAI type and IPC mode.

| PCM operation | DAI ops callback | gateway op invoked |
|---------------|------------------|--------------------|
| `SNDRV_PCM_IOCTL_HW_PARAMS` (HDA) | [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) | [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028), [`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031), [`setup_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1036) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` (SSP/DMIC) | [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) | the HDA set plus the copier DMA-config TLV |
| `SNDRV_PCM_IOCTL_PREPARE` | [`hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346) / [`non_hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470) | re-runs hw_params after xrun or restart |
| `SNDRV_PCM_TRIGGER_START` | [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) | [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1039), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1041), [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1043) |
| `SNDRV_PCM_TRIGGER_STOP` | [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) | the trigger ops then [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) | [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034) |

| DAI type | IPC4 standard | IPC4 chain-DMA | dspless | IPC3 |
|----------|---------------|----------------|---------|------|
| [`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80) | [`hda_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L438) | [`hda_ipc4_chain_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L491) | [`hda_dspless_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L576) | [`hda_ipc3_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L542) |
| [`SOF_DAI_INTEL_SSP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L78) | [`ssp_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L452) | (n/a) | (n/a) | (n/a) |
| [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) | [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) | (n/a) | (n/a) | (n/a) |
| [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) | [`sdw_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478) | [`sdw_ipc4_chain_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L503) | [`sdw_dspless_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L584) | (n/a) |

### hw_params

[`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) reserves the HDAudio LinkDMA stream and binds it to the DSP copier gateway. For the HDA family it is [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273), which forwards to [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240) with the flag [`SOF_DAI_CONFIG_FLAGS_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L62). For the SSP and DMIC families it is [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460), which runs the same HDA stream handling and then appends the gateway DMA-config TLV.

### hw_free

[`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) is [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) for all three families, which fetches the link stream with the gateway [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) op and, when one exists, calls [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117) with `release` set so the gateway [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034) op runs and the reserved host channel is freed.

### trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339) is [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), which calls the gateway [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1039), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1041), and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1043) ops in turn so the DSP pipeline state change over the IPC channel and the LinkDMA register change happen in the right order, then cleans up the link DMA on [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) and [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102).

### prepare

[`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330) is [`hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346) or [`non_hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470), which re-run the family's hw_params against the stored [`dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L93) hw_params so a stream restarted after an xrun or a drop reconfigures its LinkDMA before it runs again.

### get_hext_stream

[`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) is the one mandatory gateway op and returns the [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) already associated with the DAI, or NULL when none is assigned yet. The IPC4 variants use [`hda_ipc4_get_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L124), which also marks the pipeline so the front-end trigger skips it; the chain-DMA and IPC3 variants use the plain [`hda_get_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L117).

### assign_hext_stream and release_hext_stream

[`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031) is [`hda_assign_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L144), which calls [`hda_link_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L45) to pick a free link stream and stores it in the DAI [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L430); [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034) is [`hda_release_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L159), which clears that pointer and returns the stream to the bus. The dspless variants leave both NULL because the stream comes from the front-end runtime.

### setup_hext_stream and reset_hext_stream

[`setup_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1036) is [`hda_setup_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L168), which writes the computed format to the link stream, and [`reset_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1038) is [`hda_reset_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L174). The dspless variants substitute [`hda_dspless_setup_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L564), which only saves the format value because there is no DSP to program.

### pre_trigger, trigger, and post_trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1041) is [`hda_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L338) for every variant and starts or clears the link DMA stream. [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1039) and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1043) are present only on the non-chain IPC4 variants, as [`hda_ipc4_pre_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L295) and [`hda_ipc4_post_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L372), which step the DSP pipeline state; the IPC3 HDA variant uses [`hda_ipc3_post_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L514) instead, which sends a DAI-config message.

### codec_dai_set_stream

[`codec_dai_set_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1045) is [`hda_codec_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L179) and is present only on the HDA variants, where the codec DAI must learn the host stream tag through [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559). The SSP, DMIC, and SoundWire variants leave it NULL because their codecs receive the stream another way.

### calc_stream_format

[`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048) computes the HDAudio format word from the hw_params. The HDA variants use [`hda_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L190), which reads the codec DAI [`sig_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L619); the SSP and SoundWire variants use [`generic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) reading the physical width; the DMIC variant uses [`dmic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242), which folds an S16_LE PDM capture into a half-channel S32_LE stream.

### get_hlink

[`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) is the second mandatory op and returns the [`struct hdac_ext_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L95) for the back-end's physical link, used to program the LOSIDV stream id on legacy HDA links and the extended-link registers on the SSP, DMIC, and SoundWire links. Each back-end supplies its own, [`hda_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L215), [`ssp_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L271), [`dmic_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L279), and [`sdw_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287).

## DETAILS

### A back-end DAI is a no_pcm BE in DPCM

Every [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) DAI is the CPU side of a back-end DAI link, and the machine driver marks that link with the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) bit of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). In Dynamic PCM the front-end link owns the userspace-visible PCM device and runs the host DMA, and the back-end link carries no PCM device of its own. The DPCM core connects a front-end to one or more back-ends through DAPM routing and replays each PCM operation onto the back-end DAI, so these SOF CPU DAIs never see an `open()` or a [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L322) from userspace and implement only the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330) callbacks the DPCM core forwards. The job of the back-end DAI is to take the host stream the front-end already allocated and connect it to the DSP copier gateway that the topology placed at the edge of the firmware pipeline.

### The skl_dai[] descriptor array

[`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) is one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array carrying every CPU DAI that any skl+ Intel platform might have. According to the comment above it, "some products who use this DAI array only physically have a subset of the DAIs, but no harm is done here by adding the whole set". The SSP, DMIC, and loopback entries are always present; the HDA display, analog, and codec entries are compiled in only when the HDAudio codec support is configured:

```c
/* sound/soc/sof/intel/hda-dai.c:788 */
struct snd_soc_dai_driver skl_dai[] = {
{
	.name = "SSP0 Pin",
	.playback = {
		.channels_min = 1,
		.channels_max = 8,
	},
	.capture = {
		.channels_min = 1,
		.channels_max = 8,
	},
},
...
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
{
	/* Virtual CPU DAI for Echo reference */
	.name = "Loopback Virtual Pin",
	.capture = {
		.channels_min = 1,
		.channels_max = 2,
	},
},
#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_AUDIO_CODEC)
{
	.name = "iDisp1 Pin",
	.playback = {
		.channels_min = 1,
		.channels_max = 8,
	},
},
...
{
	.name = "Analog CPU DAI",
	.playback = {
		.channels_min = 1,
		.channels_max = 16,
	},
	.capture = {
		.channels_min = 1,
		.channels_max = 16,
	},
},
...
#endif
};
EXPORT_SYMBOL_NS(skl_dai, "SND_SOC_SOF_INTEL_HDA_COMMON");
```

The entries carry no [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointer here, only a name and the channel capability records, because the ops depend on the silicon generation and are bound at probe.

### hda_set_dai_drv_ops binds ops by name

The common DSP ops table exports the array as its [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L87) member, and at probe [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745) walks the array and installs the ops by matching each DAI name. The HDA display, analog, and digital DAIs get [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), and the SSP and DMIC binding is delegated:

```c
/* sound/soc/sof/intel/hda-dai.c:745 */
void hda_set_dai_drv_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *ops)
{
	int i;

	for (i = 0; i < ops->num_drv; i++) {
#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_AUDIO_CODEC)
		if (strstr(ops->drv[i].name, "iDisp") ||
		    strstr(ops->drv[i].name, "Analog") ||
		    strstr(ops->drv[i].name, "Digital"))
			ops->drv[i].ops = &hda_dai_ops;
#endif
	}

	ssp_set_dai_drv_ops(sdev, ops);
	dmic_set_dai_drv_ops(sdev, ops);

	if (sdev->pdata->ipc_type == SOF_IPC_TYPE_4 && !hda_use_tplg_nhlt) {
		struct sof_ipc4_fw_data *ipc4_data = sdev->private;

		ipc4_data->nhlt = intel_nhlt_init(sdev->dev);
	}
}
EXPORT_SYMBOL_NS(hda_set_dai_drv_ops, "SND_SOC_SOF_INTEL_HDA_COMMON");
```

[`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) matches `"SSP"` in the name and binds [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479), but only when the chip's [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) read through [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213) is at least [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24):

```c
/* sound/soc/sof/intel/hda-dai.c:708 */
static void ssp_set_dai_drv_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *ops)
{
	const struct sof_intel_dsp_desc *chip;
	int i;

	chip = get_chip_info(sdev->pdata);

	if (chip->hw_ip_version >= SOF_INTEL_ACE_2_0) {
		for (i = 0; i < ops->num_drv; i++) {
			if (strstr(ops->drv[i].name, "SSP"))
				ops->drv[i].ops = &ssp_dai_ops;
		}
	}
}
```

[`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) is identical except it matches `"DMIC"` and binds [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486). The version gate exists because the SSP and DMIC links can be driven as independent back-end DAIs only on ACE 2.0 silicon (LunarLake); on ACE 1.0 (MeteorLake) those entries keep a NULL [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and the SSP and DMIC paths run through the older topology DAI-config mechanism instead.

```
    hda_set_dai_drv_ops: bind ops by DAI-name substring
    ───────────────────────────────────────────────────

    ┌─────────────────┬───────────────┬──────────────────────────┐
    │ name contains   │ ops bound     │ condition                │
    ├─────────────────┼───────────────┼──────────────────────────┤
    │ "iDisp"         │ hda_dai_ops   │ HDA_AUDIO_CODEC config   │
    │ "Analog"        │ hda_dai_ops   │ HDA_AUDIO_CODEC config   │
    │ "Digital"       │ hda_dai_ops   │ HDA_AUDIO_CODEC config   │
    │ "SSP"           │ ssp_dai_ops   │ hw_ip_version >= ACE_2_0 │
    │ "DMIC"          │ dmic_dai_ops  │ hw_ip_version >= ACE_2_0 │
    └─────────────────┴───────────────┴──────────────────────────┘

    no match, or ACE_1_0 SSP/DMIC: ops stays NULL (topology path)
```

### The three snd_soc_dai_ops differ only in hw_params

The HDA back-end ops [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) sets the four PCM callbacks, with its own hw_params and prepare:

```c
/* sound/soc/sof/intel/hda-dai.c:354 */
static const struct snd_soc_dai_ops hda_dai_ops = {
	.hw_params = hda_dai_hw_params,
	.hw_free = hda_dai_hw_free,
	.trigger = hda_dai_trigger,
	.prepare = hda_dai_prepare,
};
```

The SSP and DMIC ops differ only in routing hw_params and prepare through the non-HDA functions, sharing [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) and [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) with the HDA family:

```c
/* sound/soc/sof/intel/hda-dai.c:479 */
static const struct snd_soc_dai_ops ssp_dai_ops = {
	.hw_params = non_hda_dai_hw_params,
	.hw_free = hda_dai_hw_free,
	.trigger = hda_dai_trigger,
	.prepare = non_hda_dai_prepare,
};

static const struct snd_soc_dai_ops dmic_dai_ops = {
	.hw_params = non_hda_dai_hw_params,
	.hw_free = hda_dai_hw_free,
	.trigger = hda_dai_trigger,
	.prepare = non_hda_dai_prepare,
};
```

The two structs above share hw_free and trigger with the HDA ops and part company only at the hw_params and prepare rows the table lines up:

```
    The three snd_soc_dai_ops differ only in hw_params and prepare
    ─────────────────────────────────────────────────────────────

    ┌───────────┬───────────────────┬─────────────┬─────────────┐
    │ field     │ hda_dai_ops       │ ssp_dai_ops │ dmic_dai_op │
    ├───────────┼───────────────────┼─────────────┴─────────────┤
    │ hw_params │ hda_dai_hw_params │ non_hda_dai_hw_params     │
    │ prepare   │ hda_dai_prepare   │ non_hda_dai_prepare       │
    ├───────────┼───────────────────┴───────────────────────────┤
    │ hw_free   │ hda_dai_hw_free      (shared by all three)    │
    │ trigger   │ hda_dai_trigger      (shared by all three)    │
    └───────────┴───────────────────────────────────────────────┘
```

### The generic gateway model: struct hda_dai_widget_dma_ops

The second function pointer struct, [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), is where the back-end-specific behavior is defined, and its kerneldoc names [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) and [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) as the two mandatory members. The four gateway families all consume the same generic flow and vary only in which of these members they populate:

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

The HDA IPC4 variant fills every member, because the HDA back-end both assigns its own link stream and must tell the codec DAI the stream tag:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:438 */
static const struct hda_dai_widget_dma_ops hda_ipc4_dma_ops = {
	.get_hext_stream = hda_ipc4_get_hext_stream,
	.assign_hext_stream = hda_assign_hext_stream,
	.release_hext_stream = hda_release_hext_stream,
	.setup_hext_stream = hda_setup_hext_stream,
	.reset_hext_stream = hda_reset_hext_stream,
	.pre_trigger = hda_ipc4_pre_trigger,
	.trigger = hda_trigger,
	.post_trigger = hda_ipc4_post_trigger,
	.codec_dai_set_stream = hda_codec_dai_set_stream,
	.calc_stream_format = hda_calc_stream_format,
	.get_hlink = hda_get_hlink,
};
```

Where the HDA variant filled every slot, the table marks which members each other variant drops, the two starred ones (the stream getter and the link getter) staying mandatory throughout:

```
    struct hda_dai_widget_dma_ops members (2 mandatory)
    ───────────────────────────────────────────────────

    ┌──────────────────────┬──────────────────────────────────┐
    │ member               │ omitted by                       │
    ├──────────────────────┼──────────────────────────────────┤
    │ get_hext_stream  (*) │ never (mandatory)                │
    │ get_hlink        (*) │ never (mandatory)                │
    │ assign_hext_stream   │ dspless variants                 │
    │ release_hext_stream  │ dspless variants                 │
    │ setup_hext_stream    │ -                                │
    │ reset_hext_stream    │ -                                │
    │ pre_trigger          │ chain-DMA, IPC3, dspless         │
    │ trigger              │ -                                │
    │ post_trigger         │ chain-DMA, IPC3, dspless         │
    │ codec_dai_set_stream │ SSP, DMIC, SDW (HDA only)        │
    │ calc_stream_format   │ -                                │
    └──────────────────────┴──────────────────────────────────┘

    (*) get_hext_stream + get_hlink are the two mandatory members
```

### The SSP and DMIC gateway families

The SSP and DMIC IPC4 variants share the same stream-handling and trigger ops as the HDA variant and differ only in the format calculator and the link accessor. The SSP variant [`ssp_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L452) uses the generic format calculator and the SSP link accessor, while the DMIC variant [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) swaps in the PDM-aware calculator and the DMIC link accessor; neither sets [`codec_dai_set_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1045) because those back-ends do not hand a stream tag to a HDAudio codec DAI:

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

The DMIC format calculator is the one place a back-end reinterprets the hw_params. [`dmic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L242) rewrites an S16_LE PDM capture as a half-channel S32_LE stream because the DMIC link carries two 16-bit PDM samples per 32-bit slot:

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

### The SoundWire gateway family

The SoundWire (ALH) variant [`sdw_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478) is built like the SSP variant, using [`generic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) and its own link accessor [`sdw_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287):

```c
/* sound/soc/sof/intel/hda-dai-ops.c:478 */
static const struct hda_dai_widget_dma_ops sdw_ipc4_dma_ops = {
	.get_hext_stream = hda_ipc4_get_hext_stream,
	.assign_hext_stream = hda_assign_hext_stream,
	.release_hext_stream = hda_release_hext_stream,
	.setup_hext_stream = hda_setup_hext_stream,
	.reset_hext_stream = hda_reset_hext_stream,
	.pre_trigger = hda_ipc4_pre_trigger,
	.trigger = hda_trigger,
	.post_trigger = hda_ipc4_post_trigger,
	.calc_stream_format = generic_calc_stream_format,
	.get_hlink = sdw_get_hlink,
};
```

The link accessor [`sdw_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287) returns the single SoundWire extended link rather than indexing per-DAI as the SSP and DMIC accessors do, because all SoundWire sublinks share one extended-link block on the bus:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:287 */
static struct hdac_ext_link *sdw_get_hlink(struct snd_sof_dev *sdev,
					   struct snd_pcm_substream *substream)
{
	struct hdac_bus *bus = sof_to_bus(sdev);

	return hdac_bus_eml_sdw_get_hlink(bus);
}
```

### The chain-DMA and dspless gateway variants

When the topology marks a pipeline with [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L162), the HDA and SoundWire back-ends use the chained-DMA variants [`hda_ipc4_chain_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L491) and [`sdw_ipc4_chain_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L503), which drop the pipeline [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1039) and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1043) ops because a chain DMA gateway moves data without a separately triggered DSP pipeline. They also use the plain [`hda_get_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L117) rather than the IPC4 form, so the front-end trigger is not skipped:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:503 */
static const struct hda_dai_widget_dma_ops sdw_ipc4_chain_dma_ops = {
	.get_hext_stream = hda_get_hext_stream,
	.assign_hext_stream = hda_assign_hext_stream,
	.release_hext_stream = hda_release_hext_stream,
	.setup_hext_stream = hda_setup_hext_stream,
	.reset_hext_stream = hda_reset_hext_stream,
	.trigger = hda_trigger,
	.calc_stream_format = generic_calc_stream_format,
	.get_hlink = sdw_get_hlink,
};
```

The dspless variants [`hda_dspless_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L576) and [`sdw_dspless_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L584) set neither [`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031) nor [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034), because with the DSP bypassed the stream comes from the front-end runtime rather than from a separate link allocation. Their [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) is [`hda_dspless_get_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L555), which reads the stream from `substream->runtime->private_data`, and their [`setup_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1036) is [`hda_dspless_setup_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L564), which only records the format value.

### hda_select_dai_widget_ops chooses the variant

[`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) calls [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) once per stream and caches the result in [`platform_private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L556) so the lookup happens only on the first hw_params. The selector keys on [`dspless_mode_selected`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L560) first, then on the IPC version, then on the DAI [`type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), and for the IPC4 branch it also consults [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L162) and the chip version:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:625 */
	case SOF_IPC_TYPE_4:
	{
		struct snd_sof_widget *pipe_widget = swidget->spipe->pipe_widget;
		struct sof_ipc4_pipeline *pipeline = pipe_widget->private;

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
		case SOF_DAI_INTEL_ALH:
			if (chip->hw_ip_version < SOF_INTEL_ACE_2_0)
				return NULL;
			if (pipeline->use_chain_dma)
				return &sdw_ipc4_chain_dma_ops;
			return &sdw_ipc4_dma_ops;

		default:
			break;
		}
		break;
	}
```

[`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80) selects [`hda_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L438) or its chain variant, [`SOF_DAI_INTEL_SSP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L78) selects [`ssp_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L452), [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) selects [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465), and [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81), the SoundWire back-end, selects [`sdw_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478) or [`sdw_ipc4_chain_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L503). The three non-HDA types return NULL below [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24), which mirrors the version gate in the ops binders above.

### hda_dai_get_ops caches the selection on the widget

[`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70) resolves the DAPM widget the DAI feeds with [`snd_soc_dai_get_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482), reaches the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) behind it, and caches the selected ops in [`platform_private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L556). It also enforces the mandatory-op rule, rejecting any variant whose [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) is unset:

```c
/* sound/soc/sof/intel/hda-dai.c:99 */
	sdai = swidget->private;

	/* select and set the DAI widget ops if not set already */
	if (!sdai->platform_private) {
		const struct hda_dai_widget_dma_ops *ops =
			hda_select_dai_widget_ops(sdev, swidget);
		if (!ops)
			return NULL;

		/* check if mandatory ops are set */
		if (!ops || !ops->get_hext_stream)
			return NULL;

		sdai->platform_private = ops;
	}

	return sdai->platform_private;
```

### hw_params reserves the link stream and programs the gateway

[`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240) returns early if the link is already prepared, otherwise it runs [`hda_link_dma_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L166) to reserve and program the host stream, reads back the assigned stream tag, and pushes the topology DAI config with [`hda_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L32):

```c
/* sound/soc/sof/intel/hda-dai.c:240 */
static int __maybe_unused hda_dai_hw_params_data(struct snd_pcm_substream *substream,
						 struct snd_pcm_hw_params *params,
						 struct snd_soc_dai *dai,
						 struct snd_sof_dai_config_data *data,
						 unsigned int flags)
{
	struct snd_soc_dapm_widget *w = snd_soc_dai_get_widget(dai, substream->stream);
	const struct hda_dai_widget_dma_ops *ops = hda_dai_get_ops(substream, dai);
	struct hdac_ext_stream *hext_stream;
	struct snd_sof_dev *sdev = widget_to_sdev(w);
	int ret;

	if (!ops) {
		dev_err(sdev->dev, "DAI widget ops not set\n");
		return -EINVAL;
	}

	hext_stream = ops->get_hext_stream(sdev, dai, substream);
	if (hext_stream && hext_stream->link_prepared)
		return 0;

	ret = hda_link_dma_hw_params(substream, params, dai);
	if (ret < 0)
		return ret;

	hext_stream = ops->get_hext_stream(sdev, dai, substream);

	flags |= SOF_DAI_CONFIG_FLAGS_2_STEP_STOP << SOF_DAI_CONFIG_FLAGS_QUIRK_SHIFT;
	data->dai_data = hdac_stream(hext_stream)->stream_tag - 1;

	return hda_dai_config(w, flags, data);
}
```

Inside [`hda_link_dma_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L166) the gateway ops do the back-end-specific work. It fetches an existing link stream with [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028), assigns a new one with [`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031) if needed, sets the codec stream with [`codec_dai_set_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1045) when present, resets the stream, computes the format with [`calc_stream_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1048), and sets up the stream with [`setup_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1036):

```c
/* sound/soc/sof/intel/hda-dai.c:187 */
	hext_stream = ops->get_hext_stream(sdev, cpu_dai, substream);

	if (!hext_stream) {
		if (ops->assign_hext_stream)
			hext_stream = ops->assign_hext_stream(sdev, cpu_dai, substream);
	}

	if (!hext_stream)
		return -EBUSY;

	hstream = &hext_stream->hstream;
	stream_tag = hstream->stream_tag;

	if (hext_stream->hstream.direction == SNDRV_PCM_STREAM_PLAYBACK)
		snd_hdac_ext_bus_link_set_stream_id(hlink, stream_tag);

	/* set the hdac_stream in the codec dai */
	if (ops->codec_dai_set_stream)
		ops->codec_dai_set_stream(sdev, substream, hstream);

	if (ops->reset_hext_stream)
		ops->reset_hext_stream(sdev, hext_stream);

	if (ops->calc_stream_format && ops->setup_hext_stream) {
		unsigned int format_val = ops->calc_stream_format(sdev, substream, params);

		ops->setup_hext_stream(sdev, hext_stream, format_val);
	}

	hext_stream->link_prepared = 1;
```

The actual stream pool walk is in [`hda_link_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L45), which picks a free link stream from the bus stream list, decouples host and link DMA, and is the boundary where the back-end DAI code hands off to the resource-management code that owns the [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) pool.

### non_hda_dai_hw_params adds the gateway DMA-config TLV

The SSP and DMIC families run [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372), which calls the shared HDA hw_params and then writes a [`struct sof_ipc4_dma_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L285) TLV onto the [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) reached through [`widget_to_copier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L363). The TLV tells the DSP gateway which host stream channel to read, using the same stream tag the host DMA was assigned:

```c
/* sound/soc/sof/intel/hda-dai.c:431 */
	dma_config_tlv = &ipc4_copier->dma_config_tlv[cpu_dai_id];
	dma_config_tlv->type = SOF_IPC4_GTW_DMA_CONFIG_ID;
	/* dma_config_priv_size is zero */
	dma_config_tlv->length = sizeof(dma_config_tlv->dma_config);

	dma_config = &dma_config_tlv->dma_config;

	dma_config->dma_method = SOF_IPC4_DMA_METHOD_HDA;
	dma_config->pre_allocated_by_host = 1;
	dma_config->dma_channel_id = stream_id - 1;
	dma_config->stream_id = stream_id;
	/*
	 * Currently we use a DMA for each device in ALH blob. The device will
	 * be copied in sof_ipc4_prepare_copier_module.
	 */
	dma_config->dma_stream_channel_map.device_count = 1;
	dma_config->dma_priv_config_size = 0;
```

According to the comment, a separate DMA is used for each device in the ALH blob, and the device entry is copied when the copier module is prepared. This is the link between the host stream and the DSP copier gateway for the non-HDA back-ends; the host owns the stream, and the TLV teaches the firmware copier to consume that exact stream tag.

### trigger steps the pipeline and the LinkDMA together

[`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) runs the three gateway trigger ops in order and then cleans up on stop. According to the comment above the function, "in contrast to IPC3, the dai trigger in IPC4 mixes pipeline state changes (over IPC channel) and DMA state change (direct host register changes)", which is why the pre-trigger, trigger, and post-trigger split exists:

```c
/* sound/soc/sof/intel/hda-dai.c:309 */
	if (ops->pre_trigger) {
		ret = ops->pre_trigger(sdev, dai, substream, cmd);
		if (ret < 0)
			return ret;
	}

	if (ops->trigger) {
		ret = ops->trigger(sdev, dai, substream, cmd);
		if (ret < 0)
			return ret;
	}

	if (ops->post_trigger) {
		ret = ops->post_trigger(sdev, dai, substream, cmd);
		if (ret < 0)
			return ret;
	}

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
		ret = hda_link_dma_cleanup(substream, hext_stream, dai,
					   cmd != SNDRV_PCM_TRIGGER_STOP);
```

The middle op [`hda_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L338) is the same for every variant and acts on the LinkDMA register directly, starting the stream on START and PAUSE_RELEASE and clearing it on STOP, SUSPEND, and PAUSE_PUSH:

```c
/* sound/soc/sof/intel/hda-dai-ops.c:338 */
static int hda_trigger(struct snd_sof_dev *sdev, struct snd_soc_dai *cpu_dai,
		       struct snd_pcm_substream *substream, int cmd)
{
	struct hdac_ext_stream *hext_stream = snd_soc_dai_get_dma_data(cpu_dai, substream);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		snd_hdac_ext_stream_start(hext_stream);
		break;
	...
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		hext_stream->pplcllpl = 0;
		hext_stream->pplcllpu = 0;
		snd_hdac_ext_stream_clear(hext_stream);
		break;
	default:
		dev_err(sdev->dev, "unknown trigger command %d\n", cmd);
		return -EINVAL;
	}

	return 0;
}
```

On the IPC4 path the pipeline-state half of the trigger is in [`hda_ipc4_pre_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L295) and [`hda_ipc4_post_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L372). The pre-trigger moves the pipeline to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) before a stop or pause, and the post-trigger moves it to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) after a start, so the firmware pipeline state and the LinkDMA register state advance in the right order around the [`hda_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L338) register write.

```
    IPC4 trigger: pipeline state and LinkDMA register interleave
    ────────────────────────────────────────────────────────────

    START / PAUSE_RELEASE                STOP / SUSPEND / PAUSE_PUSH
    ─────────────────────                ──────────────────────────
    pre_trigger   (none)                 pre_trigger
                                           ▶ SOF_IPC4_PIPE_PAUSED
             │                                    │
             ▼                                    ▼
    trigger: hda_trigger                 trigger: hda_trigger
      ▶ snd_hdac_ext_stream_start          ▶ snd_hdac_ext_stream_clear
             │                                    │
             ▼                                    ▼
    post_trigger                         post_trigger  (none)
      ▶ SOF_IPC4_PIPE_RUNNING

    pre/post_trigger present only on non-chain IPC4 variants
```

### hw_free releases the link stream

[`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) fetches the link stream through the gateway [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) op and, when one is present, calls [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117) with `release` true:

```c
/* sound/soc/sof/intel/hda-dai.c:221 */
static int __maybe_unused hda_dai_hw_free(struct snd_pcm_substream *substream,
					  struct snd_soc_dai *cpu_dai)
{
	const struct hda_dai_widget_dma_ops *ops = hda_dai_get_ops(substream, cpu_dai);
	struct hdac_ext_stream *hext_stream;
	struct snd_sof_dev *sdev = dai_to_sdev(substream, cpu_dai);

	if (!ops) {
		dev_err(cpu_dai->dev, "DAI widget ops not set\n");
		return -EINVAL;
	}

	hext_stream = ops->get_hext_stream(sdev, cpu_dai, substream);
	if (!hext_stream)
		return 0;

	return hda_link_dma_cleanup(substream, hext_stream, cpu_dai, true);
}
```

[`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117) clears the link stream id with [`snd_hdac_ext_bus_link_clear_stream_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c) on playback, and when releasing it calls the gateway [`release_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1034) op and drops the host channel reservation so the next stream starts from a clean state. When called with `release` false from the stop path of [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), it only clears [`link_prepared`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) so the stream is reconfigured on restart without releasing the channel, and the release itself is deferred to [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221).

### Worked example: rt722-sdca over the ALH/SoundWire back-end on Intel ACE x86 ACPI

On an Intel x86 ACPI platform whose firmware enumerates a SoundWire link, the Realtek RT722 SDCA codec sits on that link and the SOF driver presents the ALH back-end DAI for it. The [`enum sof_intel_hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14) of the chip decides which path runs. MeteorLake is [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) in [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), and LunarLake is [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) in [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164). [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) reads that version and installs one of two SoundWire callback sets:

```c
/* sound/soc/sof/intel/hda.c:170 */
	chip = get_chip_info(sdev->pdata);
	if (chip->hw_ip_version < SOF_INTEL_ACE_2_0) {
		res.mmio_base = sdev->bar[HDA_DSP_BAR];
		res.hw_ops = &sdw_intel_cnl_hw_ops;
		res.shim_base = hdev->desc->sdw_shim_base;
		res.alh_base = hdev->desc->sdw_alh_base;
		res.ext = false;
		res.ops = &sdw_callback;
	} else {
		...
		res.hw_ops = &sdw_intel_lnl_hw_ops;
		res.ext = true;
		res.ops = &sdw_ace2x_callback;
		...
	}
```

On ACE 2.0 the SoundWire core reaches the back-end DAI through [`sdw_ace2x_callback`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L131), whose [`params_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L132) member is the bridge [`sdw_ace2x_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L108) that calls [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493). That function programs the SoundWire PCMSyCM channel map twice, once to reset it and once with the real channel mask and stream tag, and runs [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) in between to reserve the LinkDMA stream and write the copier TLV:

```c
/* sound/soc/sof/intel/hda-dai.c:539 */
	ret = hdac_bus_eml_sdw_map_stream_ch(sof_to_bus(sdev), link_id, cpu_dai->id,
					     0, 0, substream->stream);
	if (ret < 0) {
		dev_err(cpu_dai->dev, "%s:  hdac_bus_eml_sdw_map_stream_ch failed %d\n",
			__func__, ret);
		return ret;
	}

	data.dai_index = (link_id << 8) | cpu_dai->id;
	data.dai_node_id = intel_alh_id;
	ret = non_hda_dai_hw_params_data(substream, params, cpu_dai, &data, flags);
	if (ret < 0) {
		dev_err(cpu_dai->dev, "%s: non_hda_dai_hw_params failed %d\n", __func__, ret);
		return ret;
	}
```

For an aggregated speaker amplifier link, [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493) then reconstructs the per-sublink channel split and writes the DMA stream channel map onto every copier on the link, using [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) with the real stream tag from the assigned [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47). The gateway ops the SoundWire DAI uses are [`sdw_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L478), so [`get_hlink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1051) resolves to [`sdw_get_hlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L287), which returns the SoundWire extended link, and the format is computed by [`generic_calc_stream_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L225) from the physical sample width.

On MeteorLake, an ACE 1.0 part, [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) installs [`sdw_callback`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L103) instead, whose [`params_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L104) member is [`sdw_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L61). That bridge does not run [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493) and the ALH branch of [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) returns NULL below ACE 2.0; the SoundWire stream is instead configured purely through the topology DAI-config message that [`hda_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L32) sends:

```c
/* sound/soc/sof/intel/hda.c:61 */
static int sdw_params_stream(struct device *dev,
			     struct sdw_intel_stream_params_data *params_data)
{
	struct snd_soc_dai *d = params_data->dai;
	struct snd_soc_dapm_widget *w = snd_soc_dai_get_widget(d, params_data->substream->stream);
	struct snd_sof_dai_config_data data = { 0 };

	if (!w) {
		dev_err(dev, "%s widget not found, check amp link num in the topology\n",
			d->name);
		return -EINVAL;
	}
	data.dai_index = (params_data->link_id << 8) | d->id;
	data.dai_data = params_data->alh_stream_id;
	data.dai_node_id = data.dai_data;

	return hda_dai_config(w, SOF_DAI_CONFIG_FLAGS_HW_PARAMS, &data);
}
```

The split means the dedicated SSP, DMIC, and SoundWire back-end DAI ops with their per-gateway [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) are the ACE 2.0 path, and on the LunarLake-class part the rt722-sdca capture or playback runs hw_params through [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493), which reserves a HDAudio LinkDMA stream for the SoundWire link and binds it to the DSP copier gateway exactly as the HDA, SSP, and DMIC back-ends do.

```
    SoundWire hw_params path by chip hw_ip_version
    ──────────────────────────────────────────────

    ┌────────────────────┬──────────────────────┬───────────────────────┐
    │                    │ ACE_1_0 (MeteorLake) │ ACE_2_0 (LunarLake)   │
    ├────────────────────┼──────────────────────┼───────────────────────┤
    │ SoundWire callback │ sdw_callback         │ sdw_ace2x_callback    │
    │ params_stream      │ sdw_params_stream    │ sdw_ace2x_params_str  │
    │ runs BE DAI hw_par │ no                   │ sdw_hda_dai_hw_params │
    │ ALH gateway ops    │ NULL (returns below) │ sdw_ipc4_dma_ops      │
    │ stream configured  │ topology DAI-config  │ LinkDMA + copier TLV  │
    └────────────────────┴──────────────────────┴───────────────────────┘
```

### The DAIs reach the machine through mach_params

The machine driver never sees [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) directly. The common ops table sets [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L87) to the array and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L88) to its count, and [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) copies those into the [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) the machine driver reads:

```c
/* sound/soc/sof/intel/hda.c:1445 */
	mach_params = &mach->mach_params;
	mach_params->platform = dev_name(sdev->dev);
	if (IS_ENABLED(CONFIG_SND_SOC_SOF_NOCODEC_DEBUG_SUPPORT) &&
	    sof_debug_check_flag(SOF_DBG_FORCE_NOCODEC))
		mach_params->num_dai_drivers = SOF_SKL_NUM_DAIS_NOCODEC;
	else
		mach_params->num_dai_drivers = desc->ops->num_drv;
	mach_params->dai_drivers = desc->ops->drv;
```

The [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L87) and [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L86) fields are how the SOF machine driver gets the CPU DAI descriptors it then references by name in its back-end DAI links, and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) bit on each such link makes the DPCM core treat them as back-ends and drive them through the callbacks above. A SUSPEND that arrives while a back-end is paused does not deliver a [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102), so [`hda_dsp_dais_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L943) runs last at component suspend and forces those DAIs to release their link streams through the same [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) path.

### The back-end DAI selecting one gateway DMA op table per link

This figure shows one [`skl_dai[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry (a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)) binding a host PCM stream (a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47)) to a DSP copier gateway (a [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332)), with [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) choosing one [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) variant per back-end family.

```
    DPCM back-end CPU DAI (no_pcm) selecting its gateway DMA ops
    ───────────────────────────────────────────────────────────

    host PCM stream (FE)                         DSP copier gateway
    ┌────────────────────┐                    ┌────────────────────┐
    │ hdac_ext_stream    │   programmed by    │ sof_ipc4_copier    │
    │ stream_tag, LinkDMA│ ◀───── BE DAI ───▶ │ dma_config_tlv[]   │
    └────────────────────┘                    └────────────────────┘
              ▲                                          ▲
              │   snd_soc_dai_ops (hw_params/trigger)    │
              │                                          │
        ┌─────┴──────────────────────────────────────────┴─────┐
        │  one skl_dai[] entry  (struct snd_soc_dai_driver)    │
        │  ops ─▶ hda_dai_ops / ssp_dai_ops / dmic_dai_ops     │
        └───────────────────────────┬──────────────────────────┘
                                    │  hda_select_dai_widget_ops()
              ┌──────────┬──────────┼──────────┬──────────┐
              ▼          ▼          ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
         │HDA gw  │ │SSP gw  │ │DMIC gw │ │SDW gw  │ │chain-DMA │
         │hda_ipc4│ │ssp_ipc4│ │dmic_ip4│ │sdw_ipc4│ │*_chain   │
         └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
         struct hda_dai_widget_dma_ops variants (per gateway)
```
