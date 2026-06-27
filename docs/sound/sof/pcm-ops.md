# SOF PCM operations

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The nine PCM bodies in [`sound/soc/sof/pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) ([`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), [`sof_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599), [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), [`sof_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287), [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315), [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497), [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637), and [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719)) are the generic dispatch layer that sits between the ASoC PCM core and the DSP, each wired into the SOF platform component by [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) and each ending by handing the firmware-specific work to the active IPC version's [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) reached through [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541), to the pipeline-module setup in [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762), and to the platform host-DMA half in [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165).

```
    ASoC PCM core          generic sof_pcm_* body         backend + setup
    ─────────────          ──────────────────────         ───────────────

    snd_soc_component_open  ─▶ sof_pcm_open      ─────────▶ pcm_open (host DMA)
    ..._hw_params           ─▶ sof_pcm_hw_params ─────────▶ pcm_hw_params + widgets
    ..._prepare             ─▶ sof_pcm_prepare   ─┬───────▶ sof_widget_list_setup
    soc_component_trigger   ─▶ sof_pcm_trigger    │       └▶ pcm_ops->hw_params
    ..._pointer             ─▶ sof_pcm_pointer    │
    ..._hw_free             ─▶ sof_pcm_hw_free    │ pcm_ops = sof_ipc_get_ops(pcm)
    ..._close               ─▶ sof_pcm_close      ▼
    ..._pcm_new             ─▶ sof_pcm_new      ┌─────────────────────────────┐
    be_hw_params_fixup      ─▶ sof_pcm_dai_link │ struct sof_ipc_pcm_ops      │
                               _fixup           │  hw_params trigger hw_free  │
                                                │  pointer  dai_link_fixup    │
                                                └──────────────┬──────────────┘
                                                               │ IPC4 (MTL/HDA):
                                                               │ ipc4_pcm_ops
                                                               ▼
                                       ┌────────────────────────────────────────┐
                                       │  DSP firmware: pipeline modules, host  │
                                       │  DMA stream descriptor, link DMA       │
                                       └────────────────────────────────────────┘

    every body returns 0 for a back-end runtime (rtd->dai_link->no_pcm) and
    otherwise resolves its struct snd_sof_pcm with snd_sof_find_spcm_dai().
```

## SUMMARY

Each body is a member of the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) fills at probe, and the ASoC PCM core reaches it through the [`snd_soc_component_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) wrappers during stream operation. The bodies are IPC-version-agnostic. They run the front-end half of an operation in C in [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) and forward the DSP message exchange to a function pointer struct so the same code drives both IPC3 and IPC4 firmware. The firmware protocol is reached through the IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member that [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) returns, the pipeline-module instantiation is reached through [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762), and the host-DMA transport is reached through the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) callbacks.

Every body shares one opening. It returns 0 immediately when the runtime belongs to a back-end DAI link ([`rtd->dai_link->no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754)), then resolves the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) for the runtime with [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616), which scans the device PCM list and matches the topology PCM [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L518) against the DAI link id. [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) copies the topology stream capabilities into the runtime hardware description and calls the platform open. [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) boots the firmware on demand, programs the host DMA, builds the connected-widget list with [`sof_pcm_setup_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L70), and creates the audio page table. [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) runs [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) to send the create-widget messages and then the IPC-version [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123). [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) orders the host-DMA trigger and the IPC pipeline-state change per ALSA command. [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) reports the position the firmware writes back. [`sof_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287) and [`sof_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599) reverse the setup, and [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) pre-allocates the DMA buffer pages once when the PCM device is created.

The DSP-specific work is never inlined into these bodies. On an Intel MTL or HDA-generation x86 platform the active IPC version is IPC4, so [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) returns [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), and the generic bodies call its members [`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588), [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), and [`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) by name through the function pointer struct without naming any IPC4 symbol in [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c). The host-DMA half goes through the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) members, where [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) reaches [`hda_dsp_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219) and [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) reaches [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177), which arms or disarms the HDA stream descriptor DMA through [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392).

## SPECIFICATIONS

The SOF PCM operation bodies are a Linux kernel software construct and have no standalone hardware specification. The DSP message protocol the bodies delegate to is defined by the Sound Open Firmware ABI, and the IPC4 variant in [`include/sound/sof/ipc4/`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h) follows Intel's Audio DSP firmware interface. On an x86 ACPI platform the host side of the audio transport is the High Definition Audio stream descriptor set defined by the Intel High Definition Audio Specification, which [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) programs through the SDnCTL DMA-run bit.

## LINUX KERNEL

### The generic component op bodies (pcm.c)

- [`'\<sof_pcm_open\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536): set the runtime hardware description from the topology stream capabilities and call the platform open
- [`'\<sof_pcm_close\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599): call the platform close and clear the per-direction substream pointer
- [`'\<sof_pcm_hw_params\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116): boot the firmware on demand, program the host DMA, build the connected-widget list, set the host DMA id, and create the audio page table
- [`'\<sof_pcm_hw_free\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287): free the DSP-side PCM through [`sof_pcm_stream_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L209) and drop the widget list
- [`'\<sof_pcm_prepare\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315): run [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) to create the firmware modules, then the IPC-version [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123)
- [`'\<sof_pcm_trigger\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385): order the platform host-DMA trigger and the IPC-version [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) per ALSA command and IPC flags
- [`'\<sof_pcm_pointer\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497): try the IPC-version [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), then the platform [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), then the firmware-written [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142)
- [`'\<sof_pcm_new\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637): the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) op pre-allocating the playback and capture DMA buffer pages
- [`'\<sof_pcm_dai_link_fixup\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719): the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L197) op forcing back-end parameters to the topology configuration or a 48 kHz default
- [`'\<sof_pcm_stream_free\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L209): call the IPC-version [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), reset the host DMA, and optionally free the widget list
- [`'\<sof_pcm_setup_connected_widgets\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L70): query DAPM for the connected widgets and stash the list in [`spcm->stream[dir].list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329)
- [`'\<snd_sof_find_swidget_by_comp_id\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L103): find the host [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) by firmware component id
- [`'\<snd_sof_pcm_period_elapsed\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43): the position-IRQ entry point that schedules the deferred period-elapsed work
- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): wire every body into the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) embedded as [`sdev->plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569)

### Runtime pipeline instantiation (sof-audio.c)

- [`'\<sof_widget_list_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762): send the create-widget messages source-to-sink, connect the pipelines, and complete each one
- [`'\<sof_widget_list_unprepare\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L751): unprepare the widgets and free the connected-widget list
- [`'\<sof_widget_list_prepare\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L738): prepare each widget in the path before the create-widget messages are sent
- [`'\<sof_widget_list_free\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L842): free the firmware modules created for the path
- [`'\<sof_walk_widgets_in_order\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L672): walk the list from the starting widget and apply one [`enum sof_widget_op`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L672) to each
- [`'\<sof_set_up_widgets_in_path\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L601): recurse along the sink path and set up every widget, recording its pipeline
- [`'\<sof_widget_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251): set up one widget in the DSP under its [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422)

### IPC-version PCM ops indirection (sof-audio.h, sof-priv.h)

- [`'\<struct sof_ipc_pcm_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123): the IPC-version function pointer struct carrying [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and the trigger-ordering flags
- [`'\<struct sof_ipc_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503): the per-IPC-version ops aggregate whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L506) member is the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) pointer
- [`'\<struct sof_ipc_tplg_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221): the IPC-version topology ops used by [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) for [`host_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L234) and by [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) for [`pipeline_complete`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L229)
- [`sof_ipc_get_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541): the macro returning `sdev->ipc->ops->ops_name` or NULL
- [`sof_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21): the macro returning the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) for the platform

### Platform host-DMA ops indirection (ops.h)

- [`'\<struct snd_sof_dsp_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165): the DSP hardware abstraction, including the [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L229), [`pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L246), [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L251), and [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L236) host-DMA callbacks and the [`hw_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L356) flags
- [`'\<snd_sof_pcm_platform_open\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L417): call [`sof_ops(sdev)->pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L229) if present
- [`'\<snd_sof_pcm_platform_close\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L428): call the platform [`pcm_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L232)
- [`'\<snd_sof_pcm_platform_hw_params\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L439): call the platform [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L236)
- [`'\<snd_sof_pcm_platform_hw_free\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L453): reset the platform host DMA through [`pcm_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L242)
- [`'\<snd_sof_pcm_platform_trigger\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464): call the platform [`pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L246)

### SOF PCM device type (sof-audio.h)

- [`'\<struct snd_sof_pcm\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352): the ALSA SOF PCM device topology creates per front-end DAI link; holds the per-direction stream state and the topology PCM record
- [`'\<struct snd_sof_pcm_stream\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329): one direction's runtime state, the firmware component id, the position record, the connected widget list, and the pipeline list
- [`'\<struct snd_sof_widget\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422): the ASoC SOF DAPM widget that backs a firmware module
- [`'\<snd_sof_find_spcm_dai\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616): match a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) to a runtime by comparing the topology PCM id to the DAI link id
- [`'\<snd_sof_find_dai\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L993): find the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) for a back-end link by name, used by the fixup

### Intel MTL/HDA IPC4 backend symbols (referenced by name)

- [`'ipc4_pcm_ops':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311): the IPC4 [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) instance the bodies dispatch to on MTL
- [`'ipc4_ops':'sound/soc/sof/ipc4.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912): the IPC4 [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) whose [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L506) member is [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311)
- [`'\<sof_ipc4_pcm_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588): the IPC4 [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member, mapping the ALSA command to a pipeline state (IPC4 internals covered on the IPC4 backend page)
- [`'\<enum sof_ipc4_pipeline_state\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137): the firmware pipeline states, including [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) and [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142)
- [`'\<hda_dsp_pcm_open\>':'sound/soc/sof/intel/hda-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219): the [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L229) host-DMA callback that claims an HDA stream and applies period constraints
- [`'\<hda_dsp_pcm_trigger\>':'sound/soc/sof/intel/hda-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177): the [`pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L246) callback delegating to [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392)
- [`'\<hda_dsp_stream_trigger\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392): set or clear the HDA stream descriptor DMA-run bit

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the ASoC platform component concept and the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) PCM callbacks these bodies implement
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end/back-end split that decides when a body returns early and what [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) fixes up
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model the SOF platform component registers into
- [`Documentation/sound/designs/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/index.rst): ALSA design notes covering the PCM substream lifecycle these bodies follow

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF architecture overview](https://thesofproject.github.io/latest/architectures/firmware/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Each body below is the function [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) assigns to one member of the SOF platform component's [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and the ASoC PCM core reaches it through the [`snd_soc_component_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) wrappers during stream operation. The body is generic across IPC versions and ends by delegating the DSP-side work to the IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member and the host-DMA work to the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) member. The mapping from the userspace PCM operation to the SOF body and the IPC-version op it calls is fixed; the IPC4 column names the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) member reached on an MTL device.

| PCM operation | component body | delegates to | host-DMA half (MTL) |
|---------------|----------------|--------------|---------------------|
| `open()` | [`sof_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) | platform [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L229) | [`hda_dsp_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`sof_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) | [`sof_pcm_setup_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L70) + [`host_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L234) | platform [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L236) |
| `SNDRV_PCM_IOCTL_PREPARE` | [`sof_pcm_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) | [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) + [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | (modules created) |
| `SNDRV_PCM_IOCTL_START` | [`sof_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177) |
| `SNDRV_PCM_IOCTL_PAUSE` (push) | [`sof_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177) |
| `SNDRV_PCM_IOCTL_DROP` | [`sof_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), then free | [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177) |
| pointer query | [`sof_pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) | [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | platform [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L251) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`sof_pcm_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287) | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | platform [`pcm_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L242) |
| `close()` | [`sof_pcm_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599) | platform [`pcm_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L232) | (HDA stream released) |
| device create | [`sof_pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) | (none; DMA pages) | (pages pre-allocated) |
| back-end fixup | [`sof_pcm_dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) | [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | (back-end params forced) |

### open and close

[`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) copies the topology stream capabilities from [`spcm->pcm.caps[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) into the runtime hardware description, sets the platform [`hw_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L356) flags from [`sof_ops(sdev)->hw_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L356), resets the per-direction position record, and calls [`snd_sof_pcm_platform_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L417). [`sof_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599) calls [`snd_sof_pcm_platform_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L428) and clears [`spcm->stream[dir].substream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329). Neither body talks to the DSP itself; both are pure host-DMA setup and teardown reached through the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165).

### hw_params and hw_free

[`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) boots the firmware on demand, programs the host DMA through [`snd_sof_pcm_platform_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L439), builds the connected-widget list with [`sof_pcm_setup_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L70) when one is not already present, sets the host DMA id on the host widget through the topology op [`host_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L234), and creates the page table with [`snd_sof_create_page_table()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-utils.c#L25). [`sof_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287) reverses it through [`sof_pcm_stream_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L209), which calls the IPC-version [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), resets the host DMA, and frees the widget list, then [`sof_widget_list_unprepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L751) drops the DAPM list.

### prepare

[`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) returns early when the stream is already prepared and no pending stop is queued, otherwise it re-runs [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), then runs [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) to send the create-widget messages, then the IPC-version [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and finally marks [`spcm->prepared[dir]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352).

### trigger

[`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) sets two booleans, `ipc_first` and `reset_hw_params`, from the command and the IPC-version flags [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`reset_hw_params_during_stop`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), then orders the platform host-DMA trigger and the IPC-version [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) accordingly. On IPC4 [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is set, so on start the IPC moves the pipeline to running before the host DMA starts, and on stop the IPC moves the pipeline to paused first while the platform stop is deferred to [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123).

### pointer

[`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) first tries the IPC-version [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) op, treating its `-EOPNOTSUPP` the same as an absent op, then tries the platform [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L251), and otherwise returns the host position the firmware wrote into [`spcm->stream[dir].posn.host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142) converted to frames.

### pcm_construct

[`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) runs once when the ALSA PCM device is created for the front-end DAI link and pre-allocates the playback and capture buffer pages with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) using [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45), sized from the topology [`buffer_size_max`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L312). It does not delegate to the IPC version; the managed buffer is released by the ALSA core during PCM teardown.

### be_hw_params_fixup

[`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) is wired only when a DSP is present. It looks up the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) for the back-end link with [`snd_sof_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L993) and, when topology has one, delegates to the IPC-version [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123); when no topology DAI exists it forces 48 kHz, stereo, [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L235).

## DETAILS

### Every body resolves its snd_sof_pcm and returns early for a back-end

The component bodies all start the same way. A back-end DAI link runtime ([`rtd->dai_link->no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L754) set) has no ALSA PCM of its own, so the body returns 0 without touching the DSP. Otherwise it resolves the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) with [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L616), which scans the device PCM list and matches the topology PCM [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L518) against the DAI link id:

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

The [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) is the per-front-end-DAI-link device that topology creates. It carries the per-direction stream state and ends in the topology PCM record, a flex-array member, so it is the last field:

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

Each direction's runtime state is a [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) holding the firmware component id, the position record the firmware updates, the connected DAPM widget [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), and the pipeline list the trigger walks:

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

[`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) shows the opening end to end. It returns early for the back-end, copies the topology capability fields into [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L367), resets the position record, and calls the platform open:

```c
/* sound/soc/sof/pcm.c:536 */
static int sof_pcm_open(struct snd_soc_component *component,
			struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_pcm_runtime *runtime = substream->runtime;
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	const struct snd_sof_dsp_ops *ops = sof_ops(sdev);
	struct snd_sof_pcm *spcm;
	struct snd_soc_tplg_stream_caps *caps;
	int ret;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;

	spcm_dbg(spcm, substream->stream, "Entry: open\n");

	caps = &spcm->pcm.caps[substream->stream];

	/* set runtime config */
	runtime->hw.info = ops->hw_info; /* platform-specific */

	/* set any runtime constraints based on topology */
	runtime->hw.formats = le64_to_cpu(caps->formats);
	runtime->hw.period_bytes_min = le32_to_cpu(caps->period_size_min);
	runtime->hw.period_bytes_max = le32_to_cpu(caps->period_size_max);
	runtime->hw.periods_min = le32_to_cpu(caps->periods_min);
	runtime->hw.periods_max = le32_to_cpu(caps->periods_max);
	...
	spcm->stream[substream->stream].posn.host_posn = 0;
	spcm->stream[substream->stream].posn.dai_posn = 0;
	spcm->stream[substream->stream].substream = substream;
	spcm->prepared[substream->stream] = false;

	ret = snd_sof_pcm_platform_open(sdev, substream);
	if (ret < 0) {
		spcm_err(spcm, substream->stream,
			 "platform pcm open failed %d\n", ret);
		return ret;
	}
	...
	return 0;
}
```

The [`hw_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L356) flags come from the platform ops, and [`snd_sof_pcm_platform_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L417) reaches the platform's own [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L229) only if it is set:

```c
/* sound/soc/sof/ops.h:417 */
static inline int
snd_sof_pcm_platform_open(struct snd_sof_dev *sdev,
			  struct snd_pcm_substream *substream)
{
	if (sof_ops(sdev) && sof_ops(sdev)->pcm_open)
		return sof_ops(sdev)->pcm_open(sdev, substream);

	return 0;
}
```

[`sof_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L599) is the mirror. It runs the platform close, keeps going even if that fails, and clears the substream pointer:

```c
/* sound/soc/sof/pcm.c:599 */
static int sof_pcm_close(struct snd_soc_component *component,
			 struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pcm *spcm;
	int err;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;

	spcm_dbg(spcm, substream->stream, "Entry: close\n");

	err = snd_sof_pcm_platform_close(sdev, substream);
	if (err < 0) {
		spcm_err(spcm, substream->stream,
			 "platform pcm close failed %d\n", err);
		/*
		 * keep going, no point in preventing the close
		 * from happening
		 */
	}

	spcm->stream[substream->stream].substream = NULL;

	return 0;
}
```

The substream slot the close cleared sits in one of the two per-direction stream entries, each pairing the firmware-written position with the connected widget and pipeline lists under the front-end pcm record:

```
    struct nesting: snd_sof_pcm holds per-direction stream state
    ──────────────────────────────────────────────────────────────

    struct snd_sof_pcm   (one per front-end DAI link, on sdev pcm_list)
      ├─ scomp
      ├─ stream[2]              struct snd_sof_pcm_stream (per dir)
      │     ├─ comp_id
      │     ├─ posn             firmware-written host/dai position
      │     ├─ substream
      │     ├─ list             connected DAPM widget list
      │     ├─ pipeline_list    pipelines the trigger walks
      │     └─ private          IPC-version blob
      ├─ params[2]
      ├─ prepared[2]
      ├─ pending_stop[2]
      └─ pcm                    struct snd_soc_tplg_pcm (flex, must be last)

    snd_sof_find_spcm_dai(): match spcm->pcm.dai_id == rtd->dai_link->id
```

### The two indirections: IPC-version pcm ops and platform DSP ops

A body forwards DSP work along two separate function pointer structs. The first is the IPC-version [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), which abstracts the firmware message protocol so the same body works for IPC3 and IPC4. It carries the per-operation function pointers and the flags that tune trigger ordering:

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

The body reaches it through the [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro, which reads the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L506) member of the active [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) or returns NULL when the IPC layer is not up:

```c
/* sound/soc/sof/sof-priv.h:541 */
#define sof_ipc_get_ops(sdev, ops_name)		\
		(((sdev)->ipc && (sdev)->ipc->ops) ? (sdev)->ipc->ops->ops_name : NULL)
```

The macro is a NULL-tolerant read, so each body that uses it tests both the returned pointer and the member it is about to call, as in `if (pcm_ops && pcm_ops->trigger)`. The second indirection is the platform [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), reached through the [`sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) macro, which drives the host side of the audio transport. Its PCM-related members are optional and platform-specific:

```c
/* sound/soc/sof/sof-priv.h:165 */
struct snd_sof_dsp_ops {
	...
	/* connect pcm substream to a host stream */
	int (*pcm_open)(struct snd_sof_dev *sdev,
			struct snd_pcm_substream *substream); /* optional */
	/* disconnect pcm substream to a host stream */
	int (*pcm_close)(struct snd_sof_dev *sdev,
			 struct snd_pcm_substream *substream); /* optional */

	/* host stream hw params */
	int (*pcm_hw_params)(struct snd_sof_dev *sdev,
			     struct snd_pcm_substream *substream,
			     struct snd_pcm_hw_params *params,
			     struct snd_sof_platform_stream_params *platform_params); /* optional */
	...
	/* host stream trigger */
	int (*pcm_trigger)(struct snd_sof_dev *sdev,
			   struct snd_pcm_substream *substream,
			   int cmd); /* optional */
	...
	/* ALSA HW info flags, will be stored in snd_pcm_runtime.hw.info */
	u32 hw_info;
	...
};
```

The split keeps the body generic. The IPC-version ops know nothing about HDA or DMA registers, and the platform ops know nothing about firmware pipeline modules; the body in [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) sequences the two. On an MTL device the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L506) member of the active [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) is [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), so [`sof_ipc_get_ops(sdev, pcm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) returns that instance and the bodies below call its members by name.

```
    Two indirections sequenced by one generic body
    ──────────────────────────────────────────────────────────────

                     generic sof_pcm_* body (pcm.c)
                       │                       │
       sof_ipc_get_ops(sdev, pcm)         sof_ops(sdev)
                       ▼                       ▼
       ┌───────────────────────────┐  ┌───────────────────────────┐
       │ struct sof_ipc_pcm_ops    │  │ struct snd_sof_dsp_ops     │
       │ (IPC firmware protocol)   │  │ (platform host DMA)        │
       │   hw_params  trigger      │  │   pcm_open   pcm_trigger   │
       │   hw_free    pointer      │  │   pcm_hw_params  pcm_close │
       │   dai_link_fixup          │  │   hw_info flags            │
       └───────────────────────────┘  └───────────────────────────┘
            knows no HDA/DMA register      knows no firmware module

    MTL: sof_ipc_pcm_ops = ipc4_pcm_ops, pcm_trigger = hda_dsp_pcm_trigger
```

### hw_params programs the host DMA and prepares the widget list

[`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) reads both function pointer structs up front, [`tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) for the host DMA id and `pcm_ops` for the repeated-call hw_free. After the firmware on-demand boot it programs the platform host DMA, builds the connected-widget list when one is not already present, sets the host DMA id on the host widget, and creates the audio page table:

```c
/* sound/soc/sof/pcm.c:116 */
static int sof_pcm_hw_params(struct snd_soc_component *component,
			     struct snd_pcm_substream *substream,
			     struct snd_pcm_hw_params *params)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);
	struct snd_sof_platform_stream_params *platform_params;
	struct snd_pcm_runtime *runtime = substream->runtime;
	struct snd_sof_widget *host_widget;
	struct snd_sof_pcm *spcm;
	int ret;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;
	...
	if (!sdev->dspless_mode_selected) {
		/*
		 * Make sure that the DSP is booted up, which might not be the
		 * case if the on-demand DSP boot is used
		 */
		ret = snd_sof_boot_dsp_firmware(sdev);
		if (ret)
			return ret;
	}

	/*
	 * Handle repeated calls to hw_params() without free_pcm() in
	 * between. At least ALSA OSS emulation depends on this.
	 */
	if (spcm->prepared[substream->stream] && pcm_ops && pcm_ops->hw_free) {
		ret = pcm_ops->hw_free(component, substream);
		if (ret < 0)
			return ret;

		spcm->prepared[substream->stream] = false;
	}
```

According to the comment, a repeated [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) without an intervening free has to undo the firmware setup first, so the body calls the IPC-version [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) before re-programming. The rest of the body programs the host DMA, builds the widget list, sets the host DMA id, and creates the page table:

```c
/* sound/soc/sof/pcm.c:116 (continued) */
	platform_params = &spcm->platform_params[substream->stream];
	ret = snd_sof_pcm_platform_hw_params(sdev, substream, params, platform_params);
	if (ret < 0) {
		spcm_err(spcm, substream->stream, "platform hw params failed\n");
		return ret;
	}

	/* if this is a repeated hw_params without hw_free, skip setting up widgets */
	if (!spcm->stream[substream->stream].list) {
		ret = sof_pcm_setup_connected_widgets(sdev, rtd, spcm, params, platform_params,
						      substream->stream);
		if (ret < 0)
			return ret;
	}

	if (!sdev->dspless_mode_selected) {
		int host_comp_id = spcm->stream[substream->stream].comp_id;

		host_widget = snd_sof_find_swidget_by_comp_id(sdev, host_comp_id);
		if (!host_widget) {
			spcm_err(spcm, substream->stream,
				 "failed to find host widget with comp_id %d\n", host_comp_id);
			return -EINVAL;
		}

		/* set the host DMA ID */
		if (tplg_ops && tplg_ops->host_config)
			tplg_ops->host_config(sdev, host_widget, platform_params);
	}

	/* create compressed page table for audio firmware */
	if (runtime->buffer_changed) {
		struct snd_dma_buffer *dmab = snd_pcm_get_dma_buf(substream);

		ret = snd_sof_create_page_table(component->dev, dmab,
				spcm->stream[substream->stream].page_table.area,
				runtime->dma_bytes);
		if (ret < 0)
			return ret;
	}

	/* save pcm hw_params */
	memcpy(&spcm->params[substream->stream], params, sizeof(*params));

	return 0;
}
```

[`sof_pcm_setup_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L70) is the DAPM half. It asks DAPM for the list of widgets between the CPU DAI and the back-end, stopping the graph walk at the back-end through [`dpcm_end_walk_at_be()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1464), stores the result in [`spcm->stream[dir].list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), and runs the per-widget prepare:

```c
/* sound/soc/sof/pcm.c:70 */
static int
sof_pcm_setup_connected_widgets(struct snd_sof_dev *sdev, struct snd_soc_pcm_runtime *rtd,
				struct snd_sof_pcm *spcm, struct snd_pcm_hw_params *params,
				struct snd_sof_platform_stream_params *platform_params, int dir)
{
	struct snd_soc_dai *dai;
	int ret, j;

	/* query DAPM for list of connected widgets and set them up */
	for_each_rtd_cpu_dais(rtd, j, dai) {
		struct snd_soc_dapm_widget_list *list;

		ret = snd_soc_dapm_dai_get_connected_widgets(dai, dir, &list,
							     dpcm_end_walk_at_be);
		if (ret < 0) {
			spcm_err(spcm, dir, "dai %s has no valid %s path\n",
				 dai->name, snd_pcm_direction_name(dir));
			return ret;
		}

		spcm->stream[dir].list = list;

		ret = sof_widget_list_prepare(sdev, spcm, params, platform_params, dir);
		if (ret < 0) {
			spcm_err(spcm, dir, "widget list prepare failed\n");
			spcm->stream[dir].list = NULL;
			snd_soc_dapm_dai_free_widgets(&list);
			return ret;
		}
	}

	return 0;
}
```

[`snd_soc_dapm_dai_get_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1596) walks the DAPM graph from the DAI's stream widget and returns the ordered list of widgets on the active path, which is the set of topology widgets the firmware will need as modules. [`sof_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287) reverses the whole sequence through [`sof_pcm_stream_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L209) and then drops the DAPM list:

```c
/* sound/soc/sof/pcm.c:287 */
static int sof_pcm_hw_free(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pcm *spcm;
	int ret;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;

	spcm_dbg(spcm, substream->stream, "Entry: hw_free\n");

	ret = sof_pcm_stream_free(sdev, substream, spcm, substream->stream, true);

	/* unprepare and free the list of DAPM widgets */
	sof_widget_list_unprepare(sdev, spcm, substream->stream);

	cancel_work_sync(&spcm->stream[substream->stream].period_elapsed_work);

	return ret;
}
```

[`sof_pcm_stream_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L209) is where the IPC-version [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is actually called. It stops the host DMA first when the IPC version asks for it, frees the firmware PCM, resets the platform DMA, and frees the widget list:

```c
/* sound/soc/sof/pcm.c:209 */
static int sof_pcm_stream_free(struct snd_sof_dev *sdev,
			       struct snd_pcm_substream *substream,
			       struct snd_sof_pcm *spcm, int dir,
			       bool free_widget_list)
{
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);
	int ret;
	int err = 0;

	if (spcm->prepared[substream->stream]) {
		/* stop DMA first if needed */
		if (pcm_ops && pcm_ops->platform_stop_during_hw_free)
			snd_sof_pcm_platform_trigger(sdev, substream,
						     SNDRV_PCM_TRIGGER_STOP);

		/* free PCM in the DSP */
		if (pcm_ops && pcm_ops->hw_free) {
			ret = pcm_ops->hw_free(sdev->component, substream);
			if (ret < 0) {
				spcm_err(spcm, substream->stream,
					 "pcm_ops->hw_free failed %d\n", ret);
				err = ret;
			}
		}

		spcm->prepared[substream->stream] = false;
		spcm->pending_stop[substream->stream] = false;
	}

	/* reset the DMA */
	ret = snd_sof_pcm_platform_hw_free(sdev, substream);
	if (ret < 0) {
		spcm_err(spcm, substream->stream,
			 "platform hw free failed %d\n", ret);
		if (!err)
			err = ret;
	}

	/* free widget list */
	if (free_widget_list) {
		ret = sof_widget_list_free(sdev, spcm, dir);
		if (ret < 0) {
			spcm_err(spcm, substream->stream,
				 "sof_widget_list_free failed %d\n", ret);
			if (!err)
				err = ret;
		}
	}

	return err;
}
```

According to the comment on [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), IPC4 only pauses a pipeline during stop and leaves the host DMA running, so the host must stop the DMA during hw_free; the early [`snd_sof_pcm_platform_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464) with [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L686) here does exactly that on an MTL device.

### prepare creates the firmware modules

[`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) turns the prepared widget list into live firmware modules. It returns early when the stream is already prepared with no pending stop, frees and re-runs [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) on an xrun recovery, then runs [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) and the IPC-version [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123):

```c
/* sound/soc/sof/pcm.c:315 */
static int sof_pcm_prepare(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream)
{
	...
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);
	struct snd_soc_dapm_widget_list *list;
	struct snd_pcm_hw_params *params;
	struct snd_sof_pcm *spcm;
	int dir = substream->stream;
	int ret;
	...
	if (spcm->prepared[substream->stream]) {
		if (!spcm->pending_stop[substream->stream])
			return 0;

		/*
		 * this case should be reached in case of xruns where we absolutely
		 * want to free-up and reset all PCM/DMA resources
		 */
		ret = sof_pcm_stream_free(sdev, substream, spcm, substream->stream, true);
		if (ret < 0)
			return ret;
	}

	ret = sof_pcm_hw_params(component, substream, &spcm->params[substream->stream]);
	if (ret < 0) {
		spcm_err(spcm, substream->stream,
			 "failed to set hw_params after resume\n");
		return ret;
	}

	list = spcm->stream[dir].list;
	params = &spcm->params[substream->stream];
	platform_params = &spcm->platform_params[substream->stream];
	ret = sof_widget_list_setup(sdev, spcm, params, platform_params, dir);
	if (ret < 0) {
		dev_err(sdev->dev, "failed widget list set up for pcm %d dir %d\n",
			spcm->pcm.pcm_id, dir);
		spcm->stream[dir].list = NULL;
		snd_soc_dapm_dai_free_widgets(&list);
		return ret;
	}

	if (pcm_ops && pcm_ops->hw_params) {
		ret = pcm_ops->hw_params(component, substream, params, platform_params);
		if (ret < 0)
			return ret;
	}

	spcm->prepared[substream->stream] = true;

	return 0;
}
```

The IPC-version [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is the second of the two calls. On an MTL device it is [`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311); the body here names only the function pointer member and leaves the IPC4 message construction to that backend. [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) sends the create-widget messages source-to-sink, connects the pipelines, and completes each one through the topology op [`pipeline_complete`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L229):

```c
/* sound/soc/sof/sof-audio.c:762 */
int sof_widget_list_setup(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm,
			  struct snd_pcm_hw_params *fe_params,
			  struct snd_sof_platform_stream_params *platform_params,
			  int dir)
{
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	struct snd_soc_dapm_widget_list *list = spcm->stream[dir].list;
	struct snd_soc_dapm_widget *widget;
	int i, ret;

	/* nothing to set up or setup has been already done */
	if (!list || spcm->setup_done[dir])
		return 0;

	/* Set up is used to send the IPC to the DSP to create the widget */
	ret = sof_walk_widgets_in_order(sdev, spcm, fe_params, platform_params,
					dir, SOF_WIDGET_SETUP);
	if (ret < 0) {
		sof_walk_widgets_in_order(sdev, spcm, fe_params, platform_params,
					  dir, SOF_WIDGET_UNPREPARE);
		return ret;
	}

	/*
	 * error in setting pipeline connections will result in route status being reset for
	 * routes that were successfully set up when the widgets are freed.
	 */
	ret = sof_setup_pipeline_connections(sdev, list, dir);
	if (ret < 0)
		goto widget_free;
	...
	spcm->setup_done[dir] = true;

	return 0;

widget_free:
	sof_walk_widgets_in_order(sdev, spcm, fe_params, platform_params, dir,
				  SOF_WIDGET_FREE);
	sof_walk_widgets_in_order(sdev, spcm, NULL, NULL, dir, SOF_WIDGET_UNPREPARE);

	return ret;
}
```

[`sof_walk_widgets_in_order()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L672) finds the starting widget for the direction (an [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447) for playback, an [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) or [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425) for capture) and dispatches one [`enum sof_widget_op`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L672) to the path from there:

```c
/* sound/soc/sof/sof-audio.c:672 */
static int
sof_walk_widgets_in_order(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm,
			  struct snd_pcm_hw_params *fe_params,
			  struct snd_sof_platform_stream_params *platform_params, int dir,
			  enum sof_widget_op op)
{
	struct snd_soc_dapm_widget_list *list = spcm->stream[dir].list;
	struct snd_soc_dapm_widget *widget;
	char *str;
	int ret = 0;
	int i;

	if (!list)
		return 0;

	for_each_dapm_widgets(list, i, widget) {
		/* starting widget for playback is of AIF type */
		if (dir == SNDRV_PCM_STREAM_PLAYBACK && widget->id != snd_soc_dapm_aif_in)
			continue;

		/* starting widget for capture is DAI type */
		if (dir == SNDRV_PCM_STREAM_CAPTURE && widget->id != snd_soc_dapm_dai_out &&
		    widget->id != snd_soc_dapm_output)
			continue;

		switch (op) {
		case SOF_WIDGET_SETUP:
			ret = sof_set_up_widgets_in_path(sdev, widget, dir, spcm);
			str = "set up";
			break;
		case SOF_WIDGET_FREE:
			ret = sof_free_widgets_in_path(sdev, widget, dir, spcm);
			str = "free";
			break;
		...
		}
		if (ret < 0) {
			dev_err(sdev->dev, "Failed to %s connected widgets\n", str);
			return ret;
		}
	}

	return 0;
}
```

[`sof_set_up_widgets_in_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L601) recurses along the sink path, calling [`sof_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251) for each widget, which sends the create-module message to the DSP under the widget's [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422):

```c
/* sound/soc/sof/sof-audio.c:251 */
int sof_widget_setup(struct snd_sof_dev *sdev, struct snd_sof_widget *swidget)
{
	guard(mutex)(&swidget->setup_mutex);
	return sof_widget_setup_unlocked(sdev, swidget);
}
```

The [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) carries the firmware component id, the DAPM widget type [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) that the walk filters on, and the [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) that serializes its setup and free:

```c
/* sound/soc/sof/sof-audio.h:422 */
struct snd_sof_widget {
	struct snd_soc_component *scomp;
	int comp_id;
	int pipeline_id;
	...
	bool prepared;

	struct mutex setup_mutex; /* to protect the swidget setup and free operations */
	...
	int id; /* id is the DAPM widget type */
	...
	bool dynamic_pipeline_widget;
	...
	struct snd_soc_dapm_widget *widget;
	struct list_head list;	/* list in sdev widget list */
	struct snd_sof_pipeline *spipe;
	...
};
```

### trigger orders the host DMA against the IPC pipeline state

[`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) does not itself talk to the DSP. It decides the order of two calls, the platform host-DMA trigger [`snd_sof_pcm_platform_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464) and the IPC-version [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), from the ALSA command and the IPC-version flags. The first switch sets `ipc_first` and `reset_hw_params`:

```c
/* sound/soc/sof/pcm.c:385 */
static int sof_pcm_trigger(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);
	struct snd_sof_pcm *spcm;
	bool reset_hw_params = false;
	bool ipc_first = false;
	int ret = 0;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;
	...
	spcm->pending_stop[substream->stream] = false;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		ipc_first = true;
		break;
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		if (pcm_ops && pcm_ops->ipc_first_on_start)
			ipc_first = true;
		break;
	case SNDRV_PCM_TRIGGER_START:
		...
		if (pcm_ops && pcm_ops->ipc_first_on_start)
			ipc_first = true;
		break;
	...
	case SNDRV_PCM_TRIGGER_STOP:
		ipc_first = true;
		if (pcm_ops && pcm_ops->reset_hw_params_during_stop)
			reset_hw_params = true;
		break;
	default:
		spcm_err(spcm, substream->stream, "Unhandled trigger cmd %d\n", cmd);
		return -EINVAL;
	}
```

With the booleans set, the body runs the platform trigger before the IPC when `ipc_first` is clear, runs the IPC-version [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), then runs the platform trigger after the IPC on a start, and on a stop may free the stream:

```c
/* sound/soc/sof/pcm.c:385 (continued) */
	if (!ipc_first)
		snd_sof_pcm_platform_trigger(sdev, substream, cmd);

	if (pcm_ops && pcm_ops->trigger)
		ret = pcm_ops->trigger(component, substream, cmd);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_START:
		/* invoke platform trigger to start DMA only if pcm_ops is successful */
		if (ipc_first && !ret)
			snd_sof_pcm_platform_trigger(sdev, substream, cmd);
		break;
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
	case SNDRV_PCM_TRIGGER_STOP:
		/* invoke platform trigger to stop DMA even if pcm_ops isn't set or if it failed */
		if (!pcm_ops || !pcm_ops->platform_stop_during_hw_free)
			snd_sof_pcm_platform_trigger(sdev, substream, cmd);
		...
		break;
	default:
		break;
	}

	/* free PCM if reset_hw_params is set and the STOP IPC is successful */
	if (!ret && reset_hw_params)
		ret = sof_pcm_stream_free(sdev, substream, spcm, substream->stream, false);

	return ret;
}
```

[`snd_sof_pcm_platform_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464) is the thin guard around the platform host-DMA trigger, and on an MTL device its [`pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L246) member is [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177):

```c
/* sound/soc/sof/ops.h:464 */
static inline int
snd_sof_pcm_platform_trigger(struct snd_sof_dev *sdev,
			     struct snd_pcm_substream *substream, int cmd)
{
	if (sof_ops(sdev) && sof_ops(sdev)->pcm_trigger)
		return sof_ops(sdev)->pcm_trigger(sdev, substream, cmd);

	return 0;
}
```

The IPC-version [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member is [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) on an MTL device, which collapses the ALSA command into a firmware pipeline state of [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137), targeting [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) on start and [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) on stop or pause. The generic body never encodes those states; it only chooses when to call the member relative to the host DMA. The full state machine and the sink-to-source pipeline traversal are covered on the IPC4 backend page.

```
    sof_pcm_trigger(): host-DMA vs IPC ordering per ALSA command
    ──────────────────────────────────────────────────────────────

    ┌──────────────────┬───────────┬──────────────────────────────┐
    │ ALSA cmd         │ ipc_first │  platform host-DMA trigger   │
    ├──────────────────┼───────────┼──────────────────────────────┤
    │ START            │  if flag  │  after IPC (when ipc_first)  │
    │ PAUSE_RELEASE    │  if flag  │  after IPC (when ipc_first)  │
    │ PAUSE_PUSH       │    true   │  unless stop_during_hw_free  │
    │ STOP             │    true   │  unless stop_during_hw_free  │
    │ SUSPEND          │   (stop)  │  unless stop_during_hw_free  │
    └──────────────────┴───────────┴──────────────────────────────┘

    flag = pcm_ops->ipc_first_on_start (set on IPC4)
    !ipc_first: platform trigger runs BEFORE the IPC trigger
    STOP also sets reset_hw_params when reset_hw_params_during_stop
```

### pointer reads the firmware-written position

[`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) tries three sources in order. It calls the IPC-version [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) first, treating its `-EOPNOTSUPP` as if the op were absent, then the platform [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L251), then the position the firmware wrote into the [`posn`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) record:

```c
/* sound/soc/sof/pcm.c:497 */
static snd_pcm_uframes_t sof_pcm_pointer(struct snd_soc_component *component,
					 struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);
	struct snd_sof_pcm *spcm;
	snd_pcm_uframes_t host, dai;
	int ret = -EOPNOTSUPP;

	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	if (pcm_ops && pcm_ops->pointer)
		ret = pcm_ops->pointer(component, substream, &host);

	if (ret != -EOPNOTSUPP)
		return ret ? ret : host;

	/* use dsp ops pointer callback directly if set */
	if (sof_ops(sdev)->pcm_pointer)
		return sof_ops(sdev)->pcm_pointer(sdev, substream);

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;

	/* read position from DSP */
	host = bytes_to_frames(substream->runtime,
			       spcm->stream[substream->stream].posn.host_posn);
	dai = bytes_to_frames(substream->runtime,
			      spcm->stream[substream->stream].posn.dai_posn);

	trace_sof_pcm_pointer_position(sdev, spcm, substream, host, dai);

	return host;
}
```

According to the comment on the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member, an `-EOPNOTSUPP` return is handled the same way as an absent callback, which is why the body falls through to the platform op and then the cached position. The firmware updates [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142) and [`dai_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L143) asynchronously, and the deferred work scheduled by [`snd_sof_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43) drives the ALSA period accounting between pointer queries.

### pcm_construct pre-allocates the DMA buffer pages

[`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) is the only body that runs once at PCM-device creation rather than per substream, and the only one that delegates to neither function pointer struct. It pre-allocates scatter-gather pages for whichever directions topology declared:

```c
/* sound/soc/sof/pcm.c:637 */
static int sof_pcm_new(struct snd_soc_component *component,
		       struct snd_soc_pcm_runtime *rtd)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pcm *spcm;
	struct snd_pcm *pcm = rtd->pcm;
	struct snd_soc_tplg_stream_caps *caps;
	int stream = SNDRV_PCM_STREAM_PLAYBACK;

	/* find SOF PCM for this RTD */
	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm) {
		dev_warn(component->dev, "warn: can't find PCM with DAI ID %d\n",
			 rtd->dai_link->id);
		return 0;
	}
	...
	/* do we need to pre-allocate playback audio buffer pages */
	if (!spcm->pcm.playback)
		goto capture;

	caps = &spcm->pcm.caps[stream];
	...
	/* pre-allocate playback audio buffer pages */
	snd_pcm_set_managed_buffer(pcm->streams[stream].substream,
				   SNDRV_DMA_TYPE_DEV_SG, sdev->dev,
				   0, le32_to_cpu(caps->buffer_size_max));
	...
capture:
	stream = SNDRV_PCM_STREAM_CAPTURE;

	/* do we need to pre-allocate capture audio buffer pages */
	if (!spcm->pcm.capture)
		return 0;

	caps = &spcm->pcm.caps[stream];
	...
	/* pre-allocate capture audio buffer pages */
	snd_pcm_set_managed_buffer(pcm->streams[stream].substream,
				   SNDRV_DMA_TYPE_DEV_SG, sdev->dev,
				   0, le32_to_cpu(caps->buffer_size_max));

	return 0;
}
```

According to the comment on the function, the managed buffer means no explicit release is needed in a PCM-free path, because [`snd_pcm_lib_preallocate_free_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L268) is called by the ALSA core. The [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45) type matches the scatter-gather page table that [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) later hands to the firmware through [`snd_sof_create_page_table()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-utils.c#L25).

### be_hw_params_fixup forces back-end parameters to topology

[`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) is the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L197) op, wired by [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) only when a DSP is present. It looks up its own component on the runtime with [`snd_soc_rtdcom_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L336) using the [`SOF_AUDIO_PCM_DRV_NAME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L24) string, finds the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) for the back-end link with [`snd_sof_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L993), and either forces a 48 kHz default or delegates to the IPC-version [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123):

```c
/* sound/soc/sof/pcm.c:719 */
int sof_pcm_dai_link_fixup(struct snd_soc_pcm_runtime *rtd, struct snd_pcm_hw_params *params)
{
	struct snd_interval *rate = hw_param_interval(params,
			SNDRV_PCM_HW_PARAM_RATE);
	struct snd_interval *channels = hw_param_interval(params,
						SNDRV_PCM_HW_PARAM_CHANNELS);
	struct snd_mask *fmt = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
	struct snd_soc_component *component =
		snd_soc_rtdcom_lookup(rtd, SOF_AUDIO_PCM_DRV_NAME);
	struct snd_sof_dai *dai =
		snd_sof_find_dai(component, (char *)rtd->dai_link->name);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	const struct sof_ipc_pcm_ops *pcm_ops = sof_ipc_get_ops(sdev, pcm);

	/* no topology exists for this BE, try a common configuration */
	if (!dai) {
		dev_warn(component->dev,
			 "warning: no topology found for BE DAI %s config\n",
			 rtd->dai_link->name);

		/*  set 48k, stereo, 16bits by default */
		rate->min = 48000;
		rate->max = 48000;

		channels->min = 2;
		channels->max = 2;

		snd_mask_none(fmt);
		snd_mask_set_format(fmt, SNDRV_PCM_FORMAT_S16_LE);

		return 0;
	}

	if (pcm_ops && pcm_ops->dai_link_fixup)
		return pcm_ops->dai_link_fixup(rtd, params);

	return 0;
}
```

The op runs on a back-end runtime, unlike the substream bodies that return early for one, because the fixup exists to clamp the back-end's hardware parameters to the values topology set for the link. On an MTL device the IPC-version [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is [`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), which reads the topology DAI configuration; the generic body names only the member.

### Each body is wired into the component at probe

[`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) fills the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) embedded as [`sdev->plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L569) and assigns every body documented here:

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *drv_name;
	...
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
	...
	pd->pcm_construct = sof_pcm_new;
	pd->ignore_machine = drv_name;
	pd->be_pcm_base = SOF_BE_PCM_BASE;
	pd->use_dai_pcm_id = true;
	pd->topology_name_prefix = "sof";
	...
	/*
	 * The fixup is only needed when the DSP is in use as with the DSPless
	 * mode we are directly using the audio interface
	 */
	if (!sdev->dspless_mode_selected)
		pd->be_hw_params_fixup = sof_pcm_dai_link_fixup;
}
```

The [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) member receives [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) and the [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L197) member receives [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) only outside DSPless mode, so the same [`pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) bodies serve every SOF platform while the descriptor varies. The descriptor and registration are covered on the SOF component page; the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) backend these bodies dispatch to on MTL is covered on the IPC4 backend page.
