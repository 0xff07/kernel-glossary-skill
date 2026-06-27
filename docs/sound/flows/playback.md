# Audio playback flow

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An aplay process that opens `/dev/snd/pcmC0D0p` and writes PCM frames drives a fixed sequence of ioctls, and on an Intel Meteor Lake (MTL) machine with a SoundWire rt722-sdca codec each ioctl descends through the ALSA PCM core in [`sound/core/pcm_native.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c), the ASoC PCM core in [`sound/soc/soc-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c), and the Sound Open Firmware component in [`sound/soc/sof/pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c), which talks to the DSP over IPC4, before it reaches hardware. The [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) carries the stream through a state machine whose values are defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306), where open sets [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), the HW_PARAMS ioctl sets [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308), the PREPARE ioctl sets [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309), and the START trigger sets [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310). The same four steps configure two parallel transports, the HD-Audio host DMA that moves frames from the application buffer into the DSP and the SoundWire stream that carries the processed PCM from the DSP out to the rt722-sdca codec.

```
    Playback path on Intel MTL SOF with a SoundWire rt722-sdca codec
    ───────────────────────────────────────────────────────────────

    control path (one ioctl per row)        data path (after START)

    aplay  /dev/snd/pcmC0D0p
    ┌───────────────────────────────────────┐
    │ open  hw_params  prepare  trigger     │
    └───┬──────┬─────────┬────────────┬─────┘
        ▼      ▼         ▼            ▼
    ALSA PCM core  (sound/core/pcm_native.c)
    ┌───────────────────────────────────────┐    application buffer
    │ snd_pcm_open / _hw_params / _prepare  │    (runtime->dma_area)
    │ snd_pcm_start  ─▶ state RUNNING       │           │
    └───┬───────────────────────────────────┘           ▼
        ▼  rtd->ops.*                            host DMA ring
    ASoC soc-pcm  (sound/soc/soc-pcm.c)         hdac_stream / BDL
    ┌───────────────────────────────────────┐           │
    │ soc_pcm_open / _hw_params / _prepare  │           ▼
    │ soc_pcm_trigger  ─▶ trigger[][]       │    DSP host gateway
    └───┬────────────────────┬──────────────┘    (copier widget)
        ▼  component          ▼  CPU+CODEC DAI     │
    SOF component        BE DAI (asoc_sdw_*)       ▼
    ┌────────────────────┐ ┌───────────────────┐ pipeline modules
    │ sof_pcm_open       │ │ sdw_prepare_stream│ on the DSP
    │ sof_pcm_hw_params  │ │ sdw_enable_stream │     │
    │ sof_pcm_trigger    │ └────────┬──────────┘     ▼
    └───┬────────────────┘          │           SoundWire data
        ▼  IPC4 to DSP              ▼           ports (DP1/DP3)
    SET_PIPELINE_STATE RUNNING   SoundWire bus ─────────▶ rt722-sdca
```

## SUMMARY

The control path begins when aplay opens the playback device node and the VFS layer routes the open to [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which reaches [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) through [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) and through it [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), where [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) sets the runtime to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) before [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) calls the substream open op. For a non-DPCM ASoC link that op is [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), installed by [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) into [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1147); it locks and calls [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854), which runs [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) on the CPU and CODEC DAIs and opens the SOF component through [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536). A dynamic (DPCM) front-end link instead gets [`dpcm_fe_dai_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760), which splits the front end from the SoundWire back end.

The HW_PARAMS ioctl reaches [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), which calls the substream hw_params op [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) and then [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) to advance to [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308). Inside [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070), [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on the rt722-sdca DAI runs [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116), which joins the codec to its SoundWire stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), and [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) runs [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), which programs the host DMA and sets up the pipeline widgets. The PREPARE ioctl reaches [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997), whose action [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) calls [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) and whose [`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976) sets [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309). [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) runs [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) on the component, and the BE DAI prepare op [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533).

The START trigger reaches [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504), whose action [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) calls the trigger op with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) and whose [`snd_pcm_post_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1475) sets [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310). [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) dispatches through the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1185) table to [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618), to the component trigger [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), and to the BE DAI trigger [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050). [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) calls [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588), which maps the START command to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) and sends the IPC4 SET_PIPELINE_STATE message through [`sof_ipc4_set_multi_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90); [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619). After START the host DMA, programmed by [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392), pushes period-sized chunks from the application buffer into the DSP, and each completed period raises an interrupt that the host driver reports with [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933).

## SPECIFICATIONS

The PCM ioctl interface, the stream states, and the trigger commands are a Linux ABI defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) rather than by an external standard. The DSP control messages follow the Sound Open Firmware IPC4 (Intel Audio DSP) protocol whose message layout is in [`include/sound/sof/ipc4/header.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h). The codec link is governed by the MIPI SoundWire and the MIPI SoundWire Device Class for Audio (SDCA) specifications, both membership-gated, and the host DMA path uses the Intel High Definition Audio stream descriptor model whose register layout the [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) in [`include/sound/hdaudio.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h) describes.

## LINUX KERNEL

### ALSA PCM core entry points (pcm_native.c, pcm.c, pcm_lib.c)

- [`'\<snd_pcm_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869): file-open handler that adds the file to the card, then loops on [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) honoring O_NONBLOCK
- [`'\<snd_pcm_open_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767): attach the substream, init constraints, and call the substream open op
- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): allocate the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) and set the initial [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) with [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725)
- [`'\<snd_pcm_hw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754): refine and apply hardware params, call the substream hw_params op, advance to [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) with [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621)
- [`'\<snd_pcm_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997): run [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) so the substream prepare op runs and the state becomes [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309)
- [`'\<snd_pcm_do_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) / [`'\<snd_pcm_post_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976): the do/post halves of the prepare action
- [`'\<snd_pcm_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504): run [`snd_pcm_action_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1490) with the target state [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310)
- [`'\<snd_pcm_do_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) / [`'\<snd_pcm_post_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1475): call the trigger op with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99), then set the running state
- [`'\<snd_pcm_period_elapsed\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933): the interrupt-time entry that takes the stream lock and calls [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900)

### snd_pcm state and runtime (uapi/sound/asound.h, pcm.h)

- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the per-substream runtime, holding [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the hw params, and the [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) application buffer pointer
- [`'\<snd_pcm_state_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306): the state type whose values are [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308), [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309), and [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310)

### ASoC PCM core (soc-pcm.c, soc-dai.c)

- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): create the ALSA PCM for a DAI link and install the [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1147) callbacks through [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510)
- [`'\<soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) / [`'\<__soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854): open the components, run [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) on each DAI, activate the runtime
- [`'\<soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) / [`'\<__soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070): run [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on the CODEC and CPU DAIs and [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) on the component
- [`'\<soc_pcm_prepare\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) / [`'\<__soc_pcm_prepare\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933): run [`snd_soc_pcm_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L588) and [`snd_soc_pcm_component_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063), then unmute and emit the DAPM stream-start event
- [`'\<soc_pcm_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198): select START/STOP order and run each row of the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1185) dispatch table
- [`'\<dpcm_fe_dai_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760): the dynamic (DPCM) front-end open op installed when [`rtd->dai_link->dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) is set, which walks the FE-to-BE path before startup
- [`'\<snd_soc_pcm_dai_trigger\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618): drive [`soc_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603) across every DAI of the runtime
- [`'\<snd_soc_dai_startup\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) / [`'\<snd_soc_dai_hw_params\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405): the per-DAI op wrappers the open and hw_params steps reach

### SOF component ops (sof/pcm.c)

- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): fill the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) named `sof-audio-component` with the PCM ops below
- [`'\<sof_pcm_open\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536): set the [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) constraints from the topology PCM caps
- [`'\<sof_pcm_hw_params\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116): boot the DSP if needed, program the host DMA via [`snd_sof_pcm_platform_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L439), set up the connected widgets, and build the host page table
- [`'\<sof_pcm_prepare\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315): set up the widget list for the pipeline and call the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) hw_params, marking the stream prepared
- [`'\<sof_pcm_trigger\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385): order the IPC and the platform DMA trigger and call the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) trigger

### SOF IPC4 pipeline trigger (sof/ipc4-pcm.c, sof/ipc4/header.h)

- [`'ipc4_pcm_ops':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311): the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) for IPC4, with [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) and [`platform_stop_during_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) set
- [`'\<sof_ipc4_pcm_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588): translate the PCM trigger command to a [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137) value and call [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414)
- [`'\<sof_ipc4_trigger_pipelines\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414): order the pipelines sink to source, transition through [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), then set the final [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142)
- [`'\<sof_ipc4_set_multi_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90): build the SET_PIPELINE_STATE IPC4 message and send it with [`sof_ipc_tx_message_no_reply()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L745)
- [`'\<sof_ipc4_set_pipeline_state\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124): the single-pipeline form of the same message, packing the instance id with [`SOF_IPC4_GLB_PIPE_STATE_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L193)
- [`'\<enum sof_ipc4_pipeline_state\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137): the DSP pipeline states, including [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141) and [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142)
- [`'\<enum sof_ipc4_global_msg\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L87): the global message type set, including [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103)

### SoundWire stream lifecycle (sdw_utils/soc_sdw_utils.c, soundwire/stream.c, codecs/rt722-sdca.c)

- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): the BE DAI prepare op that finds the stream on the CPU DAI and calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_trigger\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050): the BE DAI trigger op that calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) on START and [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) on STOP
- [`'\<sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533): move the SoundWire stream to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) by computing and applying bus params
- [`'\<sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619): move the stream to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) and start the data ports
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): the codec hw_params op that adds the slave to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)

### HDA host DMA path (sof/intel/hda-stream.c, sof/intel/hda-pcm.c, hdaudio.h)

- [`'\<struct hdac_stream\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516): the HD-audio host DMA descriptor, with the BDL buffer, the position buffer, and the [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) flag
- [`'\<struct hdac_ext_stream\>':'include/sound/hdaudio_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47): the extended stream that wraps [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) for the host and link processing-pipe pointers
- [`'\<hda_dsp_pcm_trigger\>':'sound/soc/sof/intel/hda-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177): the platform pcm_trigger op that finds the [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) and calls [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392)
- [`'\<hda_dsp_stream_trigger\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392): set or clear the stream-descriptor DMA-run bit to start or stop the host ring
- [`'\<snd_sof_pcm_platform_trigger\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464): the inline that reaches the platform pcm_trigger op from [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM substream lifecycle, the runtime state machine, and the trigger callback contract
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the mute and DAPM ordering around prepare and trigger that the playback path follows
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where a front-end PCM and a SoundWire back-end DAI are triggered on separate paths
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream states and the prepare/enable/disable transitions the BE DAI ops drive
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component and DAI ops that the rt722-sdca driver implements

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware introduction and architecture](https://thesofproject.github.io/latest/introduction/index.html)
- [ALSA project library PCM documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The userspace side of playback is the PCM character-device ioctl set, whose file_operations entry [`snd_pcm_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3472) routes to [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363), with the frame-write path handled by [`snd_pcm_xferi_frames_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3280). Each ioctl drives one step of the state machine and one layer-by-layer descent through the ASoC and SOF callbacks.

| ioctl / syscall | ALSA core function | resulting PCM state |
|-----------------|--------------------|---------------------|
| `open("/dev/snd/pcmC0D0p")` | [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) |
| `SNDRV_PCM_IOCTL_PREPARE` | [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) | [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309) |
| `SNDRV_PCM_IOCTL_START` | [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |
| period IRQ from the host DMA | [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) | (stays running) |

The per-stage entry points each layer presents to the one above it follow the same four-step shape. Open and hw_params descend synchronously; trigger START is sequenced across three layers by the dispatch table; the period interrupt is the only data-path entry point and runs on the host DMA IRQ.

| stage | open entry | hw_params entry | prepare entry | trigger START entry |
|-------|------------|-----------------|---------------|---------------------|
| ALSA PCM core | [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) | [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) | [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) | [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) |
| ASoC soc-pcm | [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) | [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) | [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) | [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) |
| SOF component | [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) | [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) | [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) | [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) |
| SOF IPC4 | (none) | [`sof_ipc4_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036) | (via hw_params) | [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) |
| SoundWire BE DAI | (none) | (codec hw_params) | [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) | [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) |
| codec / HDA DMA | (codec set_stream) | [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) | [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) | [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) |

The kernel-internal interface between the ASoC core and the SOF component is the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) fills, and the interface between the SOF component and the DSP is the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) reached as [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311).

## DETAILS

### open: the substream is created and reaches SNDRV_PCM_STATE_OPEN

When aplay opens `/dev/snd/pcmC0D0p`, the PCM character device's file_operations route the open to [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which registers the file with the card and then loops calling [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816), retrying on `-EAGAIN` unless the file was opened O_NONBLOCK:

```c
/* sound/core/pcm_native.c:2869 */
static int snd_pcm_open(struct file *file, struct snd_pcm *pcm, int stream)
{
	int err;
	wait_queue_entry_t wait;
	...
	mutex_lock(&pcm->open_mutex);
	while (1) {
		err = snd_pcm_open_file(file, pcm, stream);
		if (err >= 0)
			break;
		if (err == -EAGAIN) {
			if (file->f_flags & O_NONBLOCK) {
				err = -EBUSY;
				break;
			}
		} else
			break;
		set_current_state(TASK_INTERRUPTIBLE);
		mutex_unlock(&pcm->open_mutex);
		schedule();
		mutex_lock(&pcm->open_mutex);
		...
	}
	...
}
```

[`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) calls [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767), which attaches the substream, completes the hardware constraints, and calls the substream open op. The op is the one [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) installed:

```c
/* sound/core/pcm_native.c:2767 */
int snd_pcm_open_substream(struct snd_pcm *pcm, int stream,
			   struct file *file,
			   struct snd_pcm_substream **rsubstream)
{
	struct snd_pcm_substream *substream;
	int err;

	err = snd_pcm_attach_substream(pcm, stream, file, &substream);
	if (err < 0)
		return err;
	...
	err = substream->ops->open(substream);
	if (err < 0)
		goto error;
	...
}
```

The initial state is set inside [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), which allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) and marks it [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) through [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725):

```c
/* sound/core/pcm.c:875 */
int snd_pcm_attach_substream(struct snd_pcm *pcm, int stream,
			     struct file *file,
			     struct snd_pcm_substream **rsubstream)
{
	...
	runtime = kzalloc_obj(*runtime);
	if (runtime == NULL)
		return -ENOMEM;
	...
	__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_OPEN);
	...
	substream->runtime = runtime;
	...
}
```

[`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) is where the substream ops are chosen at card-bind time. A dynamic link gets the DPCM front-end ops with [`dpcm_fe_dai_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760) as the open handler, and a non-DPCM link gets the plain ASoC ops, with [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) as the open handler:

```c
/* sound/soc/soc-pcm.c:2909 */
	/* ASoC PCM operations */
	if (rtd->dai_link->dynamic) {
		rtd->ops.open		= dpcm_fe_dai_open;
		rtd->ops.hw_params	= dpcm_fe_dai_hw_params;
		rtd->ops.prepare	= dpcm_fe_dai_prepare;
		rtd->ops.trigger	= dpcm_fe_dai_trigger;
		rtd->ops.hw_free	= dpcm_fe_dai_hw_free;
		rtd->ops.close		= dpcm_fe_dai_close;
		rtd->ops.pointer	= soc_pcm_pointer;
	} else {
		rtd->ops.open		= soc_pcm_open;
		rtd->ops.hw_params	= soc_pcm_hw_params;
		rtd->ops.prepare	= soc_pcm_prepare;
		rtd->ops.trigger	= soc_pcm_trigger;
		rtd->ops.hw_free	= soc_pcm_hw_free;
		rtd->ops.close		= soc_pcm_close;
		rtd->ops.pointer	= soc_pcm_pointer;
	}
```

[`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) takes the DPCM mutex and delegates to [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854), which opens the components, runs the link startup, runs [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) on the CPU and CODEC DAIs, sanity-checks the merged hardware constraints, and activates the runtime:

```c
/* sound/soc/soc-pcm.c:854 */
static int __soc_pcm_open(struct snd_soc_pcm_runtime *rtd,
			  struct snd_pcm_substream *substream)
{
	struct snd_soc_component *component;
	struct snd_soc_dai *dai;
	int i, ret = 0;
	...
	ret = soc_pcm_components_open(substream);
	if (ret < 0)
		goto err;

	ret = snd_soc_link_startup(substream);
	if (ret < 0)
		goto err;

	/* startup the audio subsystem */
	for_each_rtd_dais(rtd, i, dai) {
		ret = snd_soc_dai_startup(dai, substream);
		if (ret < 0)
			goto err;
	}
	...
	snd_soc_runtime_activate(rtd, substream->stream);
	ret = 0;
err:
	if (ret < 0)
		soc_pcm_clean(rtd, substream, 1);

	return soc_pcm_ret(rtd, ret);
}
```

The component open op for SOF is [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), reached because [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) set it on the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) named `sof-audio-component`. It copies the topology PCM capabilities into [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) so the rate, format, and buffer limits the DSP firmware supports become the constraints aplay negotiates against:

```c
/* sound/soc/sof/pcm.c:536 */
static int sof_pcm_open(struct snd_soc_component *component,
			struct snd_pcm_substream *substream)
{
	...
	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;
	...
	caps = &spcm->pcm.caps[substream->stream];

	/* set runtime config */
	runtime->hw.info = ops->hw_info; /* platform-specific */

	/* set any runtime constraints based on topology */
	runtime->hw.formats = le64_to_cpu(caps->formats);
	runtime->hw.period_bytes_min = le32_to_cpu(caps->period_size_min);
	runtime->hw.period_bytes_max = le32_to_cpu(caps->period_size_max);
	...
}
```

The registration that ties the SOF ops to ASoC happens once in [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823):

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
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
	...
}
```

The link's dynamic flag decides which op set fills that slot, a dynamic front-end taking the DPCM open and trigger and a plain link taking the direct pair, the choice read back when the substream opens:

```
    soc_new_pcm() picks rtd->ops by rtd->dai_link->dynamic
    ───────────────────────────────────────────────────────

    dai_link->dynamic   open op           trigger op
    ─────────────────   ───────────────   ──────────────────
    set (DPCM FE)       dpcm_fe_dai_open  dpcm_fe_dai_trigger
    unset (plain)       soc_pcm_open      soc_pcm_trigger

    same rtd->ops slot is read later by snd_pcm_open_substream
    via substream->ops->open
```

### hw_params: the codec joins the SoundWire stream and the host DMA is programmed

The HW_PARAMS ioctl reaches [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754). After refining the parameters against the merged constraints it calls the substream hw_params op, then on success records the chosen format, rate, periods, and buffer size in the runtime and advances the state to [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308):

```c
/* sound/core/pcm_native.c:754 */
	if (substream->ops->hw_params != NULL) {
		err = substream->ops->hw_params(substream, params);
		if (err < 0)
			goto _error;
	}

	runtime->access = params_access(params);
	runtime->format = params_format(params);
	...
	runtime->buffer_size = params_buffer_size(params);
	...
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_SETUP);
```

The op is [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), which locks and calls [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070). That function runs [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on each CODEC DAI, then each CPU DAI, then [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) on the component:

```c
/* sound/soc/soc-pcm.c:1070 */
	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		...
		ret = snd_soc_dai_hw_params(codec_dai, substream,
					    &tmp_params);
		if(ret < 0)
			goto out;

		soc_pcm_set_dai_params(codec_dai, &tmp_params);
		snd_soc_dapm_update_dai(substream, &tmp_params, codec_dai);
	}

	for_each_rtd_cpu_dais(rtd, i, cpu_dai) {
		...
		ret = snd_soc_dai_hw_params(cpu_dai, substream, &tmp_params);
		if (ret < 0)
			goto out;
		...
	}

	ret = snd_soc_pcm_component_hw_params(substream, params);
```

The CODEC DAI op runs [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116). For a playback substream the rt722-sdca driver selects the receive direction and the data port (port 1 on `RT722_AIF1` for headphone, port 3 on `RT722_AIF2` for speaker), builds a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) from the negotiated rate, channel count, and sample width, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		direction = SDW_DATA_DIR_RX;
		if (dai->id == RT722_AIF1)
			port = 1;
		else if (dai->id == RT722_AIF2)
			port = 3;
		else
			return -EINVAL;
	} else {
		...
	}
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt722->slave, &stream_config,
					&port_config, 1, sdw_stream);
```

The component op is [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116). It boots the DSP firmware on demand, programs the host DMA through [`snd_sof_pcm_platform_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L439), sets up the chain of connected pipeline widgets, finds the host copier widget by its component id and assigns it the DMA stream id through the topology host_config op, and builds the firmware page table that maps the application buffer:

```c
/* sound/soc/sof/pcm.c:116 */
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
		...
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
		...
	}
```

The host DMA descriptor itself is a [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516), wrapped by a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47). It carries the buffer-descriptor-list buffer, the position buffer, the stream-descriptor register pointer, and the [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) flag the trigger toggles:

```c
/* include/sound/hdaudio.h:516 */
struct hdac_stream {
	struct hdac_bus *bus;
	struct snd_dma_buffer bdl; /* BDL buffer */
	__le32 *posbuf;		/* position buffer pointer */
	int direction;		/* playback / capture (SNDRV_PCM_STREAM_*) */

	unsigned int bufsize;	/* size of the play buffer in bytes */
	unsigned int period_bytes; /* size of the period in bytes */
	unsigned int frags;	/* number for period in the play buffer */
	unsigned int fifo_size;	/* FIFO size */

	void __iomem *sd_addr;	/* stream descriptor pointer */
	...
	struct snd_pcm_substream *substream;	/* assigned substream,
						 * set in PCM open
						 */
	...
	unsigned char stream_tag;	/* assigned stream */
	unsigned char index;		/* stream index */
	...
	bool opened:1;
	bool running:1;
	bool prepared:1;
	...
};
```

Alongside that host descriptor the codec fills two configs from the same hw_params, the stream config taking rate, channel count, and width and the port config taking the port number and channel mask, both passed to the slave-add call:

```
    hw_params data feeding sdw_stream_add_slave (rt722-sdca)
    ─────────────────────────────────────────────────────────

    params (snd_pcm_hw_params)        dai->id selects the port
        │                             ──────────────────────────
        │ params_rate                 RT722_AIF1  ──▶ port = 1
        │ params_channels             RT722_AIF2  ──▶ port = 3
        │ params_format               (playback: direction = RX)
        ▼
    ┌─────────────────────────┐     ┌───────────────────────┐
    │ struct sdw_stream_config│     │ struct sdw_port_config│
    │   frame_rate            │     │   num     = port      │
    │   ch_count              │     │   ch_mask = GENMASK   │
    │   bps                   │     └───────────┬───────────┘
    │   direction = SDW_..RX  │                 │
    └───────────┬─────────────┘                 │
                └────────────────┬──────────────┘
                                 ▼
                      sdw_stream_add_slave(rt722->slave, ...)
```

### prepare: pipeline widgets are set up and the SoundWire stream is prepared

The PREPARE ioctl reaches [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997), which runs the [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) action. The do half [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) calls the substream prepare op and the post half [`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976) sets [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309):

```c
/* sound/core/pcm_native.c:1965 */
static int snd_pcm_do_prepare(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	int err;
	snd_pcm_sync_stop(substream, true);
	err = substream->ops->prepare(substream);
	if (err < 0)
		return err;
	return snd_pcm_do_reset(substream, state);
}

static void snd_pcm_post_prepare(struct snd_pcm_substream *substream,
				 snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	runtime->control->appl_ptr = runtime->status->hw_ptr;
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_PREPARED);
}
```

The op is [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979), which calls [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933). That function runs the link prepare, the component prepare [`snd_soc_pcm_component_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063), and the DAI prepare [`snd_soc_pcm_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L588), then emits the DAPM stream-start event and unmutes any DAI that is not muted at trigger:

```c
/* sound/soc/soc-pcm.c:933 */
static int __soc_pcm_prepare(struct snd_soc_pcm_runtime *rtd,
			     struct snd_pcm_substream *substream)
{
	struct snd_soc_dai *dai;
	int i, ret = 0;
	...
	ret = snd_soc_link_prepare(substream);
	if (ret < 0)
		goto out;

	ret = snd_soc_pcm_component_prepare(substream);
	if (ret < 0)
		goto out;

	ret = snd_soc_pcm_dai_prepare(substream);
	if (ret < 0)
		goto out;
	...
	snd_soc_dapm_stream_event(rtd, substream->stream,
			SND_SOC_DAPM_STREAM_START);

	for_each_rtd_dais(rtd, i, dai) {
		if (!snd_soc_dai_mute_is_ctrled_at_trigger(dai))
			snd_soc_dai_digital_mute(dai, 0, substream->stream);
	}
out:
	...
}
```

The component prepare op is [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315). On a fresh start it sets up the DAPM widget list for the pipeline and calls the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) hw_params, then marks the stream prepared:

```c
/* sound/soc/sof/pcm.c:315 */
	list = spcm->stream[dir].list;
	params = &spcm->params[substream->stream];
	platform_params = &spcm->platform_params[substream->stream];
	ret = sof_widget_list_setup(sdev, spcm, params, platform_params, dir);
	if (ret < 0) {
		...
	}

	if (pcm_ops && pcm_ops->hw_params) {
		ret = pcm_ops->hw_params(component, substream, params, platform_params);
		if (ret < 0)
			return ret;
	}

	spcm->prepared[substream->stream] = true;
```

On the SoundWire back end the prepare reaches the BE DAI prepare op [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031), which retrieves the stream from the first CPU DAI and calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533):

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

[`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) takes the bus lock and, from [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), computes and applies the bus parameters through [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453), moving the stream to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929):

```c
/* drivers/soundwire/stream.c:1533 */
int sdw_prepare_stream(struct sdw_stream_runtime *stream)
{
	bool update_params = true;
	int ret;
	...
	sdw_acquire_bus_lock(stream);

	if (stream->state == SDW_STREAM_PREPARED) {
		ret = 0;
		goto state_err;
	}

	if (stream->state != SDW_STREAM_CONFIGURED &&
	    stream->state != SDW_STREAM_DEPREPARED &&
	    stream->state != SDW_STREAM_DISABLED) {
		pr_err("%s: %s: inconsistent state state %d\n",
		       __func__, stream->name, stream->state);
		ret = -EINVAL;
		goto state_err;
	}
	...
	ret = _sdw_prepare_stream(stream, update_params);

state_err:
	sdw_release_bus_lock(stream);
	return ret;
}
```

### trigger START: the pipeline runs, the SoundWire stream enables, the host DMA starts

The START ioctl reaches [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504), whose do half [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) calls the substream trigger op with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) and whose post half [`snd_pcm_post_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1475) sets the target state, which [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) passed as [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310):

```c
/* sound/core/pcm_native.c:1452 */
static int snd_pcm_do_start(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state)
{
	int err;

	if (substream->runtime->trigger_master != substream)
		return 0;
	err = substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_START);
	/* XRUN happened during the start */
	if (err == -EPIPE)
		__snd_pcm_set_state(substream->runtime, SNDRV_PCM_STATE_XRUN);
	return err;
}

static void snd_pcm_post_start(struct snd_pcm_substream *substream,
			       snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_trigger_tstamp(substream);
	...
	__snd_pcm_set_state(runtime, state);
	...
}
```

The op is [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198), which runs the START group of the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1185) dispatch table in forward order. The table holds three function pointers per order, the link trigger, the component trigger, and the DAI trigger:

```c
/* sound/soc/soc-pcm.c:1185 */
static int (* const trigger[][TRIGGER_MAX])(struct snd_pcm_substream *substream, int cmd, int rollback) = {
	[SND_SOC_TRIGGER_ORDER_DEFAULT] = {
		snd_soc_link_trigger,
		snd_soc_pcm_component_trigger,
		snd_soc_pcm_dai_trigger,
	},
	[SND_SOC_TRIGGER_ORDER_LDC] = {
		snd_soc_link_trigger,
		snd_soc_pcm_dai_trigger,
		snd_soc_pcm_component_trigger,
	},
};
```

```c
/* sound/soc/soc-pcm.c:1198 */
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for (i = 0; i < TRIGGER_MAX; i++) {
			r = trigger[start][i](substream, cmd, 0);
			if (r < 0)
				break;
		}
	}
```

The DAI-trigger row reaches [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618), which runs [`soc_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L603) across every DAI of the runtime and marks each one so a rollback unwinds only what started:

```c
/* sound/soc/soc-dai.c:618 */
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for_each_rtd_dais(rtd, i, dai) {
			ret = soc_dai_trigger(dai, substream, cmd);
			if (ret < 0)
				break;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 0, substream->stream);

			soc_dai_mark_push(dai, substream, trigger);
		}
		break;
	...
	}
```

The component-trigger row reaches [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385). For START the IPC4 pcm_ops set [`ipc_first_on_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123), so the function sends the pipeline-state IPC before starting the host DMA. It calls the pcm_ops trigger first, then on success invokes [`snd_sof_pcm_platform_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464) to start the DMA:

```c
/* sound/soc/sof/pcm.c:385 */
	case SNDRV_PCM_TRIGGER_START:
		...
		if (pcm_ops && pcm_ops->ipc_first_on_start)
			ipc_first = true;
		break;
	...
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
	...
	}
```

The pcm_ops trigger is [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588), which maps the START, RESUME, and PAUSE_RELEASE commands to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) and the stop-family commands to [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), then calls [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414):

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

The DSP state values come from [`enum sof_ipc4_pipeline_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137):

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

[`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) orders the pipelines so the sink runs before the source. According to the comment, IPC4 requires pipelines to be triggered in order starting at the sink and walking all the way to the source, so the list is traversed in reverse when the target is [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142). It first drives the pipelines through [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), then sets the final running state:

```c
/* sound/soc/sof/ipc4-pcm.c:414 */
	if (state == SOF_IPC4_PIPE_RUNNING || state == SOF_IPC4_PIPE_RESET)
		for (i = pipeline_list->count - 1; i >= 0; i--) {
			spipe = pipeline_list->pipelines[i];
			sof_ipc4_add_pipeline_to_trigger_list(sdev, state, spipe, trigger_list,
							      pipe_priority);
		}
	else
		...

	/* no need to pause before reset or before pause release */
	if (state == SOF_IPC4_PIPE_RESET || cmd == SNDRV_PCM_TRIGGER_PAUSE_RELEASE)
		goto skip_pause_transition;

	/*
	 * set paused state for pipelines if the final state is PAUSED or when the pipeline
	 * is set to RUNNING for the first time after the PCM is started.
	 */
	ret = sof_ipc4_set_multi_pipeline_state(sdev, SOF_IPC4_PIPE_PAUSED, trigger_list);
	...
skip_pause_transition:
	/* else set the RUNNING/RESET state in the DSP */
	ret = sof_ipc4_set_multi_pipeline_state(sdev, state, trigger_list);
```

[`sof_ipc4_set_multi_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L90) builds the SET_PIPELINE_STATE message. The message type [`SOF_IPC4_GLB_SET_PIPELINE_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L103) goes in the primary word and the new state is carried alongside, and the message is sent with [`sof_ipc_tx_message_no_reply()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L745). When the list holds one entry it falls to the single-pipeline form [`sof_ipc4_set_pipeline_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L124):

```c
/* sound/soc/sof/ipc4-pcm.c:90 */
static int sof_ipc4_set_multi_pipeline_state(struct snd_sof_dev *sdev, u32 state,
					     struct ipc4_pipeline_set_state_data *trigger_list)
{
	struct sof_ipc4_msg msg = {{ 0 }};
	u32 primary, ipc_size;
	...
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
	...
	return sof_ipc_tx_message_no_reply(sdev->ipc, &msg, ipc_size);
}
```

The link-trigger row reaches the BE DAI trigger op [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050), which calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) for the start-family commands so the SoundWire data ports begin carrying PCM to the rt722-sdca codec:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1050 */
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
```

[`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) takes the bus lock and, from [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929), runs [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576) to move the stream to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930):

```c
/* drivers/soundwire/stream.c:1619 */
int sdw_enable_stream(struct sdw_stream_runtime *stream)
{
	int ret;
	...
	sdw_acquire_bus_lock(stream);

	if (stream->state == SDW_STREAM_ENABLED) {
		ret = 0;
		goto state_err;
	}

	if (stream->state != SDW_STREAM_PREPARED &&
	    stream->state != SDW_STREAM_DISABLED) {
		pr_err("%s: %s: inconsistent state state %d\n",
		       __func__, stream->name, stream->state);
		ret = -EINVAL;
		goto state_err;
	}

	ret = _sdw_enable_stream(stream);

state_err:
	sdw_release_bus_lock(stream);
	return ret;
}
```

That enable is the link row of three the dispatch table fires in turn, the link row enabling the SoundWire stream, the component row driving the pipeline to RUNNING, and the DAI row starting the host DMA:

```
    trigger START fan-out across the soc_pcm_trigger[][] rows
    ──────────────────────────────────────────────────────────
    time ↓
    ALSA core      │ soc-pcm     │ SOF + IPC4    │ SDW BE / host DMA
    ───────────────┼─────────────┼───────────────┼──────────────────
    snd_pcm_start  │             │               │
      do_start ──▶ │ soc_pcm_    │               │
                   │  trigger    │               │
                   │ runs the    │               │
                   │ 3 rows ──▶  │               │
      link row ────────────────────────────────▶ │ asoc_sdw_trigger
                   │             │               │  ─▶ sdw_enable_
                   │             │               │     stream ENABLED
      comp row ──────────────────▶ sof_pcm_      │
                   │             │  trigger ─▶   │
                   │             │ IPC4 SET_     │
                   │             │ PIPELINE_     │
                   │             │ STATE RUNNING │
      DAI row ─────────────────────────────────▶ │ hda_dsp_stream_
                   │             │               │  trigger: DMA run
    state RUNNING  │             │               │
```

### the data path and period interrupts

Once START has set the pipeline to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) and enabled the SoundWire stream, the host DMA is the last thing started. [`snd_sof_pcm_platform_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L464) routes to the platform pcm_trigger op, which on Intel is [`hda_dsp_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L177). It recovers the [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) from the runtime private data and calls [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392):

```c
/* sound/soc/sof/intel/hda-pcm.c:177 */
int hda_dsp_pcm_trigger(struct snd_sof_dev *sdev,
			struct snd_pcm_substream *substream, int cmd)
{
	struct hdac_stream *hstream = substream->runtime->private_data;
	struct hdac_ext_stream *hext_stream = stream_to_hdac_ext_stream(hstream);

	return hda_dsp_stream_trigger(sdev, hext_stream, cmd);
}
```

[`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) enables the stream interrupt and sets the DMA-run bit in the stream-descriptor control register, then polls until the run bit reads back set and marks [`hstream->running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) true:

```c
/* sound/soc/sof/intel/hda-stream.c:392 */
	case SNDRV_PCM_TRIGGER_START:
		if (hstream->running)
			break;

		snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, SOF_HDA_INTCTL,
					1 << hstream->index,
					1 << hstream->index);

		snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
					sd_offset,
					SOF_HDA_SD_CTL_DMA_START |
					SOF_HDA_CL_DMA_SD_INT_MASK,
					SOF_HDA_SD_CTL_DMA_START |
					SOF_HDA_CL_DMA_SD_INT_MASK);

		ret = snd_sof_dsp_read_poll_timeout(sdev,
					HDA_DSP_HDA_BAR,
					sd_offset, run,
					((run &	dma_start) == dma_start),
					HDA_DSP_REG_POLL_INTERVAL_US,
					HDA_DSP_STREAM_RUN_TIMEOUT);

		if (ret >= 0)
			hstream->running = true;

		break;
```

With the host DMA running, the data path carries each frame from the application buffer [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) through the host DMA ring described by the [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) buffer-descriptor list into the DSP host gateway, where the copier module of the pipeline reads it. The DSP runs the pipeline modules and the result leaves the chip on the SoundWire data ports the rt722-sdca driver selected in its hw_params op (port 1 for headphone playback on `RT722_AIF1`), and the codec renders it.

Each time the DMA finishes a period it raises a stream interrupt, and the Intel host interrupt handling reports the completed period to the PCM core with [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933). It takes the substream lock and advances the runtime pointer through [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900), which updates the hardware pointer and wakes a writer that is blocked waiting for free space:

```c
/* sound/core/pcm_lib.c:1933 */
void snd_pcm_period_elapsed(struct snd_pcm_substream *substream)
{
	if (snd_BUG_ON(!substream))
		return;

	guard(pcm_stream_lock_irqsave)(substream);
	snd_pcm_period_elapsed_under_stream_lock(substream);
}
```

[`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900) advances the pointer with [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L443) only while the stream is running, then fires the SIGIO notification that wakes the writer:

```c
/* sound/core/pcm_lib.c:1900 */
void snd_pcm_period_elapsed_under_stream_lock(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime;

	if (PCM_RUNTIME_CHECK(substream))
		return;
	runtime = substream->runtime;

	if (!snd_pcm_running(substream) ||
	    snd_pcm_update_hw_ptr0(substream, 1) < 0)
		goto _end;

#ifdef CONFIG_SND_PCM_TIMER
	if (substream->timer_running)
		snd_timer_interrupt(substream->timer, 1);
#endif
 _end:
	snd_kill_fasync(runtime->fasync, SIGIO, POLL_IN);
}
```

The stream stays in [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) as long as aplay keeps the buffer filled, and the same four-layer descent runs in reverse on stop, where [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) sends [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) calls [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707), and [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) clears the DMA-run bit.

```
    Period-interrupt loop over the runtime->dma_area ring
    ───────────────────────────────────────────────────────

    runtime->dma_area  (buffer_size frames, divided into periods)
    ┌──────────┬──────────┬──────────┬──────────┐
    │ period 0 │ period 1 │ period 2 │ period 3 │
    └────▲─────┴──────────┴──────▲───┴──────────┘
         │ hw_ptr                │ appl_ptr
         │ (DMA drained to here) │ (aplay wrote to here)
         │                       │
    DMA period IRQ          aplay write() fills ahead of hw_ptr
         │
         ▼
    snd_pcm_period_elapsed
         │
         ▼
    snd_pcm_update_hw_ptr0  advances hw_ptr
         │
         ▼
    SIGIO / wake writer  ──▶  free space appears, write() unblocks
```

### Per-ioctl control descent beside the parallel host-DMA and SoundWire data paths

Each aplay ioctl descends from the ALSA PCM core in [`pcm_native.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c) through the ASoC PCM core in [`soc-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c) to the [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) component and the [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) back-end DAI, while after START the processed PCM travels the two parallel transports of the host DMA ring ([`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516)) into the DSP and the SoundWire data ports out to the rt722-sdca codec.

```
    Playback path on Intel MTL SOF with a SoundWire rt722-sdca codec
    ───────────────────────────────────────────────────────────────

    control path (one ioctl per row)        data path (after START)

    aplay  /dev/snd/pcmC0D0p
    ┌───────────────────────────────────────┐
    │ open  hw_params  prepare  trigger     │
    └───┬──────┬─────────┬────────────┬─────┘
        ▼      ▼         ▼            ▼
    ALSA PCM core  (sound/core/pcm_native.c)
    ┌───────────────────────────────────────┐    application buffer
    │ snd_pcm_open / _hw_params / _prepare  │    (runtime->dma_area)
    │ snd_pcm_start  ─▶ state RUNNING       │           │
    └───┬───────────────────────────────────┘           ▼
        ▼  rtd->ops.*                            host DMA ring
    ASoC soc-pcm  (sound/soc/soc-pcm.c)         hdac_stream / BDL
    ┌───────────────────────────────────────┐           │
    │ soc_pcm_open / _hw_params / _prepare  │           ▼
    │ soc_pcm_trigger  ─▶ trigger[][]       │    DSP host gateway
    └───┬────────────────────┬────────┘    (copier widget)
        ▼  component                  ▼  CPU+CODEC DAI  │
    SOF component            BE DAI (asoc_sdw_*)        ▼
    ┌────────────────────┐   ┌───────────────────┐  pipeline modules
    │ sof_pcm_open       │   │ sdw_prepare_stream│  on the DSP
    │ sof_pcm_hw_params  │   │ sdw_enable_stream │      │
    │ sof_pcm_trigger    │   └────────┬──────────┘      ▼
    └───┬────────────────┘            │            SoundWire data
        ▼  IPC4 to DSP                ▼            ports (DP1/DP3)
    SET_PIPELINE_STATE RUNNING   SoundWire bus  ─────────▶ rt722-sdca
```
