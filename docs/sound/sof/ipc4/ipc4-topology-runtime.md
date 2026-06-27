# SOF IPC4 topology runtime

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

After the IPC4 topology load phase has parsed a firmware topology file into [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) objects each carrying a pre-built private structure, the runtime half of the Sound Open Firmware IPC4 topology layer instantiates those widgets on the Intel DSP at PCM time by sending IPC messages, and the entry points are the runtime members of the function pointer struct [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973): [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) sends [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) or [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101), [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472) sends [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306), [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) patches the runtime DMA gateway node index into the DAI copier payload, [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) sends the delete-module or [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) message, [`sof_ipc4_route_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573) sends [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307), and [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) frees every still-active stream during suspend. The driver of all of this is the PCM path: [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) walks the connected DAPM widgets and calls [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) per widget, then [`sof_setup_pipeline_connections()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L329) binds the modules with [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472).

```
    Loaded widget                 widget_setup / route_setup        Live DSP
    (private struct built         (sends IPC at PCM time)           (module +
     at load time)                                                  pipeline)
    ─────────────────             ──────────────────────────       ──────────

    snd_sof_widget                sof_ipc4_widget_setup()
    ┌───────────────────────┐     ┌────────────────────────────┐
    │ id = snd_soc_dapm_    │     │ pick payload by swidget->id│
    │      aif_in            │ ──▶ │ assign instance_id (m_ida) │   MOD_INIT_
    │ private ─▶ copier      │     │ stamp MOD_INSTANCE,        │   INSTANCE
    │            data + msg  │     │   EXT_PPL_ID into msg      │ ──────────▶ ┌──────────┐
    │ spipe ─▶ pipe_widget   │     │ tx_message_no_reply(msg)   │             │ copier   │
    │ module_info (fw mod id)│     └────────────────────────────┘             │ instance │
    └────────────────────────┘                                                │ ppl = N  │
                                  sof_ipc4_widget_setup()                     └────┬─────┘
    snd_sof_widget                ┌────────────────────────────┐                  │
    ┌────────────────────────┐    │ swidget->id == scheduler:  │   CREATE_         │ bound by
    │ id = snd_soc_dapm_     │ ──▶ │   msg = pipeline->msg      │   PIPELINE        │ MOD_BIND
    │      scheduler         │     │   instance_id (pipeline_ida)──────────▶ ┌──────▼────┐ 
    │ private ─▶ pipeline   │     │   tx_message_no_reply(msg) │            │ pipeline N │
    └───────────────────────┘     └────────────────────────────┘            └────────────┘

    sof_ipc4_route_setup(): src_fw_module.id | MOD_INSTANCE(src) | MOD_BIND
                            extension = sink_fw_module.id | DST_MOD_INSTANCE(sink)
                                        | DST_MOD_QUEUE_ID | SRC_MOD_QUEUE_ID
```

## SUMMARY

The IPC4 topology layer splits its work into a load phase and a runtime phase. The load phase, owned by the per-widget ipc_setup callbacks in [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925), allocates the IPC4 private structure for each [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) (the copier, gain, mixer, src, process, and pipeline structs) and parses topology tokens into it without sending any IPC. The runtime phase, the subject of this page, sends the actual messages that create modules and pipelines on the DSP, bind them together, and tear them down. The runtime members are reached through the function pointer struct [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973), a [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) declared `extern` in [`ipc4-priv.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h#L102), and the SOF core never calls an IPC4 function directly; it fetches the ops with [`sof_ipc_get_ops(sdev, tplg)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) and invokes the member.

There is no symmetric set-up-all-pipelines op. The [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) layout declares both a [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) and a [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) member, but [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) assigns only [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) to [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) and leaves the set-up member NULL. Pipeline and widget set-up happens per widget through [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103), driven from the PCM path by [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) per widget when a stream is prepared, with no single batch entry point.

[`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) switches on [`swidget->id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) to select the IPC payload from the load-time private struct, assigns a module instance id from the firmware module's own ida through [`sof_ipc4_widget_assign_instance_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1339), stamps the instance id, parameter size, and parent pipeline id into the [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header words, and sends [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) with [`sof_ipc_tx_message_no_reply()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L745). A scheduler widget instead sends the [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) message that its [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) prepared at load time, drawing its instance id from a separate `pipeline_ida`. [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472) resolves the source output pin and sink input pin queue ids with [`sof_ipc4_get_queue_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3340) and sends [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) with both module ids encoded across the primary and extension words. [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) runs from [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) for DAI widgets and writes the runtime gateway node index into the DAI copier payload before [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) sends it; it sends no IPC of its own for SSP or DMIC. The teardown direction reverses this. [`sof_ipc4_route_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573) sends [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307), [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) sends [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) for a scheduler widget and otherwise just returns the module instance id to its ida, and [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) defers to [`sof_pcm_free_all_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261) so a suspend after an xrun leaves the kernel and firmware in sync.

## SPECIFICATIONS

The IPC4 module, pipeline, and gateway concepts come from the Intel Audio DSP firmware interface that Sound Open Firmware implements as open firmware on the Cadence-based Audio DSP shipped on Intel SoC platforms from Tiger Lake and Meteor Lake onward, rather than from a public standard. The message header words, the module and global message type values, and the instance, queue, and pipeline id bit fields the runtime ops encode are reproduced as macros in [`include/sound/sof/ipc4/header.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h). The [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and the ASoC topology binary it derives from are Linux kernel software constructs. The serial-audio gateways a DAI copier drives on an x86-64 ACPI Meteor Lake or Lunar Lake system (I2S over SSP, the SoundWire ALH gateway, and PDM over DMIC) are defined by their respective interface standards.

## LINUX KERNEL

### IPC4 runtime topology ops (ipc4-topology.c)

- [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973): the [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) instance for IPC4; assigns [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230), [`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224), [`route_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L225), [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232), and [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238); leaves [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) unassigned; declared as [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h#L102)
- [`'\<sof_ipc4_widget_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103): the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) op; selects the IPC payload by [`swidget->id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), assigns the module instance id, and sends [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) or [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101)
- [`'\<sof_ipc4_widget_free\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293): the [`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231) op; sends [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) for a scheduler widget under [`pipeline_state_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) and otherwise returns the module instance id to [`fw_module->m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h)
- [`'\<sof_ipc4_route_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472): the [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224) op; resolves source and sink queue ids and sends the [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) message
- [`'\<sof_ipc4_route_free\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573): the [`route_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L225) op; sends [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307) and returns the queue ids, skipping the IPC when source and sink share a pipeline
- [`'\<sof_ipc4_dai_config\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628): the [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) op; writes the runtime gateway node index into the DAI copier [`gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) per [`ipc4_copier->dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), or the chain-DMA link id into the pipeline message
- [`'\<sof_ipc4_tear_down_all_pipelines\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829): the [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) op; calls [`sof_pcm_free_all_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261) at system suspend so no stream is left active
- [`'\<sof_ipc4_widget_assign_instance_id\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1339): allocates a per-module-type instance id from [`fw_module->m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) bounded by [`instance_max_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h)
- [`'\<sof_ipc4_get_queue_id\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3340): returns the source output or sink input pin queue id, 0 for a single pin, from the pin binding array, or from a per-widget queue ida
- [`'\<sof_ipc4_put_queue_id\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3398): releases a queue id back to the per-widget ida on bind failure or unbind
- [`'\<sof_ipc4_set_copier_sink_format\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3422): sends a copier sink-format config-set message for a non-zero output pin of a copier source before the bind

### SOF core glue driving the runtime ops (sof-audio.c)

- [`'\<sof_widget_list_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762): at PCM prepare, walks the connected DAPM widget list with [`SOF_WIDGET_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L51) and then sets up routes and completes pipelines
- [`'\<sof_widget_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251): the locked wrapper that takes [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and calls [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144)
- [`'\<sof_widget_setup_unlocked\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144): the per-widget setup driver; invokes [`tplg_ops->widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) and, for DAI widgets, [`tplg_ops->dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232)
- [`'\<sof_setup_pipeline_connections\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L329): after the modules are created, drives [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) for every connection in the path
- [`'\<sof_route_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258): finds the [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) for a source/sink pair and calls [`tplg_ops->route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224)
- [`'\<sof_pcm_free_all_streams\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261): frees every active substream's pipelines, the work [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) delegates to
- [`'\<sof_ipc4_set_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124): the PCM-side companion that drives a created pipeline through its run states; runtime topology only creates and deletes the pipeline container, leaving its run state to the PCM-side path

### Runtime data types (sof-audio.h, ipc4-topology.h)

- [`'\<struct sof_ipc_tplg_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221): the IPC-version-independent topology op set; carries the runtime [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224), [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232), and both the [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) and [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) members
- [`'\<struct snd_sof_widget\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422): the SOF view of a DAPM widget; the [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), the [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the load-time IPC4 struct, the [`instance_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is set by setup, [`spipe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) points at the pipeline, and [`module_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) at the loaded firmware module
- [`'\<struct snd_sof_route\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531): a DAPM route reduced to [`src_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), [`sink_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), the negotiated [`src_queue_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) and [`dst_queue_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), and a [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag
- [`'\<struct snd_sof_dai\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547): the SOF DAI object; a DAI widget's [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) points here and its own [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) at the DAI [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332)
- [`'\<struct sof_ipc4_pipeline\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156): the scheduler widget's private data sent as the create-pipeline payload; holds the prebuilt [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), the [`mem_usage`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), the cached [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), and the [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) flag
- [`'\<struct sof_ipc4_copier\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332): the host, DAI, and buffer copier private data; its [`ipc_config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) is sent as the module-init payload, its [`data.gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) is patched by [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232), and its [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) is the header setup sends
- [`'\<struct sof_ipc4_gain\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429): the PGA module private data; setup sends its [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429) blob as the module-init payload
- [`'\<struct sof_ipc4_fw_module\>':'sound/soc/sof/ipc4-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h): the loaded firmware module descriptor; its [`man4_module_entry.id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) becomes the message primary word and its [`m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) the module instance id source

### IPC4 message header and field encoders (ipc4/header.h)

- [`'\<struct sof_ipc4_msg\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32): the IPC4 message; a [`primary`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) and [`extension`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header word pair plus the [`data_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) and [`data_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) payload
- [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301): the [`enum sof_ipc4_module_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L300) value (0) that creates a module instance
- [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306): the [`enum sof_ipc4_module_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L300) value (5) that binds two module pins
- [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307): the [`enum sof_ipc4_module_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L300) value (6) that unbinds two module pins
- [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101): the [`enum sof_ipc4_global_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L85) value that creates a pipeline container
- [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102): the [`enum sof_ipc4_global_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L85) value that deletes a pipeline container
- [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139): the [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137) value [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) records after deleting a pipeline
- [`SOF_IPC4_MSG_TARGET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L151): selects [`SOF_IPC4_FW_GEN_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L80) or [`SOF_IPC4_MODULE_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L83) in bit 30
- [`SOF_IPC4_MSG_DIR()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L157): sets the request or reply bit 29, [`SOF_IPC4_MSG_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L133) for an outgoing command
- [`SOF_IPC4_MSG_TYPE_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L162): packs the message type into bits 28:24, used for the global and module type values
- [`SOF_IPC4_MOD_INSTANCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L328): packs the source module instance id into the primary word of a module message
- [`SOF_IPC4_MOD_EXT_PPL_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L345): packs the parent pipeline instance id into the extension word of a module-init message
- [`SOF_IPC4_GLB_PIPE_INSTANCE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L172): packs the pipeline instance id into bits 23:16 of a create-pipeline or delete-pipeline message
- [`SOF_IPC4_MOD_EXT_DST_MOD_INSTANCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L366): packs the sink module instance id into the bind extension word
- [`SOF_IPC4_MOD_EXT_DST_MOD_QUEUE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L370): packs the sink input pin queue id into the bind extension word
- [`SOF_IPC4_MOD_EXT_SRC_MOD_QUEUE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L374): packs the source output pin queue id into the bind extension word

### x86-64 ACPI worked example (pci-mtl.c)

- [`'mtl_desc':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31): the Meteor Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h) bound to the HDA_MTL PCI id; its [`ipc_default`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c) is [`SOF_IPC_TYPE_4`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h), which selects [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) as the topology ops on an MTL or LNL system

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget and route model the SOF widgets and the bind routes are derived from
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end PCM and back-end DAI split that decides which widgets are set up on a stream and where [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) runs
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface whose copier [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) patches with the runtime node index
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the ALH DAI gateway feeds on Meteor Lake

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware introduction and architecture](https://thesofproject.github.io/latest/introduction/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Each runtime op below is a member of [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), the IPC-version-independent function pointer struct the SOF core reaches through [`sof_ipc_get_ops(sdev, tplg)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541). The IPC4 instance [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) fills in the runtime members listed here and leaves the [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) member unassigned, so the core sees a NULL there and never batches a set-up across all pipelines. The generic core treats an absent member as a no-op that returns success. Each op encodes a fixed IPC message into the [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header and ships it with [`sof_ipc_tx_message_no_reply()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L745).

| topology op | IPC4 implementation | IPC message sent |
|---|---|---|
| [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) (module) | [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) | [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) |
| [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) (scheduler) | [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) | [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) |
| [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224) | [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472) | [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) |
| [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) | [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) | none; patches the copier node id in place for HDA/ALH |
| [`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231) (scheduler) | [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) | [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) |
| [`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231) (module) | [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) | none; returns the instance id to the ida |
| [`route_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L225) | [`sof_ipc4_route_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573) | [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307) (skipped within one pipeline) |
| [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) | not assigned by [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) | none; set-up is per widget via [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) |
| [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) | [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) | none; frees streams, which cascades to per-widget frees |

### widget_setup

[`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) is [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103), called from [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) while the connected DAPM widget list is walked in path order. It reads the load-time private struct back off [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), and for a module widget it sends [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) with the module's own [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332). For a scheduler widget it sends the [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) message built into the [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) at load. A widget whose pipeline has [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) set is skipped here, since chained DMA does not create discrete module instances.

### widget_free

[`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231) is [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293), the reverse of setup, taken under the [`pipeline_state_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h). According to the comment in the function, "freeing a pipeline frees all the widgets associated with it", so it sends [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) only for a scheduler widget and then records [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139) as the cached pipeline state; for a non-scheduler module it sends no IPC and only returns the instance id to [`fw_module->m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h).

### route_setup

[`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224) is [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472), called from [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) after both endpoint modules of a [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) are created. It resolves the source output pin and the sink input pin queue ids with [`sof_ipc4_get_queue_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3340) and sends [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) with the source module id and instance in the primary word and the sink module id, instance, and both queue ids in the extension word.

### dai_config

[`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) is [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628), called from [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) for the DAI widgets (those for which [`WIDGET_IS_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L42) is true), just before [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) sends that DAI copier's module-init message. It sends no IPC. It branches on [`ipc4_copier->dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) and, when the call carries [`SOF_DAI_CONFIG_FLAGS_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h), writes the runtime gateway node index into [`copier_data->gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) for HDA and ALH; SSP and DMIC carry their node id in the load-time blob and need no runtime patch.

### route_free

[`route_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L225) is [`sof_ipc4_route_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573). It sends [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307) with the same module and queue id encoding as the bind, then returns both queue ids with [`sof_ipc4_put_queue_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3398). According to the comment in the function, "routes belonging to the same pipeline will be disconnected by the FW when the pipeline is freed", so when the source and sink widgets share a pipeline widget the unbind IPC is skipped and only the queue ids are released.

### tear_down_all_pipelines

[`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) is [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829), called at system suspend. It sends no message of its own and delegates entirely to [`sof_pcm_free_all_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261), which frees every active stream's widget list, which in turn drives [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) per widget so the delete-pipeline and instance-id releases happen through the same per-widget path used at hw_free. According to the comment in the function, the call is needed because freeing "might have been skipped when xrun happened just at the start of the suspend", which would otherwise leave the kernel and firmware out of sync.

## DETAILS

### The ops table assigns the runtime members and omits set-up-all

The SOF core reaches IPC4 through [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973), a [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221). The runtime members assigned here are [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230), [`widget_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L231), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224), [`route_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L225), [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232), and [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238):

```c
/* sound/soc/sof/ipc4-topology.c:3973 */
const struct sof_ipc_tplg_ops ipc4_tplg_ops = {
	.widget = tplg_ipc4_widget_ops,
	.token_list = ipc4_token_list,
	.control_setup = sof_ipc4_control_setup,
	.control = &tplg_ipc4_control_ops,
	.widget_setup = sof_ipc4_widget_setup,
	.widget_free = sof_ipc4_widget_free,
	.route_setup = sof_ipc4_route_setup,
	.route_free = sof_ipc4_route_free,
	.dai_config = sof_ipc4_dai_config,
	.parse_manifest = sof_ipc4_parse_manifest,
	.dai_get_param = sof_ipc4_dai_get_param,
	.tear_down_all_pipelines = sof_ipc4_tear_down_all_pipelines,
	.link_setup = sof_ipc4_link_setup,
	.host_config = sof_ipc4_host_config,
};
```

There is no `.set_up_all_pipelines =` line. The struct type does declare the member, alongside its teardown counterpart:

```c
/* sound/soc/sof/sof-audio.h:237 */
	int (*set_up_all_pipelines)(struct snd_sof_dev *sdev, bool verify);
	int (*tear_down_all_pipelines)(struct snd_sof_dev *sdev, bool verify);
```

Because the designated initializer omits [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237), the member is zero-initialized to NULL, and any core caller that consulted it would treat it as absent. IPC4 set-up is therefore not a single batch operation; it is the per-widget [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) reached through [`tplg_ops->widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230). The teardown side keeps a batch op only because suspend needs one entry point to sweep up streams that an xrun left active.

### The PCM path drives setup, then routes, then completes pipelines

The runtime ops do not call themselves; the SOF core PCM path drives them when a stream is prepared. [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) is the entry point, and it runs the widget walk first, then the route connections, then the per-pipeline completion:

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
}
```

[`sof_walk_widgets_in_order()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L672) with [`SOF_WIDGET_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L51) reaches [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) per widget, which is where the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) and [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) members are invoked. According to the comment, "Set up is used to send the IPC to the DSP to create the widget", which is the moment the load-time private struct becomes a live module on the DSP.

The per-widget setup driver pulls the topology ops once, skips a widget that has no private data, increments a use count so a shared widget is created only once, then calls the two relevant runtime members:

```c
/* sound/soc/sof/sof-audio.c:144 */
static int sof_widget_setup_unlocked(struct snd_sof_dev *sdev,
				     struct snd_sof_widget *swidget)
{
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	...
	/* widget already set up */
	if (++swidget->use_count > 1)
		return 0;
	...
	/* setup widget in the DSP */
	if (tplg_ops && tplg_ops->widget_setup) {
		ret = tplg_ops->widget_setup(sdev, swidget);
		if (ret < 0)
			goto pipe_widget_free;
	}

	/* send config for DAI components */
	if (WIDGET_IS_DAI(swidget->id)) {
		unsigned int flags = SOF_DAI_CONFIG_FLAGS_HW_PARAMS;

		/*
		 * The config flags saved during BE DAI hw_params will be used for IPC3. IPC4 does
		 * not use the flags argument.
		 */
		if (tplg_ops && tplg_ops->dai_config) {
			ret = tplg_ops->dai_config(sdev, swidget, flags, NULL);
			if (ret < 0)
				goto widget_free;
		}
	}
	...
}
```

For a DAI widget the order is fixed: [`tplg_ops->widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) runs first and sends the DAI copier module-init, and [`tplg_ops->dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) follows. For a non-DAI widget only [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) runs. The scheduler widget of a pipeline is set up before the modules in that pipeline because [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) recurses into [`swidget->spipe->pipe_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) first, so the create-pipeline message reaches the DSP before any create-module message names that pipeline as a parent.

```
    PCM-prepare setup order (sof_widget_list_setup, top to bottom)
    ───────────────────────────────────────────────────────────────

    1. SOF_WIDGET_SETUP walk          sof_walk_widgets_in_order()
       per widget ─▶ sof_widget_setup_unlocked()
       ┌──────────────────────────────────────────────────────┐
       │ scheduler (pipe_widget) first  ─▶ CREATE_PIPELINE    │
       │   then each module of that pipeline:                 │
       │     widget_setup    ─▶ MOD_INIT_INSTANCE             │
       │     if WIDGET_IS_DAI ─▶ dai_config (no IPC, patches) │
       └──────────────────────────────────────────────────────┘
                              ▼
    2. sof_setup_pipeline_connections()
       per connection ─▶ sof_route_setup() ─▶ MOD_BIND
                              ▼
    3. per-pipeline completion (run state left to PCM-side path)

    invariant: CREATE_PIPELINE precedes the MOD_INIT_INSTANCE that
               names it as parent; all modules precede MOD_BIND
```

### widget_setup selects the payload and stamps the header

[`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) is one switch over [`swidget->id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) that selects the IPC payload pointer and size, followed by a shared tail that stamps the header words and sends the message. The scheduler case takes its message and instance id apart from every other case. It draws the instance id from a dedicated `pipeline_ida` bounded by the firmware's max pipeline count and packs it into the create-pipeline primary word:

```c
/* sound/soc/sof/ipc4-topology.c:3103 */
static int sof_ipc4_widget_setup(struct snd_sof_dev *sdev, struct snd_sof_widget *swidget)
{
	struct snd_sof_widget *pipe_widget = swidget->spipe->pipe_widget;
	struct sof_ipc4_fw_data *ipc4_data = sdev->private;
	struct sof_ipc4_pipeline *pipeline;
	struct sof_ipc4_msg *msg;
	void *ipc_data = NULL;
	void *ext_data = NULL;
	u32 ipc_size = 0;
	int ret;

	switch (swidget->id) {
	case snd_soc_dapm_scheduler:
		pipeline = swidget->private;

		if (pipeline->use_chain_dma) {
			dev_warn(sdev->dev, "use_chain_dma set for scheduler %s",
				 swidget->widget->name);
			return 0;
		}
		...
		msg = &pipeline->msg;
		msg->primary |= pipeline->mem_usage;

		swidget->instance_id = ida_alloc_max(&pipeline_ida, ipc4_data->max_num_pipelines,
						     GFP_KERNEL);
		if (swidget->instance_id < 0) {
			dev_err(sdev->dev, "failed to assign pipeline id for %s: %d\n",
				swidget->widget->name, swidget->instance_id);
			return swidget->instance_id;
		}
		msg->primary &= ~SOF_IPC4_GLB_PIPE_INSTANCE_MASK;
		msg->primary |= SOF_IPC4_GLB_PIPE_INSTANCE_ID(swidget->instance_id);
		break;
```

Each module case reads the wire payload off the load-time private struct and takes the address of that struct's prebuilt [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332). The host and buffer copiers take their payload from [`ipc4_copier->ipc_config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), the DAI copier from [`dai->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), and the gain widget from its [`gain->data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429) blob:

```c
/* sound/soc/sof/ipc4-topology.c:3140 */
	case snd_soc_dapm_aif_in:
	case snd_soc_dapm_aif_out:
	case snd_soc_dapm_buffer:
	{
		struct sof_ipc4_copier *ipc4_copier = swidget->private;

		pipeline = pipe_widget->private;
		if (pipeline->use_chain_dma)
			return 0;

		ipc_size = ipc4_copier->ipc_config_size;
		ipc_data = ipc4_copier->ipc_config_data;

		msg = &ipc4_copier->msg;
		break;
	}
	case snd_soc_dapm_dai_in:
	case snd_soc_dapm_dai_out:
	{
		struct snd_sof_dai *dai = swidget->private;
		struct sof_ipc4_copier *ipc4_copier = dai->private;

		pipeline = pipe_widget->private;
		if (pipeline->use_chain_dma)
			return 0;

		ipc_size = ipc4_copier->ipc_config_size;
		ipc_data = ipc4_copier->ipc_config_data;

		msg = &ipc4_copier->msg;
		break;
	}
	case snd_soc_dapm_pga:
	{
		struct sof_ipc4_gain *gain = swidget->private;

		ipc_size = sizeof(gain->data);
		ipc_data = &gain->data;

		msg = &gain->msg;
		break;
	}
```

The shared tail runs only for a non-scheduler widget. It allocates the module instance id, masks it into the primary word, and packs the parameter size and the parent pipeline instance id into the extension word. This is the moment the message stops being the static template the load phase built and gains its runtime identity:

```c
/* sound/soc/sof/ipc4-topology.c:3233 */
	if (swidget->id != snd_soc_dapm_scheduler) {
		int module_id = msg->primary & SOF_IPC4_MOD_ID_MASK;

		ret = sof_ipc4_widget_assign_instance_id(sdev, swidget);
		if (ret < 0) {
			dev_err(sdev->dev, "failed to assign instance id for %s\n",
				swidget->widget->name);
			return ret;
		}

		msg->primary &= ~SOF_IPC4_MOD_INSTANCE_MASK;
		msg->primary |= SOF_IPC4_MOD_INSTANCE(swidget->instance_id);

		msg->extension &= ~SOF_IPC4_MOD_EXT_PARAM_SIZE_MASK;
		msg->extension |= SOF_IPC4_MOD_EXT_PARAM_SIZE(ipc_size >> 2);

		msg->extension &= ~SOF_IPC4_MOD_EXT_PPL_ID_MASK;
		msg->extension |= SOF_IPC4_MOD_EXT_PPL_ID(pipe_widget->instance_id);
		...
	}

	msg->data_size = ipc_size;
	msg->data_ptr = ipc_data;

	ret = sof_ipc_tx_message_no_reply(sdev->ipc, msg, ipc_size);

fail:
	if (ret < 0) {
		dev_err(sdev->dev, "failed to create module %s\n", swidget->widget->name);

		if (swidget->id != snd_soc_dapm_scheduler) {
			struct sof_ipc4_fw_module *fw_module = swidget->module_info;

			ida_free(&fw_module->m_ida, swidget->instance_id);
		} else {
			ida_free(&pipeline_ida, swidget->instance_id);
		}
	}

	kfree(ext_data);
	return ret;
}
```

The two id pools are distinct. The pipeline instance id comes from `pipeline_ida` in the scheduler case, and the module instance id comes from the per-module-type ida that [`sof_ipc4_widget_assign_instance_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1339) draws from. The module type's own [`m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) is bounded by the firmware-declared maximum instance count, so two copiers of the same module type get distinct instances and two modules of different types may reuse the same instance number:

```c
/* sound/soc/sof/ipc4-topology.c:1339 */
static int sof_ipc4_widget_assign_instance_id(struct snd_sof_dev *sdev,
					      struct snd_sof_widget *swidget)
{
	struct sof_ipc4_fw_module *fw_module = swidget->module_info;
	int max_instances = fw_module->man4_module_entry.instance_max_count;

	swidget->instance_id = ida_alloc_max(&fw_module->m_ida, max_instances, GFP_KERNEL);
	if (swidget->instance_id < 0) {
		dev_err(sdev->dev, "failed to assign instance id for widget %s",
			swidget->widget->name);
		return swidget->instance_id;
	}

	return 0;
}
```

The message that travels to the DSP is a [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32), two header words and a payload pointer; the runtime ops only ever set the two words and the payload, never the firmware-side reply:

```c
/* include/sound/sof/ipc4/header.h:32 */
struct sof_ipc4_msg {
	union {
		u64 header_u64;
		struct {
			u32 primary;
			u32 extension;
		};
	};

	size_t data_size;
	void *data_ptr;
};
```

It is shipped by [`sof_ipc_tx_message_no_reply()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L745), the no-reply wrapper every runtime topology op uses because module creation, binding, and deletion return only a status code:

```c
/* sound/soc/sof/sof-priv.h:745 */
static inline int sof_ipc_tx_message_no_reply(struct snd_sof_ipc *ipc, void *msg_data,
					      size_t msg_bytes)
{
	return sof_ipc_tx_message(ipc, msg_data, msg_bytes, NULL, 0);
}
```

Each widget id routes one payload and one prebuilt msg into that send, the scheduler and module tails stamping the instance id into the primary word before the payload pointer is attached:

```
    sof_ipc4_widget_setup: swidget->id selects payload and msg
    ──────────────────────────────────────────────────────────

    swidget->id            ipc_data (payload)        msg
    ──────────────────     ──────────────────────    ─────────────
    snd_soc_dapm_scheduler (none; mem_usage only)     pipeline->msg
    snd_soc_dapm_aif_in    copier->ipc_config_data    copier->msg
    snd_soc_dapm_aif_out   copier->ipc_config_data    copier->msg
    snd_soc_dapm_buffer    copier->ipc_config_data    copier->msg
    snd_soc_dapm_dai_in    dai->private copier_data    copier->msg
    snd_soc_dapm_dai_out   dai->private copier_data    copier->msg
    snd_soc_dapm_pga       &gain->data                gain->msg

    scheduler tail:  instance_id from pipeline_ida
                     msg.primary += GLB_PIPE_INSTANCE_ID(instance_id)
    module tail:     instance_id from fw_module->m_ida
                     msg.primary  += MOD_INSTANCE(instance_id)
                     msg.extension += MOD_EXT_PARAM_SIZE(ipc_size >> 2)
                     msg.extension += MOD_EXT_PPL_ID(pipe_widget instance)
    then: msg.data_ptr = ipc_data ; tx_message_no_reply()
```

### route_setup resolves queue ids and encodes a bind

Once the modules of a path are created, [`sof_setup_pipeline_connections()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L329) walks the DAPM paths and calls [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) for each connection, which finds the matching [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) and invokes [`tplg_ops->route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L224) once, guarding against a double bind with the route's [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag:

```c
/* sound/soc/sof/sof-audio.c:258 */
int sof_route_setup(struct snd_sof_dev *sdev, struct snd_soc_dapm_widget *wsource,
		    struct snd_soc_dapm_widget *wsink)
{
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	struct snd_sof_widget *src_widget = wsource->dobj.private;
	struct snd_sof_widget *sink_widget = wsink->dobj.private;
	struct snd_sof_route *sroute;
	bool route_found = false;
	...
	/* nothing to do if route is already set up */
	if (sroute->setup)
		return 0;

	if (tplg_ops && tplg_ops->route_setup) {
		int ret = tplg_ops->route_setup(sdev, sroute);

		if (ret < 0)
			return ret;
	}

	sroute->setup = true;
	return 0;
}
```

[`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472) reads the source and sink firmware module descriptors and their pipelines, fails early if either has no firmware module, then resolves the output and input pin queue ids:

```c
/* sound/soc/sof/ipc4-topology.c:3472 */
static int sof_ipc4_route_setup(struct snd_sof_dev *sdev, struct snd_sof_route *sroute)
{
	struct snd_sof_widget *src_widget = sroute->src_widget;
	struct snd_sof_widget *sink_widget = sroute->sink_widget;
	struct sof_ipc4_fw_module *src_fw_module = src_widget->module_info;
	struct sof_ipc4_fw_module *sink_fw_module = sink_widget->module_info;
	...
	sroute->src_queue_id = sof_ipc4_get_queue_id(src_widget, sink_widget,
						     SOF_PIN_TYPE_OUTPUT);
	if (sroute->src_queue_id < 0) {
		dev_err(sdev->dev,
			"failed to get src_queue_id ID from source widget %s\n",
			src_widget->widget->name);
		return sroute->src_queue_id;
	}

	sroute->dst_queue_id = sof_ipc4_get_queue_id(src_widget, sink_widget,
						     SOF_PIN_TYPE_INPUT);
	if (sroute->dst_queue_id < 0) {
		dev_err(sdev->dev,
			"failed to get dst_queue_id ID from sink widget %s\n",
			sink_widget->widget->name);
		sof_ipc4_put_queue_id(src_widget, sroute->src_queue_id,
				      SOF_PIN_TYPE_OUTPUT);
		return sroute->dst_queue_id;
	}
	...
```

The bind message itself is the source module id in the primary word, OR'd with the source instance and the [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) type, and the sink module id in the extension word, OR'd with the sink instance and both queue ids. The two halves name the two ends of the connection:

```c
/* sound/soc/sof/ipc4-topology.c:3543 */
	header = src_fw_module->man4_module_entry.id;
	header |= SOF_IPC4_MOD_INSTANCE(src_widget->instance_id);
	header |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_MOD_BIND);
	header |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	header |= SOF_IPC4_MSG_TARGET(SOF_IPC4_MODULE_MSG);

	extension = sink_fw_module->man4_module_entry.id;
	extension |= SOF_IPC4_MOD_EXT_DST_MOD_INSTANCE(sink_widget->instance_id);
	extension |= SOF_IPC4_MOD_EXT_DST_MOD_QUEUE_ID(sroute->dst_queue_id);
	extension |= SOF_IPC4_MOD_EXT_SRC_MOD_QUEUE_ID(sroute->src_queue_id);

	msg.primary = header;
	msg.extension = extension;

	ret = sof_ipc_tx_message_no_reply(sdev->ipc, &msg, 0);
	if (ret < 0) {
		dev_err(sdev->dev, "failed to bind modules %s:%d -> %s:%d\n",
			src_widget->widget->name, sroute->src_queue_id,
			sink_widget->widget->name, sroute->dst_queue_id);
		goto out;
	}

	return ret;
```

[`SOF_IPC4_MSG_TARGET(SOF_IPC4_MODULE_MSG)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L151) sets bit 30 so the firmware routes the message to a module rather than to the global pipeline manager, and [`SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_MOD_BIND)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L162) places the module type in bits 28:24. The queue id resolution that fills in the two `*_MOD_QUEUE_ID` fields returns 0 when a widget has a single pin, an index from the topology pin binding array, or an ida allocation when neither applies:

```c
/* sound/soc/sof/ipc4-topology.c:3374 */
	/* If there is only one input/output pin, queue id must be 0 */
	if (num_pins == 1)
		return 0;

	/* Allocate queue ID from pin binding array if it is defined in topology. */
	if (pin_binding) {
		for (i = 0; i < num_pins; i++) {
			if (!strcmp(pin_binding[i], buddy_name))
				return i;
		}
		...
	}

	/* If no pin binding array specified in topology, use ida to allocate one */
	return ida_alloc_max(queue_ida, num_pins, GFP_KERNEL);
```

A single-pin widget resolves to 0, a named match returns its index, and anything else allocates from the pool, with the output and input pins of each route filling src_queue_id and dst_queue_id:

```
    sof_ipc4_get_queue_id: how a pin resolves to a queue id
    ────────────────────────────────────────────────────────

    condition                          queue id returned
    ───────────────────────────────    ─────────────────────────
    num_pins == 1                  ─▶   0
    pin_binding[] names buddy      ─▶   index i of match
    otherwise                      ─▶   ida_alloc_max(queue_ida)

    called twice per route:
      SOF_PIN_TYPE_OUTPUT ─▶ sroute->src_queue_id
      SOF_PIN_TYPE_INPUT  ─▶ sroute->dst_queue_id
    on dst failure: put_queue_id(src) rolls the first one back
```

### dai_config patches the gateway node id before the copier is created

[`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) is the one runtime op that sends no IPC. It reaches the DAI copier through [`dai->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) and, on a hw_params-flagged call, rewrites the node index inside the copier payload that [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) is about to send. The HDA case writes the runtime DMA id straight into [`gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229), and SSP and DMIC do nothing because their node id was fixed at load:

```c
/* sound/soc/sof/ipc4-topology.c:3662 */
	switch (ipc4_copier->dai_type) {
	case SOF_DAI_INTEL_HDA:
		gtw_attr = ipc4_copier->gtw_attr;
		gtw_attr->lp_buffer_alloc = pipeline->lp_mode;
		if (flags & SOF_DAI_CONFIG_FLAGS_HW_PARAMS) {
			copier_data->gtw_cfg.node_id &= ~SOF_IPC4_NODE_INDEX_MASK;
			copier_data->gtw_cfg.node_id |= SOF_IPC4_NODE_INDEX(data->dai_data);
		}
		break;
	case SOF_DAI_INTEL_ALH:
		/*
		 * Do not clear the node ID when this op is invoked with
		 * SOF_DAI_CONFIG_FLAGS_HW_FREE. It is needed to free the group_ida during
		 * unprepare. The node_id for multi-gateway DAI's will be overwritten with the
		 * group_id during copier's ipc_prepare op.
		 */
		if (flags & SOF_DAI_CONFIG_FLAGS_HW_PARAMS) {
			...
		}

		break;
	case SOF_DAI_INTEL_DMIC:
	case SOF_DAI_INTEL_SSP:
		/* nothing to do for SSP/DMIC */
		break;
	default:
		dev_err(sdev->dev, "%s: unsupported dai type %d\n", __func__,
			ipc4_copier->dai_type);
		return -EINVAL;
	}

	return 0;
}
```

When the DAI pipeline carries [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), the function instead patches the chain-DMA link id into the pipeline message and returns early, because no discrete copier module is created in that mode. Because [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L232) runs immediately before [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) in [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144), the node index the host DMA layer assigned at hw_params is present in the payload by the time the module-init message is sent.

```
    sof_ipc4_dai_config: dai_type selects the node-id patch (no IPC)
    ─────────────────────────────────────────────────────────────────

    ipc4_copier->dai_type      action on HW_PARAMS
    ─────────────────────      ──────────────────────────────────────
    SOF_DAI_INTEL_HDA      ─▶  gtw_cfg.node_id += NODE_INDEX(dai_data)
                               gtw_attr->lp_buffer_alloc = lp_mode
    SOF_DAI_INTEL_ALH      ─▶  node-id kept; group handled at prepare
    SOF_DAI_INTEL_SSP      ─▶  nothing (node id fixed at load)
    SOF_DAI_INTEL_DMIC     ─▶  nothing (node id fixed at load)

    use_chain_dma set      ─▶  patch chain-DMA link id into pipeline msg,
                               return early (no discrete copier module)

    runs BEFORE widget_setup sends copier MOD_INIT_INSTANCE
```

### widget_free deletes the pipeline and releases the ids

[`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) reverses setup under the [`pipeline_state_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h). Only the scheduler branch sends an IPC, building a [`SOF_IPC4_GLB_DELETE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L102) header with the pipeline instance id, then resetting the cached state and returning the pipeline id to `pipeline_ida`:

```c
/* sound/soc/sof/ipc4-topology.c:3293 */
static int sof_ipc4_widget_free(struct snd_sof_dev *sdev, struct snd_sof_widget *swidget)
{
	struct sof_ipc4_fw_module *fw_module = swidget->module_info;
	struct sof_ipc4_fw_data *ipc4_data = sdev->private;
	int ret = 0;

	guard(mutex)(&ipc4_data->pipeline_state_mutex);

	/* freeing a pipeline frees all the widgets associated with it */
	if (swidget->id == snd_soc_dapm_scheduler) {
		struct sof_ipc4_pipeline *pipeline = swidget->private;
		struct sof_ipc4_msg msg = {{ 0 }};
		u32 header;

		if (pipeline->use_chain_dma) {
			dev_warn(sdev->dev, "use_chain_dma set for scheduler %s",
				 swidget->widget->name);
			return 0;
		}

		header = SOF_IPC4_GLB_PIPE_INSTANCE_ID(swidget->instance_id);
		header |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_DELETE_PIPELINE);
		header |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
		header |= SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG);

		msg.primary = header;

		ret = sof_ipc_tx_message_no_reply(sdev->ipc, &msg, 0);
		if (ret < 0)
			dev_err(sdev->dev, "failed to free pipeline widget %s\n",
				swidget->widget->name);

		pipeline->mem_usage = 0;
		pipeline->state = SOF_IPC4_PIPE_UNINITIALIZED;
		ida_free(&pipeline_ida, swidget->instance_id);
		swidget->instance_id = -EINVAL;
	} else {
		struct snd_sof_widget *pipe_widget = swidget->spipe->pipe_widget;
		struct sof_ipc4_pipeline *pipeline = pipe_widget->private;

		if (!pipeline->use_chain_dma)
			ida_free(&fw_module->m_ida, swidget->instance_id);
	}

	return ret;
}
```

A non-scheduler module sends no delete message, since deleting the pipeline on the DSP frees every module instance inside it; the module branch only returns the module instance id to [`fw_module->m_ida`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) so the kernel's id bookkeeping matches the firmware's. The delete-pipeline header uses [`SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L151), bit 30 clear, so the firmware routes it to the global pipeline manager rather than to a module, mirroring the create-pipeline target.

### route_free unbinds across pipelines only

[`sof_ipc4_route_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3573) sends [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307) only when the source and sink widgets are located in different pipelines. When they share a pipeline widget it skips the IPC and only returns the queue ids, because the delete-pipeline message will tear those internal connections down:

```c
/* sound/soc/sof/ipc4-topology.c:3595 */
	/*
	 * routes belonging to the same pipeline will be disconnected by the FW when the pipeline
	 * is freed. So avoid sending this IPC which will be ignored by the FW anyway.
	 */
	if (src_widget->spipe->pipe_widget == sink_widget->spipe->pipe_widget)
		goto out;

	header = src_fw_module->man4_module_entry.id;
	header |= SOF_IPC4_MOD_INSTANCE(src_widget->instance_id);
	header |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_MOD_UNBIND);
	header |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	header |= SOF_IPC4_MSG_TARGET(SOF_IPC4_MODULE_MSG);

	extension = sink_fw_module->man4_module_entry.id;
	extension |= SOF_IPC4_MOD_EXT_DST_MOD_INSTANCE(sink_widget->instance_id);
	extension |= SOF_IPC4_MOD_EXT_DST_MOD_QUEUE_ID(sroute->dst_queue_id);
	extension |= SOF_IPC4_MOD_EXT_SRC_MOD_QUEUE_ID(sroute->src_queue_id);

	msg.primary = header;
	msg.extension = extension;

	ret = sof_ipc_tx_message_no_reply(sdev->ipc, &msg, 0);
	if (ret < 0)
		dev_err(sdev->dev, "failed to unbind modules %s:%d -> %s:%d\n",
			src_widget->widget->name, sroute->src_queue_id,
			sink_widget->widget->name, sroute->dst_queue_id);
out:
	sof_ipc4_put_queue_id(sink_widget, sroute->dst_queue_id, SOF_PIN_TYPE_INPUT);
	sof_ipc4_put_queue_id(src_widget, sroute->src_queue_id, SOF_PIN_TYPE_OUTPUT);

	return ret;
}
```

The unbind extension word reuses the same [`SOF_IPC4_MOD_EXT_DST_MOD_INSTANCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L366), [`SOF_IPC4_MOD_EXT_DST_MOD_QUEUE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L370), and [`SOF_IPC4_MOD_EXT_SRC_MOD_QUEUE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L374) encoders as the bind, with only the message type changed to [`SOF_IPC4_MOD_UNBIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L307).

### tear_down_all_pipelines is the only batch op, and it frees streams

The teardown side keeps the single batch entry point the set-up side lacks. [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) sends nothing itself; it forwards to [`sof_pcm_free_all_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261):

```c
/* sound/soc/sof/ipc4-topology.c:3829 */
static int sof_ipc4_tear_down_all_pipelines(struct snd_sof_dev *sdev, bool verify)
{
	/*
	 * This function is called during system suspend, we need to make sure
	 * that all streams have been freed up.
	 * Freeing might have been skipped when xrun happened just at the start
	 * of the suspend and it sent a SNDRV_PCM_TRIGGER_STOP to the active
	 * stream. This will call sof_pcm_stream_free() with
	 * free_widget_list = false which will leave the kernel and firmware out
	 * of sync during suspend/resume.
	 *
	 * This will also make sure that paused streams handled correctly.
	 */

	return sof_pcm_free_all_streams(sdev);
}
```

[`sof_pcm_free_all_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L261) iterates every PCM and every direction, skips streams marked suspend-ignored, and frees each one's pipelines with the free-widget-list flag set, which is the cascade that reaches [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) per widget:

```c
/* sound/soc/sof/pcm.c:261 */
int sof_pcm_free_all_streams(struct snd_sof_dev *sdev)
{
	struct snd_pcm_substream *substream;
	struct snd_sof_pcm *spcm;
	int dir, ret;

	list_for_each_entry(spcm, &sdev->pcm_list, list) {
		for_each_pcm_streams(dir) {
			substream = spcm->stream[dir].substream;

			if (!substream || !substream->runtime ||
			    spcm->stream[dir].suspend_ignored)
				continue;

			if (spcm->stream[dir].list) {
				ret = sof_pcm_stream_free(sdev, substream, spcm,
							  dir, true);
				if (ret < 0)
					return ret;
			}
		}
	}

	return 0;
}
```

The asymmetry between the two directions follows from this. Set-up has no batch op because the connected-widget list is only known per stream at PCM prepare time, so [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) creates only the widgets on that stream's path. Teardown keeps a batch op because suspend must sweep every stream the kernel still believes is active, including one whose normal free was skipped by an xrun, and route every such stream back through the same per-widget [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) so the delete-pipeline messages and id releases happen exactly as they would at hw_free.

### The relation to the PCM-side pipeline state

Runtime topology creates and deletes the pipeline container; it does not run it. The created pipeline rests in its uninitialized state until the PCM trigger path drives it, and [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124) is the companion that sends the run-state command to a pipeline this layer already created. The split is clean: [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) emits [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) and records [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139) when [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293) later deletes it, while [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124) moves a created pipeline through running and paused via [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103). The [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) carries the cached [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) field both layers read, but only this runtime topology layer ever sends the create and delete messages.

```
    Pipeline lifecycle: which layer owns each transition
    ──────────────────────────────────────────────────────

         (no pipeline on DSP)
              │  ▲
   runtime ───┤  └─── runtime topology
   topology:  │       widget_free:
   widget_    ▼       GLB_DELETE_PIPELINE
   setup:  ┌──────────────────────────┐
   GLB_    │ SOF_IPC4_PIPE_            │
   CREATE_ │      UNINITIALIZED       │ ◀── cached state both layers read
   PIPELINE└────────────┬─────────────┘
                        │  PCM-side path (ipc4-pcm.c)
                        ▼  GLB_SET_PIPELINE_STATE
            ┌──────────────────────────┐
            │   running  ◀──▶  paused  │   PCM-side owns these edges
            └──────────────────────────┘

    runtime topology: only CREATE_PIPELINE / DELETE_PIPELINE
    PCM-side path    : only SET_PIPELINE_STATE (run / pause)
```
