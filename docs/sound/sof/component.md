# SOF ASoC component

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Sound Open Firmware registers itself with the SoC sound layer as one ASoC platform component whose static description is a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) built at probe by [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) into the [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) field of the per-device [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), registered by [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), wiring each generic PCM callback (`sof_pcm_open`, `sof_pcm_hw_params`, `sof_pcm_prepare`, `sof_pcm_trigger`, `sof_pcm_pointer`, `sof_pcm_hw_free`, `sof_pcm_new`) to a body that locates the per-front-end-DAI-link [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) with [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616) and routes the DSP-side work to the active IPC version's [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) reached through the [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro.

```
    SOF ASoC platform component (one per snd_sof_dev)
    ─────────────────────────────────────────────────

    struct snd_soc_component_driver  plat_drv  ("sof-audio-component")
    ┌─────────────────────────────────────────────────────────────┐
    │  name "sof-audio-component"   probe ─▶ sof_pcm_probe        │
    │  open ─▶ sof_pcm_open      hw_params ─▶ sof_pcm_hw_params   │
    │  prepare ─▶ sof_pcm_prepare   trigger ─▶ sof_pcm_trigger    │
    │  hw_free ─▶ sof_pcm_hw_free   pointer ─▶ sof_pcm_pointer    │
    │  pcm_construct ─▶ sof_pcm_new                               │
    │  be_hw_params_fixup ─▶ sof_pcm_dai_link_fixup              │
    └────────────────┬────────────────────────────┬──────────────┘
                     │ snd_sof_find_spcm_dai       │ sof_ipc_get_ops(sdev, pcm)
                     ▼                             ▼
    sdev->pcm_list                       struct sof_ipc_pcm_ops  (per IPC ver)
    ┌──────────────────────────┐         ┌───────────────────────────────┐
    │ struct snd_sof_pcm  pcm0 │         │ hw_params  hw_free  trigger   │
    │   stream[PLAYBACK]       │         │ pointer  dai_link_fixup       │
    │   stream[CAPTURE]        │         │ ipc_first_on_start (flags)    │
    │ struct snd_sof_pcm  pcm1 │         └───────────────┬───────────────┘
    │   ...                    │                         │ IPC4 = ipc4_pcm_ops
    └──────────────────────────┘                         ▼
                                          ┌─────────────────────────────┐
                                          │  DSP firmware: pipeline     │
                                          │  modules, host DMA, link DMA│
                                          └─────────────────────────────┘
```

## SUMMARY

SOF presents one ASoC platform component to the SoC sound layer rather than a codec, and that component's static description is the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) embedded as [`sdev->plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569). A codec driver writes that descriptor as a static initializer, but SOF cannot, because the same [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) code serves every DSP platform and the back-end fixup pointer and the ignore-machine string vary with the matched machine. [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) fills the descriptor at probe, assigning the name "sof-audio-component", every PCM operation, the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback, and the topology fields, then [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) registers it with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) alongside the DAI driver array from [`sof_ops(sdev)->drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350). The name string equals the [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24) macro that the SOF code later passes to [`snd_soc_rtdcom_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L336) to find its own component on a runtime. The descriptor sets [`be_pcm_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to [`SOF_BE_PCM_BASE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L38) (16), marks [`use_dai_pcm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so the DAI link PCM id becomes the device number, sets [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so the module refcount rises only while a PCM is open, and sets [`ignore_machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to the machine driver name so topology front-ends replace the machine driver's.

The per-PCM tracking object is the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352). Topology creates one per front-end DAI link and links it onto [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and each object carries a two-element [`stream[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array of [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), the per-direction [`prepared[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) and [`setup_done[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) flags, and the topology PCM record [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) as a trailing flex-array member. Each [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) holds the firmware component id [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), the position record [`posn`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) the firmware updates, the connected DAPM widget [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), and the active substream pointer [`substream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329). Three lookups walk [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), so a component op resolves its object by runtime through [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616), by name through [`snd_sof_find_spcm_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L911), and by firmware component id through [`snd_sof_find_spcm_comp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L936).

The DSP-specific work behind each callback is never inlined into the component body. It is reached through the IPC-version function pointer struct [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), retrieved through the [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro that reads the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) member of the active [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) at [`sdev->ipc->ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547). On an Intel MTL or HDA-generation platform that pointer is the IPC4 instance [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), wired into [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) at [`.pcm = &ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L923). The macro returns NULL when the IPC layer is not up, so every call site tests the returned pointer and the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member separately before dereferencing. The per-callback bodies (`sof_pcm_open`, `sof_pcm_hw_params`, `sof_pcm_prepare`, `sof_pcm_trigger`, `sof_pcm_pointer`, `sof_pcm_hw_free`, `sof_pcm_new`) are documented alongside the SOF PCM operations, and the IPC4 implementations of the ops members alongside the IPC4 PCM ops.

## SPECIFICATIONS

The SOF ASoC platform component is a Linux kernel software construct and has no standalone hardware specification. SOF is open firmware, and the DSP message protocol the component delegates to through [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is defined by the Sound Open Firmware ABI, whose IPC4 variant in [`include/sound/sof/ipc4/`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h) follows Intel's Audio DSP firmware interface. On an x86-64 ACPI platform a SOF instance is described to the kernel by an ACPI device (for example INTC10DE on Meteor Lake) that the SOF PCI or ACPI glue matches, and the host side of the audio transport the platform ops drive is the High Definition Audio stream descriptor set defined by the Intel High Definition Audio Specification.

## LINUX KERNEL

### Component descriptor build and registration (pcm.c, core.c)

- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): fill the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) embedded as [`sdev->plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569), set the name to "sof-audio-component", and wire every PCM op and topology field
- [`'\<sof_probe_continue\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454): the probe-tail flow that calls [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) and registers the component and DAI drivers with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'\<sof_pcm_probe\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, run at card bind, resumes the device and loads the DSP topology through [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c)
- [`'\<sof_pcm_remove\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L797): the component [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, tears the topology down through [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c)
- [`'\<snd_soc_rtdcom_lookup\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L336): find a component on a runtime by driver name, used by SOF with [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24) to recover its own component
- [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24): the component name string "sof-audio-component"
- [`SOF_BE_PCM_BASE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L38): the value 16 assigned to [`be_pcm_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)

### The ASoC component descriptor and runtime (soc-component.h, soc-core.c)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the static description SOF populates, holding every PCM callback pointer, [`be_pcm_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`use_dai_pcm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`ignore_machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the runtime component the ASoC core builds from the descriptor at registration; its [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L210) drvdata holds the back pointer to [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): the device-managed registration SOF calls, building one runtime component carrying the DAI drivers and unregistering it when the device is removed
- [`'\<snd_soc_component_get_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356): return the [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) every SOF component op reads from the component

### The SOF PCM tracking object (sof-audio.h, sof-audio.c)

- [`'\<struct snd_sof_pcm\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352): the ALSA SOF PCM device topology creates per front-end DAI link; holds the two-element [`stream[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array, the [`prepared[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352)/[`setup_done[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) flags, and the trailing topology [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) record
- [`'\<struct snd_sof_pcm_stream\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329): one direction's runtime state, the firmware [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), the [`posn`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) record, the connected DAPM widget [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), and the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) pointer
- [`'\<struct sof_ipc_stream_posn\>':'include/sound/sof/stream.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L136): the position record the firmware writes back, with [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142) and [`dai_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L143)
- [`'\<snd_sof_find_spcm_dai\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616): match a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) to a runtime by comparing the topology PCM [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) to the DAI link id
- [`'\<snd_sof_find_spcm_name\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L911): match by DAI name or stream-caps name
- [`'\<snd_sof_find_spcm_comp\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L936): match by firmware [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) and report the direction

### IPC-version PCM ops indirection (sof-audio.h, sof-priv.h)

- [`'\<struct sof_ipc_pcm_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123): the IPC-version function pointer struct carrying `hw_params`, `hw_free`, `trigger`, `dai_link_fixup`, `pcm_setup`, `pcm_free`, `pointer`, `delay`, and the trigger-ordering flags
- [`'\<struct sof_ipc_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503): the per-IPC-version ops aggregate whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) member is the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) pointer
- [`sof_ipc_get_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541): the macro returning [`sdev->ipc->ops->ops_name`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) or NULL when the IPC layer is not up
- [`sof_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21): the macro returning the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) at [`sdev->pdata->desc->ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547)
- [`'\<struct snd_sof_dsp_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165): the platform DSP abstraction whose [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) DAI-driver array registers under the one component

### Per-device anchor (sof-priv.h)

- [`'\<struct snd_sof_dev\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547): the SOF device object holding the embedded [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) descriptor, the [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) of [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352), the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer, and the [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) handle the ops indirection reads

### Intel MTL/IPC4 worked-example symbols (ipc4-pcm.c, ipc4.c)

- [`'ipc4_pcm_ops':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311): the IPC4 [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) instance, setting [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123)
- [`'ipc4_ops':'sound/soc/sof/ipc4.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912): the IPC4 [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) member is [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311)
- [`'\<sof_ipc4_pcm_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588): the IPC4 [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member, mapping the ALSA command to a [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) or [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) state

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the ASoC platform component concept and the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) PCM callbacks SOF fills
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model SOF registers into as a platform component
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end/back-end split topology drives and the [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) back-end that each component op returns early for
- [`Documentation/sound/designs/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/index.rst): ALSA design notes covering the PCM substream lifecycle the component operations follow

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF architecture overview](https://thesofproject.github.io/latest/architectures/firmware/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The component, its descriptor, and the per-PCM objects each have one creator, so a reader can follow the chain from the probe-time descriptor build to the runtime component and then to the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) objects topology creates and the IPC-version ops the component delegates to. [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) populates the descriptor in place inside [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) builds the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) from it, topology loading creates each [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352), and the IPC layer publishes the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) pointer the component reads per operation.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569)) | filled by [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) | embedded in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) for the device's life |
| [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) | [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | from probe to device removal (devm) |
| [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) | topology loading via [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759) | on [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) until topology removal |
| [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) | embedded in [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) ([`stream[2]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352)) | with its parent object |
| [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | static per IPC version (e.g. [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311)) | const, selected by [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) |

### The descriptor is built at runtime

[`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) writes the descriptor in place rather than as a static initializer, because the back-end fixup pointer is wired only when a DSP is in use and the [`ignore_machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) string comes from the matched machine table, neither of which is known at compile time. The descriptor is held in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) as [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) so it persists for the device's lifetime, and the comment on that field records that it cannot be const.

### The component name doubles as the lookup key

The descriptor name "sof-audio-component" equals the [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24) macro, so SOF code that holds only a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) recovers its own component with [`snd_soc_rtdcom_lookup(rtd, SOF_AUDIO_PCM_DRV_NAME)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L336). The literal in [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) and the macro must stay in step.

### Two ops structs behind the component

A component op reaches DSP work along two function pointer structs. The IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), reached through [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541), abstracts the firmware message protocol so the same body works for IPC3 and IPC4. The platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), reached through [`sof_ops(sdev)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21), drives the host side of the audio transport. The bodies that sequence the two are documented as the SOF PCM operations; this page covers the descriptor that names them and the indirection that selects the IPC version.

## DETAILS

### The component descriptor is the plat_drv field of snd_sof_dev

A codec driver writes a static [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) initializer. SOF does not, because the same [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) code serves every DSP platform and the descriptor varies with the platform. The descriptor is the [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) field embedded in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and the comment on that field records why it cannot be const:

```c
/* sound/soc/sof/sof-priv.h:547 */
struct snd_sof_dev {
	struct device *dev;
	spinlock_t ipc_lock;	/* lock for IPC users */
	spinlock_t hw_lock;	/* lock for HW IO access */
	...
	/*
	 * ASoC components. plat_drv fields are set dynamically so
	 * can't use const
	 */
	struct snd_soc_component_driver plat_drv;
	...
	/* IPC */
	struct snd_sof_ipc *ipc;
	...
	struct list_head pcm_list;
	...
	struct snd_soc_component *component;
	...
};
```

According to the comment, the [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) fields are set dynamically so the struct cannot be const. The same object also carries the [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) handle the ops indirection reads, the [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) the per-PCM objects link onto, and the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer the topology code sets once the runtime component exists.

```
    plat_drv is embedded; component points back into snd_sof_dev
    ────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ struct snd_sof_dev                                       │
    │   ┌────────────────────────────────────────────────────┐ │
    │   │ plat_drv  struct snd_soc_component_driver          │ │
    │   └────────────────────────────────────────────────────┘ │
    │ ipc        struct snd_sof_ipc *                          │
    │ pcm_list   struct list_head                              │
    │   component  struct snd_soc_component * ◀──┐             │
    └────────────────────────────────────────────┼─────────────┘
                                                 │ drvdata back pointer
    devm_snd_soc_register_component(&plat_drv) ──┘
       builds the runtime struct snd_soc_component
```

### snd_sof_new_platform_drv fills the descriptor

[`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) assigns the component name, every PCM operation, the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback, and the topology-related fields, and it conditionally wires the back-end fixup. The PCM-operation pointers name the bodies documented as the SOF PCM operations; this descriptor is what registers them as the component's callbacks:

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *drv_name;

	if (plat_data->machine)
		drv_name = plat_data->machine->drv_name;
	else if (plat_data->of_machine)
		drv_name = plat_data->of_machine->drv_name;
	else
		drv_name = NULL;

	pd->name = "sof-audio-component";
	pd->probe = sof_pcm_probe;
	pd->remove = sof_pcm_remove;
	pd->open = sof_pcm_open;
	pd->close = sof_pcm_close;
	pd->hw_params = sof_pcm_hw_params;
	pd->prepare = sof_pcm_prepare;
	pd->hw_free = sof_pcm_hw_free;
	pd->trigger = sof_pcm_trigger;
	pd->pointer = sof_pcm_pointer;
	pd->ack = sof_pcm_ack;
	pd->delay = sof_pcm_delay;

#if IS_ENABLED(CONFIG_SND_SOC_SOF_COMPRESS)
	pd->compress_ops = &sof_compressed_ops;
#endif

	pd->pcm_construct = sof_pcm_new;
	pd->ignore_machine = drv_name;
	pd->be_pcm_base = SOF_BE_PCM_BASE;
	pd->use_dai_pcm_id = true;
	pd->topology_name_prefix = "sof";

	 /* increment module refcount when a pcm is opened */
	pd->module_get_upon_open = 1;

	pd->legacy_dai_naming = 1;

	/*
	 * The fixup is only needed when the DSP is in use as with the DSPless
	 * mode we are directly using the audio interface
	 */
	if (!sdev->dspless_mode_selected)
		pd->be_hw_params_fixup = sof_pcm_dai_link_fixup;
}
```

The [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is "sof-audio-component". The [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) hooks load and tear down topology, the substream operations [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) through [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) are the per-stream callbacks, and [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is the PCM-create hook. The topology fields set [`be_pcm_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to [`SOF_BE_PCM_BASE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L38), mark [`use_dai_pcm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so the DAI link PCM id becomes the device number, set [`topology_name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to "sof", and set [`ignore_machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) to the matched machine driver name so topology front-ends replace the machine driver's. According to the comment, the fixup is only needed when the DSP is in use, so [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is wired to [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) only outside DSPless mode.

The name literal equals the [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24) macro, which the SOF code uses elsewhere to find its own component on a runtime, so the literal here and the macro stay in step:

```c
/* sound/soc/sof/sof-audio.h:24 */
#define SOF_AUDIO_PCM_DRV_NAME	"sof-audio-component"
```

```c
/* sound/soc/sof/sof-audio.h:38 */
#define SOF_BE_PCM_BASE		16
```

The relevant fields the descriptor uses are the standard ASoC ones plus the topology group at the tail of [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67):

```c
/* include/sound/soc-component.h:67 */
struct snd_soc_component_driver {
	const char *name;
	...
	int (*probe)(struct snd_soc_component *component);
	void (*remove)(struct snd_soc_component *component);
	...
	/* pcm creation and destruction */
	int (*pcm_construct)(struct snd_soc_component *component,
			     struct snd_soc_pcm_runtime *rtd);
	void (*pcm_destruct)(struct snd_soc_component *component,
			     struct snd_pcm *pcm);
	...
	int (*open)(struct snd_soc_component *component,
		    struct snd_pcm_substream *substream);
	int (*close)(struct snd_soc_component *component,
		     struct snd_pcm_substream *substream);
	...
	int (*hw_params)(struct snd_soc_component *component,
			 struct snd_pcm_substream *substream,
			 struct snd_pcm_hw_params *params);
	int (*hw_free)(struct snd_soc_component *component,
		       struct snd_pcm_substream *substream);
	int (*prepare)(struct snd_soc_component *component,
		       struct snd_pcm_substream *substream);
	int (*trigger)(struct snd_soc_component *component,
		       struct snd_pcm_substream *substream, int cmd);
	snd_pcm_uframes_t (*pointer)(struct snd_soc_component *component,
				     struct snd_pcm_substream *substream);
	...
	unsigned int module_get_upon_open:1;
	...
	/* this component uses topology and ignore machine driver FEs */
	const char *ignore_machine;
	const char *topology_name_prefix;
	int (*be_hw_params_fixup)(struct snd_soc_pcm_runtime *rtd,
				  struct snd_pcm_hw_params *params);
	bool use_dai_pcm_id;	/* use DAI link PCM ID as PCM device number */
	int be_pcm_base;	/* base device ID for all BE PCMs */
	...
};
```

The [`pcm_destruct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) pointer is left NULL, so the ASoC core's default buffer free runs at PCM destruction; SOF only supplies [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (the [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) pre-allocation). The [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) bit defers the module refcount from probe to the first PCM open, according to the comment in the body, so the SOF module can unload while no stream is active.

### sof_probe_continue registers the component and the DAI drivers

[`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) builds the descriptor early in the probe tail, then after the firmware has booted registers it together with the DAI driver array the platform ops expose:

```c
/* sound/soc/sof/core.c:454 */
static int sof_probe_continue(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *plat_data = sdev->pdata;
	int ret;
	...
	/* set up platform component driver */
	snd_sof_new_platform_drv(sdev);
	...
skip_dsp_init:
	/* hereafter all FW boot flows are for PM reasons */
	sdev->first_boot = false;

	/* now register audio DSP platform driver and dai */
	ret = devm_snd_soc_register_component(sdev->dev, &sdev->plat_drv,
					      sof_ops(sdev)->drv,
					      sof_ops(sdev)->num_drv);
	if (ret < 0) {
		dev_err(sdev->dev,
			"error: failed to register DSP DAI driver %d\n", ret);
		goto fw_trace_err;
	}
	...
}
```

The [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) members come from the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) reached through [`sof_ops(sdev)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21), so the DAI drivers a platform exposes (HDA link DAIs, SoundWire DAIs, DMIC DAIs) all register under the one component the descriptor describes. [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) builds the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) from the descriptor and records a devres release action, so the component is torn down automatically when the SOF device is removed.

### The component probe loads topology

The descriptor's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) hook is [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759), run by the ASoC core when the component binds to its card. It resumes the device, records the runtime component in [`sdev->component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and loads the DSP topology, which is what creates the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) objects:

```c
/* sound/soc/sof/pcm.c:759 */
static int sof_pcm_probe(struct snd_soc_component *component)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *tplg_filename;
	int ret;

	/*
	 * make sure the device is pm_runtime_active before loading the
	 * topology and initiating IPC or bus transactions
	 */
	ret = pm_runtime_resume_and_get(component->dev);
	if (ret < 0 && ret != -EACCES)
		return ret;

	/* load the default topology */
	sdev->component = component;

	tplg_filename = devm_kasprintf(sdev->dev, GFP_KERNEL,
				       "%s/%s",
				       plat_data->tplg_filename_prefix,
				       plat_data->tplg_filename);
	if (!tplg_filename) {
		ret = -ENOMEM;
		goto pm_error;
	}

	ret = snd_sof_load_topology(component, tplg_filename);
	if (ret < 0)
		dev_err(component->dev, "error: failed to load DSP topology %d\n",
			ret);

pm_error:
	pm_runtime_put_autosuspend(component->dev);

	return ret;
}
```

The matching [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) hook reverses it:

```c
/* sound/soc/sof/pcm.c:797 */
static void sof_pcm_remove(struct snd_soc_component *component)
{
	/* remove topology */
	snd_soc_tplg_component_remove(component);
}
```

[`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356) is how every SOF component op recovers the [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547); it returns the device drvdata SOF set at device probe:

```c
/* include/sound/soc-component.h:356 */
static inline void *snd_soc_component_get_drvdata(struct snd_soc_component *c)
{
	return dev_get_drvdata(c->dev);
}
```

### The snd_sof_pcm tracking object

The [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) is the per-front-end-DAI-link device topology creates. It carries the per-direction stream state and ends in the topology PCM record, which is a flex-array member, so it is the last field:

```c
/* sound/soc/sof/sof-audio.h:352 */
struct snd_sof_pcm {
	struct snd_soc_component *scomp;
	struct snd_sof_pcm_stream stream[2];
	struct list_head list;	/* list in sdev pcm list */
	struct snd_pcm_hw_params params[2];
	struct snd_sof_platform_stream_params platform_params[2];
	bool prepared[2]; /* PCM_PARAMS set successfully */
	bool setup_done[2]; /* the setup of the SOF PCM device is done */
	bool pending_stop[2]; /* only used if (!pcm_ops->platform_stop_during_hw_free) */

	/* Must be last - ends in a flex-array member. */
	struct snd_soc_tplg_pcm pcm;
};
```

The [`stream[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array is indexed by playback and capture, the [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) node places the object on [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), the [`prepared[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) flag tracks whether the IPC-version hw_params has run for a direction, and the [`setup_done[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) flag tracks whether the connected widgets have been created in the firmware. The trailing topology [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) record holds the [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) the lookup matches and the stream capability tables the open callback copies into the runtime.

Each direction's runtime state is a [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) holding the firmware component id, the position record the firmware updates, the connected DAPM widget [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), and the active substream pointer:

```c
/* sound/soc/sof/sof-audio.h:329 */
struct snd_sof_pcm_stream {
	u32 comp_id;
	struct snd_dma_buffer page_table;
	struct sof_ipc_stream_posn posn;
	struct snd_pcm_substream *substream;
	struct snd_compr_stream *cstream;
	struct work_struct period_elapsed_work;
	struct snd_soc_dapm_widget_list *list; /* list of connected DAPM widgets */
	bool d0i3_compatible; /* DSP can be in D0I3 when this pcm is opened */
	bool pause_supported; /* PCM device supports PAUSE operation */
	unsigned int dsp_max_burst_size_in_ms; /* The maximum size of the host DMA burst in ms */
	...
	bool suspend_ignored;
	struct snd_sof_pcm_stream_pipeline_list pipeline_list;

	/* used by IPC implementation and core does not touch it */
	void *private;
};
```

The [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) is the firmware module id of the host-DMA widget for the direction, the [`posn`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) record is where the firmware writes the host and DAI positions the pointer callback reports, the [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) is the connected-widget list the prepare path builds, and the [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) pointer is reserved for the IPC implementation. The position record itself is the firmware-defined [`struct sof_ipc_stream_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L136):

```c
/* include/sound/sof/stream.h:136 */
struct sof_ipc_stream_posn {
	struct sof_ipc_reply rhdr;
	uint32_t comp_id;	/**< host component ID */
	uint32_t flags;		/**< see SOF_TIME_ flags */
	uint32_t wallclock_hi;	/**< upper 32bits of 64bit monotonic wallclock */
	uint32_t wallclock_lo;	/**< lower 32bits of 64bit monotonic wallclock */
	uint64_t host_posn;	/**< host DMA position in bytes */
	uint64_t dai_posn;	/**< DAI DMA position in bytes */
	...
} __packed;
```

That position record sits inside each of the two stream entries the tracking object lays out, playback and capture bracketing the flags and the trailing topology record:

```
    struct snd_sof_pcm memory layout (one per front-end DAI link)
    ────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ scomp        struct snd_soc_component *                  │
    │ ┌──────────────────────────────────────────────────────┐ │
    │ │ stream[0]  PLAYBACK  struct snd_sof_pcm_stream       │ │
    │ │   comp_id   posn   substream   list (widgets)        │ │
    │ │ stream[1]  CAPTURE   struct snd_sof_pcm_stream       │ │
    │ └──────────────────────────────────────────────────────┘ │
    │ list         on sdev->pcm_list                           │
    │ prepared[2]  setup_done[2]  pending_stop[2]              │
    │ pcm          struct snd_soc_tplg_pcm  (flex, last)       │
    └──────────────────────────────────────────────────────────┘
```

### Each component op resolves its snd_sof_pcm by runtime

Every component op begins by returning 0 for a back-end runtime (`rtd->dai_link->no_pcm`), then resolving the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) for the front-end runtime with [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616), which walks [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and matches the topology PCM [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) against the DAI link id:

```c
/* sound/soc/sof/sof-audio.h:616 */
static inline
struct snd_sof_pcm *snd_sof_find_spcm_dai(struct snd_soc_component *scomp,
					  struct snd_soc_pcm_runtime *rtd)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	struct snd_sof_pcm *spcm;

	list_for_each_entry(spcm, &sdev->pcm_list, list) {
		if (le32_to_cpu(spcm->pcm.dai_id) == rtd->dai_link->id)
			return spcm;
	}

	return NULL;
}
```

The lookup reads the device from the component drvdata with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), so a component op needs only the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) the ASoC core passes it to reach both the [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and the per-PCM object. Two sibling lookups serve callers that hold a different key. [`snd_sof_find_spcm_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L911) matches by DAI name or stream-caps name:

```c
/* sound/soc/sof/sof-audio.c:911 */
struct snd_sof_pcm *snd_sof_find_spcm_name(struct snd_soc_component *scomp,
					   const char *name)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	struct snd_sof_pcm *spcm;

	list_for_each_entry(spcm, &sdev->pcm_list, list) {
		/* match with PCM dai name */
		if (strcmp(spcm->pcm.dai_name, name) == 0)
			return spcm;

		/* match with playback caps name if set */
		if (*spcm->pcm.caps[0].name &&
		    !strcmp(spcm->pcm.caps[0].name, name))
			return spcm;

		/* match with capture caps name if set */
		if (*spcm->pcm.caps[1].name &&
		    !strcmp(spcm->pcm.caps[1].name, name))
			return spcm;
	}

	return NULL;
}
```

[`snd_sof_find_spcm_comp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L936) matches by firmware component id and reports back which direction matched, which is how a firmware position message (carrying only a [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329)) finds its stream:

```c
/* sound/soc/sof/sof-audio.c:936 */
struct snd_sof_pcm *snd_sof_find_spcm_comp(struct snd_soc_component *scomp,
					   unsigned int comp_id,
					   int *direction)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	struct snd_sof_pcm *spcm;
	int dir;

	list_for_each_entry(spcm, &sdev->pcm_list, list) {
		for_each_pcm_streams(dir) {
			if (spcm->stream[dir].comp_id == comp_id) {
				*direction = dir;
				return spcm;
			}
		}
	}

	return NULL;
}
```

All three walk the same [`sdev->pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547); they differ only in the key. The runtime lookup is the one the component callbacks use, since they always hold the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) the ASoC core hands them.

```
    Three keys, one sdev->pcm_list
    ──────────────────────────────

    key: rtd->dai_link->id ───▶ snd_sof_find_spcm_dai  ──┐
                                  (pcm.dai_id)            │
    key: DAI / caps name   ───▶ snd_sof_find_spcm_name ──┤
                                  (pcm.dai_name)          │
    key: firmware comp_id  ───▶ snd_sof_find_spcm_comp ──┤
                                  (stream[dir].comp_id)   │  + direction
                                                          ▼
                                          ┌────────────────────────────┐
                                          │ sdev->pcm_list             │
                                          │  struct snd_sof_pcm  ...   │
                                          └────────────────────────────┘
```

### The IPC-version pcm ops indirection

The component body never inlines DSP message exchange. It delegates to the IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), which abstracts the firmware protocol so the same body works for IPC3 and IPC4. The struct carries the per-operation function pointers and the flags that tune trigger ordering:

```c
/* sound/soc/sof/sof-audio.h:123 */
struct sof_ipc_pcm_ops {
	int (*hw_params)(struct snd_soc_component *component, struct snd_pcm_substream *substream,
			 struct snd_pcm_hw_params *params,
			 struct snd_sof_platform_stream_params *platform_params);
	int (*hw_free)(struct snd_soc_component *component, struct snd_pcm_substream *substream);
	int (*trigger)(struct snd_soc_component *component,  struct snd_pcm_substream *substream,
		       int cmd);
	int (*dai_link_fixup)(struct snd_soc_pcm_runtime *rtd, struct snd_pcm_hw_params *params);
	int (*pcm_setup)(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm);
	void (*pcm_free)(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm);
	int (*pointer)(struct snd_soc_component *component,
		       struct snd_pcm_substream *substream,
		       snd_pcm_uframes_t *pointer);
	snd_pcm_sframes_t (*delay)(struct snd_soc_component *component,
				   struct snd_pcm_substream *substream);
	bool reset_hw_params_during_stop;
	bool ipc_first_on_start;
	bool platform_stop_during_hw_free;
	bool d0i3_supported_in_s0ix;
};
```

The function-pointer members map one-to-one onto the component callbacks that call them, and the [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) members let an IPC version allocate and free its own state in the [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) pointer. According to the kernel-doc on the struct, the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) callback may return `-EOPNOTSUPP`, which the caller handles the same as an absent op. The boolean flags drive the trigger ordering: [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) sends the IPC before the platform host-DMA trigger on start, and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) defers the host-DMA stop to hw_free, which is needed on IPC4 where a pipeline is only paused (not stopped) on the stop trigger.

The component reaches the active struct through the [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro, which reads the named member of the active [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) or returns NULL when the IPC layer is not up:

```c
/* sound/soc/sof/sof-priv.h:541 */
#define sof_ipc_get_ops(sdev, ops_name)		\
		(((sdev)->ipc && (sdev)->ipc->ops) ? (sdev)->ipc->ops->ops_name : NULL)
```

The macro guards two dereferences, the [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) handle and its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) aggregate, so a component op that runs before the IPC layer is ready receives NULL and skips the DSP-side work rather than faulting. The aggregate it indexes is the per-IPC-version [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) member is the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) the component wants:

```c
/* sound/soc/sof/sof-priv.h:503 */
struct sof_ipc_ops {
	const struct sof_ipc_tplg_ops *tplg;
	const struct sof_ipc_pm_ops *pm;
	const struct sof_ipc_pcm_ops *pcm;
	const struct sof_ipc_fw_loader_ops *fw_loader;
	const struct sof_ipc_fw_tracing_ops *fw_tracing;
	...
};
```

Every call site reads the pointer and then tests both it and the specific member before dereferencing, so a sparse [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) (one that fills only some members) is handled the same as a fully populated one. The bodies that perform these tests and sequence the result against the platform host-DMA ops are documented as the SOF PCM operations.

```
    sof_ipc_get_ops(sdev, pcm) dereference chain
    ────────────────────────────────────────────

    struct snd_sof_dev
    ┌──────────────┐
    │ ipc          │──▶ struct snd_sof_ipc
    └──────────────┘    ┌──────────────┐
       guard: ipc       │ ops          │──▶ struct sof_ipc_ops
                        └──────────────┘    ┌──────────────┐
              guard: ipc->ops               │ pcm          │──┐
                                            └──────────────┘  │
                                                              ▼
                                          struct sof_ipc_pcm_ops
                                          ┌────────────────────────┐
                                          │ hw_params  trigger     │
                                          │ hw_free  pointer       │
                                          └────────────────────────┘
       returns NULL when ipc or ipc->ops is unset
```

### Intel MTL routes to ipc4_pcm_ops

On an Intel MTL or HDA-generation x86-64 platform the active [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) is the IPC4 aggregate [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912), whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) member points at the IPC4 [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) instance:

```c
/* sound/soc/sof/ipc4.c:912 */
const struct sof_ipc_ops ipc4_ops = {
	.init = sof_ipc4_init,
	.exit = sof_ipc4_exit,
	.post_fw_boot = sof_ipc4_post_boot,
	.tx_msg = sof_ipc4_tx_msg,
	.rx_msg = sof_ipc4_rx_msg,
	.set_get_data = sof_ipc4_set_get_data,
	.get_reply = sof_ipc4_get_reply,
	.pm = &ipc4_pm_ops,
	.fw_loader = &ipc4_loader_ops,
	.tplg = &ipc4_tplg_ops,
	.pcm = &ipc4_pcm_ops,
	.fw_tracing = &ipc4_mtrace_ops,
};
```

So [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) returns [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) on these platforms. That instance fills the firmware-side function pointers and sets the two ordering flags MTL needs:

```c
/* sound/soc/sof/ipc4-pcm.c:1311 */
const struct sof_ipc_pcm_ops ipc4_pcm_ops = {
	.hw_params = sof_ipc4_pcm_hw_params,
	.trigger = sof_ipc4_pcm_trigger,
	.hw_free = sof_ipc4_pcm_hw_free,
	.dai_link_fixup = sof_ipc4_pcm_dai_link_fixup,
	.pcm_setup = sof_ipc4_pcm_setup,
	.pcm_free = sof_ipc4_pcm_free,
	.pointer = sof_ipc4_pcm_pointer,
	.delay = sof_ipc4_pcm_delay,
	.ipc_first_on_start = true,
	.platform_stop_during_hw_free = true,
};
```

The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) is the one the component's trigger body calls; it collapses the ALSA command into a firmware pipeline state and hands off to the pipeline-state setter:

```c
/* sound/soc/sof/ipc4-pcm.c:588 */
static int sof_ipc4_pcm_trigger(struct snd_soc_component *component,
				struct snd_pcm_substream *substream, int cmd)
{
	int state;

	/* determine the pipeline state */
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_START:
		state = SOF_IPC4_PIPE_RUNNING;
		break;
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		state = SOF_IPC4_PIPE_PAUSED;
		break;
	default:
		dev_err(component->dev, "%s: unhandled trigger cmd %d\n", __func__, cmd);
		return -EINVAL;
	}

	/* set the pipeline state */
	return sof_ipc4_trigger_pipelines(component, substream, state, cmd);
}
```

The IPC4 member bodies (the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) functions, and the [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) pipeline driver they call) are documented as the IPC4 PCM ops. The component descriptor on this page is what selects that instance per device and routes each generic PCM callback into it.

### SOF platform component op dispatch to runtime and IPC ops

The [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) wires [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), and [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) to fan each PCM operation toward runtime pipeline setup via [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) and toward the IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) before reaching the DSP firmware.

```
    SOF ASoC platform component (one per snd_sof_dev)
    ─────────────────────────────────────────────────

    struct snd_soc_component_driver  plat_drv  ("sof-audio-component")
    ┌─────────────────────────────────────────────────────────────┐
    │  open ─▶ sof_pcm_open      hw_params ─▶ sof_pcm_hw_params   │
    │  prepare ─▶ sof_pcm_prepare   trigger ─▶ sof_pcm_trigger    │
    │  hw_free ─▶ sof_pcm_hw_free   pointer ─▶ sof_pcm_pointer    │
    │  pcm_construct ─▶ sof_pcm_new                               │
    │  be_hw_params_fixup ─▶ sof_pcm_dai_link_fixup               │
    └─────────────────────────────────┬───────────────────────────┘
                                      │ one PCM operation
                   ┌──────────────────┴─────────────────────┐
                   ▼                                        ▼
        runtime pipeline setup                   IPC-version pcm ops
        sof_widget_list_setup                    sof_ipc_get_ops(sdev, pcm)
        ┌──────────────────────┐                 ┌───────────────────────┐
        │ walk DAPM widget list│                 │ struct sof_ipc_pcm_ops│
        │ create FW modules    │                 │  hw_params / trigger  │
        │ connect pipelines    │                 │  hw_free / pointer    │
        └──────────┬───────────┘                 └──────────┬────────────┘
                   │ widget_setup IPC                       │ IPC4 (MTL/HDA)
                   ▼                                        ▼
        ┌─────────────────────────────────────────────────────────┐
        │   DSP firmware: pipeline modules, host DMA, link DMA    │
        └─────────────────────────────────────────────────────────┘
```
