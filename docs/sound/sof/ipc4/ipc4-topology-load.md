# SOF IPC4 topology load

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

When the ASoC topology loader hands a parsed firmware topology to Sound Open Firmware, the IPC4 load-time layer turns each [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) into a per-widget private structure and pre-builds the DSP module-init message that the runtime setup will later send, and the whole step is driven by one function pointer struct, [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973), a [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) whose [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member points at the per-type table [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925) and indexes it by the widget's [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) to select an [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) callback, a [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), and an [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) callback. The [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447) slot runs [`sof_ipc4_widget_setup_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L621) and allocates a [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), the [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) slot runs [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) and allocates the DAI copier, the [`snd_soc_dapm_scheduler`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L456) slot runs [`sof_ipc4_widget_setup_comp_pipeline()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L926) and allocates a [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), and the [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_src`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L458), and [`snd_soc_dapm_effect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L457) slots run [`sof_ipc4_widget_setup_comp_pga()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L986), [`sof_ipc4_widget_setup_comp_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1043), [`sof_ipc4_widget_setup_comp_src()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1074), and [`sof_ipc4_widget_setup_comp_process()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1200) to allocate [`struct sof_ipc4_gain`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429), [`struct sof_ipc4_mixer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441), [`struct sof_ipc4_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463), and [`struct sof_ipc4_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522). Every setup body parses the pin formats through [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400) and stamps the module header through [`sof_ipc4_widget_setup_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522), and none of them sends IPC; the runtime send is owned by [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) at PCM open.

```
    Topology widget + tokens         ipc_setup (load)          Private struct
    ────────────────────────         ────────────────          + init template
    ─────────────────────────────────────────────────────────────────────────

    struct snd_sof_widget
    ┌─────────────────────────┐
    │ id = snd_soc_dapm_      │   tplg_ipc4_widget_ops[id]
    │      aif_in             │   .ipc_setup ───────────┐
    │ tuples[] (parsed toks)  │                         │
    │ module_info (fw module) │                         ▼
    │ private  ───────────────┼──┐    sof_ipc4_widget_setup_pcm()
    └─────────────────────────┘  │    ┌───────────────────────────────────┐
                                  │    │ kzalloc(sof_ipc4_copier)         │
       widget-type ─▶ ipc_setup   │    │ sof_ipc4_get_audio_fmt():        │
       ───────────────────────    │    │   in/out pin fmts ─▶ available_fmt│
       aif_in/out  copier (pcm)   │    │   base_config (is_pages)          │
       buffer      copier (pcm)   │    │ node_id = SOF_IPC4_NODE_TYPE(..)  │
       dai_in/out  copier (dai)   └───▶│ sof_ipc4_widget_setup_msg():      │
       scheduler   pipeline            │   msg.primary = module id |       │
       pga         gain               │     MOD_INIT_INSTANCE             │
       mixer       mixer              │   msg.extension = core/domain     │
       src         src                └──────────────┬────────────────────┘
       effect      process                           │  (no IPC sent)
                                                      ▼
                                       swidget->private = copier
                                       copier.msg = MOD_INIT_INSTANCE template

       scheduler ─▶ sof_ipc4_widget_setup_comp_pipeline()
       ┌───────────────────────────────────────────────────────┐
       │ kzalloc(sof_ipc4_pipeline)                            │
       │ parse SOF_SCHED_TOKENS ─▶ priority, core_id, lp_mode  │
       │ msg.primary = GLB_CREATE_PIPELINE | priority          │
       │ state = SOF_IPC4_PIPE_UNINITIALIZED                   │
       └───────────────────────────────────────────────────────┘

    Runtime send (at PCM open):
    sof_ipc4_widget_setup() reads swidget->private, sends MOD_INIT_INSTANCE
    or GLB_CREATE_PIPELINE; sof_ipc4_route_setup() sends MOD_BIND.
```

## SUMMARY

Topology load and runtime setup are two phases that share the per-widget private structure but never overlap in time. The generic ASoC topology loader parses the binary into [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) objects with their topology tokens in [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), then calls back into SOF through [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186), which walks [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and runs [`widget_ops[swidget->id].ipc_setup(swidget)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) for every widget. The per-type table is [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925), an array of [`struct sof_ipc_tplg_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) sized [`SND_SOC_DAPM_TYPE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L464) and indexed by [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), and the same table also carries the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) that the parser reads to fill [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) before the setup callback runs.

Each [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) body allocates the IPC4 private structure for its widget kind, parses the tokens into it, and hangs it off [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422). The host and buffer copiers go through [`sof_ipc4_widget_setup_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L621), the DAI copier through [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748), the scheduler through [`sof_ipc4_widget_setup_comp_pipeline()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L926), and the gain, mixer, sample-rate-converter, and generic processing modules through [`sof_ipc4_widget_setup_comp_pga()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L986), [`sof_ipc4_widget_setup_comp_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1043), [`sof_ipc4_widget_setup_comp_src()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1074), and [`sof_ipc4_widget_setup_comp_process()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1200). The two shared helpers do the bulk of the work. [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400) reads the pin-format token sets into the widget's [`struct sof_ipc4_available_audio_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201) and the [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) of the module payload, and [`sof_ipc4_widget_setup_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522) resolves the firmware module by UUID and writes the [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) header into the module's [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32). The scheduler is the exception that pre-builds a [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) header instead and records [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139) as the starting [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156).

The format that the load-time templates carry is the full set of pin formats the topology offers. Choosing one concrete format for a given PCM is a runtime-prepare step, done by [`sof_ipc4_init_input_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1576) and [`sof_ipc4_init_output_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1477) from the prepare ops, and the send of the templates that this page builds is owned by [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103), [`sof_ipc4_widget_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3293), [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472), and [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628), which run at PCM open and are described on the runtime page. On an x86-64 ACPI Meteor Lake or Lunar Lake machine the descriptor that selects IPC4, and therefore [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973), is [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31) or [`lnl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31).

## SPECIFICATIONS

The IPC4 module, pipeline, and gateway concepts the load-time templates encode come from the Intel Audio DSP firmware interface (the Cadence-based Audio DSP shipped on Intel SoC platforms from Tiger Lake and Meteor Lake onward) rather than from a public standard, and the wire layout of the create-module and create-pipeline messages is reproduced as macros in [`include/sound/sof/ipc4/header.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h). The [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and the ASoC topology binary it derives from are Linux kernel software constructs defined by the ASoC topology ABI in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h). The serial-audio formats a DAI copier carries (I2S over SSP, the SoundWire ALH gateway, and PDM over DMIC) are defined by their respective interface standards. The firmware image format and the topology binary themselves are defined by the Sound Open Firmware project, whose public documentation is listed under OTHER SOURCES.

## LINUX KERNEL

### IPC4 topology ops tables (ipc4-topology.c, ipc4-priv.h)

- [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973): the [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) instance for IPC4; its [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member is the load-time per-type table and its [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) is the full IPC4 token catalog; declared as [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h#L102)
- [`'tplg_ipc4_widget_ops':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925): the per-type table of [`struct sof_ipc_tplg_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) indexed by [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423); each populated slot supplies [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), a [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), and the runtime [`ipc_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181)/[`ipc_unprepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) ops
- [`'\<struct sof_ipc_tplg_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221): the IPC-version-independent topology op set; the load-time members are [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) and [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), the runtime members are [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221)
- [`'\<struct sof_ipc_tplg_widget_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181): the per-widget-type op set; its first three members [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), and [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) drive topology load

### Per-widget ipc_setup bodies (ipc4-topology.c)

- [`'\<sof_ipc4_widget_setup_pcm\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L621): ipc_setup for [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447), [`snd_soc_dapm_aif_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L448), and [`snd_soc_dapm_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L455); allocates the host/buffer [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), sets [`gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) from the [`SOF_IPC4_NODE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L56) token (this page calls it the host copier; the brief's "comp_host" maps to this body)
- [`'\<sof_ipc4_widget_setup_comp_dai\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748): ipc_setup for [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) and [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452); allocates the DAI [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), parses [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332)/[`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), and builds the gateway config blob per [`enum sof_ipc_dai_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76)
- [`'\<sof_ipc4_widget_setup_comp_pipeline\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L926): ipc_setup for [`snd_soc_dapm_scheduler`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L456); allocates the [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) and prebuilds its [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) message
- [`'\<sof_ipc4_widget_setup_comp_pga\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L986): ipc_setup for [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430); allocates the [`struct sof_ipc4_gain`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429), defaulting the channel mask to [`SOF_IPC4_GAIN_ALL_CHANNELS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L65) and the initial value to [`SOF_IPC4_VOL_ZERO_DB`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L66)
- [`'\<sof_ipc4_widget_setup_comp_mixer\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1043): ipc_setup for [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428); allocates the [`struct sof_ipc4_mixer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441), which carries only a [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441) and a message
- [`'\<sof_ipc4_widget_setup_comp_src\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1074): ipc_setup for [`snd_soc_dapm_src`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L458); allocates the [`struct sof_ipc4_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463) and records the [`sink_rate`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452) from [`SOF_SRC_TOKENS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/tokens.h)
- [`'\<sof_ipc4_widget_setup_comp_process\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1200): ipc_setup for [`snd_soc_dapm_effect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L457); allocates the [`struct sof_ipc4_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522), reads the init-config type from [`module_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), and sizes the [`ipc_config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522) blob and optional [`struct sof_ipc4_base_module_cfg_ext`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L503)

### Format and message build helpers (ipc4-topology.c)

- [`'\<sof_ipc4_get_audio_fmt\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400): parses the input and output pin-format token sets into the widget's [`struct sof_ipc4_available_audio_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201) and the module payload's [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L317); called by every per-type setup body
- [`'\<sof_ipc4_free_audio_fmt\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L493): releases the pin-format arrays [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400) allocated, called on the error tail of each setup body and from each ipc_free
- [`'\<sof_ipc4_widget_setup_msg\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522): resolves the firmware module by UUID through [`sof_ipc4_widget_set_module_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L507), then writes the module ID and [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) type into the [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header
- [`'\<sof_ipc4_widget_set_module_info\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L507): looks up the loaded firmware module by the widget's UUID and stores it in [`module_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422)
- [`'\<sof_ipc4_init_input_audio_fmt\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1576) / [`'\<sof_ipc4_init_output_audio_fmt\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1477): the runtime-prepare selectors that pick one concrete pin format out of [`available_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201) for a given PCM, called from the prepare ops at stream setup
- [`'\<sof_update_ipc_object\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L56): the token-to-struct decoder every setup body calls to copy a named token set into a destination struct

### IPC4 module and pipeline private types (ipc4-topology.h)

- [`'\<struct sof_ipc4_copier\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332): the host, DAI, and buffer copier private data; wraps the wire payload [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), the parsed [`available_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), the [`dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332)/[`dai_index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), the gateway-attribute blob [`gtw_attr`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), and the module [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332)
- [`'\<struct sof_ipc4_copier_data\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229): the wire-format copier IPC payload, with the [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) input format, the [`out_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229), and the [`gtw_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) gateway node ID
- [`'\<struct sof_ipc4_pipeline\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156): the scheduler widget's private data; holds [`priority`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), [`core_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), and the prebuilt [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156)
- [`'\<struct sof_ipc4_gain\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429): the PGA module private data; the [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429) blob is a [`struct sof_ipc4_gain_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L418) carrying the base config and the [`struct sof_ipc4_gain_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L404)
- [`'\<struct sof_ipc4_mixer\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441): the mixer module private data; carries only a [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441), an [`available_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441), and a message
- [`'\<struct sof_ipc4_src\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463): the sample-rate-converter module private data; the [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463) blob is a [`struct sof_ipc4_src_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452) carrying the base config and the [`sink_rate`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452)
- [`'\<struct sof_ipc4_process\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522): the generic processing module private data; carries the [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522), the optional [`base_config_ext`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522), and a variable-length [`ipc_config_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522) blob
- [`'\<struct sof_ipc4_available_audio_format\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201): the parsed input and output pin formats and their counts, filled by [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400)
- [`'\<struct sof_ipc4_gtw_attributes\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L242): the gateway attributes bit field a copier appends as its config blob
- [`'\<struct sof_copier_gateway_cfg\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L215): the gateway node ID, DMA buffer size, and trailing config blob inside [`struct sof_ipc4_copier_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229)

### SOF core glue and the load-time caller (sof-audio.h, topology.c)

- [`'\<struct snd_sof_widget\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422): the SOF view of a DAPM widget; the [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the parsed tokens, [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the IPC4 structure the setup body builds, and [`module_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the loaded firmware module
- [`'\<struct sof_ipc4_msg\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32): the IPC4 message; a [`primary`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) and [`extension`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header word pair plus a payload pointer and size, embedded in every per-widget private struct
- [`'\<struct sof_ipc4_base_module_cfg\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L317): the common module config header at the front of every module payload; its [`is_pages`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L317) and audio-format fields are filled at load and prepare
- [`'\<sof_complete\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186): the ASoC topology-loader completion callback; walks [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and runs each widget's [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181)
- [`'\<sof_widget_ready\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409): the per-widget create callback; reads the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) from the table and parses the tokens into [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) before [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186) runs the setup
- [`'\<sof_ipc4_widget_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103): the runtime [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op that sends the templates this page builds; owned by the runtime page

### IPC4 message header values (ipc4/header.h)

- [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301): the [`enum sof_ipc4_module_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L300) value (0) that creates a module instance; written into every module template by [`sof_ipc4_widget_setup_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522)
- [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101): the global message type the scheduler template carries
- [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139): the initial [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) a freshly built pipeline records
- [`SOF_IPC4_MSG_TYPE_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L162): packs the message type into the primary header word
- [`SOF_IPC4_MSG_TARGET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L151): selects the module or firmware-generic message space, set to [`SOF_IPC4_MODULE_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L83) for a module and [`SOF_IPC4_FW_GEN_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L80) for a pipeline
- [`SOF_IPC4_MOD_EXT_CORE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L349): packs the target DSP core into the module template's extension word
- [`SOF_IPC4_GLB_PIPE_PRIORITY()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L176): packs the pipeline priority into the create-pipeline primary word

### x86-64 ACPI worked example (pci-mtl.c, pci-lnl.c)

- [`'mtl_desc':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31): the Meteor Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) with [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L40) set to `BIT(SOF_IPC_TYPE_4)`, which selects the IPC4 ops and therefore [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973)
- [`'lnl_desc':'sound/soc/sof/intel/pci-lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31): the Lunar Lake descriptor, also IPC4-only, naming the [`intel/sof-ipc4-tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L51) topology directory the [`.tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L51) file is loaded from

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget and route model whose [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) is the index into the per-type op table
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the front-end PCM and back-end DAI are separate, matching the host copier and DAI copier split
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component and card model whose topology loader invokes the SOF topology ops
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the ALH DAI copier gateway blob feeds on Meteor Lake

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware introduction and architecture](https://thesofproject.github.io/latest/introduction/index.html)
- [Sound Open Firmware: IPC4 ABI and topology](https://thesofproject.github.io/latest/introduction/ipc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The objects below are the per-widget private structures the load phase allocates and the two ops structures that drive it. Each private structure has one creator, the [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) callback for its widget type, and is held in [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until the matching [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) releases it, so a reader can follow a link from the per-type table to the structure it builds and back to the message template it leaves for the runtime send. The two ops structures are statically defined, one per kernel image, and the table is selected by the platform's IPC type at probe.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) (host/buffer) | [`sof_ipc4_widget_setup_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L621) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) (DAI) | [`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) | [`dai->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) until ipc_free |
| [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) | [`sof_ipc4_widget_setup_comp_pipeline()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L926) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc4_gain`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429) | [`sof_ipc4_widget_setup_comp_pga()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L986) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc4_mixer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441) | [`sof_ipc4_widget_setup_comp_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1043) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc4_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463) | [`sof_ipc4_widget_setup_comp_src()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1074) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc4_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522) | [`sof_ipc4_widget_setup_comp_process()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1200) | [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) until ipc_free |
| [`struct sof_ipc_tplg_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) table [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925) | static per kernel image | whole driver lifetime |
| [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) instance [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) | static per kernel image | whole driver lifetime |

### The per-type table and the load-time entry points

The load-time half of [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) is the [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member, which points at [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925), and the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member, which is the full IPC4 token catalog. For each widget, [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) reads the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) out of the matching table slot and parses the topology private data into [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), then [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186) runs the slot's [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) to turn those tokens into the private structure. The runtime members [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) are not exercised here.

### ipc_setup and ipc_free

[`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) takes one [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), allocates the IPC4 structure for its widget kind, parses the tokens, and stores the structure on [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422). [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) is the inverse, releasing the pin-format arrays through [`sof_ipc4_free_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L493) and then the structure itself; for the copier it is [`sof_ipc4_widget_free_comp_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L733), and for the pipeline it is [`sof_ipc4_widget_free_comp_pipeline()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L502). Neither op sends IPC, so the firmware is untouched by the load phase.

### token_list

[`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) is an array of [`enum sof_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/tokens.h) IDs naming the token sets the parser reads for a widget kind. The copier types share [`copier_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3865), the scheduler uses [`pipeline_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3877), and the gain, mixer, src, and process types use [`pga_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3882), [`mixer_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3891), [`src_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3899), and [`process_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3917), each of which includes the audio-format token sets so [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400) finds its tuples.

## DETAILS

### The two phases and where load runs

The IPC4 topology layer separates allocation from instantiation, and this page is the allocation half. Topology load creates a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) for every widget in the topology binary and runs the matching [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) callback, which allocates the IPC4 structure, parses the topology tokens into it, pre-builds the create-module or create-pipeline header, and hangs the structure off [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422). No IPC is sent. At PCM open the runtime op [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) reads that structure back, selects a concrete audio format, and sends the prepared message; that send is the runtime page's subject.

[`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is the carrier that ties the DAPM widget, the parsed tokens, the loaded firmware module, and the IPC4 private structure together:

```c
/* sound/soc/sof/sof-audio.h:422 */
struct snd_sof_widget {
	struct snd_soc_component *scomp;
	int comp_id;
	int pipeline_id;
	...
	int core;
	int id; /* id is the DAPM widget type */
	...
	int instance_id;
	...
	struct snd_soc_dapm_widget *widget;
	struct list_head list;	/* list in sdev widget list */
	struct snd_sof_pipeline *spipe;
	void *module_info;
	...
	int num_tuples;
	struct snd_sof_tuple *tuples;
	...
};
```

The [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) and is the index into the per-type table. [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the tokens the setup body consumes, [`module_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) holds the loaded firmware module descriptor whose ID becomes the message header, and the [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) field (declared later in the struct) holds the IPC4 structure the setup body allocates.

The load-time setup runs from [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186), the completion callback the generic ASoC loader invokes once every widget, control, and route from the topology file has been created. It walks the pipelines, runs the scheduler widget's [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) first, then the non-scheduler widgets of that pipeline:

```c
/* sound/soc/sof/topology.c:2222 */
	/* Update the scheduler widget's IPC structure */
	if (widget_ops && widget_ops[pipe_widget->id].ipc_setup) {
		ret = widget_ops[pipe_widget->id].ipc_setup(pipe_widget);
		...
	}

	/* set the pipeline and update the IPC structure for the non scheduler widgets */
	list_for_each_entry(swidget, &sdev->widget_list, list)
		if (swidget->widget->id != snd_soc_dapm_scheduler &&
		    swidget->pipeline_id == pipe_widget->pipeline_id) {
			ret = sof_set_widget_pipeline(sdev, spipe, swidget);
			...
			if (widget_ops && widget_ops[swidget->id].ipc_setup) {
				ret = widget_ops[swidget->id].ipc_setup(swidget);
				...
			}
		}
```

The `widget_ops` local is the IPC4 per-type table reached through [`sof_ipc_get_ops(sdev, tplg)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541), so the same generic loader serves IPC3 and IPC4 and the indexing by [`swidget->id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) picks the right body.

### The ops tables: ipc4_tplg_ops and tplg_ipc4_widget_ops

The SOF core reaches IPC4 through [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973). Its load-time members are the per-type table and the token catalog; the rest are the runtime ops the sibling page documents:

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
	...
};
```

The per-type table [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925) is a fixed-size array of [`struct sof_ipc_tplg_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) indexed by [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423). Each designated initializer names the [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) body, the [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) body, the token list and its size, and the optional prepare/unprepare ops:

```c
/* sound/soc/sof/ipc4-topology.c:3925 */
static const struct sof_ipc_tplg_widget_ops tplg_ipc4_widget_ops[SND_SOC_DAPM_TYPE_COUNT] = {
	[snd_soc_dapm_aif_in] =  {sof_ipc4_widget_setup_pcm, sof_ipc4_widget_free_comp_pcm,
				  copier_token_list, ARRAY_SIZE(copier_token_list),
				  NULL, sof_ipc4_prepare_copier_module,
				  sof_ipc4_unprepare_copier_module},
	...
	[snd_soc_dapm_dai_in] = {sof_ipc4_widget_setup_comp_dai, sof_ipc4_widget_free_comp_dai,
				 copier_token_list, ARRAY_SIZE(copier_token_list), NULL,
				 sof_ipc4_prepare_copier_module,
				 sof_ipc4_unprepare_copier_module},
	...
	[snd_soc_dapm_scheduler] = {sof_ipc4_widget_setup_comp_pipeline,
				    sof_ipc4_widget_free_comp_pipeline,
				    pipeline_token_list, ARRAY_SIZE(pipeline_token_list), NULL,
				    NULL, NULL},
	[snd_soc_dapm_pga] = {sof_ipc4_widget_setup_comp_pga, sof_ipc4_widget_free_comp_pga,
			      pga_token_list, ARRAY_SIZE(pga_token_list), NULL,
			      sof_ipc4_prepare_gain_module,
			      NULL},
	[snd_soc_dapm_mixer] = {sof_ipc4_widget_setup_comp_mixer, sof_ipc4_widget_free_comp_mixer,
				mixer_token_list, ARRAY_SIZE(mixer_token_list),
				NULL, sof_ipc4_prepare_mixer_module,
				NULL},
	[snd_soc_dapm_src] = {sof_ipc4_widget_setup_comp_src, sof_ipc4_widget_free_comp_src,
				src_token_list, ARRAY_SIZE(src_token_list),
				NULL, sof_ipc4_prepare_src_module,
				NULL},
	[snd_soc_dapm_effect] = {sof_ipc4_widget_setup_comp_process,
				sof_ipc4_widget_free_comp_process,
				process_token_list, ARRAY_SIZE(process_token_list),
				NULL, sof_ipc4_prepare_process_module,
				NULL},
};
```

The slot layout is the [`struct sof_ipc_tplg_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) definition, whose first three members are the two load-time function pointers and the token list that the parser reads:

```c
/* sound/soc/sof/sof-audio.h:181 */
struct sof_ipc_tplg_widget_ops {
	int (*ipc_setup)(struct snd_sof_widget *swidget);
	void (*ipc_free)(struct snd_sof_widget *swidget);
	enum sof_tokens *token_list;
	int token_list_size;
	int (*bind_event)(struct snd_soc_component *scomp, struct snd_sof_widget *swidget,
			  u16 event_type);
	int (*ipc_prepare)(struct snd_sof_widget *swidget,
			   struct snd_pcm_hw_params *fe_params,
			   struct snd_sof_platform_stream_params *platform_params,
			   struct snd_pcm_hw_params *source_params, int dir);
	void (*ipc_unprepare)(struct snd_sof_widget *swidget);
};
```

Indexing this slot by the widget type picks one body and token list per row, and the parser reads the token list before the setup body runs:

```
    tplg_ipc4_widget_ops[swidget->id]: widget type selects the load body
    ────────────────────────────────────────────────────────────────────

    enum snd_soc_dapm_type    ipc_setup body              token_list
    ──────────────────────    ───────────────────────     ───────────────
    snd_soc_dapm_aif_in   ─▶  setup_pcm           ─▶ host copier_token_list
    snd_soc_dapm_aif_out  ─▶  setup_pcm           ─▶ buf  copier_token_list
    snd_soc_dapm_buffer   ─▶  setup_pcm           ─▶      copier_token_list
    snd_soc_dapm_dai_in   ─▶  setup_comp_dai      ─▶  DAI  copier_token_list
    snd_soc_dapm_dai_out  ─▶  setup_comp_dai      ─▶  DAI  copier_token_list
    snd_soc_dapm_scheduler ▶  setup_comp_pipeline ─▶ pipeline_token_list
    snd_soc_dapm_pga      ─▶  setup_comp_pga      ─▶      pga_token_list
    snd_soc_dapm_mixer    ─▶  setup_comp_mixer    ─▶      mixer_token_list
    snd_soc_dapm_src      ─▶  setup_comp_src      ─▶      src_token_list
    snd_soc_dapm_effect   ─▶  setup_comp_process  ─▶      process_token_list

    sof_widget_ready() reads token_list ─▶ parses tuples
    sof_complete() then runs ipc_setup ─▶ swidget->private
```

### The generic build model: get_audio_fmt then setup_msg

Every per-type setup body follows the same shape. It allocates the private structure, calls [`sof_ipc4_get_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L400) to parse the pin formats and the base config, parses any module-specific tokens with [`sof_update_ipc_object()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L56), and calls [`sof_ipc4_widget_setup_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522) to stamp the create-module header. The format parser is shared by all module types and fills the widget's [`struct sof_ipc4_available_audio_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201) plus the [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L317) of the module payload:

```c
/* sound/soc/sof/ipc4-topology.c:400 */
static int sof_ipc4_get_audio_fmt(struct snd_soc_component *scomp,
				  struct snd_sof_widget *swidget,
				  struct sof_ipc4_available_audio_format *available_fmt,
				  struct sof_ipc4_base_module_cfg *module_base_cfg)
{
	struct sof_ipc4_pin_format *in_format = NULL;
	struct sof_ipc4_pin_format *out_format;
	int ret;

	ret = sof_update_ipc_object(scomp, available_fmt,
				    SOF_AUDIO_FMT_NUM_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(*available_fmt), 1);
	...
	if (!available_fmt->num_input_formats && !available_fmt->num_output_formats) {
		dev_err(scomp->dev, "No input/output pin formats set in topology\n");
		return -EINVAL;
	}
	...
	/* set is_pages in the module's base_config */
	ret = sof_update_ipc_object(scomp, module_base_cfg, SOF_COMP_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(*module_base_cfg), 1);
	...
	if (available_fmt->num_input_formats) {
		in_format = kzalloc_objs(*in_format,
					 available_fmt->num_input_formats);
		...
		available_fmt->input_pin_fmts = in_format;

		ret = sof_update_ipc_object(scomp, in_format,
					    SOF_IN_AUDIO_FORMAT_TOKENS, swidget->tuples,
					    swidget->num_tuples, sizeof(*in_format),
					    available_fmt->num_input_formats);
		...
	}

	if (available_fmt->num_output_formats) {
		out_format = kzalloc_objs(*out_format,
					  available_fmt->num_output_formats);
		...
		ret = sof_update_ipc_object(scomp, out_format,
					    SOF_OUT_AUDIO_FORMAT_TOKENS, swidget->tuples,
					    swidget->num_tuples, sizeof(*out_format),
					    available_fmt->num_output_formats);
		...
		available_fmt->output_pin_fmts = out_format;
		...
	}

	return 0;
	...
}
```

The parser allocates one [`struct sof_ipc4_pin_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L188) per declared input pin and one per declared output pin and stores both arrays in the [`struct sof_ipc4_available_audio_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201). According to the comment on [`sof_ipc4_free_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L493) the function releases exactly this memory:

```c
/* sound/soc/sof/ipc4-topology.h:201 */
struct sof_ipc4_available_audio_format {
	struct sof_ipc4_pin_format *output_pin_fmts;
	struct sof_ipc4_pin_format *input_pin_fmts;
	u32 num_input_formats;
	u32 num_output_formats;
};
```

The header stamp resolves the firmware module by the widget's UUID and writes the module ID together with the [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) type and the target core into the message words:

```c
/* sound/soc/sof/ipc4-topology.c:522 */
static int sof_ipc4_widget_setup_msg(struct snd_sof_widget *swidget, struct sof_ipc4_msg *msg)
{
	struct sof_ipc4_fw_module *fw_module;
	uint32_t type;
	int ret;

	ret = sof_ipc4_widget_set_module_info(swidget);
	if (ret)
		return ret;

	fw_module = swidget->module_info;

	msg->primary = fw_module->man4_module_entry.id;
	msg->primary |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_MOD_INIT_INSTANCE);
	msg->primary |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	msg->primary |= SOF_IPC4_MSG_TARGET(SOF_IPC4_MODULE_MSG);

	msg->extension = SOF_IPC4_MOD_EXT_CORE_ID(swidget->core);

	switch (swidget->comp_domain) {
	case SOF_COMP_DOMAIN_LL:
		type = 0;
		break;
	case SOF_COMP_DOMAIN_DP:
		type = 1;
		break;
	default:
		type = (fw_module->man4_module_entry.type & SOF_IPC4_MODULE_DP) ? 1 : 0;
		break;
	}
	msg->extension |= SOF_IPC4_MOD_EXT_DOMAIN(type);

	return 0;
}
```

The message it fills is a [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32), a primary and extension header-word pair plus a payload pointer that the runtime op points at the per-widget wire payload before sending:

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

At this point the template is complete and idle. The instance ID and pipeline ID that the runtime send stamps into the extension are not known until PCM open, which is why the load-time header carries only the module ID, the type, the core, and the domain.

```
    Tokens feed two shared helpers into the private struct fields
    ─────────────────────────────────────────────────────────────

    swidget->tuples (parsed topology tokens)
      │
      ├─ SOF_AUDIO_FMT_NUM_TOKENS ──┐
      ├─ SOF_IN_AUDIO_FORMAT_TOKENS ┤   sof_ipc4_get_audio_fmt()
      ├─ SOF_OUT_AUDIO_FORMAT_TOKENS┼─▶ ┌──────────────────────────────┐
      ├─ SOF_COMP_TOKENS (is_pages) │   │ available_fmt.input_pin_fmts │
      │                             │   │ available_fmt.output_pin_fmts│
      │                             └─▶ │ base_config.is_pages         │
      │                                 └──────────────────────────────┘
      │
      └─ (widget UUID) ─────────────▶   sof_ipc4_widget_setup_msg()
                                        ┌──────────────────────────────┐
         module_info.man4_module_entry  │ msg.primary  : module id +   │
                          .id ────────▶ │    MOD_INIT_INSTANCE         │
         swidget->core ──────────────▶  │ msg.extension : core + domain│
                                        └──────────────────────────────┘
```

### ipc_setup builds the copier for a host AIF widget

[`sof_ipc4_widget_setup_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L621) is the ipc_setup body for the host AIF and buffer widgets, and it is the body the brief refers to as the host-copier setup. It allocates a [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332), parses the input audio format into [`available_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) and [`data.base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229), and for an AIF widget parses the host node-type token:

```c
/* sound/soc/sof/ipc4-topology.c:621 */
static int sof_ipc4_widget_setup_pcm(struct snd_sof_widget *swidget)
{
	struct sof_ipc4_available_audio_format *available_fmt;
	struct snd_soc_component *scomp = swidget->scomp;
	struct sof_ipc4_copier *ipc4_copier;
	struct snd_sof_pcm *spcm;
	int node_type = 0;
	int ret, dir;

	ipc4_copier = kzalloc_obj(*ipc4_copier);
	if (!ipc4_copier)
		return -ENOMEM;

	swidget->private = ipc4_copier;
	available_fmt = &ipc4_copier->available_fmt;
	...
	ret = sof_ipc4_get_audio_fmt(scomp, swidget, available_fmt,
				     &ipc4_copier->data.base_config);
	if (ret)
		goto free_copier;

	/*
	 * This callback is used by host copier and module-to-module copier,
	 * and only host copier needs to set gtw_cfg.
	 */
	if (!WIDGET_IS_AIF(swidget->id))
		goto skip_gtw_cfg;

	ret = sof_update_ipc_object(scomp, &node_type,
				    SOF_COPIER_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(node_type), 1);
	...
```

After parsing the node type it allocates the gateway-attribute blob, sets the gateway config length, and writes the node ID. The AIF case encodes the node type with [`SOF_IPC4_NODE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L56); the buffer case marks the node invalid because a buffer copier has no DMA gateway:

```c
/* sound/soc/sof/ipc4-topology.c:701 */
	switch (swidget->id) {
	case snd_soc_dapm_aif_in:
	case snd_soc_dapm_aif_out:
		ipc4_copier->data.gtw_cfg.node_id = SOF_IPC4_NODE_TYPE(node_type);
		break;
	case snd_soc_dapm_buffer:
		ipc4_copier->data.gtw_cfg.node_id = SOF_IPC4_INVALID_NODE_ID;
		ipc4_copier->ipc_config_size = 0;
		break;
	default:
		dev_err(scomp->dev, "invalid widget type %d\n", swidget->id);
		ret = -EINVAL;
		goto free_gtw_attr;
	}

	/* set up module info and message header */
	ret = sof_ipc4_widget_setup_msg(swidget, &ipc4_copier->msg);
	if (ret)
		goto free_gtw_attr;

	return 0;
```

The copier private structure it builds is [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332). The [`data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) member is the wire payload, [`gtw_attr`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) is the gateway-attribute config blob the copier appends, and [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) is the header the runtime op sends:

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

The wire payload [`struct sof_ipc4_copier_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) carries the input audio format and the gateway configuration the DSP needs to attach the DMA gateway:

```c
/* sound/soc/sof/ipc4-topology.h:229 */
struct sof_ipc4_copier_data {
	struct sof_ipc4_base_module_cfg base_config;
	struct sof_ipc4_audio_format out_format;
	uint32_t copier_feature_mask;
	struct sof_copier_gateway_cfg gtw_cfg;
};
```

The gateway node ID is a [`SOF_IPC4_NODE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L56)-encoded value in the [`struct sof_copier_gateway_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L215), and the gateway-attribute blob that follows it is the [`struct sof_ipc4_gtw_attributes`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L242) bit field:

```c
/* sound/soc/sof/ipc4-topology.h:242 */
struct sof_ipc4_gtw_attributes {
	uint32_t lp_buffer_alloc : 1;
	uint32_t alloc_from_reg_file : 1;
	uint32_t rsvd : 30;
};
```

That attributes blob hangs off gtw_attr inside the copier, which wraps the wire payload (itself nesting the gateway config) beside the format set and the MOD_INIT_INSTANCE message:

```
    struct sof_ipc4_copier nesting (host copier private data)
    ──────────────────────────────────────────────────────────

    struct sof_ipc4_copier
    ┌──────────────────────────────────────────────────────┐
    │ data : struct sof_ipc4_copier_data                   │
    │   ┌────────────────────────────────────────────────┐ │
    │   │ base_config : sof_ipc4_base_module_cfg (in fmt)│ │
    │   │ out_format  : sof_ipc4_audio_format            │ │
    │   │ copier_feature_mask                            │ │
    │   │ gtw_cfg : struct sof_copier_gateway_cfg        │ │
    │   │   ┌──────────────────────────────────────────┐ │ │
    │   │   │ node_id = SOF_IPC4_NODE_TYPE(node_type)  │ │ │
    │   │   │ dma_buffer_size                          │ │ │
    │   │   │ config_length / config_data[]            │ │ │
    │   │   └──────────────────────────────────────────┘ │ │
    │   └────────────────────────────────────────────────┘ │
    │ available_fmt : sof_ipc4_available_audio_format      │
    │ gtw_attr ─▶ struct sof_ipc4_gtw_attributes (blob)    │
    │ msg : struct sof_ipc4_msg  (MOD_INIT_INSTANCE)       │
    └──────────────────────────────────────────────────────┘
```

### ipc_setup builds the DAI copier and its gateway blob

[`sof_ipc4_widget_setup_comp_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L748) is the ipc_setup body for the DAI widgets. It allocates the same [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) but hangs it off [`dai->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) rather than the widget, parses the DAI type and index tokens, sets the node ID, and then branches on [`ipc4_copier->dai_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) to build the per-interface gateway blob:

```c
/* sound/soc/sof/ipc4-topology.c:748 */
static int sof_ipc4_widget_setup_comp_dai(struct snd_sof_widget *swidget)
{
	...
	struct snd_sof_dai *dai = swidget->private;
	struct sof_ipc4_copier *ipc4_copier;
	...
	ipc4_copier = kzalloc_obj(*ipc4_copier);
	if (!ipc4_copier)
		return -ENOMEM;

	available_fmt = &ipc4_copier->available_fmt;
	...
	ret = sof_ipc4_get_audio_fmt(scomp, swidget, available_fmt,
				     &ipc4_copier->data.base_config);
	if (ret)
		goto free_copier;

	ret = sof_update_ipc_object(scomp, &node_type,
				    SOF_COPIER_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(node_type), 1);
	...
	ret = sof_update_ipc_object(scomp, ipc4_copier,
				    SOF_DAI_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(u32), 1);
	...
	dai->type = ipc4_copier->dai_type;
	ipc4_copier->data.gtw_cfg.node_id = SOF_IPC4_NODE_TYPE(node_type);
	...
```

The DAI-type switch handles each interface separately. The [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) case counts the aggregated SoundWire ALH endpoints by walking the widget's source paths and the device's other ALH DAIs, then allocates the ALH config blob:

```c
/* sound/soc/sof/ipc4-topology.c:806 */
	switch (ipc4_copier->dai_type) {
	case SOF_DAI_INTEL_ALH:
	{
		struct sof_ipc4_alh_configuration_blob *blob;
		struct snd_soc_dapm_path *p;
		struct snd_sof_widget *w;
		int src_num = 0;

		snd_soc_dapm_widget_for_each_source_path(swidget->widget, p)
			src_num++;
		...
	}
```

The DAI copier shares its [`msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) header build with [`sof_ipc4_widget_setup_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L522) like the host copier, so the only difference between the two copier paths is the gateway node and the config blob. The runtime gateway node index for HDA and ALH is written later by [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628), which the runtime page covers.

### ipc_setup builds the pipeline and pre-builds its create message

[`sof_ipc4_widget_setup_comp_pipeline()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L926) is the scheduler widget's ipc_setup, and it is the one body that builds a pipeline container rather than a module. It allocates a [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), parses the scheduler tokens into it, records the target core on the pipeline, and pre-builds the [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) header:

```c
/* sound/soc/sof/ipc4-topology.c:926 */
static int sof_ipc4_widget_setup_comp_pipeline(struct snd_sof_widget *swidget)
{
	struct snd_soc_component *scomp = swidget->scomp;
	struct sof_ipc4_pipeline *pipeline;
	struct snd_sof_pipeline *spipe = swidget->spipe;
	int ret;

	pipeline = kzalloc_obj(*pipeline);
	if (!pipeline)
		return -ENOMEM;

	ret = sof_update_ipc_object(scomp, pipeline, SOF_SCHED_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(*pipeline), 1);
	...
	swidget->core = pipeline->core_id;
	spipe->core_mask |= BIT(pipeline->core_id);
	if (pipeline->direction_valid) {
		spipe->direction = pipeline->direction;
		spipe->direction_valid = true;
	}

	if (pipeline->use_chain_dma) {
		dev_dbg(scomp->dev, "Set up chain DMA for %s\n", swidget->widget->name);
		swidget->private = pipeline;
		return 0;
	}
	...
	swidget->private = pipeline;

	pipeline->msg.primary = SOF_IPC4_GLB_PIPE_PRIORITY(pipeline->priority);
	pipeline->msg.primary |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_CREATE_PIPELINE);
	pipeline->msg.primary |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	pipeline->msg.primary |= SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG);

	pipeline->msg.extension = pipeline->lp_mode;
	pipeline->msg.extension |= SOF_IPC4_GLB_PIPE_EXT_CORE_ID(pipeline->core_id);
	pipeline->state = SOF_IPC4_PIPE_UNINITIALIZED;

	return 0;
err:
	kfree(pipeline);
	return ret;
}
```

The header targets [`SOF_IPC4_FW_GEN_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L80) rather than a module, because a pipeline is a firmware-generic object and not a module instance, and the [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) is set to [`SOF_IPC4_PIPE_UNINITIALIZED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L139) so the runtime trigger machinery knows the pipeline has not been created on the DSP yet. The structure it fills is [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156):

```c
/* sound/soc/sof/ipc4-topology.h:156 */
struct sof_ipc4_pipeline {
	uint32_t priority;
	uint32_t lp_mode;
	uint32_t mem_usage;
	uint32_t core_id;
	int state;
	bool use_chain_dma;
	struct sof_ipc4_msg msg;
	bool skip_during_fe_trigger;
	bool direction_valid;
	u32 direction;
};
```

When the scheduler carries the [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) attribute the body returns early without building the create-pipeline header, because a chained-DMA pipeline is driven by a different runtime message.

```
    SOF_SCHED_TOKENS ─▶ sof_ipc4_pipeline fields ─▶ create message words
    ───────────────────────────────────────────────────────────────────

    parsed field            packs into          msg word
    ──────────────────      ────────────────    ──────────────────────
    priority         ──▶ GLB_PIPE_PRIORITY  ──▶ msg.primary
    (const)          ──▶ GLB_CREATE_PIPELINE──▶ msg.primary
    (const)          ──▶ TARGET(FW_GEN_MSG) ──▶ msg.primary
    lp_mode          ─────────────────────────▶ msg.extension
    core_id          ──▶ GLB_PIPE_EXT_CORE_ID──▶ msg.extension

    swidget->core   = core_id ;  spipe->core_mask gets BIT(core_id)
    state           = SOF_IPC4_PIPE_UNINITIALIZED
    use_chain_dma set ─▶ return early, no create-pipeline header built
```

### ipc_setup builds the gain, mixer, src, and process modules

The four remaining module types follow the generic build model with module-specific tokens. The gain body allocates a [`struct sof_ipc4_gain`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L429), seeds the channel mask and initial value, parses the audio format and the gain tokens, then stamps the module header:

```c
/* sound/soc/sof/ipc4-topology.c:986 */
static int sof_ipc4_widget_setup_comp_pga(struct snd_sof_widget *swidget)
{
	struct snd_soc_component *scomp = swidget->scomp;
	struct sof_ipc4_gain *gain;
	int ret;

	gain = kzalloc_obj(*gain);
	if (!gain)
		return -ENOMEM;

	swidget->private = gain;

	gain->data.params.channels = SOF_IPC4_GAIN_ALL_CHANNELS_MASK;
	gain->data.params.init_val = SOF_IPC4_VOL_ZERO_DB;

	ret = sof_ipc4_get_audio_fmt(scomp, swidget, &gain->available_fmt, &gain->data.base_config);
	if (ret)
		goto err;

	ret = sof_update_ipc_object(scomp, &gain->data.params, SOF_GAIN_TOKENS,
				    swidget->tuples, swidget->num_tuples, sizeof(gain->data), 1);
	...
	ret = sof_ipc4_widget_setup_msg(swidget, &gain->msg);
	if (ret)
		goto err;

	sof_ipc4_widget_update_kcontrol_module_id(swidget);

	return 0;
err:
	sof_ipc4_free_audio_fmt(&gain->available_fmt);
	kfree(gain);
	swidget->private = NULL;
	return ret;
}
```

The gain private structure wraps a [`struct sof_ipc4_gain_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L418) wire blob, which is the base config followed by a [`struct sof_ipc4_gain_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L404):

```c
/* sound/soc/sof/ipc4-topology.h:429 */
struct sof_ipc4_gain {
	struct sof_ipc4_gain_data data;
	struct sof_ipc4_available_audio_format available_fmt;
	struct sof_ipc4_msg msg;
};
```

The mixer body is the shortest, because a mixer carries no module-specific parameters beyond its base config. It allocates a [`struct sof_ipc4_mixer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441), parses the audio format, and stamps the header:

```c
/* sound/soc/sof/ipc4-topology.c:1043 */
static int sof_ipc4_widget_setup_comp_mixer(struct snd_sof_widget *swidget)
{
	struct snd_soc_component *scomp = swidget->scomp;
	struct sof_ipc4_mixer *mixer;
	int ret;
	...
	mixer = kzalloc_obj(*mixer);
	if (!mixer)
		return -ENOMEM;

	swidget->private = mixer;

	ret = sof_ipc4_get_audio_fmt(scomp, swidget, &mixer->available_fmt,
				     &mixer->base_config);
	if (ret)
		goto err;

	ret = sof_ipc4_widget_setup_msg(swidget, &mixer->msg);
	if (ret)
		goto err;

	return 0;
err:
	sof_ipc4_free_audio_fmt(&mixer->available_fmt);
	kfree(mixer);
	swidget->private = NULL;
	return ret;
}
```

The [`struct sof_ipc4_mixer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L441) reflects that minimal payload, a base config, the available format, and the message:

```c
/* sound/soc/sof/ipc4-topology.h:441 */
struct sof_ipc4_mixer {
	struct sof_ipc4_base_module_cfg base_config;
	struct sof_ipc4_available_audio_format available_fmt;
	struct sof_ipc4_msg msg;
};
```

The sample-rate-converter body allocates a [`struct sof_ipc4_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463), parses the SRC tokens to record the [`sink_rate`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452), and adds the widget's core to the pipeline mask:

```c
/* sound/soc/sof/ipc4-topology.c:1074 */
static int sof_ipc4_widget_setup_comp_src(struct snd_sof_widget *swidget)
{
	struct snd_soc_component *scomp = swidget->scomp;
	struct snd_sof_pipeline *spipe = swidget->spipe;
	struct sof_ipc4_src *src;
	int ret;
	...
	src = kzalloc_obj(*src);
	if (!src)
		return -ENOMEM;

	swidget->private = src;

	ret = sof_ipc4_get_audio_fmt(scomp, swidget, &src->available_fmt,
				     &src->data.base_config);
	if (ret)
		goto err;

	ret = sof_update_ipc_object(scomp, &src->data, SOF_SRC_TOKENS, swidget->tuples,
				    swidget->num_tuples, sizeof(*src), 1);
	...
	spipe->core_mask |= BIT(swidget->core);

	dev_dbg(scomp->dev, "SRC sink rate %d\n", src->data.sink_rate);

	ret = sof_ipc4_widget_setup_msg(swidget, &src->msg);
	if (ret)
		goto err;

	return 0;
err:
	sof_ipc4_free_audio_fmt(&src->available_fmt);
	kfree(src);
	swidget->private = NULL;
	return ret;
}
```

The [`struct sof_ipc4_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L463) wraps a [`struct sof_ipc4_src_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452) wire blob, which is the base config plus the [`sink_rate`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L452):

```c
/* sound/soc/sof/ipc4-topology.h:463 */
struct sof_ipc4_src {
	struct sof_ipc4_src_data data;
	struct sof_ipc4_available_audio_format available_fmt;
	struct sof_ipc4_msg msg;
};
```

The generic processing body parses one extra thing the other modules do not, the init-config type that decides whether a base-config extension carrying the pin formats is appended. [`sof_ipc4_widget_setup_comp_process()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1200) allocates a [`struct sof_ipc4_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522), parses the format, stamps the header, reads the init-config type out of the firmware module info, and sizes the config blob accordingly:

```c
/* sound/soc/sof/ipc4-topology.c:1200 */
static int sof_ipc4_widget_setup_comp_process(struct snd_sof_widget *swidget)
{
	...
	struct sof_ipc4_process *process;
	void *cfg;
	int ret;

	process = kzalloc_obj(*process);
	if (!process)
		return -ENOMEM;

	swidget->private = process;

	ret = sof_ipc4_get_audio_fmt(scomp, swidget, &process->available_fmt,
				     &process->base_config);
	if (ret)
		goto err;

	ret = sof_ipc4_widget_setup_msg(swidget, &process->msg);
	if (ret)
		goto err;

	/* parse process init module payload config type from module info */
	fw_module = swidget->module_info;
	process->init_config = FIELD_GET(SOF_IPC4_MODULE_INIT_CONFIG_MASK,
					 fw_module->man4_module_entry.type);

	process->ipc_config_size = sizeof(struct sof_ipc4_base_module_cfg);

	/* allocate memory for base config extension if needed */
	if (process->init_config == SOF_IPC4_MODULE_INIT_CONFIG_TYPE_BASE_CFG_WITH_EXT) {
		struct sof_ipc4_base_module_cfg_ext *base_cfg_ext;
		u32 ext_size = struct_size(base_cfg_ext, pin_formats,
					   size_add(swidget->num_input_pins,
						    swidget->num_output_pins));

		base_cfg_ext = kzalloc(ext_size, GFP_KERNEL);
		...
		base_cfg_ext->num_input_pin_fmts = swidget->num_input_pins;
		base_cfg_ext->num_output_pin_fmts = swidget->num_output_pins;
		process->base_config_ext = base_cfg_ext;
		process->base_config_ext_size = ext_size;
		process->ipc_config_size += ext_size;
	}

	cfg = kzalloc(process->ipc_config_size, GFP_KERNEL);
	...
	process->ipc_config_data = cfg;
	...
}
```

The [`struct sof_ipc4_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L522) holds both the fixed base config and the optional extension, plus the variable-length config blob the runtime send transmits:

```c
/* sound/soc/sof/ipc4-topology.h:522 */
struct sof_ipc4_process {
	struct sof_ipc4_base_module_cfg base_config;
	struct sof_ipc4_base_module_cfg_ext *base_config_ext;
	struct sof_ipc4_audio_format output_format;
	struct sof_ipc4_available_audio_format available_fmt;
	void *ipc_config_data;
	uint32_t ipc_config_size;
	struct sof_ipc4_msg msg;
	u32 base_config_ext_size;
	u32 init_config;
};
```

Lining the gain, mixer, rate-converter, and processing module structs side by side shows their shared shape, a base-config wire blob above available_fmt and msg, with the processing box adding the optional extension that init_config selects:

```
    Four module private structs share wire-blob + available_fmt + msg
    ──────────────────────────────────────────────────────────────────

    sof_ipc4_gain       sof_ipc4_mixer      sof_ipc4_src
    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
    │ data           │  │ base_config    │  │ data           │
    │  base_config   │  │                │  │  base_config   │
    │  params        │  │                │  │  sink_rate     │
    │ available_fmt  │  │ available_fmt  │  │ available_fmt  │
    │ msg            │  │ msg            │  │ msg            │
    └────────────────┘  └────────────────┘  └────────────────┘

    sof_ipc4_process
    ┌──────────────────────────────────────────┐
    │ base_config                              │
    │ base_config_ext ─▶ pin_formats[] (opt)   │  init_config selects ext
    │ output_format                            │
    │ available_fmt                            │
    │ ipc_config_data / ipc_config_size (blob) │
    │ msg                                      │
    └──────────────────────────────────────────┘
```

### The format the templates carry is resolved at prepare time

Every template the load phase builds carries the entire set of pin formats the topology declares, held in the widget's [`struct sof_ipc4_available_audio_format`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L201). Selecting one concrete format for a given PCM is a runtime-prepare step. [`sof_ipc4_init_input_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1576) matches the negotiated hardware parameters against the input pin formats and copies the chosen one into the module's [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L317), and [`sof_ipc4_init_output_audio_fmt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L1477) does the same for the output reference format. Both run from the per-type [`ipc_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) ops named in the table (for example [`sof_ipc4_prepare_copier_module`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c) for the copiers), which the runtime page covers; the load phase only parses and stores the candidates.

### Load finishes idle, the runtime send takes over

When [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2186) returns, every widget has its IPC4 private structure on [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) with a complete create-module or create-pipeline template, and the DSP has received nothing. The transition from these templates to live DSP state happens at PCM open, when [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) reads the private structure, stamps the instance and pipeline IDs into the message extension, points [`data_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) at the wire payload, and sends the [`SOF_IPC4_MOD_INIT_INSTANCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L301) or [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) message, and when [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472) sends the [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306) message to connect the modules. The bodies of those runtime ops are reproduced on the sibling IPC4 topology runtime page.

### Topology widget to IPC4 copier and pipeline conversion

A loaded [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) becomes a [`struct sof_ipc4_copier`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L332) carrying its [`base_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L229) input format and [`gtw_cfg.node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L216), the scheduler widget becomes a [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) carrying a [`SOF_IPC4_GLB_CREATE_PIPELINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L101) template, and the runtime route bind ties the module instances together with [`SOF_IPC4_MOD_BIND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L306).

```
    Loaded topology                 IPC4 conversion           Intel DSP
    ─────────────────               ───────────────           ─────────

    snd_sof_widget                  sof_ipc4_copier
    ┌────────────────────────┐      ┌────────────────────────┐
    │ id = snd_soc_dapm_     │      │ data: copier_data      │
    │      aif_in            │ ───▶ │   base_config (in fmt) │
    │ private  ──────────────┼──┐   │   gtw_cfg.node_id      │
    │ spipe ─▶ pipe_widget   │  │   │ available_fmt          │
    │ module_info (fw module)│  └──▶│ msg: primary/extension │
    └────────────────────────┘      └────────────┬───────────┘
                                                 │ MOD_INIT_INSTANCE
       sof_ipc4_pipeline                         ▼  (in pipeline N)
       ┌─────────────────────┐         ┌───────────────────────┐
       │ priority, core_id   │ ──────▶ │  copier module        │
       │ msg (CREATE_PIPELINE)         │  instance, ppl_id = N │
       │ state = UNINIT      │         └───────────────────────┘
       └─────────────────────┘     route_setup: MOD_BIND src→sink
```
