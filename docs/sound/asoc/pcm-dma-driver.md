# ASoC PCM DMA driver

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The ASoC platform component is the piece that moves PCM data between the ALSA application buffer and the audio hardware, and on most ASoC systems it is a thin shim over the kernel dmaengine framework supplied by [`sound/soc/soc-generic-dmaengine-pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c). A controller driver calls [`devm_snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L109), which allocates one [`struct dmaengine_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) wrapping an embedded [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and registers it with a fixed [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) whose PCM ops are the generic [`dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L148), [`dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L168), [`dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L278), and [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219) wired to the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) field. Those component ops delegate to the transport-neutral helpers in [`sound/core/pcm_dmaengine.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c), [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307), [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189), and [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251), each of which translates one ALSA PCM action into the matching [`dmaengine`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h) primitive on the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) requested for the substream. The DMA buffer itself is preallocated and torn down by the ALSA managed-buffer helper [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380), called from the `pcm_construct` op so the driver never allocates or frees the buffer by hand. On Intel x86-64 the dominant ASoC path is Sound Open Firmware, where the DMA is a host-to-DSP HDA stream rather than a generic dmaengine channel, so the component ops are [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), and [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) instead, but the same [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) hook and the same [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) buffer contract apply.

```
    ALSA application buffer (mmap), runtime->dma_area / dma_addr
            │  open / hw_params / trigger / pointer
            ▼
    struct snd_soc_component (PCM/DMA platform component)
    ┌──────────────────────────────────────────────────────────┐
    │  driver->open     ─▶ dmaengine_pcm_open                  │
    │  driver->trigger  ─▶ dmaengine_pcm_trigger               │
    │  driver->pointer  ─▶ dmaengine_pcm_pointer               │
    │  driver->pcm_construct ─▶ dmaengine_pcm_new (prealloc)   │
    └──────────────────────────────┬───────────────────────────┘
                                   │ delegates to core helpers
                                   ▼
    struct dmaengine_pcm  (wraps the component, holds chan[2])
    ┌──────────────────────────────────────────────────────────┐
    │  config ─▶ snd_dmaengine_pcm_config                      │
    │  chan[PLAYBACK]  ─▶ struct dma_chan                      │
    │  chan[CAPTURE]   ─▶ struct dma_chan                      │
    └──────────────────────────────┬───────────────────────────┘
                                   │ dmaengine_prep_dma_cyclic,
                                   │ dmaengine_submit, _tx_status
                                   ▼
                          dmaengine DMA channel / controller

    managed DMA buffer (snd_pcm_set_managed_buffer):
        prealloc at pcm_construct ─▶ runtime->dma_area / dma_addr
        per hw_params alloc, per hw_free release (core-driven)
```

## SUMMARY

A PCM/DMA platform component owns the data movement for an ASoC stream and registers as one [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) carrying a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) whose PCM ops the ASoC core calls during stream operation. The generic dmaengine bridge supplies a ready-made component driver. [`snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433), reached through the device-managed [`devm_snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L109), allocates a [`struct dmaengine_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) holding the per-direction [`chan`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) array and a pointer to the caller's [`struct snd_dmaengine_pcm_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141), then registers it with the static [`dmaengine_pcm_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L327) driver through [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885).

The component driver maps each PCM op to a core helper. [`dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L148) sets the runtime hardware parameters with [`dmaengine_pcm_set_runtime_hwparams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L98) and then calls [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) to attach the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) to the substream, [`dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L168) forwards to [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189), and [`dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L278) forwards to [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251). The [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219) requests the DMA channels and preallocates each substream's buffer with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380). The hardware-parameter side runs through [`dmaengine_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L76), which invokes the platform's [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callback, usually the supplied [`snd_dmaengine_pcm_prepare_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L50), to fill a [`struct dma_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447) from the CPU DAI's [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) via [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106).

The buffer contract is the same for every ASoC platform component. [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and its all-substream variant [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401) preallocate at construct time and place the substream into managed mode, in which the PCM core allocates the buffer before the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op and frees it after [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), so the position reported by the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op is always an offset into a buffer the core owns. On Intel x86-64 Sound Open Firmware platforms the DMA is an HDA host stream programmed by the DSP firmware, registered through [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) rather than the dmaengine bridge, and its [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) reads the DMA position from a firmware position structure or from the HDA stream registers via [`hda_dsp_stream_get_position()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L1063), while its [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) still preallocates the buffer with the same [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380).

## SPECIFICATIONS

The ASoC PCM/DMA platform component is a Linux kernel software construct and has no standalone hardware specification. The generic dmaengine bridge sits on the kernel [`dmaengine`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h) slave-DMA API, also an internal kernel interface. On Intel x86-64 the Sound Open Firmware host-stream path moves data over an HDA stream defined by the Intel High Definition Audio Specification, and the firmware interface between host and DSP is defined by the Sound Open Firmware project.

## LINUX KERNEL

### Generic dmaengine component ops (soc-generic-dmaengine-pcm.c)

- [`'\<dmaengine_pcm_open\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L148): the component [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; sets runtime hwparams, then calls [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) with the per-direction channel
- [`'\<dmaengine_pcm_close\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L162): the component [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; forwards to [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370)
- [`'\<dmaengine_pcm_trigger\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L168): the component [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; forwards to [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189)
- [`'\<dmaengine_pcm_pointer\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L278): the component [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; selects [`snd_dmaengine_pcm_pointer_no_residue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235) or [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) by the `SND_DMAENGINE_PCM_FLAG_NO_RESIDUE` flag
- [`'\<dmaengine_pcm_hw_params\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L76): the component [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; runs the [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callback and applies the result with [`dmaengine_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h)
- [`'\<dmaengine_pcm_new\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219): the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; requests channels and preallocates each substream's buffer with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380)
- [`'\<dmaengine_pcm_set_runtime_hwparams\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L98): builds the [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) from the DAI DMA data and the channel's [`struct dma_slave_caps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h), or copies a driver-supplied [`pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141)
- [`'\<snd_dmaengine_pcm_prepare_slave_config\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L50): generic [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141); calls [`snd_hwparams_to_dma_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c) then [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106)
- [`'\<dmaengine_pcm_can_report_residue\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L200): reads [`struct dma_slave_caps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h) and clears residue reporting when the granularity is `DMA_RESIDUE_GRANULARITY_DESCRIPTOR`

### Registration (soc-generic-dmaengine-pcm.c, soc-devres.c)

- [`'\<snd_dmaengine_pcm_register\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433): allocate a [`struct dmaengine_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175), request channels, and add the component with [`dmaengine_pcm_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L327) or [`dmaengine_pcm_component_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L339)
- [`'\<devm_snd_dmaengine_pcm_register\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L109): device-managed wrapper that registers the dmaengine PCM and unregisters it at device teardown
- [`'\<dmaengine_pcm_component\>':'sound/soc/soc-generic-dmaengine-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L327): the static [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) wiring the generic open/close/hw_params/trigger/pointer/pcm_construct ops

### Core dmaengine PCM helpers (pcm_dmaengine.c)

- [`'\<snd_dmaengine_pcm_open\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307): allocate a [`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L24), store the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) in it, and hang it off [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_dmaengine_pcm_close\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370): synchronize and free the runtime data through [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347)
- [`'\<snd_dmaengine_pcm_trigger\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189): map each `SNDRV_PCM_TRIGGER_*` command to the matching dmaengine call (prepare/submit/issue, pause, resume, terminate)
- [`'\<snd_dmaengine_pcm_pointer\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251): query [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h) and convert the residue into a frame position and a [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_dmaengine_pcm_pointer_no_residue\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235): the period-counting fallback that returns [`prtd->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L24) as frames when residue is unreliable
- [`'\<dmaengine_pcm_prepare_and_submit\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150): build a cyclic descriptor with [`dmaengine_prep_dma_cyclic()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h), attach the period callback, and submit it
- [`'\<dmaengine_pcm_dma_complete\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136): the per-period DMA callback that advances [`prtd->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L24) and calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933)
- [`'\<snd_dmaengine_pcm_set_config_from_dai_data\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106): copy [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), and [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) from the DAI DMA data into the src or dst side of the slave config by direction

### Types (dmaengine_pcm.h)

- [`'\<struct dmaengine_pcm\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175): the bridge object embedding the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), the per-direction [`chan`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) array, the [`config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) pointer, and the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) word
- [`'\<struct snd_dmaengine_pcm_config\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141): the per-platform configuration with the [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) and [`compat_request_channel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callbacks, [`chan_names`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141), optional [`pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141), and [`prealloc_buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141)
- [`'\<struct snd_dmaengine_dai_dma_data\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77): the CPU DAI's DMA description (register [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`fifo_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77)) that the slave config is built from

### ALSA managed-buffer helpers (pcm_memory.c)

- [`'\<snd_pcm_set_managed_buffer\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380): preallocate one substream's buffer and turn on managed mode, so the core allocates before [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and frees after [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`'\<snd_pcm_set_managed_buffer_all\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401): the same for every substream of a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534)
- [`'\<snd_pcm_lib_preallocate_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L322): the unmanaged preallocation primitive both managed helpers wrap through [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c)

### SOF/HDA host-stream component (sof/pcm.c, sof/intel)

- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): fill the SOF [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) with [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497), and [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637)
- [`'\<sof_pcm_pointer\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497): report the host DMA position from the firmware position structure or the platform pointer op, sourcing it from the host stream rather than from a dmaengine residue
- [`'\<sof_pcm_new\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637): the SOF [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op preallocating the buffer with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and `SNDRV_DMA_TYPE_DEV_SG`
- [`'\<hda_dsp_stream_get_position\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L1063): read the HDA stream DMA position from the DPIB register or position buffer of a [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the ASoC platform driver class, covering the audio DMA driver and the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) it exports
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where a front-end PCM/DMA component and back-end DAIs are triggered independently
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA PCM model, the buffer preallocation helpers, and the pointer callback contract
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated kernel-doc index for the PCM and memory-management helpers

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project home](https://www.alsa-project.org/wiki/Main_Page)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The interface a controller driver presents to the ASoC core is one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and the core reaches the PCM/DMA component only through that driver's function pointer struct. The generic bridge supplies a complete one and the driver supplies only a [`struct snd_dmaengine_pcm_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) describing its DMA particulars. The mapping from the PCM action a userspace client requests to the component op the core calls and the dmaengine primitive that op runs is fixed.

| PCM action | component op | dmaengine primitive |
|------------|--------------|---------------------|
| PCM device creation | [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`dmaengine_pcm_new`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219)) | `dma_request_slave_channel`, `snd_pcm_set_managed_buffer` |
| `open()` | [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`dmaengine_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L148)) | attach `dma_chan` to substream |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`dmaengine_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L76)) | `dmaengine_slave_config` |
| `SNDRV_PCM_IOCTL_START` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (START) | `dmaengine_prep_dma_cyclic`, `dmaengine_submit`, `dma_async_issue_pending` |
| `SNDRV_PCM_IOCTL_PAUSE` (push) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (PAUSE_PUSH) | `dmaengine_pause` |
| `SNDRV_PCM_IOCTL_DROP` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (STOP) | `dmaengine_terminate_async` |
| pointer query (period elapsed) | [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`dmaengine_pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L278)) | `dmaengine_tx_status` (residue) |
| `close()` | [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ([`dmaengine_pcm_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L162)) | `dmaengine_synchronize`, free runtime data |

### snd_dmaengine_pcm_config: the driver's DMA description

A controller driver that uses the generic bridge fills a [`struct snd_dmaengine_pcm_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) and passes it to [`devm_snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L109), or passes NULL to accept the default configuration. The [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callback is the only field most drivers set, and it is usually pointed at the supplied [`snd_dmaengine_pcm_prepare_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L50).

```c
/* include/sound/dmaengine_pcm.h:141 */
struct snd_dmaengine_pcm_config {
	int (*prepare_slave_config)(struct snd_pcm_substream *substream,
			struct snd_pcm_hw_params *params,
			struct dma_slave_config *slave_config);
	struct dma_chan *(*compat_request_channel)(
			struct snd_soc_pcm_runtime *rtd,
			struct snd_pcm_substream *substream);
	int (*process)(struct snd_pcm_substream *substream,
		       int channel, unsigned long hwoff,
		       unsigned long bytes);
	const char *name;
	dma_filter_fn compat_filter_fn;
	struct device *dma_dev;
	const char *chan_names[SNDRV_PCM_STREAM_LAST + 1];

	const struct snd_pcm_hardware *pcm_hardware;
	unsigned int prealloc_buffer_size;
};
```

### snd_dmaengine_dai_dma_data: the CPU DAI's DMA particulars

The CPU DAI driver describes its DMA endpoint in a [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) and publishes it with [`snd_soc_dai_init_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L511) so the bridge can read it back through [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497) at hw_params time.

```c
/* include/sound/dmaengine_pcm.h:77 */
struct snd_dmaengine_dai_dma_data {
	dma_addr_t addr;
	enum dma_slave_buswidth addr_width;
	u32 maxburst;
	void *filter_data;
	const char *chan_name;
	unsigned int fifo_size;
	unsigned int flags;
	void *peripheral_config;
	size_t peripheral_size;
	u32 port_window_size;
};
```

### dmaengine_pcm: the bridge object

[`struct dmaengine_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175) embeds the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) so the component pointer the core holds can be turned back into the bridge by container-of, and it caches the requested channels and the driver's config.

```c
/* include/sound/dmaengine_pcm.h:175 */
struct dmaengine_pcm {
	struct dma_chan *chan[SNDRV_PCM_STREAM_LAST + 1];
	const struct snd_dmaengine_pcm_config *config;
	struct snd_soc_component component;
	unsigned int flags;
};
```

## DETAILS

### Registration builds the component over the dmaengine channels

A controller driver brings up the platform component by calling [`devm_snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L109), and the device-managed wrapper hands off to [`snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433) and records a release action so the component is torn down when the device goes away. A driver that accepts the default channel handling passes a NULL config, which makes [`snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433) fall back to its built-in default configuration.

The device-managed wrapper allocates a [`devres`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) cookie that records the parent device, calls the bare [`snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433), and on success adds the cookie so [`devm_dmaengine_pcm_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L104) calls [`snd_dmaengine_pcm_unregister()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L472) at device teardown:

```c
/* sound/soc/soc-devres.c:109 */
int devm_snd_dmaengine_pcm_register(struct device *dev,
	const struct snd_dmaengine_pcm_config *config, unsigned int flags)
{
	struct device **ptr;
	int ret;

	ptr = devres_alloc(devm_dmaengine_pcm_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_dmaengine_pcm_register(dev, config, flags);
	if (ret == 0) {
		*ptr = dev;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

[`snd_dmaengine_pcm_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L433) allocates the [`struct dmaengine_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L175), requests the DMA channels for the substream directions, selects the [`dmaengine_pcm_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L327) driver (or the [`dmaengine_pcm_component_process`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L339) variant when a [`process`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callback is set), and adds it to the card with [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885):

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:433 */
int snd_dmaengine_pcm_register(struct device *dev,
	const struct snd_dmaengine_pcm_config *config, unsigned int flags)
{
	const struct snd_soc_component_driver *driver;
	struct dmaengine_pcm *pcm;
	int ret;

	pcm = kzalloc_obj(*pcm);
	if (!pcm)
		return -ENOMEM;
	...
	if (!config)
		config = &snd_dmaengine_pcm_default_config;
	pcm->config = config;
	pcm->flags = flags;
	...
	ret = dmaengine_pcm_request_chan_of(pcm, dev, config);
	if (ret)
		goto err_free_dma;

	if (config->process)
		driver = &dmaengine_pcm_component_process;
	else
		driver = &dmaengine_pcm_component;

	ret = snd_soc_component_initialize(&pcm->component, driver, dev);
	if (ret)
		goto err_free_dma;

	ret = snd_soc_add_component(&pcm->component, NULL, 0);
	if (ret)
		goto err_free_dma;

	return 0;
...
}
```

The component driver it installs is the fixed set of generic ops, with [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) bound to [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219):

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:327 */
static const struct snd_soc_component_driver dmaengine_pcm_component = {
	.name		= SND_DMAENGINE_PCM_DRV_NAME,
	.probe_order	= SND_SOC_COMP_ORDER_LATE,
	.open		= dmaengine_pcm_open,
	.close		= dmaengine_pcm_close,
	.hw_params	= dmaengine_pcm_hw_params,
	.trigger	= dmaengine_pcm_trigger,
	.pointer	= dmaengine_pcm_pointer,
	.pcm_construct	= dmaengine_pcm_new,
	.sync_stop	= dmaengine_pcm_sync_stop,
};
```

### pcm_construct requests channels and preallocates the managed buffer

When the ASoC core creates the ALSA PCM device for a DAI link it calls the component's [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, which for the bridge is [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219). For each present substream it requests the channel if it was not already requested, calls [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) to preallocate and arm managed mode, and clears residue reporting through [`dmaengine_pcm_can_report_residue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L200) when the channel cannot report a fine-grained residue:

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:219 */
static int dmaengine_pcm_new(struct snd_soc_component *component,
			     struct snd_soc_pcm_runtime *rtd)
{
	struct dmaengine_pcm *pcm = soc_component_to_pcm(component);
	const struct snd_dmaengine_pcm_config *config = pcm->config;
	struct device *dev = component->dev;
	size_t prealloc_buffer_size;
	size_t max_buffer_size;
	unsigned int i;

	if (config->prealloc_buffer_size)
		prealloc_buffer_size = config->prealloc_buffer_size;
	else
		prealloc_buffer_size = prealloc_buffer_size_kbytes * 1024;
	...
	for_each_pcm_streams(i) {
		struct snd_pcm_substream *substream = rtd->pcm->streams[i].substream;
		if (!substream)
			continue;
		...
		snd_pcm_set_managed_buffer(substream,
				SNDRV_DMA_TYPE_DEV_IRAM,
				dmaengine_dma_dev(pcm, substream),
				prealloc_buffer_size,
				max_buffer_size);

		if (!dmaengine_pcm_can_report_residue(dev, pcm->chan[i]))
			pcm->flags |= SND_DMAENGINE_PCM_FLAG_NO_RESIDUE;
		...
	}

	return 0;
}
```

[`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) is a thin wrapper over [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c) with its managed flag set, and according to its kernel-doc the managed mode is what removes the explicit allocate and free from the driver, "PCM core will allocate a buffer automatically before PCM hw_params ops call, and release the buffer after PCM hw_free ops call as well, so that the driver doesn't need to invoke the allocation and the release explicitly in its callback":

```c
/* sound/core/pcm_memory.c:380 */
int snd_pcm_set_managed_buffer(struct snd_pcm_substream *substream, int type,
				struct device *data, size_t size, size_t max)
{
	return preallocate_pages(substream, type, data, size, max, true);
}
```

The unmanaged primitive [`snd_pcm_lib_preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L322) is the same call with the managed flag cleared, so the bytes are reserved at construct time but the substream is never put into managed mode and a driver that uses it must allocate and free the buffer itself in its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) ops:

```c
/* sound/core/pcm_memory.c:322 */
void snd_pcm_lib_preallocate_pages(struct snd_pcm_substream *substream,
				  int type, struct device *data,
				  size_t size, size_t max)
{
	preallocate_pages(substream, type, data, size, max, false);
}
```

A driver that preallocates for the whole PCM at once uses [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401), which runs the same managed preallocation for every substream of a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) through [`preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L361) rather than one substream at a time, and is the call most simple platform drivers reach for instead of the per-substream loop the dmaengine bridge runs:

```c
/* sound/core/pcm_memory.c:401 */
int snd_pcm_set_managed_buffer_all(struct snd_pcm *pcm, int type,
				   struct device *data,
				   size_t size, size_t max)
{
	return preallocate_pages_for_all(pcm, type, data, size, max, true);
}
```

The result of preallocation is that [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) and [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) are set before the first transfer, which is what the cyclic descriptor and the pointer math below depend on.

```
    Managed buffer: the core owns alloc and free (managed mode)
    ────────────────────────────────────────────────────────────
    time ───────────────────────────────────────────────────────▶

    pcm_construct    snd_pcm_set_managed_buffer(): prealloc +
    (dmaengine_pcm_new)                 arm managed mode
            │
            ▼
    hw_params        ◀── core allocates the buffer here, before
                         the component hw_params op runs
            │                 (sets runtime->dma_area / dma_addr)
            ▼
    trigger START    cyclic descriptor walks runtime->dma_addr
            │
            ▼
    hw_free          ◀── core frees the buffer here, after
                         the component hw_free op runs
            │
            ▼
    PCM teardown     no explicit alloc or free in the driver
```

### open attaches the channel to the substream

The component [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L148) first programs the runtime hardware description, then calls the core helper to bind the channel:

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:148 */
static int dmaengine_pcm_open(struct snd_soc_component *component,
			      struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm *pcm = soc_component_to_pcm(component);
	struct dma_chan *chan = pcm->chan[substream->stream];
	int ret;

	ret = dmaengine_pcm_set_runtime_hwparams(component, substream);
	if (ret)
		return ret;

	return snd_dmaengine_pcm_open(substream, chan);
}
```

[`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) allocates the per-substream runtime data, stores the channel in it, and parks it in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), which every later helper reads back. According to its kernel-doc this is why the field is off limits to the driver, "this function will use private_data field of the substream's runtime. So it is not available to your pcm driver implementation":

```c
/* sound/core/pcm_dmaengine.c:307 */
int snd_dmaengine_pcm_open(struct snd_pcm_substream *substream,
	struct dma_chan *chan)
{
	struct dmaengine_pcm_runtime_data *prtd;
	int ret;

	if (!chan)
		return -ENXIO;

	ret = snd_pcm_hw_constraint_integer(substream->runtime,
					    SNDRV_PCM_HW_PARAM_PERIODS);
	if (ret < 0)
		return ret;

	prtd = kzalloc_obj(*prtd);
	if (!prtd)
		return -ENOMEM;

	prtd->dma_chan = chan;

	substream->runtime->private_data = prtd;

	return 0;
}
```

### hw_params turns DAI DMA data into a slave config

The component [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L76) zeroes a [`struct dma_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447), runs the driver's [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) callback to fill it, and applies it with [`dmaengine_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h):

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:76 */
static int dmaengine_pcm_hw_params(struct snd_soc_component *component,
				   struct snd_pcm_substream *substream,
				   struct snd_pcm_hw_params *params)
{
	struct dmaengine_pcm *pcm = soc_component_to_pcm(component);
	struct dma_chan *chan = snd_dmaengine_pcm_get_chan(substream);
	struct dma_slave_config slave_config;
	int ret;

	if (!pcm->config->prepare_slave_config)
		return 0;

	memset(&slave_config, 0, sizeof(slave_config));

	ret = pcm->config->prepare_slave_config(substream, params, &slave_config);
	if (ret)
		return ret;

	return dmaengine_slave_config(chan, &slave_config);
}
```

The default callback [`snd_dmaengine_pcm_prepare_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L50) reads the CPU DAI's [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) with [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497), fills the rate-dependent fields with [`snd_hwparams_to_dma_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c), and copies the endpoint fields with [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106). It rejects the multi-CPU case and otherwise leaves the slave config fully described by the single CPU DAI's DMA data, which is why a platform that needs anything more elaborate supplies its own [`prepare_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L141) instead:

```c
/* sound/soc/soc-generic-dmaengine-pcm.c:50 */
int snd_dmaengine_pcm_prepare_slave_config(struct snd_pcm_substream *substream,
	struct snd_pcm_hw_params *params, struct dma_slave_config *slave_config)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_dmaengine_dai_dma_data *dma_data;
	int ret;

	if (rtd->dai_link->num_cpus > 1) {
		dev_err(rtd->dev,
			"%s doesn't support Multi CPU yet\n", __func__);
		return -EINVAL;
	}

	dma_data = snd_soc_dai_get_dma_data(snd_soc_rtd_to_cpu(rtd, 0), substream);

	ret = snd_hwparams_to_dma_slave_config(substream, params, slave_config);
	if (ret)
		return ret;

	snd_dmaengine_pcm_set_config_from_dai_data(substream, dma_data,
		slave_config);

	return 0;
}
```

The endpoint copy [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106) writes the destination side of the slave config for a playback substream and the source side for a capture substream, so the same DAI DMA data describes both directions and the direction of the substream picks which half of the slave config it populates:

```c
/* sound/core/pcm_dmaengine.c:106 */
void snd_dmaengine_pcm_set_config_from_dai_data(
	const struct snd_pcm_substream *substream,
	const struct snd_dmaengine_dai_dma_data *dma_data,
	struct dma_slave_config *slave_config)
{
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		slave_config->dst_addr = dma_data->addr;
		slave_config->dst_maxburst = dma_data->maxburst;
		slave_config->dst_port_window_size = dma_data->port_window_size;
		if (dma_data->flags & SND_DMAENGINE_PCM_DAI_FLAG_PACK)
			slave_config->dst_addr_width =
				DMA_SLAVE_BUSWIDTH_UNDEFINED;
		if (dma_data->addr_width != DMA_SLAVE_BUSWIDTH_UNDEFINED)
			slave_config->dst_addr_width = dma_data->addr_width;
	} else {
		slave_config->src_addr = dma_data->addr;
		slave_config->src_maxburst = dma_data->maxburst;
		slave_config->src_port_window_size = dma_data->port_window_size;
		if (dma_data->flags & SND_DMAENGINE_PCM_DAI_FLAG_PACK)
			slave_config->src_addr_width =
				DMA_SLAVE_BUSWIDTH_UNDEFINED;
		if (dma_data->addr_width != DMA_SLAVE_BUSWIDTH_UNDEFINED)
			slave_config->src_addr_width = dma_data->addr_width;
	}

	slave_config->peripheral_config = dma_data->peripheral_config;
	slave_config->peripheral_size = dma_data->peripheral_size;
}
```

The CPU DAI publishes that data in its probe through [`snd_soc_dai_init_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L511), which stores the per-direction [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) so it is reachable from the substream by the time hw_params runs.

```
    hw_params builds one dma_slave_config from two sources
    ───────────────────────────────────────────────────────────
    (substream direction selects which half is written)

    struct snd_pcm_hw_params        struct snd_dmaengine_dai_dma_data
    ┌──────────────────────────┐    ┌──────────────────────────────┐
    │ format ─▶ bus width      │    │ addr, maxburst, addr_width,  │
    │ stream ─▶ direction      │    │ port_window_size             │
    └─────────────┬────────────┘    └───────────────┬──────────────┘
                  │ snd_hwparams_to_                │ ..._set_config_
                  │ dma_slave_config()              │ from_dai_data()
                  ▼                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ struct dma_slave_config                                     │
    │  playback ─▶ DMA_MEM_TO_DEV: dst_addr, dst_addr_width,      │
    │                              dst_maxburst                   │
    │  capture  ─▶ DMA_DEV_TO_MEM: src_addr, src_addr_width,      │
    │                              src_maxburst                   │
    └─────────────────────────────────────────────────────────────┘
    applied to the channel by dmaengine_slave_config()
```

### trigger maps PCM commands to dmaengine calls

The component [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L168) is a one-line forwarder to [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189), which is the switch that turns each `SNDRV_PCM_TRIGGER_*` command into a dmaengine operation. START builds and submits a fresh cyclic descriptor and issues it, RESUME and PAUSE_RELEASE resume the channel, SUSPEND either pauses or terminates depending on whether the runtime advertises pause support, PAUSE_PUSH pauses, and STOP terminates asynchronously:

```c
/* sound/core/pcm_dmaengine.c:189 */
int snd_dmaengine_pcm_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	struct snd_pcm_runtime *runtime = substream->runtime;
	int ret;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
		ret = dmaengine_pcm_prepare_and_submit(substream);
		if (ret)
			return ret;
		dma_async_issue_pending(prtd->dma_chan);
		break;
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		dmaengine_resume(prtd->dma_chan);
		break;
	case SNDRV_PCM_TRIGGER_SUSPEND:
		if (runtime->info & SNDRV_PCM_INFO_PAUSE)
			dmaengine_pause(prtd->dma_chan);
		else
			dmaengine_terminate_async(prtd->dma_chan);
		break;
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		dmaengine_pause(prtd->dma_chan);
		break;
	case SNDRV_PCM_TRIGGER_STOP:
		dmaengine_terminate_async(prtd->dma_chan);
		break;
	default:
		return -EINVAL;
	}

	return 0;
}
```

The START path runs [`dmaengine_pcm_prepare_and_submit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150), which programs a cyclic transfer over the whole ALSA ring with [`dmaengine_prep_dma_cyclic()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h), using the buffer base [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) preallocated by the managed buffer, one period as the wakeup unit, and registers [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) as the per-period callback. Each period boundary fires that callback, which advances the software position counter [`prtd->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L24) by one period, wraps it at the buffer end, and tells the PCM core a period elapsed with [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933). This counter is the fallback the no-residue pointer path reads.

```c
/* sound/core/pcm_dmaengine.c:136 */
static void dmaengine_pcm_dma_complete(void *arg)
{
	unsigned int new_pos;
	struct snd_pcm_substream *substream = arg;
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);

	new_pos = prtd->pos + snd_pcm_lib_period_bytes(substream);
	if (new_pos >= snd_pcm_lib_buffer_bytes(substream))
		new_pos = 0;
	prtd->pos = new_pos;

	snd_pcm_period_elapsed(substream);
}
```

The cyclic descriptor loops the whole ring and fires the per-period callback at each boundary, advancing the position counter and telling the PCM core a period elapsed:

```
    Cyclic transfer over the ALSA ring, one period per IRQ
    ────────────────────────────────────────────────────────────
    runtime->dma_addr .. + snd_pcm_lib_buffer_bytes (whole ring)

    ┌─────────┬─────────┬─────────┬─────────┐
    │ period0 │ period1 │ period2 │ period3 │  ◀─ dmaengine cyclic
    └─────────┴─────────┴────▲────┴─────────┘     descriptor loops
                             │                    the buffer
                  DMA position sweeps ─▶ and wraps at the end

    at each period boundary the descriptor fires:
      dmaengine_pcm_dma_complete()
        prtd->pos += snd_pcm_lib_period_bytes  (wrap at buffer end)
        snd_pcm_period_elapsed() ─▶ advance hw_ptr, wake poll()
```

### pointer reports the DMA position from residue

The component [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L278) chooses between two implementations by the `SND_DMAENGINE_PCM_FLAG_NO_RESIDUE` flag that [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219) set when the channel cannot report residue at period granularity. The residue-based [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) queries the channel for how many bytes of the cyclic buffer remain with [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h), converts the residue into a position by subtracting it from the buffer size, and also fills [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) from the in-flight byte count so the reported position accounts for data already handed to the controller:

```c
/* sound/core/pcm_dmaengine.c:251 */
snd_pcm_uframes_t snd_dmaengine_pcm_pointer(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	struct snd_pcm_runtime *runtime = substream->runtime;
	struct dma_tx_state state;
	enum dma_status status;
	unsigned int buf_size;
	unsigned int pos = 0;

	status = dmaengine_tx_status(prtd->dma_chan, prtd->cookie, &state);
	if (status == DMA_IN_PROGRESS || status == DMA_PAUSED) {
		buf_size = snd_pcm_lib_buffer_bytes(substream);
		if (state.residue > 0 && state.residue <= buf_size)
			pos = buf_size - state.residue;

		runtime->delay = bytes_to_frames(runtime,
						 state.in_flight_bytes);
	}

	return bytes_to_frames(runtime, pos);
}
```

The fallback [`snd_dmaengine_pcm_pointer_no_residue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235) returns the period-counter position [`prtd->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L24) maintained by [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136), which its kernel-doc marks as unreliable, "This function is deprecated and should not be used by new drivers, as its results may be unreliable". It does no hardware query at all, just converting the byte counter the period callback advanced into frames, which is why it can only ever resolve to a period boundary and never to the exact word the controller is consuming:

```c
/* sound/core/pcm_dmaengine.c:235 */
snd_pcm_uframes_t snd_dmaengine_pcm_pointer_no_residue(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	return bytes_to_frames(substream->runtime, prtd->pos);
}
```

The NO_RESIDUE flag picks one of the two readers, the residue query resolving to the exact consumed byte and the period counter falling back to the last boundary:

```
    pointer: NO_RESIDUE flag selects the position source
    ────────────────────────────────────────────────────────────

    flag state        helper                      position source
    ────────────────  ──────────────────────────  ───────────────
    clear (residue)   snd_dmaengine_pcm_pointer   buf_size - residue
                      (dmaengine_tx_status)       fine-grained
    set (no residue)  ..._pointer_no_residue      prtd->pos
                      (deprecated, unreliable)    period boundary

    both return frames via bytes_to_frames(); residue is the bytes
    of the cyclic buffer not yet consumed by the controller
```

### close synchronizes and frees the runtime data

The component [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L162) forwards to [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370), which calls [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347) with `release_channel` false, so the runtime state is torn down but the channel stays owned by the bridge for the next open:

```c
/* sound/core/pcm_dmaengine.c:370 */
int snd_dmaengine_pcm_close(struct snd_pcm_substream *substream)
{
	__snd_dmaengine_pcm_close(substream, false);
	return 0;
}
```

The shared helper [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347) terminates a paused channel, waits for any in-flight transfer to drain with [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h), optionally releases the channel, and frees the per-substream runtime data, which is the allocation [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) made:

```c
/* sound/core/pcm_dmaengine.c:347 */
static void __snd_dmaengine_pcm_close(struct snd_pcm_substream *substream,
				      bool release_channel)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	struct dma_tx_state state;
	enum dma_status status;

	status = dmaengine_tx_status(prtd->dma_chan, prtd->cookie, &state);
	if (status == DMA_PAUSED)
		dmaengine_terminate_async(prtd->dma_chan);

	dmaengine_synchronize(prtd->dma_chan);
	if (release_channel)
		dma_release_channel(prtd->dma_chan);
	kfree(prtd);
}
```

The managed buffer is not freed here. Because [`dmaengine_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-generic-dmaengine-pcm.c#L219) put each substream into managed mode, the PCM core releases the buffer after the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op and at PCM teardown, so the lifecycle of the buffer is owned by the core and the lifecycle of the per-substream DMA state is owned by open and close.

### x86-64 SOF: the host-DSP HDA stream path

On Intel x86-64 the ASoC platform component is usually the Sound Open Firmware audio component, registered by [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) rather than the dmaengine bridge. It fills its own [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) with SOF ops, and the relevant ones for this page are the same four roles, [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67):

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
	...
	pd->open = sof_pcm_open;
	pd->close = sof_pcm_close;
	pd->hw_params = sof_pcm_hw_params;
	pd->prepare = sof_pcm_prepare;
	pd->hw_free = sof_pcm_hw_free;
	pd->trigger = sof_pcm_trigger;
	pd->pointer = sof_pcm_pointer;
	...
	pd->pcm_construct = sof_pcm_new;
	...
}
```

The buffer contract is unchanged. The SOF [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) preallocates each direction's buffer with the same [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380), using the scatter-gather buffer type for the host stream:

```c
/* sound/soc/sof/pcm.c:637 */
	/* pre-allocate playback audio buffer pages */
	...
	snd_pcm_set_managed_buffer(pcm->streams[stream].substream,
				   SNDRV_DMA_TYPE_DEV_SG, sdev->dev,
				   0, le32_to_cpu(caps->buffer_size_max));
```

The pointer path differs because there is no dmaengine residue to read. [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) reports the host position from a firmware IPC position structure or from the DSP pointer op, and only falls back to reading the position out of the HDA stream registers when neither is available:

```c
/* sound/soc/sof/pcm.c:497 */
static snd_pcm_uframes_t sof_pcm_pointer(struct snd_soc_component *component,
					 struct snd_pcm_substream *substream)
{
	...
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
	...
	/* read position from DSP */
	host = bytes_to_frames(substream->runtime,
			       spcm->stream[substream->stream].posn.host_posn);
	...
	return host;
}
```

On Intel HDA hardware the register-level position read is [`hda_dsp_stream_get_position()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L1063), which reads the DPIB position register or the position buffer of the [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h) carried in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the same runtime slot the dmaengine path uses for its own runtime data. It selects a read strategy from the `sof_hda_position_quirk` setting, with the recommended path reading the DPIB register that reflects the bytes the controller actually transferred, and it wraps the value at the stream's [`bufsize`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h) the same way the cyclic position counter wraps at the ALSA buffer end:

```c
/* sound/soc/sof/intel/hda-stream.c:1063 */
snd_pcm_uframes_t hda_dsp_stream_get_position(struct hdac_stream *hstream,
					      int direction, bool can_sleep)
{
	struct hdac_ext_stream *hext_stream = stream_to_hdac_ext_stream(hstream);
	struct sof_intel_hda_stream *hda_stream = hstream_to_sof_hda_stream(hext_stream);
	struct snd_sof_dev *sdev = hda_stream->sdev;
	snd_pcm_uframes_t pos;

	switch (sof_hda_position_quirk) {
	...
	case SOF_HDA_POSITION_QUIRK_USE_DPIB_REGISTERS:
		/*
		 * In case VC1 traffic is disabled this is the recommended option
		 */
		pos = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR,
				       AZX_REG_VS_SDXDPIB_XBASE +
				       (AZX_REG_VS_SDXDPIB_XINTERVAL *
					hstream->index));
		break;
	case SOF_HDA_POSITION_QUIRK_USE_DPIB_DDR_UPDATE:
		...
		pos = snd_hdac_stream_get_pos_posbuf(hstream);
		break;
	default:
		dev_err_once(sdev->dev, "hda_position_quirk value %d not supported\n",
			     sof_hda_position_quirk);
		pos = 0;
		break;
	}

	if (pos >= hstream->bufsize)
		pos = 0;

	return pos;
}
```

The HDA stream is therefore the host-DSP DMA, and [`sof_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L497) fills the same role for it that [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) fills for a generic dmaengine channel.
