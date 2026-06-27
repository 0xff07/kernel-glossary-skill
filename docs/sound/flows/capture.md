# Audio capture flow

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A capture stream on an Intel Meteor Lake laptop running Sound Open Firmware (SOF) with a Realtek rt722-sdca SoundWire codec is one PCM substream that the ALSA PCM core in [`sound/core/pcm_native.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c) advances through [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308), [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309), and [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) by running the per-substream [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) installed by ASoC, the ASoC dynamic-PCM layer in [`sound/soc/soc-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c) splits the work into a front-end (FE) host DMA link handled by the SOF component through [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) / [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) / [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) and a back-end (BE) SoundWire link handled by [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) and the machine ops [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) / [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050), and SOF drives the DSP capture pipeline over IPC4 through [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) and [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) while the codec joins the SoundWire TX data port to the same stream with [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) and the host DMA ring is programmed by [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) and read back by [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497).

```
    Capture path (Intel MTL SOF + rt722-sdca over SoundWire)
    ────────────────────────────────────────────────────────

    userspace  arecord ── read() / mmap ──▶ app buffer
       │  open / ioctl(HW_PARAMS, PREPARE, START)
       ▼
    ┌──────────────────────────────────────────────────────────┐
    │ ALSA PCM core   pcm_native.c                             │
    │   snd_pcm_open ▸ hw_params ▸ prepare ▸ start             │
    │   runtime->state: OPEN ▸ SETUP ▸ PREPARED ▸ RUNNING      │
    └───────────────────────────┬──────────────────────────────┘
                                │ rtd->ops (soc_new_pcm)
                                ▼
    ┌──────────────────────────────────────────────────────────┐
    │ ASoC DPCM   soc-pcm.c                                    │
    │   FE host link  ◀──────────────▶  BE SoundWire link      │
    └──────────┬──────────────────────────────────┬────────────┘
               │ component ops                     │ snd_soc_ops + DAI ops
               ▼                                   ▼
    ┌────────────────────────┐         ┌────────────────────────┐
    │ SOF   sof/pcm.c        │         │ rt722-sdca codec       │
    │   IPC4 capture         │         │   TX port 2 (aif1) /   │
    │   pipeline (host=sink) │         │   TX port 6 (aif3)     │
    └──────────┬─────────────┘         └───────────┬────────────┘
               │ host DMA ring                     │ SoundWire bus
               ▼                                   ▼
       ┌───────────────┐                   ┌───────────────┐
       │ HDA host DMA  │ ◀── DSP copier ── │  ADC / DMic   │
       │ position buf  │     gateway       │  capture      │
       └───────┬───────┘                   └───────────────┘
               │ period IRQ ▸ snd_pcm_period_elapsed
               ▼
       app read pointer advances

    control path: open ▸ hw_params ▸ prepare ▸ trigger (top to bottom)
    data path:    mic ▸ TX port ▸ DSP copier ▸ host DMA ▸ app (bottom to top)
```

## SUMMARY

The application opens [`/dev/snd/pcmCxDyc`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645), where the trailing `c` marks the capture substream named by the [`pcmC%iD%i%c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645) format string, and the open reaches [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which adds the file to the card and loops on [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) until the substream is free. The substream callbacks were installed by ASoC at card-build time in [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909), which gives the dynamic FE link the `dpcm_fe_dai_*` ops and gives the no_pcm codec BE link the direct `soc_pcm_*` ops. The SOF component open op [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) seeds the host DMA runtime constraints from topology, and the runtime is left in [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307).

The [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) ioctl runs [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), which refines the parameters, allocates the managed DMA buffer with [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420), calls the FE [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and on success advances the runtime to [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) through [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621). The FE host op [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) programs the host DMA through [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) and connects the DSP capture widgets, while the codec BE op [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) takes the capture branch, selecting the SoundWire TX data port (port 2 for the headset-mic capture DAI on [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226), port 6 for the four-channel digital-mic capture DAI on [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228)), setting [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172), and joining the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), which advances the SoundWire stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926).

The [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) ioctl runs [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997), whose action [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) calls the FE prepare op and moves the runtime to [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309). The SOF FE prepare op [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) materializes the DSP widget list, and the machine BE prepare op [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) to advance the SoundWire stream to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929).

The [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) ioctl runs [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504), whose action [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) calls the FE trigger op with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) and sets [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310). The SOF FE trigger op [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) sends an IPC4 message through [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588) and [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) to drive the capture pipeline to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142), and the machine BE trigger op [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) to advance the SoundWire stream to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930). From then on the microphone ADC samples flow out of the codec TX data port, across the SoundWire bus into the DSP copier gateway, through the capture pipeline whose sink is the host DMA, and into the mmapped buffer, and each host DMA period completion drives [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) (scheduled through the SOF work item [`snd_sof_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43)) so the application read pointer advances.

## SPECIFICATIONS

The capture flow is a Linux kernel software construct with no single hardware specification. The host DMA is the HD Audio stream descriptor ring defined by the Intel High Definition Audio Specification, the codec link is governed by the MIPI SoundWire Specification and the MIPI SoundWire Device Class for Audio (SDCA) that the rt722-sdca codec implements, and the DSP control transport is the SOF IPC4 (Intel Audio DSP) message protocol. The PCM sample formats the stream carries, for example [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183) and [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187), are the ALSA PCM format definitions. The MIPI specifications are membership-gated and are not linked here.

## LINUX KERNEL

### ALSA PCM core entry points (pcm_native.c, pcm_lib.c)

- [`'\<snd_pcm_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869): open the PCM, take a module reference, and loop on [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816); the device node is the capture substream `pcmCxDyc`
- [`'\<snd_pcm_common_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363): the ioctl dispatch that routes [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692), and [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) to their handlers
- [`'\<snd_pcm_hw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754): refine parameters, allocate the DMA buffer, call the ops [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and set [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308)
- [`'\<snd_pcm_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) / [`'\<snd_pcm_do_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965): run the ops [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and move to [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309)
- [`'\<snd_pcm_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) / [`'\<snd_pcm_do_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452): run the ops [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) and move to [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310)
- [`'\<snd_pcm_set_state\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621): write [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) in the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_pcm_mmap_data\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969): map the DMA buffer into the application address space, rejecting `VM_WRITE` for a capture substream
- [`'\<snd_pcm_period_elapsed\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) / [`'\<snd_pcm_period_elapsed_under_stream_lock\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900): update the hardware pointer and wake readers when a captured period is ready

### ASoC dynamic PCM (soc-pcm.c, soc-dai.c, soc-link.c)

- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): create the ALSA PCM and install [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1083); the dynamic FE gets [`dpcm_fe_dai_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760), the codec BE gets [`soc_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917)
- [`'\<dpcm_fe_dai_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760): resolve the FE-to-BE path and open the FE and connected BEs
- [`'\<dpcm_fe_dai_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151): apply parameters to every connected BE, then to the FE
- [`'\<dpcm_fe_dai_prepare\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2510): prepare the connected BEs through [`dpcm_be_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2510) then the FE through [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854)
- [`'\<dpcm_fe_dai_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2450) / [`'\<dpcm_be_dai_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184): trigger the FE, then propagate the command to every connected BE
- [`'\<soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) / [`'\<__soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854): open the codec DAI and component on the BE link
- [`'\<soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) / [`'\<__soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070): apply parameters to the codec DAI through [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405)
- [`'\<soc_pcm_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198): order the component, DAI, and link triggers for the BE
- [`'\<snd_soc_link_prepare\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86) / [`'\<snd_soc_link_trigger\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142): call the machine link's [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) prepare and trigger ops, which on the SoundWire BE are [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) and [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050)
- [`'\<snd_soc_dai_get_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L579): read the SoundWire stream handle back from the CPU DAI for the prepare and trigger ops

### SOF PCM component (sof/pcm.c)

- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): fill the SOF [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) with the [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L839), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L841), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L842), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L844), and [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L845) callbacks and the BE [`be_hw_params_fixup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L869)
- [`'\<sof_pcm_open\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536): seed [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) from topology caps and reset the position counters
- [`'\<sof_pcm_hw_params\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116): program the host DMA, find the host widget by [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329), build the page table, and connect the DSP widget list for the capture stream
- [`'\<sof_pcm_prepare\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315): set up the connected widget list and re-run hw_params after a resume or xrun
- [`'\<sof_pcm_trigger\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385): order the IPC4 pipeline command against the platform DMA start and stop, always in non-atomic context
- [`'\<sof_pcm_pointer\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497): report the capture position from the DSP-written [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142)
- [`'\<snd_sof_pcm_period_elapsed\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43) / [`'\<snd_sof_pcm_period_elapsed_work\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L26): defer [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) to a work item so a STOP IPC is not sent from interrupt context
- [`'\<sof_pcm_dai_link_fixup\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L719): fix the BE rate, channels, and format from topology

### SOF IPC4 pipeline trigger (sof/ipc4-pcm.c)

- [`'\<sof_ipc4_pcm_trigger\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588): map the PCM trigger command to a pipeline state, [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) to [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142)
- [`'\<sof_ipc4_trigger_pipelines\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414): walk the pipeline list sink-to-source and set each pipeline's state in the DSP
- [`'\<sof_ipc4_pcm_hw_params\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1036): prime the IPC4 timestamp and position info for delay reporting
- [`'\<sof_ipc4_pcm_pointer\>':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161): compute the host-side capture pointer and the head/tail delay across the DSP, with the capture branch reading the DAI counter as the head
- [`'ipc4_pcm_ops':'sound/soc/sof/ipc4-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311): the [`struct sof_ipc_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) wiring trigger, hw_params, hw_free, dai_link_fixup, and pointer for IPC4
- [`'\<enum sof_ipc4_pipeline_state\>':'include/sound/sof/ipc4/header.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L137): [`SOF_IPC4_PIPE_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L140), [`SOF_IPC4_PIPE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L141), [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142)

### Intel HDA host DMA and position (sof/intel/hda-stream.c)

- [`'\<hda_dsp_stream_hw_params\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554): program the HD Audio stream descriptor (BDL, cyclic buffer length, format, position buffer) for the host DMA ring; the capture branch leaves [`fifo_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L739) zero
- [`'\<hda_dsp_stream_check\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L816): per-stream interrupt service that calls [`snd_sof_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43) when the IPC position is not used
- [`'\<hda_dsp_stream_threaded_handler\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L865): the threaded IRQ that loops over [`hda_dsp_stream_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L816)

### rt722-sdca codec capture (codecs/rt722-sdca.c)

- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): select the SoundWire TX data port and [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) for capture, then call [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`'\<rt722_sdca_set_sdw_stream\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op that stores the SoundWire stream handle as the DAI [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424)
- [`'rt722_sdca_dai':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries; the capture endpoints are "DP2 Headset Capture" on [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) and "DP6 DMic Capture" on [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228)

### SoundWire stream lifecycle (drivers/soundwire/stream.c)

- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): add the codec to the stream and advance it to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926)
- [`'\<sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533): program bus parameters and move the stream to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929)
- [`'\<sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619): enable the data ports and move the stream to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930)
- [`'\<enum sdw_stream_state\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926): the stream states from [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) to [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926)
- [`'\<enum sdw_data_direction\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172): [`SDW_DATA_DIR_RX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) (data into the port, playback) and [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) (data out of the port, capture)

### Machine driver SoundWire ops (machine and sdw_utils)

- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the Intel SoundWire machine [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) binding [`asoc_sdw_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) and [`asoc_sdw_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) on the codec BE link
- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): fetch the stream from the CPU DAI and call [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_trigger\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050): call [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) on START and [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) on STOP

### State and position types

- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the per-substream runtime carrying [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the buffer geometry, and the DMA area
- [`'\<struct snd_sof_pcm\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352): the SOF PCM device with per-direction [`stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) and [`prepared`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) flags
- [`'\<struct snd_sof_pcm_stream\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329): one direction's DSP mapping, holding the [`posn`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) record and the [`period_elapsed_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329)
- [`'\<struct sof_ipc_stream_posn\>':'include/sound/sof/stream.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L136): the DSP-written position with [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142) and [`dai_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L143) in bytes

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the FE host link and the BE codec link are opened, parametrized, and triggered independently
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget graph whose connected-widget list SOF builds for the capture pipeline
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream state machine the prepare and trigger ops drive
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM interface, the runtime states, and the period and buffer model
- [`Documentation/sound/hd-audio/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/index.rst): the HD Audio controller and stream model used by the host DMA

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library PCM documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The application uses the ALSA PCM character-device ioctls, and each one drives one runtime state transition. The mapping from the userspace request to the PCM core handler, the FE op SOF runs, the BE op the codec and machine run, and the resulting [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is fixed for the capture direction.

| userspace request | PCM core handler | SOF FE op | codec/machine BE op | resulting state |
|-------------------|------------------|-----------|---------------------|-----------------|
| `open("pcmCxDyc")` | [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) | [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) | [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) | [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) | [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) | [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) |
| [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) | [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) | [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315) | [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) | [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309) |
| [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) | [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) | [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385) | [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |
| `read()` / `mmap` | [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) | (DSP runs) | (codec runs) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |

The SoundWire stream that the codec BE drives advances through [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) one step behind the PCM ioctls.

| ioctl stage | SoundWire op | stream state after |
|-------------|--------------|--------------------|
| hw_params | [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) | [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) |
| prepare | [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) | [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) |
| trigger START | [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) | [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) |

## DETAILS

### Open: the substream and the three layers

The capture device node is `pcmCxDyc`, where the trailing `c` distinguishes the capture substream from the playback `p`. The name is set in [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044) with [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dev_printk.h#L162), choosing the suffix from the stream index:

```c
/* sound/core/pcm.c:645 */
	dev_set_name(pstr->dev, "pcmC%iD%i%c", pcm->card->number, pcm->device,
		     stream == SNDRV_PCM_STREAM_PLAYBACK ? 'p' : 'c');
```

Opening that node reaches [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which adds the file to the card, takes a module reference, and loops on [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) until the substream is free. The substream callbacks were installed by ASoC at card-build time. [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) chooses the op set from whether the link is [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795). On the Intel SoundWire machine the host-facing FE link is dynamic and the codec link is a [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) BE, so the FE substream gets the DPCM ops and the codec BE substream gets the direct ops:

```c
/* sound/soc/soc-pcm.c:2947 */
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

The FE ops belong to the SOF audio component, since SOF registers the FE host link under its own [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) wires the component callbacks the DPCM FE ops invoke and installs the BE fixup:

```c
/* sound/soc/sof/pcm.c:836 */
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
```

[`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) seeds the host DMA constraints from the topology stream caps so the application sees the periods and buffer sizes the DSP firmware supports, and it resets the per-direction position counters that the pointer op reads later:

```c
/* sound/soc/sof/pcm.c:563 */
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
```

After a successful open the runtime is in [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), the first of the [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306) values:

```c
/* include/uapi/sound/asound.h:306 */
typedef int __bitwise snd_pcm_state_t;
#define	SNDRV_PCM_STATE_OPEN		((__force snd_pcm_state_t) 0) /* stream is open */
#define	SNDRV_PCM_STATE_SETUP		((__force snd_pcm_state_t) 1) /* stream has a setup */
#define	SNDRV_PCM_STATE_PREPARED	((__force snd_pcm_state_t) 2) /* stream is ready to start */
#define	SNDRV_PCM_STATE_RUNNING		((__force snd_pcm_state_t) 3) /* stream is running */
```

### HW_PARAMS: buffer, host DMA, and the codec TX port

The [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) ioctl is dispatched in [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) to [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754). It refines the parameters, allocates the managed DMA buffer with [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420), calls the FE ops [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), records the negotiated geometry into the runtime, and on success sets [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308):

```c
/* sound/core/pcm_native.c:800 */
	if (substream->managed_buffer_alloc) {
		err = snd_pcm_lib_malloc_pages(substream,
					       params_buffer_bytes(params));
		if (err < 0)
			goto _error;
		runtime->buffer_changed = err > 0;
	}

	if (substream->ops->hw_params != NULL) {
		err = substream->ops->hw_params(substream, params);
		if (err < 0)
			goto _error;
	}
	...
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_SETUP);
```

On the FE the op is [`dpcm_fe_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151), which applies the parameters to every connected BE and then to the FE. The FE host work runs in [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), which programs the platform host DMA, locates the host DMA widget by component id, builds the firmware page table for the just-allocated buffer, and connects the DSP widget list for the capture direction:

```c
/* sound/soc/sof/pcm.c:162 */
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
```

The platform layer that [`snd_sof_pcm_platform_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L389) calls is the Intel HDA host DMA programming in [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554). It writes the buffer descriptor list address, the cyclic buffer length, the stream format, and enables the position buffer that reports DMA progress. The FIFO-size read is conditioned on direction, so the capture branch leaves [`fifo_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L739) zero where playback would read it from the descriptor:

```c
/* sound/soc/sof/intel/hda-stream.c:730 */
	/* read FIFO size */
	if (hstream->direction == SNDRV_PCM_STREAM_PLAYBACK) {
		hstream->fifo_size =
			snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR,
					 sd_offset +
					 SOF_HDA_ADSP_REG_SD_FIFOSIZE);
		hstream->fifo_size &= SOF_HDA_SD_FIFOSIZE_FIFOS_MASK;
		hstream->fifo_size += 1;
	} else {
		hstream->fifo_size = 0;
	}
```

On the codec BE, [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) calls each codec DAI's hw_params through [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405), reaching [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116). The direction test is where capture and playback diverge in the codec. The capture branch sets [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) and selects port 2 for the headset-mic capture DAI on [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226) or port 6 for the four-channel digital-mic capture DAI on [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228), while the playback branch sets [`SDW_DATA_DIR_RX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) and selects a different port:

```c
/* sound/soc/codecs/rt722-sdca.c:1144 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		direction = SDW_DATA_DIR_RX;
		if (dai->id == RT722_AIF1)
			port = 1;
		else if (dai->id == RT722_AIF2)
			port = 3;
		else
			return -EINVAL;
	} else {
		direction = SDW_DATA_DIR_TX;
		if (dai->id == RT722_AIF1)
			port = 2;
		else if (dai->id == RT722_AIF3)
			port = 6;
		else
			return -EINVAL;
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

The [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) value names data leaving the codec port toward the bus, which is the capture direction, the inverse of the playback [`SDW_DATA_DIR_RX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) that carries data into the port:

```c
/* include/linux/soundwire/sdw.h:172 */
enum sdw_data_direction {
	SDW_DATA_DIR_RX = 0,
	SDW_DATA_DIR_TX = 1,
};
```

The codec received that [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) handle earlier through its [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op [`rt722_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102), which stashed it in the DAI per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) slot:

```c
/* sound/soc/codecs/rt722-sdca.c:1102 */
static int rt722_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}
```

The first [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) on a stream advances it from allocated to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), which ties the codec hw_params step to the SoundWire stream lifecycle. According to the comment, the bus does not yet know how many peripherals will join, so the first add is what sets the state:

```c
/* drivers/soundwire/stream.c:2201 */
	/*
	 * Change stream state to CONFIGURED on first Slave add.
	 * Bus is not aware of number of Slave(s) in a stream at this
	 * point so cannot depend on all Slave(s) to be added in order to
	 * change stream state to CONFIGURED.
	 */
	stream->state = SDW_STREAM_CONFIGURED;
```

The port and bus direction handed to that add come from a two-way test, capture selecting TX with port 2 or 6 and playback selecting RX with port 1 or 3 by the DAI id:

```
    rt722_sdca_pcm_hw_params: direction selects port + SDW dir
    ───────────────────────────────────────────────────────────

    substream->stream   dai->id      direction       port
    ─────────────────   ──────────   ─────────────   ────
    PLAYBACK            RT722_AIF1   SDW_DATA_DIR_RX    1
    PLAYBACK            RT722_AIF2   SDW_DATA_DIR_RX    3
    CAPTURE             RT722_AIF1   SDW_DATA_DIR_TX    2
    CAPTURE             RT722_AIF3   SDW_DATA_DIR_TX    6

    chosen port + direction go into stream_config / port_config,
    then sdw_stream_add_slave advances the stream to CONFIGURED
```

### PREPARE: DSP widget list and SoundWire prepare

The [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) ioctl runs [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997), which runs the non-atomic prepare action. The action [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) calls the FE ops prepare and resets the position:

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
```

The FE op [`dpcm_fe_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2510) prepares the connected BEs through [`dpcm_be_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2510) and then the FE through [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854), advancing the FE link state to [`SND_SOC_DPCM_STATE_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38):

```c
/* sound/soc/soc-pcm.c:2510 */
static int dpcm_fe_dai_prepare(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(substream);
	int stream = substream->stream, ret = 0;

	snd_soc_dpcm_mutex_lock(fe);
	...
	dpcm_set_fe_update_state(fe, stream, SND_SOC_DPCM_UPDATE_FE);

	ret = dpcm_be_dai_prepare(fe, stream);
	if (ret < 0)
		goto out;

	/* call prepare on the frontend */
	ret = __soc_pcm_prepare(fe, substream);
	if (ret < 0)
		goto out;

	fe->dpcm[stream].state = SND_SOC_DPCM_STATE_PREPARE;
	...
}
```

The FE host prepare reaches [`sof_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L315), which sets up the connected widget list with [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h), re-running hw_params first if the stream is recovering from an xrun, so the DSP capture pipeline graph is materialized before the trigger:

```c
/* sound/soc/sof/pcm.c:358 */
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
	...
	spcm->prepared[substream->stream] = true;
```

The codec BE prepare runs through the machine link op. The Intel SoundWire machine sets its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) on the codec link:

```c
/* sound/soc/intel/boards/sof_sdw.c:865 */
static const struct snd_soc_ops sdw_ops = {
	.startup = asoc_sdw_startup,
	.prepare = asoc_sdw_prepare,
	.trigger = asoc_sdw_trigger,
	.hw_params = asoc_sdw_hw_params,
	.hw_free = asoc_sdw_hw_free,
	.shutdown = asoc_sdw_shutdown,
};
```

That prepare op is reached from the BE prepare path through [`snd_soc_link_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86). [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) reads the SoundWire stream handle back from the first CPU DAI with [`snd_soc_dai_get_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L579) and calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533):

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

[`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) computes and applies the bus parameters and moves the stream from [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929). After [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) returns, the runtime is in [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309), ready to be triggered.

### START: IPC4 pipeline RUNNING and SoundWire enable

The [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) ioctl runs [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504), and its action [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) calls the FE ops trigger with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99):

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
```

The FE op [`dpcm_fe_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2450) triggers the FE host link and then propagates the command to every BE through [`dpcm_be_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184), which calls [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) on the codec BE substream. The FE host trigger reaches [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), which orders the IPC4 pipeline command against the platform DMA start. With [`ipc_first`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) set for a START, the IPC runs first and the host DMA is started only after the pipeline IPC succeeds:

```c
/* sound/soc/sof/pcm.c:457 */
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
```

The IPC4 pcm_ops trigger is [`sof_ipc4_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L588), wired in the [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311) function pointer struct. It maps the START command to the [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) pipeline state and forwards both the state and the original command:

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
	...
	/* set the pipeline state */
	return sof_ipc4_trigger_pipelines(component, substream, state, cmd);
}
```

[`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) walks the pipeline list and sets each pipeline's state in the firmware. According to the comment, IPC4 requires the trigger to start at the sink and walk to the source, so for a START or RESET it traverses [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) in reverse; for a capture stream the sink is the host DMA, so the host pipeline is triggered first on the way to RUNNING:

```c
/* sound/soc/sof/ipc4-pcm.c:493 */
	/*
	 * IPC4 requires pipelines to be triggered in order starting at the sink and
	 * walking all the way to the source. So traverse the pipeline_list in the order
	 * sink->source when starting PCM's and in the reverse order to pause/stop PCM's.
	 ...
	 */
	if (state == SOF_IPC4_PIPE_RUNNING || state == SOF_IPC4_PIPE_RESET)
		for (i = pipeline_list->count - 1; i >= 0; i--) {
			spipe = pipeline_list->pipelines[i];
			sof_ipc4_add_pipeline_to_trigger_list(sdev, state, spipe, trigger_list,
							      pipe_priority);
		}
```

The pipeline state values come from the IPC4 header, where [`SOF_IPC4_PIPE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L142) is the capture-active state:

```c
/* include/sound/sof/ipc4/header.h:137 */
enum sof_ipc4_pipeline_state {
	SOF_IPC4_PIPE_INVALID_STATE,
	SOF_IPC4_PIPE_UNINITIALIZED,
	SOF_IPC4_PIPE_RESET,
	SOF_IPC4_PIPE_PAUSED,
	SOF_IPC4_PIPE_RUNNING,
};
```

The codec BE trigger, propagated by [`dpcm_be_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) into [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) and then through [`snd_soc_link_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142), runs the machine op [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050). On START it enables the SoundWire stream with [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619), and on STOP it disables it with [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1066 */
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
```

[`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) enables the bus data ports and moves the stream from [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930). After the FE trigger op returns success, [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) leaves the runtime in [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310).

```
    START trigger across the DPCM front-end and back-end
    ──────────────────────────────────────────────────────
    time ↓
    ALSA core       │ DPCM FE       │ SOF host+IPC4 │ codec BE / SDW
    ────────────────┼───────────────┼───────────────┼────────────────
    snd_pcm_start   │               │               │
      do_start ──▶  │ dpcm_fe_dai_  │               │
                    │  trigger      │               │
      FE host ──────────────────────▶ sof_pcm_      │
                    │               │  trigger      │
                    │               │ ipc_first ─▶  │
                    │               │ IPC4 pipe     │
                    │               │ RUNNING       │
                    │               │ then DMA      │
      BE propagate ─▶ dpcm_be_dai_  │               │
                    │  trigger ─────────────────────▶ soc_pcm_trigger
                    │               │               │  ─▶ asoc_sdw_
                    │               │               │     trigger
                    │               │               │  ─▶ sdw_enable_
                    │               │               │     stream ENABLED
    state RUNNING   │               │               │
```

### Running: the capture data path and the read pointer

With the pipeline RUNNING and the SoundWire stream ENABLED, the microphone ADC (the headset-mic codec on [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226), or the digital-mic array on [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228)) drives samples out of the codec TX data port (port 2 or port 6) onto the SoundWire bus. The DSP copier gateway pulls those samples off the bus into the capture pipeline, and the pipeline whose sink is the host DMA copies the processed frames into the host DMA ring, the same buffer that [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) allocated and [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) programmed as the cyclic DMA target.

Each completed period raises a host DMA interrupt. The Intel HDA threaded handler [`hda_dsp_stream_threaded_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L865) loops over [`hda_dsp_stream_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L816), which acknowledges the stream status and, when the DSP does not report position over IPC, notifies ALSA directly:

```c
/* sound/soc/sof/intel/hda-stream.c:852 */
		/* Inform ALSA only if the IPC position is not used */
		if (s->substream && sof_hda->no_ipc_position) {
			snd_sof_pcm_period_elapsed(s->substream);
		} else if (s->cstream) {
			hda_dsp_compr_bytes_transferred(s, s->cstream->direction);
			snd_compr_fragment_elapsed(s->cstream);
		}
```

[`snd_sof_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L43) does not call the ALSA core directly from the interrupt path. According to its comment, calling [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) inline could send a STOP IPC from interrupt context on drain or xrun, so it schedules a work item instead:

```c
/* sound/soc/sof/pcm.c:56 */
	/*
	 * snd_pcm_period_elapsed() can be called in interrupt context
	 * before IRQ_HANDLED is returned. Inside snd_pcm_period_elapsed(),
	 * when the PCM is done draining or xrun happened, a STOP IPC will
	 * then be sent and this IPC will hit IPC timeout.
	 * To avoid sending IPC before the previous IPC is handled, we
	 * schedule delayed work here to call the snd_pcm_period_elapsed().
	 */
	schedule_work(&spcm->stream[substream->stream].period_elapsed_work);
```

The work function [`snd_sof_pcm_period_elapsed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L26) runs [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) in process context, reaching it through the [`struct snd_sof_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L329) the work item is embedded in:

```c
/* sound/soc/sof/pcm.c:26 */
static void snd_sof_pcm_period_elapsed_work(struct work_struct *work)
{
	struct snd_sof_pcm_stream *sps =
		container_of(work, struct snd_sof_pcm_stream,
			     period_elapsed_work);

	snd_pcm_period_elapsed(sps->substream);
}
```

[`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) takes the stream lock and calls [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900), which updates the hardware pointer with [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c) and wakes any reader blocked in [`read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) or `poll`:

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
```

The pointer the application reads back is reported by [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497). On Meteor Lake the IPC4 [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L123) member [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) supplies the value; the fallback path in [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) reads the [`host_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L142) the DSP writes into the [`struct sof_ipc_stream_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L136) record and converts it to frames:

```c
/* sound/soc/sof/pcm.c:525 */
	/* read position from DSP */
	host = bytes_to_frames(substream->runtime,
			       spcm->stream[substream->stream].posn.host_posn);
	dai = bytes_to_frames(substream->runtime,
			      spcm->stream[substream->stream].posn.dai_posn);

	trace_sof_pcm_pointer_position(sdev, spcm, substream, host, dai);

	return host;
```

The DSP-written position is held in the firmware-shared [`struct sof_ipc_stream_posn`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/stream.h#L136), which keeps the host DMA position separate from the DAI position so the core can report both the application-side and the wire-side progress:

```c
/* include/sound/sof/stream.h:136 */
struct sof_ipc_stream_posn {
	struct sof_ipc_reply rhdr;
	uint32_t comp_id;	/**< host component ID */
	uint32_t flags;		/**< SOF_TIME_ */
	uint32_t wallclock_hz;	/**< frequency of wallclock in Hz */
	uint32_t timestamp_ns;	/**< resolution of timestamp in ns */
	uint64_t host_posn;	/**< host DMA position in bytes */
	uint64_t dai_posn;	/**< DAI DMA position in bytes */
	uint64_t comp_posn;	/**< comp position in bytes */
	uint64_t wallclock;	/**< audio wall clock */
	uint64_t timestamp;	/**< system time stamp */
	uint32_t xrun_comp_id;	/**< comp ID of XRUN component */
	int32_t xrun_size;	/**< XRUN size in bytes */
};
```

For the IPC4 delay calculation, [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) treats the two ends of the DSP differently by direction. On capture the DAI counter is the head and the host counter is the tail, the reverse of playback, because samples enter at the DAI side and leave at the host side:

```c
/* sound/soc/sof/ipc4-pcm.c:1255 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		head_cnt = host_cnt;
		tail_cnt = dai_cnt;
	} else {
		head_cnt = dai_cnt;
		tail_cnt = host_cnt;
	}
```

The application reads the captured frames from the mmapped buffer, set up by [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969), which for a capture stream requires only `VM_READ`, with the read pointer kept current by each period-elapsed update. The cycle of host DMA period interrupt, deferred [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933), and pointer advance repeats until the application drains and stops the stream.

```
    Capture data path and the deferred period-elapsed work
    ────────────────────────────────────────────────────────

    mic ADC ─▶ TX port ─▶ SoundWire bus ─▶ DSP copier gateway
                                                  │
                                                  ▼ writes frames
    host DMA cyclic ring (runtime->dma_area, position buffer)
    ┌──────────┬──────────┬──────────┬──────────┐
    │ period 0 │ period 1 │ period 2 │ period 3 │
    └──────────┴─────▲────┴──────────┴──────▲───┘
                     │ host_posn (DSP)      │ app read ptr
                     │ (sof_pcm_pointer)    │ (arecord read())

    period IRQ
        │  hda_dsp_stream_check
        ▼
    snd_sof_pcm_period_elapsed
        │  schedule_work  (no STOP IPC from IRQ context)
        ▼
    snd_sof_pcm_period_elapsed_work  (process context)
        │
        ▼
    snd_pcm_period_elapsed ─▶ update hw_ptr ─▶ wake reader
```

### Capture versus playback at every layer

The capture flow and the playback flow are the same code path taken in opposite directions at each layer. In the codec, [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) selects a TX data port with [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) for capture (port 2 on aif1, port 6 on aif3) where playback selects an RX port with [`SDW_DATA_DIR_RX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L172) (port 1 on aif1, port 3 on aif2). In the DSP, the capture pipeline has the host DMA copier as its sink and the DAI copier as its source, the reverse of the playback pipeline, so [`sof_ipc4_trigger_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L414) walks the list sink-to-source for both but the physical data moves the opposite way. In the host DMA, [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) leaves [`fifo_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L739) zero for the capture branch and reads it only for playback, and [`sof_ipc4_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1161) swaps the head and tail counters for the delay. The PCM core state machine and the SoundWire stream state machine run identically for both directions; the [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168) and [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167) indices and the [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) access permissions are what differ.

```
    Capture vs playback: same code, opposite direction per layer
    ──────────────────────────────────────────────────────────────

    layer / field            capture            playback
    ──────────────────────   ────────────────   ────────────────
    codec SDW direction      SDW_DATA_DIR_TX    SDW_DATA_DIR_RX
    rt722 port (aif1)        2                  1
    rt722 port (other aif)   6  (aif3)          3  (aif2)
    DSP pipeline sink        host DMA copier    DAI copier
    hda fifo_size            0  (left unset)    read from SD
    ipc4 delay head          dai_cnt            host_cnt
    ipc4 delay tail          host_cnt           dai_cnt
    mmap access              VM_READ only       VM_WRITE allowed

    PCM state machine and SoundWire state machine: identical both ways
```
