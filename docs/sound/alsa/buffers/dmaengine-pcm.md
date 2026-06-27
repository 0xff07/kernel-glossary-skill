# dmaengine PCM glue

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The dmaengine PCM glue is the generic ALSA-core helper set in [`sound/core/pcm_dmaengine.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c) and [`include/sound/dmaengine_pcm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h) that bridges one PCM substream to the kernel dmaengine slave-DMA framework, and it carries the per-substream state in a [`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) hung off [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) allocates that record and stores the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) the caller assigns, [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106) fills a [`struct dma_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447) from a CPU DAI's [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) maps each `SNDRV_PCM_TRIGGER_*` command onto a dmaengine call, and the per-period callback [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) advances the software position and calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933). On x86-64 ACPI SOF/HDA systems the host-side audio DMA is driven by the HDA controller's own stream DMA engine rather than this glue, so this page documents the generic core helper set, and the HDA host-stream path is out of scope here.

```
    PCM substream                       dmaengine framework
    ┌──────────────────────┐
    │ runtime->dma_addr    │           snd_dmaengine_dai_dma_data
    │ runtime->dma_area    │           ┌────────────────────────┐
    │ runtime->private_data│           │ addr, addr_width       │
    └──────────┬───────────┘           │ maxburst, flags        │
               │                       └───────────┬────────────┘
               ▼                                   │ set_config_from
    dmaengine_pcm_runtime_data                     ▼  _dai_data
    ┌──────────────────────┐           ┌────────────────────────┐
    │ dma_chan ────────────┼──────────▶│ struct dma_slave_config│
    │ cookie               │  open     │ dst/src addr, maxburst │
    │ pos (period counter) │           └───────────┬────────────┘
    └──────────┬───────────┘                       │ slave_config
               │ trigger START                     ▼
               ▼                          struct dma_chan
    prep_dma_cyclic + submit  ─────────▶  (dmaengine controller)
               │                                   │
               │  desc->callback                   │ per period IRQ
               ▼                                   ▼
    dmaengine_pcm_dma_complete ──▶ snd_pcm_period_elapsed
               │                                   │
               └──── pos += period, wrap ──────────┘ wakes poll()ing
                                                     userspace
```

## SUMMARY

The dmaengine PCM glue translates the ALSA PCM operation contract into the kernel dmaengine slave-DMA API for one substream at a time. Each open allocates a [`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) that holds the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338), the submission [`cookie`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22), and a period-counting position, and it is reached from any later helper through the [`substream_to_prtd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L29) accessor that reads [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) takes a channel a caller already selected, while [`snd_dmaengine_pcm_request_channel()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L283) obtains one through a filter for the caller to pass to open; [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370) drains and frees the record while [`snd_dmaengine_pcm_close_release_chan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L386) also releases the channel.

The slave configuration comes from two sources. [`snd_hwparams_to_dma_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L54) derives the transfer direction and bus width from the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408), and [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106) copies the register [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), and [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) from the DAI DMA data into the destination half of the config for a playback substream and the source half for a capture substream. [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) builds and submits a cyclic descriptor over the whole ALSA ring on START through [`dmaengine_pcm_prepare_and_submit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150) and issues it with [`dma_async_issue_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1447), resumes on RESUME and PAUSE_RELEASE, pauses on PAUSE_PUSH, and terminates on STOP.

The position the PCM core reads back comes from the channel residue. [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) queries [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241) and subtracts the residue from the buffer size to get a byte offset, while the period-counting fallback [`snd_dmaengine_pcm_pointer_no_residue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235) returns the [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) counter maintained by [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136). That completion callback runs at each cyclic period boundary, advances [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) by one period with wraparound, and calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933), which is the wakeup the PCM core needs to advance the stream and unblock a waiting userspace client. The generic ASoC platform consumer of these helpers is a dmaengine bridge component, and the managed DMA buffer the cyclic descriptor walks is preallocated by the ALSA core.

## SPECIFICATIONS

The dmaengine PCM glue is a Linux kernel software construct with no standalone hardware specification. Its lower contract is the kernel dmaengine slave-DMA API, an internal kernel interface documented under [`Documentation/driver-api/dmaengine/`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/dmaengine/), and its upper contract is the ALSA PCM operation set whose userspace side is the [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) `SNDRV_PCM_*` interface. The cyclic transfer mode and the residue-reporting capability the glue depends on are properties of the dmaengine provider, defined by that API rather than by an external standard.

## LINUX KERNEL

### Per-substream state and accessor (pcm_dmaengine.c)

- [`'\<struct dmaengine_pcm_runtime_data\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22): the per-substream record holding the [`dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338), the submission [`cookie`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22), and the period-counting [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22)
- [`'\<substream_to_prtd\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L29): read the record back from [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_dmaengine_pcm_get_chan\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L35): return the stored [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) for a substream

### Channel acquisition and release (pcm_dmaengine.c)

- [`'\<snd_dmaengine_pcm_open\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307): allocate the [`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22), store the passed channel, and apply the integer-periods constraint
- [`'\<snd_dmaengine_pcm_request_channel\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L283): request a `DMA_SLAVE` plus `DMA_CYCLIC` capable channel via [`dma_request_channel()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1626)
- [`'\<snd_dmaengine_pcm_close\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370): drain and free the record through [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347) without releasing the channel
- [`'\<snd_dmaengine_pcm_close_release_chan\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L386): the same drain and free, then [`dma_release_channel()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1529)
- [`'\<__snd_dmaengine_pcm_close\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347): terminate a paused channel, [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1190), optionally release, and [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) the record

### Slave-config construction (pcm_dmaengine.c)

- [`'\<snd_hwparams_to_dma_slave_config\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L54): map the [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) physical width and direction onto the [`struct dma_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447) direction and bus width
- [`'\<snd_dmaengine_pcm_set_config_from_dai_data\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106): copy [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), and [`port_window_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) into the direction-selected half of the slave config
- [`'\<snd_dmaengine_pcm_refine_runtime_hwparams\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L405): read the channel's [`struct dma_slave_caps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L817) and mask the [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) formats and `SNDRV_PCM_INFO_*` flags to what the DMA supports

### Trigger, submit, and completion (pcm_dmaengine.c)

- [`'\<snd_dmaengine_pcm_trigger\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189): map each `SNDRV_PCM_TRIGGER_*` command to the matching dmaengine call
- [`'\<dmaengine_pcm_prepare_and_submit\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150): build the cyclic descriptor with [`dmaengine_prep_dma_cyclic()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1038), attach the period callback, and [`dmaengine_submit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1247)
- [`'\<dmaengine_pcm_dma_complete\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136): the per-period callback that advances [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) and calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933)
- [`'\<snd_dmaengine_pcm_sync_stop\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L333): [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1190) a non-paused channel so a stopped stream is fully quiesced

### Pointer and residue (pcm_dmaengine.c)

- [`'\<snd_dmaengine_pcm_pointer\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251): query [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241), turn the residue into a frame position, and set [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_dmaengine_pcm_pointer_no_residue\>':'sound/core/pcm_dmaengine.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235): the period-counting fallback returning [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) as frames

### Types and flags (dmaengine_pcm.h)

- [`'\<struct snd_dmaengine_dai_dma_data\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77): the CPU DAI's DMA endpoint description ([`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`peripheral_config`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), [`port_window_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77))
- [`'\<snd_pcm_substream_to_dma_direction\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L21): map the substream direction to `DMA_MEM_TO_DEV` or `DMA_DEV_TO_MEM`
- [`'\<SND_DMAENGINE_PCM_DAI_FLAG_PACK\>':'include/sound/dmaengine_pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L55): the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) bit declaring packed samples, which leaves the addr width undefined and the format mask open

### PCM core wakeup (pcm_lib.c)

- [`'\<snd_pcm_period_elapsed\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933): acquire the stream lock and run [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900) to advance the runtime by one period

### dmaengine primitives (dmaengine.h)

- [`'\<struct dma_chan\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338): the slave-DMA channel handle the prtd holds
- [`'\<struct dma_slave_config\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447): the per-direction address, burst, and width the glue fills before each run
- [`'\<dmaengine_prep_dma_cyclic\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1038): prepare a [`struct dma_async_tx_descriptor`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L614) that loops over the ring one period at a time
- [`'\<dmaengine_submit\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1247) / [`'\<dma_async_issue_pending\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1447): queue the descriptor and flush it to hardware
- [`'\<dmaengine_pause\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1225) / [`'\<dmaengine_resume\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1233) / [`'\<dmaengine_terminate_async\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1164): the pause, resume, and stop primitives the trigger switch calls
- [`'\<dmaengine_tx_status\>':'include/linux/dmaengine.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241): report the [`struct dma_tx_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L737) residue and in-flight bytes the pointer path reads

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/dmaengine/client.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/dmaengine/client.rst): the slave-DMA client API (channel request, slave config, cyclic prepare, submit, issue, terminate, tx_status) the glue is built on
- [`Documentation/driver-api/dmaengine/provider.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/dmaengine/provider.rst): the controller side, including cyclic transfers and residue-granularity reporting the pointer path depends on
- [`Documentation/driver-api/dmaengine/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/dmaengine/index.rst): the dmaengine documentation index
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA PCM model, the buffer and pointer callback contract, and the period-elapsed notification

## OTHER SOURCES

- [DMAengine slave API (kernel.org HTML render of client.rst)](https://docs.kernel.org/driver-api/dmaengine/client.html)
- [The DMA engine slave API (LWN coverage)](https://lwn.net/Articles/657765/)
- [ALSA project home](https://www.alsa-project.org/wiki/Main_Page)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The glue presents one helper set that a PCM open/close/trigger/pointer implementation calls; the helpers carry no function pointer struct of their own and expose no ioctl. A caller assigns a channel at open, runs the slave-config and trigger helpers during operation, and reads the pointer helper for position. The mapping from the PCM action a userspace client requests to the helper that runs and the dmaengine primitive that helper issues is fixed.

| PCM action | helper | dmaengine primitive |
|------------|--------|---------------------|
| `open()` | [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) | store `dma_chan`, allocate prtd |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106) | fill [`struct dma_slave_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L447) |
| `SNDRV_PCM_IOCTL_START` | [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) (START) | [`dmaengine_prep_dma_cyclic()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1038), [`dmaengine_submit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1247), [`dma_async_issue_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1447) |
| `SNDRV_PCM_IOCTL_PAUSE` (push) | [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) (PAUSE_PUSH) | [`dmaengine_pause()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1225) |
| `SNDRV_PCM_IOCTL_PAUSE` (release) | [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) (PAUSE_RELEASE) | [`dmaengine_resume()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1233) |
| `SNDRV_PCM_IOCTL_DROP` | [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) (STOP) | [`dmaengine_terminate_async()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1164) |
| pointer query | [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) | [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241) (residue) |
| `close()` | [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370) | [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1190), free prtd |

### snd_dmaengine_dai_dma_data: the DAI DMA description

A CPU DAI describes its DMA endpoint in a [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77), and the slave config the glue applies is built from it. The register [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) is the peripheral side of the transfer, [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) and [`maxburst`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) size each beat and burst, and [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) carries [`SND_DMAENGINE_PCM_DAI_FLAG_PACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L55).

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

### dmaengine_pcm_runtime_data: the per-substream state

[`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) is the state the glue keeps per substream. It holds the channel, the [`cookie`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) returned by [`dmaengine_submit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1247) so [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241) can be queried later, and the [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) byte counter the no-residue path returns.

```c
/* sound/core/pcm_dmaengine.c:22 */
struct dmaengine_pcm_runtime_data {
	struct dma_chan *dma_chan;
	dma_cookie_t cookie;

	unsigned int pos;
};

static inline struct dmaengine_pcm_runtime_data *substream_to_prtd(
	const struct snd_pcm_substream *substream)
{
	return substream->runtime->private_data;
}
```

## DETAILS

### The ALSA-core bridge to the kernel dmaengine framework

The glue is the layer that turns the ALSA PCM substream contract into the kernel dmaengine slave-DMA API. It sits below the PCM open/close/trigger/pointer callbacks and above a [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338), and it owns one thing the caller hands it, the channel, plus the state needed to drive a cyclic transfer over the ALSA ring and to report position. The slave-DMA API it uses, the channel request, the slave config, the cyclic descriptor prepare, the submit and issue, the pause/resume/terminate, and the tx_status residue query, is documented in [`Documentation/driver-api/dmaengine/client.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/dmaengine/client.rst), and the ALSA side it serves is the PCM model in [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst).

On x86-64 ACPI SOF/HDA systems the host-side audio DMA is not a generic dmaengine channel; the HDA controller has its own per-stream DMA engine programmed by the DSP firmware, and the host position is read from the HDA stream registers rather than from a dmaengine residue, so these helpers do not run on that path. This page documents the generic core helper set, which a generic ASoC dmaengine bridge component wraps for a slave-DMA controller.

```
    Where the glue sits: PCM ops above, slave-DMA API below
    ────────────────────────────────────────────────────────
    ┌───────────────────────────────────────────────────────┐
    │ ALSA PCM ops: open close trigger pointer sync_stop    │
    └───────────────────────────┬───────────────────────────┘
                                ▼
    ┌───────────────────────────────────────────────────────┐
    │ dmaengine PCM glue (pcm_dmaengine.c)                  │
    │   prtd: dma_chan, cookie, pos                         │
    └───────────────────────────┬───────────────────────────┘
                                ▼
    ┌───────────────────────────────────────────────────────┐
    │ dmaengine slave-DMA API                               │
    │   request_channel  slave_config  prep_dma_cyclic      │
    │   submit  issue_pending  pause  resume  terminate     │
    │   tx_status (residue)                                 │
    └───────────────────────────┬───────────────────────────┘
                                ▼
                         struct dma_chan
                     (dmaengine controller)
```

### The prtd per-substream state and channel acquisition

The glue allocates one [`struct dmaengine_pcm_runtime_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) per open and parks it in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), and every later helper reads it back through [`substream_to_prtd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L29). [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) rejects a NULL channel, applies the integer-periods constraint with [`snd_pcm_hw_constraint_integer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c) so a cyclic period count is whole, allocates the record, and stores the channel. According to its kernel-doc the private_data slot is then off limits to the caller, "this function will use private_data field of the substream's runtime. So it is not available to your pcm driver implementation":

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

Any later helper that needs the channel back reads it from the prtd through [`snd_dmaengine_pcm_get_chan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L35), the one-line accessor that returns the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338) [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307) stored. It is what an ASoC dmaengine bridge calls between open and close to reach the channel for a slave-config or hw-param query without touching [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) itself:

```c
/* sound/core/pcm_dmaengine.c:35 */
struct dma_chan *snd_dmaengine_pcm_get_chan(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);

	return prtd->dma_chan;
}
```

A caller that has not already selected a channel first obtains one with [`snd_dmaengine_pcm_request_channel()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L283), which asks the dmaengine layer for a channel that advertises both `DMA_SLAVE` and `DMA_CYCLIC`, then passes that channel to [`snd_dmaengine_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L307):

```c
/* sound/core/pcm_dmaengine.c:283 */
struct dma_chan *snd_dmaengine_pcm_request_channel(dma_filter_fn filter_fn,
	void *filter_data)
{
	dma_cap_mask_t mask;

	dma_cap_zero(mask);
	dma_cap_set(DMA_SLAVE, mask);
	dma_cap_set(DMA_CYCLIC, mask);

	return dma_request_channel(mask, filter_fn, filter_data);
}
```

Close mirrors open. [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370) and [`snd_dmaengine_pcm_close_release_chan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L386) both call [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347), which terminates a still-paused channel, waits for any in-flight transfer to drain with [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1190), optionally releases the channel, and frees the record that open allocated. The two entry points differ only in the `release_channel` argument:

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

The two public entry points are thin wrappers that fix that `release_channel` argument. [`snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L370) passes `false`, draining and freeing the prtd but leaving the channel for the caller to keep, and pairs with an open that took a caller-owned channel:

```c
/* sound/core/pcm_dmaengine.c:370 */
int snd_dmaengine_pcm_close(struct snd_pcm_substream *substream)
{
	__snd_dmaengine_pcm_close(substream, false);
	return 0;
}
```

[`snd_dmaengine_pcm_close_release_chan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L386) passes `true`, so the same drain and free is followed by [`dma_release_channel()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1529), and it pairs with an open over a channel obtained through [`snd_dmaengine_pcm_request_channel()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L283):

```c
/* sound/core/pcm_dmaengine.c:386 */
int snd_dmaengine_pcm_close_release_chan(struct snd_pcm_substream *substream)
{
	__snd_dmaengine_pcm_close(substream, true);
	return 0;
}
```

Open acquires the channel and close drains and frees it, the two ends of one drain path:

```
    open and close pair through one drain path
    ───────────────────────────────────────────
    ┌──────────────────────────────────────────────────────────┐
    │ open path             close path        release_channel  │
    │ ────────────────────  ────────────────  ───────────────  │
    │ caller-owned chan      ..._pcm_close()         false     │
    │ ..._request_channel()  ..._close_release_      true      │
    │                        chan()                            │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ __snd_dmaengine_pcm_close(release_channel)               │
    │   prtd = substream_to_prtd(substream)                    │
    │   if status == DMA_PAUSED: dmaengine_terminate_async     │
    │   dmaengine_synchronize   (drain in-flight)              │
    │   if release_channel: dma_release_channel                │
    │   kfree(prtd)                                            │
    └──────────────────────────────────────────────────────────┘
```

### Quiescing a stopped channel with sync_stop

The PCM core's `sync_stop` callback runs after a stream has been triggered to STOP to make sure the DMA is genuinely idle before the buffer is reused or freed. [`snd_dmaengine_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L333) queries the channel with [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241) and, as long as the channel is not in [`DMA_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L57), calls [`dmaengine_synchronize()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1190) to wait for the terminated transfer and its [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) callbacks to finish. The paused case is skipped because a paused channel still holds an in-flight descriptor that a later resume or close must own, which is the same guard [`__snd_dmaengine_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L347) applies in reverse:

```c
/* sound/core/pcm_dmaengine.c:333 */
int snd_dmaengine_pcm_sync_stop(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	struct dma_tx_state state;
	enum dma_status status;

	status = dmaengine_tx_status(prtd->dma_chan, prtd->cookie, &state);
	if (status != DMA_PAUSED)
		dmaengine_synchronize(prtd->dma_chan);

	return 0;
}
```

The status read picks one of two actions, draining a running channel and leaving a paused one alone:

```
    sync_stop: drain only a non-paused channel
    ───────────────────────────────────────────
    dmaengine_tx_status(chan, cookie) ──▶ status

    ┌────────────────────────────────────────────────────┐
    │ status            action                           │
    │ ────────────────  ─────────────────────────────────│
    │ DMA_PAUSED        skip (keep in-flight descriptor) │
    │ any other         dmaengine_synchronize  (drain)   │
    └────────────────────────────────────────────────────┘
    (__snd_dmaengine_pcm_close applies the inverse guard and
     terminates the DMA_PAUSED case instead of skipping it)
```

### Building the dma_slave_config from the DAI DMA data and hw_params

The slave config the channel runs under is assembled in two steps. [`snd_hwparams_to_dma_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L54) sets the transfer direction and the bus width from the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408). A playback substream is memory-to-device with the destination width set, a capture substream is device-to-memory with the source width set, and the width follows the sample's physical word size:

```c
/* sound/core/pcm_dmaengine.c:54 */
int snd_hwparams_to_dma_slave_config(const struct snd_pcm_substream *substream,
	const struct snd_pcm_hw_params *params,
	struct dma_slave_config *slave_config)
{
	enum dma_slave_buswidth buswidth;
	int bits;

	bits = params_physical_width(params);
	if (bits < 8 || bits > 64)
		return -EINVAL;
	else if (bits == 8)
		buswidth = DMA_SLAVE_BUSWIDTH_1_BYTE;
	else if (bits == 16)
		buswidth = DMA_SLAVE_BUSWIDTH_2_BYTES;
	else if (bits == 24)
		buswidth = DMA_SLAVE_BUSWIDTH_3_BYTES;
	else if (bits <= 32)
		buswidth = DMA_SLAVE_BUSWIDTH_4_BYTES;
	else
		buswidth = DMA_SLAVE_BUSWIDTH_8_BYTES;

	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		slave_config->direction = DMA_MEM_TO_DEV;
		slave_config->dst_addr_width = buswidth;
	} else {
		slave_config->direction = DMA_DEV_TO_MEM;
		slave_config->src_addr_width = buswidth;
	}

	slave_config->device_fc = false;

	return 0;
}
```

[`snd_dmaengine_pcm_set_config_from_dai_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L106) then writes the peripheral endpoint into the same config. The substream direction selects which half is written, the destination side for playback and the source side for capture, so one [`struct snd_dmaengine_dai_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) describes both directions. The [`addr_width`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L77) copy is conditional, and according to its kernel-doc, "The {dst,src}_addr_width field will only be initialized if the SND_DMAENGINE_PCM_DAI_FLAG_PACK flag is set or if the addr_width field of the DAI DMA data struct is not equal to DMA_SLAVE_BUSWIDTH_UNDEFINED. If both conditions are met the latter takes priority":

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

The packed-samples case is the [`SND_DMAENGINE_PCM_DAI_FLAG_PACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L55) flag, and according to its comment, "If this flag is set the dmaengine driver won't put any restriction on the supported sample formats and set the DMA transfer size to undefined". The same flag governs [`snd_dmaengine_pcm_refine_runtime_hwparams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L405), which otherwise reads the channel's [`struct dma_slave_caps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L817) and masks the [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) format set down to the physical widths the DMA can move.

That refinement runs before a stream starts so the advertised [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) only ever offers what the channel can actually carry. [`snd_dmaengine_pcm_refine_runtime_hwparams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L405) calls [`dma_get_slave_caps()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1572) on the [`struct dma_chan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L338), turns the pause/resume and residue-granularity capabilities into the [`SNDRV_PCM_INFO_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L287), `SNDRV_PCM_INFO_RESUME`, and `SNDRV_PCM_INFO_BATCH` flags, and picks the destination or source `addr_widths` mask by direction. Unless the pack flag is set it then walks every PCM format with [`pcm_for_each_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h) and keeps in [`hw->formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) only those whose physical width the DMA bus can move, so user space can never select a format that would produce corrupted audio:

```c
/* sound/core/pcm_dmaengine.c:405 */
int snd_dmaengine_pcm_refine_runtime_hwparams(
	struct snd_pcm_substream *substream,
	struct snd_dmaengine_dai_dma_data *dma_data,
	struct snd_pcm_hardware *hw,
	struct dma_chan *chan)
{
	struct dma_slave_caps dma_caps;
	u32 addr_widths = BIT(DMA_SLAVE_BUSWIDTH_1_BYTE) |
			  BIT(DMA_SLAVE_BUSWIDTH_2_BYTES) |
			  BIT(DMA_SLAVE_BUSWIDTH_4_BYTES);
	snd_pcm_format_t i;
	int ret = 0;

	if (!hw || !chan || !dma_data)
		return -EINVAL;

	ret = dma_get_slave_caps(chan, &dma_caps);
	if (ret == 0) {
		if (dma_caps.cmd_pause && dma_caps.cmd_resume)
			hw->info |= SNDRV_PCM_INFO_PAUSE | SNDRV_PCM_INFO_RESUME;
		if (dma_caps.residue_granularity <= DMA_RESIDUE_GRANULARITY_SEGMENT)
			hw->info |= SNDRV_PCM_INFO_BATCH;

		if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK)
			addr_widths = dma_caps.dst_addr_widths;
		else
			addr_widths = dma_caps.src_addr_widths;
	}

	/*
	 * If SND_DMAENGINE_PCM_DAI_FLAG_PACK is set keep
	 * hw.formats set to 0, meaning no restrictions are in place.
	 * In this case it's the responsibility of the DAI driver to
	 * provide the supported format information.
	 */
	if (!(dma_data->flags & SND_DMAENGINE_PCM_DAI_FLAG_PACK))
		/*
		 * Prepare formats mask for valid/allowed sample types. If the
		 * dma does not have support for the given physical word size,
		 * it needs to be masked out so user space can not use the
		 * format which produces corrupted audio.
		 * In case the dma driver does not implement the slave_caps the
		 * default assumption is that it supports 1, 2 and 4 bytes
		 * widths.
		 */
		pcm_for_each_format(i) {
			int bits = snd_pcm_format_physical_width(i);

			/*
			 * Enable only samples with DMA supported physical
			 * widths
			 */
			switch (bits) {
			case 8:
			case 16:
			case 24:
			case 32:
			case 64:
				if (addr_widths & (1 << (bits / 8)))
					hw->formats |= pcm_format_to_bits(i);
				break;
			default:
				/* Unsupported types */
				break;
			}
		}

	return ret;
}
```

The two callers fill the config between them, hardware parameters giving width and direction and the DAI data giving the addresses:

```
    Two sources fill one dma_slave_config
    ─────────────────────────────────────────
    (the substream direction selects which half is written)

    struct snd_pcm_hw_params       struct snd_dmaengine_dai_dma_data
    ┌─────────────────────────┐    ┌───────────────────────────────┐
    │ format  → bus width     │    │ addr, maxburst, addr_width,   │
    │ stream  → direction     │    │ port_window_size              │
    └────────────┬────────────┘    └───────────────┬───────────────┘
                 │ snd_hwparams_to_                 │ ..._set_config_
                 │ dma_slave_config()               │ from_dai_data()
                 ▼                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ struct dma_slave_config                                     │
    │   playback ─▶ DMA_MEM_TO_DEV : dst_addr, dst_addr_width,    │
    │                               dst_maxburst                  │
    │   capture  ─▶ DMA_DEV_TO_MEM : src_addr, src_addr_width,    │
    │                               src_maxburst                  │
    └─────────────────────────────────────────────────────────────┘
```

### The trigger mapping to submit, resume, pause, and terminate

[`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) is the switch that turns each PCM trigger command into one dmaengine call. START builds and submits a fresh cyclic descriptor through [`dmaengine_pcm_prepare_and_submit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150) and flushes it with [`dma_async_issue_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1447); RESUME and PAUSE_RELEASE both [`dmaengine_resume()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1233); SUSPEND pauses when the runtime advertises [`SNDRV_PCM_INFO_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L287) and otherwise terminates; PAUSE_PUSH pauses; and STOP terminates asynchronously with [`dmaengine_terminate_async()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1164):

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

The START path runs [`dmaengine_pcm_prepare_and_submit()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L150), which programs a cyclic transfer over the whole ALSA ring with [`dmaengine_prep_dma_cyclic()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1038). It uses the buffer base [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the whole buffer length as the cyclic span, one period as the wakeup unit, resets the [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) counter, registers [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) as the per-period callback, and saves the submission [`cookie`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22). The `DMA_PREP_INTERRUPT` flag is set unless the runtime asked for no per-period wakeup:

```c
/* sound/core/pcm_dmaengine.c:150 */
static int dmaengine_pcm_prepare_and_submit(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	struct dma_chan *chan = prtd->dma_chan;
	struct dma_async_tx_descriptor *desc;
	enum dma_transfer_direction direction;
	unsigned long flags = DMA_CTRL_ACK;

	direction = snd_pcm_substream_to_dma_direction(substream);

	if (!substream->runtime->no_period_wakeup)
		flags |= DMA_PREP_INTERRUPT;

	prtd->pos = 0;
	desc = dmaengine_prep_dma_cyclic(chan,
		substream->runtime->dma_addr,
		snd_pcm_lib_buffer_bytes(substream),
		snd_pcm_lib_period_bytes(substream), direction, flags);

	if (!desc)
		return -ENOMEM;

	desc->callback = dmaengine_pcm_dma_complete;
	desc->callback_param = substream;
	prtd->cookie = dmaengine_submit(desc);

	return 0;
}
```

The transfer direction comes from [`snd_pcm_substream_to_dma_direction()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/dmaengine_pcm.h#L21), which returns `DMA_MEM_TO_DEV` for playback and `DMA_DEV_TO_MEM` for capture, matching the direction [`snd_hwparams_to_dma_slave_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L54) wrote into the slave config.

```
    snd_dmaengine_pcm_trigger: command to dmaengine call
    ────────────────────────────────────────────────────
    ┌──────────────────────────────────────────────────────────┐
    │ SNDRV_PCM_TRIGGER_*    dmaengine call                    │
    │ ─────────────────────  ──────────────────────────────────│
    │ START                  prep_dma_cyclic + submit, then    │
    │                        dma_async_issue_pending           │
    │ RESUME                 dmaengine_resume                  │
    │ PAUSE_RELEASE          dmaengine_resume                  │
    │ SUSPEND  (INFO_PAUSE)  dmaengine_pause                   │
    │ SUSPEND  (otherwise)   dmaengine_terminate_async         │
    │ PAUSE_PUSH             dmaengine_pause                   │
    │ STOP                   dmaengine_terminate_async         │
    └──────────────────────────────────────────────────────────┘
```

### The pointer and residue path

The PCM core asks for position by calling the pointer helper. [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251) queries the channel with [`dmaengine_tx_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/dmaengine.h#L1241), and when the transfer is in progress or paused it converts the reported residue, the bytes of the cyclic buffer not yet consumed, into a position by subtracting it from the buffer size, then fills [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) from the in-flight byte count so the reported position accounts for data already handed to the controller:

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

When the channel cannot report a fine-grained residue, the caller selects [`snd_dmaengine_pcm_pointer_no_residue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L235) instead, which returns the [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) byte counter maintained one period at a time by the completion callback. Its kernel-doc marks it as unreliable, "This function is deprecated and should not be used by new drivers, as its results may be unreliable". It does no dmaengine query at all, just converting the period-granular [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) that [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) keeps into a frame offset:

```c
/* sound/core/pcm_dmaengine.c:235 */
snd_pcm_uframes_t snd_dmaengine_pcm_pointer_no_residue(struct snd_pcm_substream *substream)
{
	struct dmaengine_pcm_runtime_data *prtd = substream_to_prtd(substream);
	return bytes_to_frames(substream->runtime, prtd->pos);
}
```

Both helpers return frames through [`bytes_to_frames()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L751), so the value the PCM core receives is always a frame offset into the buffer the cyclic descriptor walks.

```
    snd_dmaengine_pcm_pointer: residue to ring position
    ───────────────────────────────────────────────────
    buf_size = whole cyclic buffer (runtime->dma_addr ..)

    0                         pos               buf_size
    ├───────────────────────────┼──────────────────────┤
    │ consumed by DMA           │ residue (not yet)    │
    └───────────────────────────┴──────────────────────┘
             pos = buf_size − residue   (bytes)
             frames = bytes_to_frames(pos)
             runtime->delay  ◀── state.in_flight_bytes
```

### The completion callback feeding snd_pcm_period_elapsed

[`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) is the callback the cyclic descriptor fires at each period boundary, and it is where the dmaengine side rejoins the PCM core. It advances [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L22) by one period using [`snd_pcm_lib_period_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L810), wraps it at the buffer end so the counter tracks the cyclic position, and calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933):

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

[`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) takes the PCM stream lock and runs [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900), and according to its kernel-doc, "It's typically called by any type of IRQ handler when hardware IRQ occurs to notify event that the batch of audio data frames as the same size as the period of buffer is already processed in audio data transmission":

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

The callback runs in the dmaengine provider's interrupt context, so the lock [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) takes is the IRQ-safe stream lock. That call advances the runtime's hardware pointer, checks for an underrun or overrun against the application pointer, and wakes any task sleeping on the substream.

```
    dmaengine_pcm_dma_complete advances pos one period
    ──────────────────────────────────────────────────
    cyclic buffer = N periods; one IRQ per period boundary

    ┌────────┬────────┬────────┬────────┐
    │ period │ period │ period │ period │ ◀─ buffer_bytes
    │   0    │   1    │   2    │  N−1   │
    └────────┴────────┴────────┴────────┘
      ▲ pos += period_bytes each callback
      └─ if pos >= buffer_bytes: pos = 0   (wrap)
         then snd_pcm_period_elapsed(substream)
```

### Userspace interaction

This glue exposes no ABI of its own. A userspace client never names a dmaengine channel or a residue; it opens the PCM character device, runs the standard `SNDRV_PCM_IOCTL_*` sequence, and either mmaps the buffer or transfers through the read/write path, all defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The glue serves that contract from below; a [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) reaches [`snd_dmaengine_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L189) (START), and a pointer query reaches [`snd_dmaengine_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L251), whose residue-derived frame offset becomes the hardware pointer the client reads back.

The period-elapsed callback is the wakeup a `poll()`ing client waits on. [`dmaengine_pcm_dma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_dmaengine.c#L136) calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) at each cyclic period boundary, and that advance of the runtime pointer is what signals the substream's wait queue, so a client blocked in `poll()` returns once a period's worth of frames has moved through the DMA. The mmap'd [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) the client reads or writes is the same buffer at [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) that the cyclic descriptor walks, and that buffer is preallocated and bound to the runtime by the ALSA core.
