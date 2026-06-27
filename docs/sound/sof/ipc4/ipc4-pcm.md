# SOF IPC4 PCM operations

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Sound Open Firmware divides a PCM device into a host-side ALSA substream and a graph of processing pipelines running on the audio DSP, and the IPC4 PCM operations are the function pointer struct that turns an ALSA trigger on that substream into a SET_PIPELINE_STATE command sent to the DSP. The generic core in [`sound/soc/sof/pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) is unaware of which firmware ABI is loaded; it reaches one [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) through the [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro and invokes its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and [`delay`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) members. For a DSP running IPC4 firmware that struct is [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), whose [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) maps a [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) and a [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) or [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), then hands the state to [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414), which walks the [`struct snd_sof_pcm_stream_pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) for the stream and issues the command to every pipeline in dependency order through [`sof_ipc4_set_multi_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90) or [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124). The [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) state is reached not from the trigger but from [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614).

```
    PCM trigger ──▶ IPC4 SET_PIPELINE_STATE sequence to the DSP
    ───────────────────────────────────────────────────────────

    SNDRV_PCM_TRIGGER_START                       sof_ipc4_pcm_trigger()
              │                                   maps cmd ─▶ state
              ▼
    ┌───────────────────────────────────────────────────────────┐
    │  state = SOF_IPC4_PIPE_RUNNING (4)                        │
    │  walk pipeline_list[] in sink ─▶ source order             │
    └──────────────────────────────┬────────────────────────────┘
                                   │  sof_ipc4_trigger_pipelines()
              ┌──────────┬─────────┼─────────┬──────────┐
              ▼          ▼         ▼         ▼          ▼
         ┌────────┐ ┌────────┐         ┌────────┐ ┌────────┐
         │ pipe N │ │pipe N-1│   ...   │ pipe 1 │ │ pipe 0 │
         │ (sink) │ │        │         │        │ │(source)│
         └────────┘ └────────┘         └────────┘ └────────┘
              SET_PIPELINE_STATE RUNNING, one IPC for the set

    trigger ─▶ state mapping (sof_ipc4_pcm_trigger)
    ┌─────────────────────────────┬────────────────────────────┐
    │ START / RESUME / PAUSE_REL  │ SOF_IPC4_PIPE_RUNNING (4)  │
    │ STOP / SUSPEND / PAUSE_PUSH │ SOF_IPC4_PIPE_PAUSED  (3)  │
    │ hw_free (separate op)       │ SOF_IPC4_PIPE_RESET   (2)  │
    └─────────────────────────────┴────────────────────────────┘

    RUNNING and RESET walk sink ─▶ source (reverse list);
    PAUSED walks source ─▶ sink (forward list).
```

## SUMMARY

A SOF PCM device is represented by a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) holding a two-element [`stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array of [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), one per direction, and each direction carries a [`struct snd_sof_pcm_stream_pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) naming the DSP pipelines that move and process that stream. The version-agnostic PCM core in [`sound/soc/sof/pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c) registers [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), and [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) as the ASoC component callbacks, and each one fetches the IPC-specific [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) with [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) and forwards to its function pointers when present. For IPC4 firmware that struct is [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), wired into the IPC4 descriptor at [`sound/soc/sof/ipc4.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L923).

The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) collapses the ALSA command to one of [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) or [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) and calls [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414), while [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614) issues [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) through the same path. [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) reads the per-direction [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), builds a [`struct ipc4_pipeline_set_state_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L174) trigger list, walks it sink to source for [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) and [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) and source to sink for [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), and emits the command through [`sof_ipc4_set_multi_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90) or [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124), each of which encodes [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103) into the message header. When the first pipeline of the stream carries the [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) attribute the trigger detours to [`sof_ipc4_chain_dma_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L312) instead. [`sof_ipc4_pcm_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L908) and [`sof_ipc4_pcm_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L890) allocate and release the per-stream pipeline array and the IPC4 private data, [`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L794) constrains the back-end DAI hardware parameters to what the topology copier supports, and [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) and [`sof_ipc4_pcm_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1286) report stream position and latency from timestamp state that has no part in the pipeline state command.

## SPECIFICATIONS

The IPC4 PCM operations are a Linux kernel software construct and have no standalone hardware specification. The DSP firmware ABI they target, including the SET_PIPELINE_STATE message and the pipeline state values, is defined by the Intel Audio DSP firmware interface that Sound Open Firmware implements, and the message field encodings are reproduced as macros in [`include/sound/sof/ipc4/header.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h). On x86-64 ACPI platforms the host controller and stream DMA the host side drives are the HD-Audio controller defined by the Intel High Definition Audio Specification.

## LINUX KERNEL

### Generic IPC PCM ops and dispatch (sof-audio.h, pcm.c, sof-priv.h)

- [`'\<struct sof_ipc_pcm_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123): the version-agnostic function pointer struct with the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), and [`delay`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) members and the behaviour flags [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123)
- [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541): the macro that returns [`sdev->ipc->ops->pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) or NULL, by which the core reaches the active IPC version's PCM ops
- [`'\<sof_pcm_trigger\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385): the ASoC trigger callback that orders the platform DMA trigger against the IPC and forwards to [`pcm_ops->trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123)
- [`'\<sof_pcm_hw_params\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116): the ASoC hw_params callback that forwards to [`pcm_ops->hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) after setting up the connected widgets
- [`'\<sof_pcm_dai_link_fixup\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719): the back-end DAI link fixup that forwards to [`pcm_ops->dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123)

### IPC4 PCM ops table and members (ipc4-pcm.c, ipc4-priv.h)

- [`'ipc4_pcm_ops':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311): the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) instance for IPC4 firmware, declared `extern` in [`ipc4-priv.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h#L104) and assigned into the IPC4 descriptor at [`sound/soc/sof/ipc4.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L923); sets [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) true
- [`'\<sof_ipc4_pcm_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588): the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; maps the ALSA command to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) or [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141)
- [`'\<sof_ipc4_pcm_hw_params\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036): the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; resets and rebuilds the delay-reporting timestamp info for the stream
- [`'\<sof_ipc4_pcm_hw_free\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614): the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; sends [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) through [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414)
- [`'\<sof_ipc4_pcm_dai_link_fixup\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L794): the [`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; constrains rate, channels, and format to the topology copier's supported audio format
- [`'\<sof_ipc4_pcm_setup\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L908): the [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; allocates the per-direction [`pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) array and the [`struct sof_ipc4_pcm_stream_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46)
- [`'\<sof_ipc4_pcm_free\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L890): the [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; frees the pipeline array and the private data for both directions
- [`'\<sof_ipc4_pcm_pointer\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161): the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; converts the host byte counter to a frame pointer and computes the DSP delay from the host and DAI counters
- [`'\<sof_ipc4_pcm_delay\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1286): the [`delay`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member; returns the delay value the pointer callback cached in the timestamp info

### Pipeline trigger machinery (ipc4-pcm.c)

- [`'\<sof_ipc4_trigger_pipelines\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414): builds the trigger list, orders the walk by state, and sends the SET_PIPELINE_STATE command under [`pipeline_state_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h)
- [`'\<sof_ipc4_add_pipeline_to_trigger_list\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L171): decides per pipeline whether to add it to the trigger list, comparing [`started_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) and [`paused_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519)
- [`'\<sof_ipc4_update_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L210): records the new [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) on each triggered pipeline and adjusts the per-pipeline counts by command
- [`'\<sof_ipc4_set_multi_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90): sends one SET_PIPELINE_STATE for the whole trigger list, or falls to the single-pipeline path when the list has one entry
- [`'\<sof_ipc4_set_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124): sends SET_PIPELINE_STATE for a single pipeline instance id
- [`'\<sof_ipc4_chain_dma_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L312): the chained-DMA path for pipelines with [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156); sends a [`SOF_IPC4_GLB_CHAIN_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L95) message instead of SET_PIPELINE_STATE
- [`'\<sof_ipc4_pipeline_state_str\>':'sound/soc/sof/ipc4.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L242): maps an [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137) value to its name string for debug output

### Per-PCM stream and pipeline data (sof-audio.h, ipc4-topology.h)

- [`'\<struct snd_sof_pcm\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352): the SOF PCM device with a two-element [`stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array, one per direction
- [`'\<struct snd_sof_pcm_stream\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329): one direction's state, carrying the [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) and the IPC-private [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) pointer
- [`'\<struct snd_sof_pcm_stream_pipeline_list\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323): the array of [`struct snd_sof_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) pointers and the [`count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) for one stream
- [`'\<struct snd_sof_pipeline\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519): one pipeline's [`pipe_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519), [`started_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519), and [`paused_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519)
- [`'\<struct sof_ipc4_pipeline\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156): the IPC4 pipeline config in [`pipe_widget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519), with the cached [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156), the [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) flag, and the [`skip_during_fe_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) flag
- [`'\<struct ipc4_pipeline_set_state_data\>':'sound/soc/sof/ipc4-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L174): the trigger list, a [`count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L174) and a flexible array of [`pipeline_instance_ids`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L174)
- [`'\<struct sof_ipc4_pcm_stream_priv\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46): the IPC4 [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) blob, carrying the [`time_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46) pointer and the [`chain_dma_allocated`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46) flag

### Pipeline state enum and message encoding (ipc4/header.h)

- [`'\<enum sof_ipc4_pipeline_state\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137): the DSP pipeline states; [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) (2), [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) (3), [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) (4)
- [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103): the global message type for the pipeline state command, encoded into the header by [`SOF_IPC4_MSG_TYPE_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L162)
- [`SOF_IPC4_GLB_PIPE_STATE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L193): packs a pipeline instance id into bits 23:16 of the primary word
- [`SOF_IPC4_GLB_PIPE_STATE_EXT_MULTI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L200): the extension bit marking a multi-pipeline state message
- [`SOF_IPC4_FW_GEN_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L80): the message target selecting the firmware generic message space, set by [`SOF_IPC4_MSG_TARGET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L151)

### x86-64 ACPI worked example (pci-mtl.c, mtl.c)

- [`'mtl_desc':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31): the Meteor Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h) with [`ipc_default`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L41) set to [`SOF_IPC_TYPE_4`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h), which selects [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311)
- [`'mtl_chip_info':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760): the Meteor Lake [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h) carrying the [`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L764) and [`ipc_ack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L766) register offsets the SET_PIPELINE_STATE message travels through

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model the SOF PCM core maps onto DSP pipelines
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget graph whose pipeline widgets back each [`struct snd_sof_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519)
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface that [`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L794) constrains for the back-end link

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware introduction and architecture](https://thesofproject.github.io/latest/introduction/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every callback below is a field of [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), the version-agnostic function pointer struct the SOF PCM core reaches through [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541). The IPC4 instance [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) fills in eight of them, and the generic caller treats an absent member as a no-op returning success. The pipeline-state result belongs to IPC4, since the same [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member backed by IPC3 firmware drives a different message. The mapping from the ALSA trigger command to the DSP pipeline state the IPC4 trigger requests is fixed.

| ALSA trigger command | IPC4 op | DSP pipeline state |
|----------------------|---------|--------------------|
| [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) |
| [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) |
| [`SNDRV_PCM_TRIGGER_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L101) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) |
| [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) |
| [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) |
| [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) | [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) |

### hw_params

[`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) runs from [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) after the connected DAPM widgets are set up, and for IPC4 it is [`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036), which resets the delay-reporting [`stream_start_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036) and [`llp_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036) and rebuilds the timestamp info. The pipeline graph itself is created during topology load, so this member only prepares the position-tracking state for the stream.

### hw_free

[`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614), and it is the only path that drives the pipelines to [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140). It calls [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) with the RESET state and a zero command. According to the comment in the function, "command is not relevant with RESET, so just pass 0". A STOP trigger therefore leaves the firmware pipelines in [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), and the following hw_free brings them to RESET; the IPC4 ops set [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) so the host DMA is stopped at the same point.

### trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588), called from [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385). It maps the ALSA command to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) for START, RESUME, and PAUSE_RELEASE and to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) for STOP, SUSPEND, and PAUSE_PUSH, then calls [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414). Because the IPC4 ops set [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) sends this IPC before it starts the host DMA on a START and after it stops the DMA on a STOP.

### dai_link_fixup

[`dai_link_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is [`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L794), called from [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) on the back-end DAI link. It reads the topology copier on the DAI, constrains the negotiated rate and channel count to what that copier supports through [`sof_ipc4_pcm_dai_link_fixup_rate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L690) and [`sof_ipc4_pcm_dai_link_fixup_channels()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L742), and forces a single sample format when the copier supports only one bit depth.

### pcm_setup and pcm_free

[`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), reached from topology PCM load in [`sound/soc/sof/topology.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1760), is [`sof_ipc4_pcm_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L908), which allocates the per-direction [`pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) array sized for the maximum pipeline count and the IPC4 [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) data. [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) is [`sof_ipc4_pcm_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L890), called from topology PCM removal at [`sound/soc/sof/topology.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1857), and it releases that array and the private data for both directions.

### pointer and delay

[`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`delay`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) report stream position and latency, backed for IPC4 by [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) and [`sof_ipc4_pcm_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1286). Both read from the timestamp info that [`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036) prepared, and neither has any part in the pipeline state command.

## DETAILS

### The generic ops struct and the version dispatch

The SOF PCM core is one set of ASoC component callbacks shared by every firmware ABI, and the per-version behaviour is reached through one function pointer struct. [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) names the PCM-stage callbacks and a small set of behaviour flags:

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

The core fetches the active version's instance with the [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) macro, which dereferences the IPC ops chain and yields NULL when no IPC is attached:

```c
/* sound/soc/sof/sof-priv.h:541 */
#define sof_ipc_get_ops(sdev, ops_name)		\
		(((sdev)->ipc && (sdev)->ipc->ops) ? (sdev)->ipc->ops->ops_name : NULL)
```

For IPC4 firmware the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L923) member of the IPC ops resolves to [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), wired in near the bottom of the IPC4 descriptor:

```c
/* sound/soc/sof/ipc4.c:923 */
	.pcm = &ipc4_pcm_ops,
```

That one assignment is the right-hand branch of the dispatch, where the version-agnostic component callbacks reach the lookup and land on either the IPC3 or the IPC4 ops table for the firmware in use:

```
    Version dispatch: one generic core, one IPC-version ops table
    ──────────────────────────────────────────────────────────────

    sof_pcm_trigger()  sof_pcm_hw_params()  sof_pcm_dai_link_fixup()
                          │  (version-agnostic core, pcm.c)
                          ▼
                  sof_ipc_get_ops(sdev, pcm)
                          │  sdev->ipc->ops->pcm  (NULL if no IPC)
            ┌─────────────┴─────────────┐
            ▼                           ▼
    ┌────────────────────┐    ┌────────────────────┐
    │ IPC3 firmware      │    │ IPC4 firmware      │
    │ struct             │    │ ipc4_pcm_ops       │
    │ sof_ipc_pcm_ops    │    │ (this page)        │
    └────────────────────┘    └─────────┬──────────┘
                                        ▼
                          .trigger = sof_ipc4_pcm_trigger
                          .hw_free = sof_ipc4_pcm_hw_free
```

### The IPC4 ops table

[`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) fills in the eight callbacks and two of the behaviour flags. Setting [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) orders the SET_PIPELINE_STATE IPC ahead of the host DMA start, and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) keeps the host DMA running until hw_free because the firmware only pauses the pipeline on a STOP trigger:

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

The generic trigger callback [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) consults [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) to decide whether the platform DMA trigger or the IPC runs first, then calls the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member:

```c
/* sound/soc/sof/pcm.c:457 */
	if (!ipc_first)
		snd_sof_pcm_platform_trigger(sdev, substream, cmd);

	if (pcm_ops && pcm_ops->trigger)
		ret = pcm_ops->trigger(component, substream, cmd);
```

The comment on [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) states the reason the flag exists. According to that comment, the flag means "a pipeline is only paused during stop/pause/suspend triggers. The FW keeps the host DMA running in this case and therefore the host must do the same and should stop the DMA during hw_free".

### The trigger maps a command to a pipeline state

[`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) is the whole of the trigger member. It is a single switch that folds the six ALSA trigger commands it handles into two pipeline states and forwards them, passing the original command along so the lower layer can tell a pause from a stop:

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

A STOP folds to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), the same state as a PAUSE_PUSH. The transition to [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) happens separately in [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614), which the core runs after the STOP, so a stopped stream rests in PAUSED and only reaches RESET once its hardware parameters are freed:

```c
/* sound/soc/sof/ipc4-pcm.c:614 */
static int sof_ipc4_pcm_hw_free(struct snd_soc_component *component,
				struct snd_pcm_substream *substream)
{
	/* command is not relevant with RESET, so just pass 0 */
	return sof_ipc4_trigger_pipelines(component, substream, SOF_IPC4_PIPE_RESET, 0);
}
```

### A PCM stream maps to a list of pipelines

The state command does not target one DSP object; it targets every pipeline that carries the stream, and the mapping is stored per direction. [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) holds a two-element [`stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) array, and each [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) carries the [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) for its direction:

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
	/*
	 * flag to indicate that the DSP pipelines should be kept
	 * active or not while suspending the stream
	 */
	bool suspend_ignored;
	struct snd_sof_pcm_stream_pipeline_list pipeline_list;

	/* used by IPC implementation and core does not touch it */
	void *private;
};
```

The list is a flat array of pipeline pointers and a count:

```c
/* sound/soc/sof/sof-audio.h:323 */
struct snd_sof_pcm_stream_pipeline_list {
	struct snd_sof_pipeline **pipelines;
	u32 count;
};
```

Each entry is a [`struct snd_sof_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519), which back-points to the DAPM pipeline widget and counts how many PCMs have started and paused it, so a pipeline shared by two streams is triggered correctly when one stops while the other plays:

```c
/* sound/soc/sof/sof-audio.h:519 */
struct snd_sof_pipeline {
	struct snd_sof_widget *pipe_widget;
	int started_count;
	int paused_count;
	int complete;
	unsigned long core_mask;
	struct list_head list;
	bool direction_valid;
	u32 direction;
};
```

The IPC4-specific configuration, including the cached firmware [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) and the [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) and [`skip_during_fe_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) flags, is held in [`pipe_widget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) as a [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156):

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

[`sof_ipc4_pcm_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L908) allocates the [`pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L323) array for both directions at topology PCM load, sized for the firmware's maximum pipeline count, and attaches the IPC4 [`struct sof_ipc4_pcm_stream_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46) as the [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) blob:

```c
/* sound/soc/sof/ipc4-pcm.c:908 */
static int sof_ipc4_pcm_setup(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm)
{
	struct snd_sof_pcm_stream_pipeline_list *pipeline_list;
	struct sof_ipc4_fw_data *ipc4_data = sdev->private;
	struct sof_ipc4_pcm_stream_priv *stream_priv;
	struct sof_ipc4_timestamp_info *time_info;
	bool support_info = true;
	u32 abi_version;
	u32 abi_offset;
	int stream;
	...
	for_each_pcm_streams(stream) {
		pipeline_list = &spcm->stream[stream].pipeline_list;

		/* allocate memory for max number of pipeline IDs */
		pipeline_list->pipelines = kzalloc_objs(*pipeline_list->pipelines,
							ipc4_data->max_num_pipelines);
		if (!pipeline_list->pipelines) {
			sof_ipc4_pcm_free(sdev, spcm);
			return -ENOMEM;
		}

		stream_priv = kzalloc_obj(*stream_priv);
		if (!stream_priv) {
			sof_ipc4_pcm_free(sdev, spcm);
			return -ENOMEM;
		}

		spcm->stream[stream].private = stream_priv;
		...
	}

	return 0;
}
```

The IPC4 private blob is small, holding the optional timestamp pointer and the chained-DMA allocation flag the chain-DMA trigger reads:

```c
/* sound/soc/sof/ipc4-pcm.c:46 */
struct sof_ipc4_pcm_stream_priv {
	struct sof_ipc4_timestamp_info *time_info;

	bool chain_dma_allocated;
};
```

[`sof_ipc4_pcm_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L890) is the matching teardown, freeing the array and the private data for both directions:

```c
/* sound/soc/sof/ipc4-pcm.c:890 */
static void sof_ipc4_pcm_free(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm)
{
	struct snd_sof_pcm_stream_pipeline_list *pipeline_list;
	struct sof_ipc4_pcm_stream_priv *stream_priv;
	int stream;

	for_each_pcm_streams(stream) {
		pipeline_list = &spcm->stream[stream].pipeline_list;
		kfree(pipeline_list->pipelines);
		pipeline_list->pipelines = NULL;

		stream_priv = spcm->stream[stream].private;
		kfree(stream_priv->time_info);
		kfree(spcm->stream[stream].private);
		spcm->stream[stream].private = NULL;
	}
}
```

The array that helper releases is the middle of a longer chain, the per-direction stream pointing at the pipeline list and each pipeline reaching its pipe widget's private IPC4 config with the cached state:

```
    struct nesting: one snd_sof_pcm reaches the IPC4 pipeline config
    ──────────────────────────────────────────────────────────────────

    struct snd_sof_pcm
      └─ stream[2]            struct snd_sof_pcm_stream (one per dir)
           ├─ pipeline_list   struct snd_sof_pcm_stream_pipeline_list
           │     ├─ count
           │     └─ pipelines ──▶ struct snd_sof_pipeline *[]
           │                        ├─ pipe_widget
           │                        ├─ started_count
           │                        └─ paused_count
           │              pipe_widget->private ──▶ struct sof_ipc4_pipeline
           │                                         ├─ state
           │                                         ├─ use_chain_dma
           │                                         └─ skip_during_fe_trigger
           └─ private ──────────▶ struct sof_ipc4_pcm_stream_priv
                                    ├─ time_info
                                    └─ chain_dma_allocated
```

### Walking the pipelines in dependency order

[`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) is where the state becomes a command on the wire. It reads the [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) for the substream direction, returns at once when the list is empty, and inspects the first pipeline to decide whether the chained-DMA path applies:

```c
/* sound/soc/sof/ipc4-pcm.c:414 */
static int sof_ipc4_trigger_pipelines(struct snd_soc_component *component,
				      struct snd_pcm_substream *substream, int state, int cmd)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_sof_pcm_stream_pipeline_list *pipeline_list;
	struct sof_ipc4_fw_data *ipc4_data = sdev->private;
	struct ipc4_pipeline_set_state_data *trigger_list;
	struct snd_sof_widget *pipe_widget;
	struct sof_ipc4_pipeline *pipeline;
	struct snd_sof_pipeline *spipe;
	struct snd_sof_pcm *spcm;
	u8 *pipe_priority;
	int ret;
	int i;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;
	...
	pipeline_list = &spcm->stream[substream->stream].pipeline_list;

	/* nothing to trigger if the list is empty */
	if (!pipeline_list->pipelines || !pipeline_list->count)
		return 0;

	spipe = pipeline_list->pipelines[0];
	pipe_widget = spipe->pipe_widget;
	pipeline = pipe_widget->private;
```

After the chain-DMA branch (covered below), the function allocates the trigger list and a priority scratch array, then takes [`pipeline_state_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-priv.h) with a scoped guard so two concurrent triggers cannot interleave their state changes:

```c
/* sound/soc/sof/ipc4-pcm.c:478 */
	/* allocate memory for the pipeline data */
	trigger_list = kzalloc_flex(*trigger_list, pipeline_instance_ids,
				    pipeline_list->count);
	if (!trigger_list)
		return -ENOMEM;

	pipe_priority = kzalloc(pipeline_list->count, GFP_KERNEL);
	if (!pipe_priority) {
		kfree(trigger_list);
		return -ENOMEM;
	}

	guard(mutex)(&ipc4_data->pipeline_state_mutex);
```

The order of the walk is the dependency order of the graph. The comment in the function states the rule, and the two loops implement it. A start (RUNNING) and a reset walk the list from the last entry to the first, sink to source, so a downstream pipeline is running before the source feeds it; a pause walks the list forward, source to sink, so the source stops producing before its consumers go away:

```c
/* sound/soc/sof/ipc4-pcm.c:490 */
	/*
	 * IPC4 requires pipelines to be triggered in order starting at the sink and
	 * walking all the way to the source. So traverse the pipeline_list in the order
	 * sink->source when starting PCM's and in the reverse order to pause/stop PCM's.
	 * Skip the pipelines that have their skip_during_fe_trigger flag set. If there is a fork
	 * in the pipeline, the order of triggering between the left/right paths will be
	 * indeterministic. But the sink->source trigger order sink->source would still be
	 * guaranteed for each fork independently.
	 */
	if (state == SOF_IPC4_PIPE_RUNNING || state == SOF_IPC4_PIPE_RESET)
		for (i = pipeline_list->count - 1; i >= 0; i--) {
			spipe = pipeline_list->pipelines[i];
			sof_ipc4_add_pipeline_to_trigger_list(sdev, state, spipe, trigger_list,
							      pipe_priority);
		}
	else
		for (i = 0; i < pipeline_list->count; i++) {
			spipe = pipeline_list->pipelines[i];
			sof_ipc4_add_pipeline_to_trigger_list(sdev, state, spipe, trigger_list,
							      pipe_priority);
		}
```

[`sof_ipc4_add_pipeline_to_trigger_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L171) filters each candidate by its share counts so a pipeline used by more than one PCM only changes state when the last user requires it. It skips a pipeline flagged [`skip_during_fe_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) except on RESET, and otherwise compares [`started_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) and [`paused_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519):

```c
/* sound/soc/sof/ipc4-pcm.c:171 */
static void
sof_ipc4_add_pipeline_to_trigger_list(struct snd_sof_dev *sdev, int state,
				      struct snd_sof_pipeline *spipe,
				      struct ipc4_pipeline_set_state_data *trigger_list,
				      s8 *pipe_priority)
{
	struct snd_sof_widget *pipe_widget = spipe->pipe_widget;
	struct sof_ipc4_pipeline *pipeline = pipe_widget->private;

	if (pipeline->skip_during_fe_trigger && state != SOF_IPC4_PIPE_RESET)
		return;

	switch (state) {
	case SOF_IPC4_PIPE_RUNNING:
		/*
		 * Trigger pipeline if all PCMs containing it are paused or if it is RUNNING
		 * for the first time
		 */
		if (spipe->started_count == spipe->paused_count)
			sof_ipc4_add_pipeline_by_priority(trigger_list, pipe_widget, pipe_priority,
							  false);
		break;
	case SOF_IPC4_PIPE_RESET:
		/* RESET if the pipeline is neither running nor paused */
		if (!spipe->started_count && !spipe->paused_count)
			sof_ipc4_add_pipeline_by_priority(trigger_list, pipe_widget, pipe_priority,
							  true);
		break;
	case SOF_IPC4_PIPE_PAUSED:
		/* Pause the pipeline only when its started_count is 1 more than paused_count */
		if (spipe->paused_count == (spipe->started_count - 1))
			sof_ipc4_add_pipeline_by_priority(trigger_list, pipe_widget, pipe_priority,
							  true);
		break;
	default:
		break;
	}
}
```

For a RUNNING transition that is not a reset and not a pause release, [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) first sends the pipelines to PAUSED, then issues the final RUNNING state. According to the comment in the function, the PAUSED step runs "if the final state is PAUSED or when the pipeline is set to RUNNING for the first time after the PCM is started", which gives the firmware a defined intermediate state before it runs:

```c
/* sound/soc/sof/ipc4-pcm.c:521 */
	/* no need to pause before reset or before pause release */
	if (state == SOF_IPC4_PIPE_RESET || cmd == SNDRV_PCM_TRIGGER_PAUSE_RELEASE)
		goto skip_pause_transition;

	/*
	 * set paused state for pipelines if the final state is PAUSED or when the pipeline
	 * is set to RUNNING for the first time after the PCM is started.
	 */
	ret = sof_ipc4_set_multi_pipeline_state(sdev, SOF_IPC4_PIPE_PAUSED, trigger_list);
	if (ret < 0) {
		spcm_err(spcm, substream->stream, "failed to pause all pipelines\n");
		goto free;
	}
```

After the final state succeeds, the function calls [`sof_ipc4_update_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L210) over every pipeline so the cached state and the share counts track what the firmware now holds:

```c
/* sound/soc/sof/ipc4-pcm.c:574 */
	/* update RUNNING/RESET state for all pipelines that were just triggered */
	for (i = 0; i < pipeline_list->count; i++) {
		spipe = pipeline_list->pipelines[i];
		sof_ipc4_update_pipeline_state(sdev, state, cmd, spipe, trigger_list);
	}
```

[`sof_ipc4_update_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L210) writes the firmware state into the [`struct sof_ipc4_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) when the pipeline appears in the trigger list, then adjusts [`started_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) and [`paused_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) by command, letting the share-count test above behave correctly for a pipeline used by two PCMs:

```c
/* sound/soc/sof/ipc4-pcm.c:221 */
	/* set state for pipeline if it was just triggered */
	for (i = 0; i < trigger_list->count; i++) {
		if (trigger_list->pipeline_instance_ids[i] == pipe_widget->instance_id) {
			pipeline->state = state;
			break;
		}
	}

	switch (state) {
	case SOF_IPC4_PIPE_PAUSED:
		switch (cmd) {
		case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
			/*
			 * increment paused_count if the PAUSED is the final state during
			 * the PAUSE trigger
			 */
			spipe->paused_count++;
			break;
		case SNDRV_PCM_TRIGGER_STOP:
		case SNDRV_PCM_TRIGGER_SUSPEND:
			/*
			 * decrement started_count if PAUSED is the final state during the
			 * STOP trigger
			 */
			spipe->started_count--;
			break;
		default:
			break;
		}
		break;
	case SOF_IPC4_PIPE_RUNNING:
		switch (cmd) {
		case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
			/* decrement paused_count for RELEASE */
			spipe->paused_count--;
			break;
		case SNDRV_PCM_TRIGGER_START:
		case SNDRV_PCM_TRIGGER_RESUME:
			/* increment started_count for START/RESUME */
			spipe->started_count++;
			break;
		default:
			break;
		}
		break;
	default:
		break;
	}
```

### Encoding the SET_PIPELINE_STATE command

The trigger list is the IPC payload. [`struct ipc4_pipeline_set_state_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L174) is a count followed by a flexible array of pipeline instance ids:

```c
/* sound/soc/sof/ipc4-topology.h:174 */
struct ipc4_pipeline_set_state_data {
	u32 count;
	DECLARE_FLEX_ARRAY(u32, pipeline_instance_ids);
};
```

[`sof_ipc4_set_multi_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90) builds the message header. It places the target state in the low bits of the primary word, sets the message type to [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103) with [`SOF_IPC4_MSG_TYPE_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L162), targets the firmware generic message space with [`SOF_IPC4_FW_GEN_MSG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L80), sets the [`SOF_IPC4_GLB_PIPE_STATE_EXT_MULTI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L200) extension bit, and attaches the trigger list as the data payload:

```c
/* sound/soc/sof/ipc4-pcm.c:90 */
static int sof_ipc4_set_multi_pipeline_state(struct snd_sof_dev *sdev, u32 state,
					     struct ipc4_pipeline_set_state_data *trigger_list)
{
	struct sof_ipc4_msg msg = {{ 0 }};
	u32 primary, ipc_size;
	char debug_buf[32];

	/* trigger a single pipeline */
	if (trigger_list->count == 1)
		return sof_ipc4_set_pipeline_state(sdev, trigger_list->pipeline_instance_ids[0],
						   state);
	...
	primary = state;
	primary |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_SET_PIPELINE_STATE);
	primary |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	primary |= SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG);
	msg.primary = primary;

	/* trigger multiple pipelines with a single IPC */
	msg.extension = SOF_IPC4_GLB_PIPE_STATE_EXT_MULTI;

	/* ipc_size includes the count and the pipeline IDs for the number of pipelines */
	ipc_size = sizeof(u32) * (trigger_list->count + 1);
	msg.data_size = ipc_size;
	msg.data_ptr = trigger_list;

	return sof_ipc_tx_message_no_reply(sdev->ipc, &msg, ipc_size);
}
```

When the list holds one pipeline the function above falls through to [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124), which packs the single instance id into bits 23:16 with [`SOF_IPC4_GLB_PIPE_STATE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L193) and sends no payload:

```c
/* sound/soc/sof/ipc4-pcm.c:124 */
int sof_ipc4_set_pipeline_state(struct snd_sof_dev *sdev, u32 instance_id, u32 state)
{
	struct sof_ipc4_msg msg = {{ 0 }};
	u32 primary;
	...
	primary = state;
	primary |= SOF_IPC4_GLB_PIPE_STATE_ID(instance_id);
	primary |= SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_SET_PIPELINE_STATE);
	primary |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	primary |= SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG);

	msg.primary = primary;

	return sof_ipc_tx_message_no_reply(sdev->ipc, &msg, 0);
}
```

The state value placed in the low bits is one of the [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137) constants. The three states the PCM path uses are [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140) (2), [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) (3), and [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) (4):

```c
/* include/sound/sof/ipc4/header.h:137 */
enum sof_ipc4_pipeline_state {
	SOF_IPC4_PIPE_INVALID_STATE,
	SOF_IPC4_PIPE_UNINITIALIZED,
	SOF_IPC4_PIPE_RESET,
	SOF_IPC4_PIPE_PAUSED,
	SOF_IPC4_PIPE_RUNNING,
	SOF_IPC4_PIPE_EOS
};
```

One of those state values occupies the low 16 bits of the primary word, the message type and the pipeline instance id stacking above it in their own fields:

```
    SET_PIPELINE_STATE primary word (sof_ipc4_set_pipeline_state)
    ──────────────────────────────────────────────────────────────

    bit  31 30   28      24 23        16 15                       0
    ┌─────────┬─────────┬───────────┬───────────────────────────────┐
    │ tgt dir │  type   │  pipe id  │ pipeline state                │
    │ (31:30) │ (28:24) │  (23:16)  │ (15:0)                        │
    └─────────┴─────────┴───────────┴───────────────────────────────┘

    type    = SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_SET_PIPELINE_STATE)
    pipe id = SOF_IPC4_GLB_PIPE_STATE_ID(instance_id)  (bits 23:16)
    state   = SOF_IPC4_PIPE_RESET / PAUSED / RUNNING   (low bits)
    dir 29  = SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST)
    tgt 30  = SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG)

    multi-pipeline form leaves the pipe id field unused; the ids travel
    in the data payload, extension bit 0 = SOF_IPC4_GLB_PIPE_STATE_EXT_MULTI
```

### Chained DMA bypasses SET_PIPELINE_STATE

When the first pipeline of the stream has [`use_chain_dma`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.h#L156) set, [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) does not build a trigger list at all. It calls [`sof_ipc4_chain_dma_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L312) and returns, because in that mode there is no DSP processing and the samples move from host DMA to a single DSP buffer and out over link DMA:

```c
/* sound/soc/sof/ipc4-pcm.c:445 */
	if (pipeline->use_chain_dma) {
		struct sof_ipc4_timestamp_info *time_info;

		time_info = sof_ipc4_sps_to_time_info(&spcm->stream[substream->stream]);

		ret = sof_ipc4_chain_dma_trigger(sdev, spcm, substream->stream,
						 pipeline_list, state, cmd);
		if (ret || !time_info)
			return ret;
		...
	}
```

[`sof_ipc4_chain_dma_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L312) carries a header comment with the chained-DMA state diagram and turns the same three states into a [`SOF_IPC4_GLB_CHAIN_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L95) message that allocates, enables, disables, or frees the chain rather than setting a pipeline state. A RUNNING state allocates and enables the chain, a PAUSED state leaves it allocated but disabled, and a RESET state disables and frees it:

```c
/* sound/soc/sof/ipc4-pcm.c:325 */
	switch (state) {
	case SOF_IPC4_PIPE_RUNNING: /* Allocate and start chained dma */
		allocate = true;
		enable = true;
		/*
		 * SOF assumes creation of a new stream from the presence of fifo_size
		 * in the message, so we must leave it out in pause release case.
		 */
		if (cmd == SNDRV_PCM_TRIGGER_PAUSE_RELEASE)
			set_fifo_size = false;
		else
			set_fifo_size = true;
		break;
	case SOF_IPC4_PIPE_PAUSED: /* Disable chained DMA. */
		allocate = true;
		enable = false;
		set_fifo_size = false;
		break;
	case SOF_IPC4_PIPE_RESET: /* Disable and free chained DMA. */

		/* ChainDMA can only be reset if it has been allocated */
		if (!stream_priv->chain_dma_allocated)
			return 0;

		allocate = false;
		enable = false;
		set_fifo_size = false;
		break;
	default:
		spcm_err(spcm, direction, "Unexpected pipeline state %d\n", state);
		return -EINVAL;
	}
```

The message header sets the type to [`SOF_IPC4_GLB_CHAIN_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L95) and the allocate and enable bits track the decoded action, after which the function records the chain's allocation state in [`chain_dma_allocated`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L46) so a later RESET knows whether there is anything to free:

```c
/* sound/soc/sof/ipc4-pcm.c:358 */
	msg.primary = SOF_IPC4_MSG_TYPE_SET(SOF_IPC4_GLB_CHAIN_DMA);
	msg.primary |= SOF_IPC4_MSG_DIR(SOF_IPC4_MSG_REQUEST);
	msg.primary |= SOF_IPC4_MSG_TARGET(SOF_IPC4_FW_GEN_MSG);
	...
	if (allocate)
		msg.primary |= SOF_IPC4_GLB_CHAIN_DMA_ALLOCATE_MASK;

	if (enable)
		msg.primary |= SOF_IPC4_GLB_CHAIN_DMA_ENABLE_MASK;

	ret = sof_ipc_tx_message_no_reply(sdev->ipc, &msg, 0);
	/* Update the ChainDMA allocation state */
	if (!ret)
		stream_priv->chain_dma_allocated = allocate;

	return ret;
```

The function header documents how suspend reaches RESET on this path the same way the non-chained path does. According to that comment, "during system suspend, the suspend trigger is followed by a hw_free in sof_pcm_trigger(). So, the final state during suspend would be RESET", which mirrors the pause-then-reset ordering [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614) drives for SET_PIPELINE_STATE.

```
    ChainDMA: pipeline state decoded to GLB_CHAIN_DMA action bits
    ──────────────────────────────────────────────────────────────

    ┌──────────────────────┬──────────┬────────┬───────────────┐
    │ state                │ allocate │ enable │ set_fifo_size │
    ├──────────────────────┼──────────┼────────┼───────────────┤
    │ SOF_IPC4_PIPE_RUNNING│   true   │  true  │ true, except  │
    │                      │          │        │ PAUSE_RELEASE │
    │ SOF_IPC4_PIPE_PAUSED │   true   │ false  │     false     │
    │ SOF_IPC4_PIPE_RESET  │  false   │ false  │     false     │
    └──────────────────────┴──────────┴────────┴───────────────┘

    allocate → SOF_IPC4_GLB_CHAIN_DMA_ALLOCATE_MASK in msg.primary
    enable   → SOF_IPC4_GLB_CHAIN_DMA_ENABLE_MASK in msg.primary
    RESET is a no-op when the chain was never allocated
```

### Delay reporting prepared at hw_params and read at pointer

[`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036) does not touch the pipelines. It resets the position-tracking fields for the stream and rebuilds the timestamp info, so the later pointer reads start from a known base:

```c
/* sound/soc/sof/ipc4-pcm.c:1036 */
static int sof_ipc4_pcm_hw_params(struct snd_soc_component *component,
				  struct snd_pcm_substream *substream,
				  struct snd_pcm_hw_params *params,
				  struct snd_sof_platform_stream_params *platform_params)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sof_ipc4_timestamp_info *time_info;
	struct snd_sof_pcm *spcm;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;

	time_info = sof_ipc4_sps_to_time_info(&spcm->stream[substream->stream]);
	/* delay calculation is not supported by current fw_reg ABI */
	if (!time_info)
		return 0;

	time_info->stream_start_offset = SOF_IPC4_INVALID_STREAM_POSITION;
	time_info->llp_offset = 0;

	sof_ipc4_build_time_info(sdev, &spcm->stream[substream->stream]);

	return 0;
}
```

[`sof_ipc4_pcm_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1286) does no calculation of its own; it returns the delay value the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) callback last stored in the timestamp info, and 0 when no timestamp info exists:

```c
/* sound/soc/sof/ipc4-pcm.c:1286 */
static snd_pcm_sframes_t sof_ipc4_pcm_delay(struct snd_soc_component *component,
					    struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sof_ipc4_timestamp_info *time_info;
	struct snd_sof_pcm *spcm;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return 0;

	time_info = sof_ipc4_sps_to_time_info(&spcm->stream[substream->stream]);
	/*
	 * Report the stored delay value calculated in the pointer callback.
	 * In the unlikely event that the calculation was skipped/aborted, the
	 * default 0 delay returned.
	 */
	if (time_info)
		return time_info->delay;

	/* No delay information available, report 0 as delay */
	return 0;
}
```

[`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) is the function that computes the delay. It reads the host byte counter, converts it to frames, reads the DAI or link counter, subtracts the firmware-supplied [`stream_start_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036), and stores the difference between the two sides of the DSP as the delay, while returning the wrapped host pointer:

```c
/* sound/soc/sof/ipc4-pcm.c:1161 */
static int sof_ipc4_pcm_pointer(struct snd_soc_component *component,
				struct snd_pcm_substream *substream,
				snd_pcm_uframes_t *pointer)
{
	...
	/* For delay calculation we need the host counter */
	host_cnt = snd_sof_pcm_get_host_byte_counter(sdev, component, substream);

	/* Store the original value to host_ptr */
	host_ptr = host_cnt;

	/* convert the host_cnt to frames */
	host_cnt = div64_u64(host_cnt, frames_to_bytes(substream->runtime, 1));
	...
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		head_cnt = host_cnt;
		tail_cnt = dai_cnt;
	} else {
		head_cnt = dai_cnt;
		tail_cnt = host_cnt;
	}

	if (unlikely(head_cnt < tail_cnt))
		time_info->delay = DELAY_BOUNDARY - tail_cnt + head_cnt;
	else
		time_info->delay = head_cnt - tail_cnt;
	...
	/*
	 * Convert the host byte counter to PCM pointer which wraps in buffer
	 * and it is in frames
	 */
	div64_u64_rem(host_ptr, snd_pcm_lib_buffer_bytes(substream), &host_ptr);
	*pointer = bytes_to_frames(substream->runtime, host_ptr);

	return 0;
}
```

### The back-end DAI link fixup constrains hardware parameters

[`sof_ipc4_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L794) runs from [`sof_pcm_dai_link_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719) on the back-end DAI link to clamp the negotiated parameters to what the topology copier on that DAI can carry. It looks up the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h) for the link, reads the copier from its [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h) pointer, and returns early when the pipeline is a chain-DMA pipeline that uses no copier:

```c
/* sound/soc/sof/ipc4-pcm.c:794 */
static int sof_ipc4_pcm_dai_link_fixup(struct snd_soc_pcm_runtime *rtd,
				       struct snd_pcm_hw_params *params)
{
	struct snd_soc_component *component = snd_soc_rtdcom_lookup(rtd, SOF_AUDIO_PCM_DRV_NAME);
	struct snd_sof_dai *dai = snd_sof_find_dai(component, rtd->dai_link->name);
	struct snd_mask *fmt = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_soc_dai *cpu_dai = snd_soc_rtd_to_cpu(rtd, 0);
	struct sof_ipc4_audio_format *ipc4_fmt;
	struct sof_ipc4_copier *ipc4_copier;
	bool single_bitdepth = false;
	u32 valid_bits = 0;
	int dir, ret;
	...
	ipc4_copier = dai->private;
	...
	for_each_pcm_streams(dir) {
		struct snd_soc_dapm_widget *w = snd_soc_dai_get_widget(cpu_dai, dir);

		if (w) {
			...
			struct sof_ipc4_pipeline *pipeline = pipe_widget->private;

			/* Chain DMA does not use copiers, so no fixup needed */
			if (pipeline->use_chain_dma)
				return 0;
			...
		}
	}
```

The rest of the function clamps the rate and channel count through [`sof_ipc4_pcm_dai_link_fixup_rate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L690) and [`sof_ipc4_pcm_dai_link_fixup_channels()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L742), and when the copier supports only one bit depth it clears the format mask and re-sets the single supported sample format:

```c
/* sound/soc/sof/ipc4-pcm.c:853 */
	ret = sof_ipc4_pcm_dai_link_fixup_rate(sdev, params, ipc4_copier);
	if (ret)
		return ret;

	ret = sof_ipc4_pcm_dai_link_fixup_channels(sdev, params, ipc4_copier);
	if (ret)
		return ret;

	if (single_bitdepth) {
		snd_mask_none(fmt);
		valid_bits = SOF_IPC4_AUDIO_FORMAT_CFG_V_BIT_DEPTH(ipc4_fmt->fmt_cfg);
		dev_dbg(component->dev, "Set %s to %d bit format\n", dai->name, valid_bits);
	}

	/* Set format if it is specified */
	switch (valid_bits) {
	case 16:
		snd_mask_set_format(fmt, SNDRV_PCM_FORMAT_S16_LE);
		break;
	case 24:
		snd_mask_set_format(fmt, SNDRV_PCM_FORMAT_S24_LE);
		break;
	case 32:
		snd_mask_set_format(fmt, SNDRV_PCM_FORMAT_S32_LE);
		break;
	default:
		break;
	}
```

### x86-64 ACPI worked example: Intel Meteor Lake

On a Meteor Lake laptop the SOF driver binds through the HD-Audio PCI device matched by [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31). The descriptor sets the default IPC to [`SOF_IPC_TYPE_4`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h), which is what causes [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) to resolve the PCM ops to [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311):

```c
/* sound/soc/sof/intel/pci-mtl.c:31 */
static const struct sof_dev_desc mtl_desc = {
	.use_acpi_target_states	= true,
	.machines               = snd_soc_acpi_intel_mtl_machines,
	.alt_machines		= snd_soc_acpi_intel_mtl_sdw_machines,
	.resindex_lpe_base      = 0,
	.resindex_pcicfg_base   = -1,
	.resindex_imr_base      = -1,
	.irqindex_host_ipc      = -1,
	.chip_info = &mtl_chip_info,
	.ipc_supported_mask	= BIT(SOF_IPC_TYPE_4),
	.ipc_default		= SOF_IPC_TYPE_4,
	.dspless_mode_supported	= true,		/* Only supported for HDaudio */
	...
	.ops = &sof_mtl_ops,
	.ops_init = sof_mtl_ops_init,
	.ops_free = hda_ops_free,
};
```

The SET_PIPELINE_STATE message the IPC4 PCM ops produce reaches the DSP through the inter-processor communication registers named in [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), the [`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L764) doorbell and the [`ipc_ack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L766) acknowledge register:

```c
/* sound/soc/sof/intel/mtl.c:760 */
const struct sof_intel_dsp_desc mtl_chip_info = {
	.cores_num = 3,
	.init_core_mask = BIT(0),
	.host_managed_cores_mask = BIT(0),
	.ipc_req = MTL_DSP_REG_HFIPCXIDR,
	.ipc_req_mask = MTL_DSP_REG_HFIPCXIDR_BUSY,
	.ipc_ack = MTL_DSP_REG_HFIPCXIDA,
	.ipc_ack_mask = MTL_DSP_REG_HFIPCXIDA_DONE,
	.ipc_ctl = MTL_DSP_REG_HFIPCXCTL,
	...
};
```

When a media player on this laptop starts a stereo playback stream, ALSA issues [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99). [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) sees [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) set and calls [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) before starting the host DMA. The trigger maps the command to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142), and [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) walks the stream's pipelines sink to source, sends them to PAUSED then RUNNING through the [`MTL_DSP_REG_HFIPCXIDR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L764) doorbell, and only then does the host DMA start filling the buffer. When the user presses pause, [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) maps to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) and the same pipelines are walked source to sink; when the stream is finally closed, [`sof_ipc4_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L614) sends them to [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140).
