# ASoC CPU DAI driver

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A CPU DAI driver describes the SoC or host side of an audio link, the port on the application processor that a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) names through its [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), while the codec DAI driver describes the peripheral on the far end of the same wire. Both halves use the identical [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) descriptor and the same [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) function pointer struct, so the difference is one of role rather than of type. On an Intel x86-64 platform the CPU side is the Sound Open Firmware DSP, and its platform component registers an array of back-end DAIs in [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) per HDA, SSP, DMIC, or ALH endpoint, named `"Analog CPU DAI"`, `"SSP0 Pin"`, `"DMIC01 Pin"`, `"iDisp1 Pin"`, and the like. The SOF component populates the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointer of each entry at probe time through [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745), matching by name so an HDA-link DAI gets [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), an SSP DAI gets [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479), and a DMIC DAI gets [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486), then hands the whole array to the machine layer as [`mach_params->dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) in [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438). Each of these is a DPCM back-end DAI, sitting on a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) whose [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit is set, so it carries no ALSA PCM device of its own and is driven by the core only when a front-end PCM routes audio onto it.

```
    SOF DSP platform component (sof_hda_common_ops)
    ┌────────────────────────────────────────────────────────────┐
    │  .drv ─▶ skl_dai[SOF_SKL_NUM_DAIS]                         │
    │  each entry a struct snd_soc_dai_driver  (CPU / back-end)  │
    └──────────────────────────────┬─────────────────────────────┘
                                   │ hda_set_dai_drv_ops() binds .ops by name
          ┌──────────┬─────────────┼─────────────┬──────────────┐
          ▼          ▼             ▼             ▼              ▼
    ┌──────────┐┌──────────┐┌────────────┐┌────────────┐┌──────────────┐
    │ iDisp1   ││ Analog   ││  SSP0 Pin  ││ DMIC01 Pin ││ Alt Analog   │
    │ Pin (HDA)││ CPU DAI  ││   (SSP)    ││  (DMIC)    ││ CPU DAI (ALH)│
    │hda_dai_op││hda_dai_op││ssp_dai_ops ││dmic_dai_ops││ hda_dai_ops  │
    └──────────┘└──────────┘└────────────┘└────────────┘└──────────────┘
        no_pcm back-end DAIs, hosted by the SOF DSP (the CPU side)

    contrast: a codec DAI driver (rt5682, far end of the same link)
    ┌────────────────────────────────────────────────────────────┐
    │  struct snd_soc_dai_driver  rt5682_dai[]                   │
    │  .ops fixed at compile time, programs the codec serial port│
    └────────────────────────────────────────────────────────────┘
```

## SUMMARY

A CPU DAI driver and a codec DAI driver are the two ends of one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and they share a representation. Each is one or more [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries placed in an array and registered under a component, each declares [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capabilities as two [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) records, and each points at one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) function pointer struct. The CPU DAI is the SoC-internal port that moves the stream between the link and the DMA or DSP, and the codec DAI is the off-chip device that drives the analog pins. The link binds them by the [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) and [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) name entries.

A component publishes its DAIs through [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932), which allocates the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and forwards the descriptor array to [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885), which calls [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) to register each entry and link the resulting runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) instances onto the component. On Intel the SOF DSP is that component. Its [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) carries the back-end DAI table in [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351), set to [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) and [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424) in [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17), and that table reaches the topology through [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438) as [`mach_params->dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78). Every [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry is a DPCM back-end DAI whose [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) sets [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), so it exposes no PCM character device and runs only when a front-end PCM is connected to it.

The CPU DAI's [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) implements the host-side meaning of each PCM operation, programming DMA and DSP rather than a codec serial port. The SOF HDA-link ops [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) fill in [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), and their handlers reach the HDAudio link DMA and the IPC4 pipeline through a per-widget [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027). The SSP and DMIC variants [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) substitute [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) and [`non_hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470), which add an IPC4 DMA-config TLV for endpoints that the host does not drive over an HDA stream.

## SPECIFICATIONS

The [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) descriptor and the CPU-versus-codec distinction are Linux kernel software constructs with no standalone hardware specification. The transports the SOF back-end DAIs front are defined by their interface standards. The HDA-link DAIs (`"Analog CPU DAI"`, `"iDisp1 Pin"`) follow the Intel High Definition Audio Specification, the SSP DAIs (`"SSP0 Pin"`) follow the I2S/TDM serial-audio conventions of the Intel audio DSP, and the DMIC DAIs (`"DMIC01 Pin"`) carry PDM digital-microphone data.

## LINUX KERNEL

### Generic DAI descriptor and link types (soc-dai.h, soc.h)

- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the static per-DAI descriptor a CPU/platform or codec driver registers; identical type on both sides of a link
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct; a CPU DAI fills the same fields a codec DAI does but programs DMA/DSP instead of a serial port
- [`'\<struct snd_soc_pcm_stream\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610): one direction's capability record (`formats`, `rates`, `channels_min`/`channels_max`); the core intersects the CPU record with the codec record
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): the runtime instance allocated per descriptor at registration
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): one link in a card; its [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit marks a DPCM back end
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): the `name`/`dai_name` pair that selects the CPU or codec DAI for a link by string

### Component and DAI registration (soc-core.c, soc-devres.c)

- [`'\<snd_soc_register_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932): allocate a component, initialize it, and add it with its DAI descriptor array
- [`'\<snd_soc_add_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885): register the DAIs, set up the regmap, and place the component on the global list under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48)
- [`'\<snd_soc_register_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773): loop over the descriptor array, registering each entry and rolling back on failure
- [`'\<snd_soc_register_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706): allocate one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) and link it onto the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): the device-managed form most drivers call

### SOF platform component and back-end DAI table (sof/intel)

- [`'\<skl_dai\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788): the array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) CPU/back-end DAIs (`SSP0..5 Pin`, `DMIC01 Pin`, `DMIC16k Pin`, `iDisp1..4 Pin`, `Analog CPU DAI`, `Digital CPU DAI`, `Alt Analog CPU DAI`)
- [`'sof_hda_common_ops':'sound/soc/sof/intel/hda-common-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17): the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) that sets [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) to [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351) to [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424)
- [`'\<struct snd_sof_dsp_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165): the SOF DSP function pointer struct; [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350)/[`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351) carry the CPU DAI table
- [`'\<struct sof_dev_desc\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128): the per-device descriptor whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L173) points at the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165)
- [`'\<hda_set_mach_params\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438): copy [`desc->ops->drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) into [`mach_params->dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) so the topology can match the back-end DAIs
- [`'\<struct snd_soc_acpi_mach_params\>':'include/sound/soc-acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78): the machine-configuration block that carries [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) and [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78)

### SOF back-end DAI ops binding (sof/intel/hda-dai.c)

- [`'\<hda_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745): bind each [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) by matching its `name` against `"iDisp"`, `"Analog"`, `"Digital"`
- [`'hda_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354): the HDA-link CPU DAI ops (`hw_params`, `hw_free`, `trigger`, `prepare`)
- [`'ssp_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479): the SSP CPU DAI ops, bound by [`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) on ACE 2.0 and later hardware
- [`'dmic_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486): the DMIC CPU DAI ops, bound by [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723)

### SOF CPU DAI callback handlers (sof/intel/hda-dai.c)

- [`'\<hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273): the HDA-link [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler, a thin wrapper over [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240)
- [`'\<hda_dai_hw_free\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221): the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler, releasing the link DMA through [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117)
- [`'\<hda_dai_trigger\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287): the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler, mixing IPC4 pipeline state changes with direct DMA register changes
- [`'\<hda_dai_prepare\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346): the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler, re-running [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) from the cached DPCM params
- [`'\<non_hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) / [`'\<non_hda_dai_prepare\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L470): the SSP/DMIC variants, adding an IPC4 DMA-config TLV via [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372)
- [`'\<hda_dai_get_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70): select the per-widget [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) the handlers dispatch through

### CPU-side back-end link wiring in the machine driver (intel/boards)

- [`'\<set_ssp_codec_link\>':'sound/soc/intel/boards/sof_board_helpers.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L180): build a back-end [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), set [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) to `"SSP%d Pin"`, and set [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<set_dmic_link\>':'sound/soc/intel/boards/sof_board_helpers.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L226): build a DMIC back end with [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) `"DMIC01 Pin"` or `"DMIC16k Pin"`
- [`'\<set_idisp_hdmi_link\>':'sound/soc/intel/boards/sof_board_helpers.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L276): build an HDMI/iDisp back end with [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) `"iDisp%d Pin"`

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept and the AC97, I2S, and PCM families
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model the SOF back ends use, and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) back-end link
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform/CPU side of ASoC and its DMA and DAI driver
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): how a machine driver names the CPU and codec DAIs of each link
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK/BCLK/LRCLK relationships the clocking ops configure

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Intel SOF audio DSP DAI overview](https://thesofproject.github.io/latest/architectures/firmware/sof-common/dai.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every callback a CPU DAI implements is a field of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), the same struct a codec DAI uses, and the same [`snd_soc_dai_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) wrapper in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) reaches each one, testing for the op and treating an absent op as success. What differs is the body of the op. A codec DAI programs its serial port over I2C or SoundWire, while a CPU DAI programs the host DMA and, on SOF, the DSP pipeline. The SOF HDA-link ops [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) supply four of these callbacks and leave the rest NULL, so the wrapper short-circuits the unimplemented ones.

| PCM operation | DAI op (wrapper) | SOF HDA-link handler |
|---------------|------------------|----------------------|
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) | [`hda_dai_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) |
| `SNDRV_PCM_IOCTL_PREPARE` | [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354) | [`hda_dai_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346) |
| `SNDRV_PCM_IOCTL_START` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603) (START) | [`hda_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) |
| `SNDRV_PCM_IOCTL_DROP` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603) (STOP) | [`hda_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) | [`hda_dai_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) |

### hw_params and hw_free

[`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) on a CPU DAI claims the host transport for the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408). For the SOF HDA-link DAI, [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) assigns and configures an HDAudio link DMA stream and primes the IPC4 copier, and [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) releases that stream through [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117). For an SSP or DMIC DAI, [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460) does the same link-DMA setup and then writes a DMA-config TLV into the copier so the DSP knows which stream tag carries the endpoint.

### prepare

[`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) runs after a parameter change and after an xrun recovery. The SOF handler [`hda_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L346) re-applies the cached DPCM parameters by calling [`hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L273) again with the back end's stored parameters, so a back-end DAI that lost its link state during a front-end reconfiguration re-establishes the stream before it restarts.

### trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) on a CPU DAI starts and stops the data flow on the host side. [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) dispatches the command through the per-widget [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) steps, then on STOP or SUSPEND cleans up the link DMA. According to the comment on [`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287), "In contrast to IPC3, the dai trigger in IPC4 mixes pipeline state changes (over IPC channel) and DMA state change (direct host register changes)", so the back-end op both messages the DSP and touches host registers in one call.

## DETAILS

### A CPU DAI and a codec DAI are the two ends of one link

A [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) names its endpoints by string, and both endpoints are [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) entries holding a component name and a DAI name. The CPU entry selects a DAI the platform component registered, and the codec entry selects a DAI the codec component registered:

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

Both the CPU DAI and the codec DAI are described by the same descriptor type. There is no separate "CPU DAI driver" struct. The SoC side and the codec side both populate [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and the role is decided by which component registers it and which side of the link names it:

```c
/* include/sound/soc-dai.h:403 */
struct snd_soc_dai_driver {
	/* DAI description */
	const char *name;
	unsigned int id;
	unsigned int base;
	struct snd_soc_dobj dobj;
	const struct of_phandle_args *dai_args;

	/* ops */
	const struct snd_soc_dai_ops *ops;
	const struct snd_soc_cdai_ops *cops;

	/* DAI capabilities */
	struct snd_soc_pcm_stream capture;
	struct snd_soc_pcm_stream playback;
	unsigned int symmetric_rate:1;
	unsigned int symmetric_channels:1;
	unsigned int symmetric_sample_bits:1;
};
```

The same fields group into description, ops, and capability bands, with the side of the link a given copy serves fixed by the component that registers it:

```
    struct snd_soc_dai_driver: same type on both sides
    ───────────────────────────────────────────────────
    role is set by which component registers it,
    not by the struct type
    ┌──────────────────────────────────────────────────────┐
    ├─ description ────────────────────────────────────────┤
    │ name   id   base   dobj   dai_args                   │
    ├─ ops ────────────────────────────────────────────────┤
    │ ops   ─────▶ const snd_soc_dai_ops *                 │
    │ cops  ─────▶ const snd_soc_cdai_ops *                │
    ├─ capabilities ───────────────────────────────────────┤
    │ playback ─▶ struct snd_soc_pcm_stream                │
    │ capture  ─▶ struct snd_soc_pcm_stream                │
    │ symmetric_rate:1  _channels:1  _sample_bits:1        │
    └──────────────────────────────────────────────────────┘
```

### The link struct carries the endpoints and the back-end flag

The [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is the machine-driver record that joins the two halves. Its [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the CPU/platform DAIs and its [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the codec DAIs, both as [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) name entries, and the [`platforms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) array names the component that owns the PCM/DMA. The struct is large; the load-bearing fields for a CPU DAI back end are the endpoint arrays and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit that marks the link as a DPCM back end with no PCM device of its own:

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
	/* For unidirectional dai links */
	unsigned int playback_only:1;
	unsigned int capture_only:1;
	...
	/* Do not create a PCM for this DAI link (Backend link) */
	unsigned int no_pcm:1;

	/* This DAI link can route to other DAI links at runtime (Frontend)*/
	unsigned int dynamic:1;
	...
};
```

The [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) name entry is the field the board helpers fill with `"SSP%d Pin"`, `"DMIC01 Pin"`, or `"iDisp%d Pin"`, and that string is what the core resolves against the CPU DAIs the SOF platform component registered. The [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit on a back-end link is the counterpart to the [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit on a front-end link, and the [`playback_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)/[`capture_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bits let a microphone or HDMI back end declare a single direction.

```
    struct snd_soc_dai_link: endpoints and FE/BE bits
    ──────────────────────────────────────────────────
    ┌──────────────────────────────────────────────────┐
    ├─ endpoints, each a dai_link_component ───────────┤
    │ cpus       num_cpus       ─▶ name / dai_name     │
    │ codecs     num_codecs     ─▶ name / dai_name     │
    │ platforms  num_platforms  ─▶ owns PCM / DMA      │
    ├─ role bits ──────────────────────────────────────┤
    │ no_pcm:1       back end, no PCM device           │
    │ dynamic:1      front end, routes at runtime      │
    │ playback_only:1  capture_only:1                  │
    └──────────────────────────────────────────────────┘
```

### The SOF DSP registers the CPU DAI array

The Intel SOF DSP is the platform component on an x86-64 ACPI system, and its [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) carries the CPU DAI table in two fields, the descriptor array pointer [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) and the count [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351):

```c
/* sound/soc/sof/sof-priv.h:350 */
	/* DAI ops */
	struct snd_soc_dai_driver *drv;
	int num_drv;
```

The shared HDA function pointer struct [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) sets those two fields to [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) and [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424), which a board's [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) reaches through its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L173) pointer:

```c
/* sound/soc/sof/intel/hda-common-ops.c:86 */
	/* DAI drivers */
	.drv		= skl_dai,
	.num_drv	= SOF_SKL_NUM_DAIS,
```

[`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) is the array of CPU/back-end DAIs. Each element is one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) that names a host-side port and declares only its channel range, leaving [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) unset in the static initializer so it can be bound at probe time. The SSP entries carry stereo-to-8-channel playback and capture, the DMIC entries carry capture only, and the HDA-codec entries carry the wide `"Analog CPU DAI"` and `"iDisp%d Pin"` ports:

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
...
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
};
EXPORT_SYMBOL_NS(skl_dai, "SND_SOC_SOF_INTEL_HDA_COMMON");
```

The channel ranges line up by direction, the SSP and analog ports declaring both playback and capture while the capture-only DMIC and playback-only iDisp rows leave the other column blank:

```
    skl_dai capability records (snd_soc_pcm_stream)
    ────────────────────────────────────────────────
    snd_sof_dsp_ops.drv ─▶ skl_dai[SOF_SKL_NUM_DAIS]
    ┌──────────────────┬────────────────┬────────────────┐
    │ name             │ playback ch    │ capture ch     │
    ├──────────────────┼────────────────┼────────────────┤
    │ SSP0 Pin         │ 1 .. 8         │ 1 .. 8         │
    │ DMIC01 Pin       │ --             │ 1 .. 4         │
    │ iDisp1 Pin       │ 1 .. 8         │ --             │
    │ Analog CPU DAI   │ 1 .. 16        │ 1 .. 16        │
    └──────────────────┴────────────────┴────────────────┘
    -- = direction not declared by that entry
```

### Binding the ops to each back-end DAI by name

The static [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entries have no [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) until [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745) runs during DSP probe. It walks the array and assigns [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) to every HDA-link DAI it identifies by a `"iDisp"`, `"Analog"`, or `"Digital"` substring in the name, then delegates the SSP and DMIC entries to two helpers:

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
```

[`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) assigns [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) to each `"SSP"`-named DAI, and only on ACE 2.0 and later hardware where the host drives the SSP link DMA directly. [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) follows the same shape for `"DMIC"`-named DAIs. The three resulting ops tables differ only in the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handlers, the HDA-link table dispatching through the HDA stream path and the SSP/DMIC tables adding the IPC4 DMA-config TLV:

```c
/* sound/soc/sof/intel/hda-dai.c:354 */
static const struct snd_soc_dai_ops hda_dai_ops = {
	.hw_params = hda_dai_hw_params,
	.hw_free = hda_dai_hw_free,
	.trigger = hda_dai_trigger,
	.prepare = hda_dai_prepare,
};
```

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

Set side by side, the two tables share the release and start/stop handlers and differ only on the format-setup and prepare ops, where the non-HDA variants add an IPC4 DMA-config TLV:

```
    snd_soc_dai_ops vtables bound by name
    ─────────────────────────────────────
    ┌────────────┬───────────────────┬──────────────────────┐
    │ op field   │ hda_dai_ops       │ ssp / dmic_dai_ops   │
    ├────────────┼───────────────────┼──────────────────────┤
    │ hw_params  │ hda_dai_hw_params │ non_hda_dai_hw_params│
    │ hw_free    │ hda_dai_hw_free   │ hda_dai_hw_free      │
    │ trigger    │ hda_dai_trigger   │ hda_dai_trigger      │
    │ prepare    │ hda_dai_prepare   │ non_hda_dai_prepare  │
    └────────────┴───────────────────┴──────────────────────┘
    tables differ only in hw_params and prepare;
    non_hda variants add an IPC4 DMA-config TLV
```

### Handing the array to the machine layer

Once the ops are bound, the array is offered to the machine driver and topology through [`hda_set_mach_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1438), which copies the descriptor table and its count out of [`desc->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L173) into the [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) the machine match carries:

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

The [`dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) and [`num_dai_drivers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) fields of [`struct snd_soc_acpi_mach_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L78) are the channel by which the SOF platform exports its CPU DAI set, so the topology can resolve each back-end link's [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) name to one of the registered DAIs:

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

### Registration allocates the runtime CPU DAIs

A component publishes its DAI array through [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932), which allocates the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), initializes it, and forwards the descriptor array and count to [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885). That function takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), optionally byte-swaps the capability formats, then calls [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) to register every descriptor in the array before placing the component on the global list.

Most drivers do not call [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) directly but reach it through the device-managed wrapper [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), which records a devres action so the component is torn down automatically when the device unbinds:

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

[`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) does the allocation and the one-time initialization, allocating the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) with `devm_kzalloc`, running [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850), then handing the same descriptor array straight to [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885):

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

[`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) is where the descriptor array becomes live DAIs. Under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) it byte-swaps the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) formats when the component declares an endianness, calls [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) to turn each descriptor into a runtime DAI, wires up the regmap if the component has neither `read` nor `write`, then adds the component to `component_list` and rebinds any cards that were waiting for it:

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

	if (component->driver->endianness) {
		for (i = 0; i < num_dai; i++) {
			convert_endianness_formats(&dai_drv[i].playback);
			convert_endianness_formats(&dai_drv[i].capture);
		}
	}

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

The inner [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) loop is the step that produces one runtime CPU DAI per descriptor:

```c
/* sound/soc/soc-core.c:2773 */
static int snd_soc_register_dais(struct snd_soc_component *component,
				 struct snd_soc_dai_driver *dai_drv,
				 size_t count)
{
	struct snd_soc_dai *dai;
	unsigned int i;
	int ret;

	for (i = 0; i < count; i++) {
		dai = snd_soc_register_dai(component, dai_drv + i, count == 1 &&
					   component->driver->legacy_dai_naming);
		if (dai == NULL) {
			ret = -ENOMEM;
			goto err;
		}
	}

	return 0;

err:
	snd_soc_unregister_dais(component);

	return ret;
}
```

[`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) loops over the descriptor array and calls [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) once per entry, allocating a runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) for each [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) descriptor and unwinding the whole set if any single registration fails. The runtime DAIs land on the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), where the binder's [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L917) later finds each back-end link's named CPU DAI.

### The back-end DAI is named on the link's CPU side

A back-end DAI exists because a machine driver creates a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) whose [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry names one of the registered SOF DAIs and whose [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) bit is set. [`set_ssp_codec_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L180) builds exactly that for an SSP-attached codec, setting the CPU [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) to `"SSP%d Pin"` so it resolves to the matching [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry, and marking the link [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). It receives the caller's [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) by pointer and fills in its fields, naming the link `"SSP%d-Codec"` and leaving the codec entry for the caller:

```c
/* sound/soc/intel/boards/sof_board_helpers.c:180 */
static int set_ssp_codec_link(struct device *dev, struct snd_soc_dai_link *link,
			      int be_id, enum snd_soc_acpi_intel_codec codec_type,
			      int ssp_codec)
{
	struct snd_soc_dai_link_component *cpus;

	dev_dbg(dev, "link %d: ssp codec %s, ssp %d\n", be_id,
		snd_soc_acpi_intel_get_codec_name(codec_type), ssp_codec);

	/* link name */
	link->name = devm_kasprintf(dev, GFP_KERNEL, "SSP%d-Codec", ssp_codec);
	if (!link->name)
		return -ENOMEM;
```

```c
/* sound/soc/intel/boards/sof_board_helpers.c:194 */
	/* cpus */
	cpus = devm_kzalloc(dev, sizeof(struct snd_soc_dai_link_component),
			    GFP_KERNEL);
	if (!cpus)
		return -ENOMEM;

	if (soc_intel_is_byt() || soc_intel_is_cht()) {
		/* backward-compatibility for BYT/CHT boards */
		cpus->dai_name = devm_kasprintf(dev, GFP_KERNEL, "ssp%d-port",
						ssp_codec);
	} else {
		cpus->dai_name = devm_kasprintf(dev, GFP_KERNEL, "SSP%d Pin",
						ssp_codec);
	}
	if (!cpus->dai_name)
		return -ENOMEM;

	link->cpus = cpus;
	link->num_cpus = 1;

	/* codecs - caller to handle */

	/* platforms */
	link->platforms = platform_component;
	link->num_platforms = ARRAY_SIZE(platform_component);

	link->id = be_id;
	link->no_pcm = 1;
```

Because [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is set, this link is a DPCM back end with no ALSA PCM character device, and the ASoC core runs its CPU DAI ops only when a front-end PCM routes a running stream onto it. The same helper file sets [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) to `"DMIC01 Pin"` in [`set_dmic_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L226) and to `"iDisp%d Pin"` in [`set_idisp_hdmi_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L276), each name matching a [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) entry the SOF DSP registered.

[`set_dmic_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L226) picks the [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) from the requested PDM rate, `"DMIC01 Pin"` for the base array and `"DMIC16k Pin"` for the 16 kHz endpoint, points the codec at the fixed DMIC component, and sets [`capture_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) on top of [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) because a microphone back end has no playback direction:

```c
/* sound/soc/intel/boards/sof_board_helpers.c:226 */
static int set_dmic_link(struct device *dev, struct snd_soc_dai_link *link,
			 int be_id, enum sof_dmic_be_type be_type)
{
	struct snd_soc_dai_link_component *cpus;

	/* cpus */
	cpus = devm_kzalloc(dev, sizeof(struct snd_soc_dai_link_component),
			    GFP_KERNEL);
	if (!cpus)
		return -ENOMEM;

	switch (be_type) {
	case SOF_DMIC_01:
		dev_dbg(dev, "link %d: dmic01\n", be_id);

		link->name = "dmic01";
		cpus->dai_name = "DMIC01 Pin";
		break;
	case SOF_DMIC_16K:
		dev_dbg(dev, "link %d: dmic16k\n", be_id);

		link->name = "dmic16k";
		cpus->dai_name = "DMIC16k Pin";
		break;
	default:
		dev_err(dev, "invalid be type %d\n", be_type);
		return -EINVAL;
	}

	link->cpus = cpus;
	link->num_cpus = 1;
	...
	link->id = be_id;
	if (be_type == SOF_DMIC_01)
		link->init = dmic_init;
	link->ignore_suspend = 1;
	link->no_pcm = 1;
	link->capture_only = 1;

	return 0;
}
```

[`set_idisp_hdmi_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L276) builds the display-audio back end, formatting [`cpus->dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) as `"iDisp%d Pin"` so it resolves to the matching `iDisp` entry in [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), pairing it with the HDA HDMI codec DAI when one is present and with [`snd_soc_dummy_dlc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-utils.c#L258) otherwise, and setting [`playback_only`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) since HDMI is output only:

```c
/* sound/soc/intel/boards/sof_board_helpers.c:276 */
static int set_idisp_hdmi_link(struct device *dev, struct snd_soc_dai_link *link,
			       int be_id, int hdmi_id, bool idisp_codec)
{
	struct snd_soc_dai_link_component *cpus, *codecs;
	...
	cpus->dai_name = devm_kasprintf(dev, GFP_KERNEL, "iDisp%d Pin", hdmi_id);
	if (!cpus->dai_name)
		return -ENOMEM;

	link->cpus = cpus;
	link->num_cpus = 1;

	/* codecs */
	if (idisp_codec) {
		codecs = devm_kzalloc(dev,
				      sizeof(struct snd_soc_dai_link_component),
				      GFP_KERNEL);
		if (!codecs)
			return -ENOMEM;

		codecs->name = "ehdaudio0D2";
		codecs->dai_name = devm_kasprintf(dev, GFP_KERNEL,
						  "intel-hdmi-hifi%d", hdmi_id);
		if (!codecs->dai_name)
			return -ENOMEM;

		link->codecs = codecs;
	} else {
		link->codecs = &snd_soc_dummy_dlc;
	}
	link->num_codecs = 1;
	...
	link->id = be_id;
	link->init = (hdmi_id == 1) ? hdmi_init : NULL;
	link->no_pcm = 1;
	link->playback_only = 1;

	return 0;
}
```

Across the three setters the shape is the same. Each allocates a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) for [`cpus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), writes the CPU [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) string that names one registered SOF DAI, attaches the shared [`platform_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_board_helpers.c#L173), and sets [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), which is the entire machine-side definition of a CPU DAI back end.

```
    board helper sets cpus->dai_name and the BE flags
    ─────────────────────────────────────────────────
    ┌──────────────────────┬────────────────┬──────────────────┐
    │ board helper         │ cpus->dai_name │ extra flags      │
    ├──────────────────────┼────────────────┼──────────────────┤
    │ set_ssp_codec_link   │ SSP%d Pin      │ no_pcm           │
    │ set_dmic_link        │ DMIC01 Pin     │ no_pcm           │
    │   (or 16 kHz)        │ DMIC16k Pin    │ + capture_only   │
    │ set_idisp_hdmi_link  │ iDisp%d Pin    │ no_pcm           │
    │   (HDMI out)         │                │ + playback_only  │
    └──────────────────────┴────────────────┴──────────────────┘
    each name resolves to one registered skl_dai entry
```

### The CPU DAI hw_params bridges to the DSP

When a front-end stream reaches the SSP back-end DAI, its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op runs [`non_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L460), which forwards to [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372). That helper selects the per-widget [`struct hda_dai_widget_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) with [`hda_dai_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L70), assigns an HDAudio link DMA stream, reads back the allocated stream tag, and writes it into the IPC4 copier's DMA-config TLV so the DSP pipeline routes the endpoint to that DMA channel:

```c
/* sound/soc/sof/intel/hda-dai.c:372 */
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
	...
	hstream = &hext_stream->hstream;
	stream_id = hstream->stream_tag;
	...
	/* configure TLV */
	ipc4_copier = widget_to_copier(w);
	...
	dma_config->dma_method = SOF_IPC4_DMA_METHOD_HDA;
	dma_config->pre_allocated_by_host = 1;
	dma_config->dma_channel_id = stream_id - 1;
	dma_config->stream_id = stream_id;
```

The CPU DAI op is the bridge between the ALSA PCM operation and the DSP, claiming the host DMA stream and then describing that stream to the firmware copier. The codec DAI on the same link, by contrast, programs an off-chip serial port and never touches a host DMA stream tag, which is the concrete difference the shared [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) type lets each side express in its own [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) body.

### The trigger op messages the DSP and the DMA together

[`hda_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L287) is the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler shared by all three ops tables. It fetches the widget DMA ops, runs the optional [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) steps in order, and on STOP or SUSPEND tears down the link DMA:

```c
/* sound/soc/sof/intel/hda-dai.c:287 */
static int __maybe_unused hda_dai_trigger(struct snd_pcm_substream *substream, int cmd,
					  struct snd_soc_dai *dai)
{
	const struct hda_dai_widget_dma_ops *ops = hda_dai_get_ops(substream, dai);
	struct hdac_ext_stream *hext_stream;
	struct snd_sof_dev *sdev;
	int ret;

	if (!ops) {
		dev_err(dai->dev, "DAI widget ops not set\n");
		return -EINVAL;
	}
	...
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
		if (ret < 0) {
			dev_err(sdev->dev, "%s: failed to clean up link DMA\n", __func__);
			return ret;
		}
		break;
	default:
		break;
	}

	return 0;
}
```

The split between [`pre_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027), and [`post_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1027) is where the IPC4 pipeline message and the host DMA register write are ordered against each other, and [`hda_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L221) releases the same link DMA on teardown through [`hda_link_dma_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L117), closing the resource the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op claimed.
