# PCM operations (snd_pcm_ops)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A PCM substream is driven through one function pointer struct, [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), which a driver fills in and the ALSA PCM core reaches through the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer of each [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464). The fifteen callbacks in that struct cover the whole life of a stream, [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) at the ends, [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) on the configuration path, [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) on the running path, and [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) for data movement and timing. A userspace client never touches these pointers. It issues ioctls on the PCM character device, and [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) dispatches each one into a core helper in [`pcm_native.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c) that validates the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) state, calls the matching op, and advances the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer is set by the driver through [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510); for an ASoC card the soc-pcm layer fills a [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) in [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) so the generic callbacks fan a request out across every CPU DAI, codec DAI, and component of the link.

```
        userspace ioctl on /dev/snd/pcmC0D0p
                        │
                        ▼
        snd_pcm_common_ioctl()           sound/core/pcm_native.c
          HW_PARAMS ─▶ snd_pcm_hw_params()  ─▶ ops->hw_params  state ▶ SETUP
          SW_PARAMS ─▶ snd_pcm_sw_params()  ─▶ (no op)         state unchanged
          PREPARE   ─▶ snd_pcm_prepare()    ─▶ ops->prepare    state ▶ PREPARED
          HW_FREE   ─▶ snd_pcm_hw_free()    ─▶ ops->hw_free    state ▶ OPEN
                        │
                        ▼
        substream->ops  ─▶  struct snd_pcm_ops   (set by snd_pcm_set_ops)
                            open close hw_params hw_free prepare
                            trigger pointer copy mmap ack ...
```

## SUMMARY

The driver-facing contract of an ALSA PCM device is one [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) per direction. A driver populates the callbacks its hardware needs, then registers them on every substream of a direction with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510), which writes the pointer into [`substream->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) for each [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) in the [`streams[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) array of the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534). From that point the PCM core dereferences the op pointers directly at the file-operation entry points, with no per-call wrapper macro of the kind ASoC uses for DAI ops.

The callbacks split by phase. [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) runs from [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) and [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) from [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) at the file-descriptor ends. The configuration path is three ops, [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) invoked by [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) by [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) by [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965). The running path is [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), called for start by [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) and for stop by [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530), together with [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), read by [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) to track buffer progress. The data-movement ops [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) are consulted in [`__snd_pcm_lib_xfer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271), the mapping ops [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) in [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) and [`snd_pcm_mmap_data_fault()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3872), and [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) in [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227). The driver-private [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is reached through [`snd_pcm_ops_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L212) and falls back to [`snd_pcm_lib_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1856) when the driver supplies none. Each helper records the new lifecycle state with [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) or [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725), so the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) field always reflects which ops have run.

## SPECIFICATIONS

The [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) interface is a Linux kernel software construct and has no standalone hardware specification. The PCM control-flow protocol it implements (the OPEN, SETUP, PREPARED, RUNNING state set and the ioctl numbers that drive transitions) is defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). On x86-64 platforms the underlying audio controllers (Intel High Definition Audio, USB Audio Class, SoundWire codecs) are specified by their own standards, which constrain what a driver's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) ops program while leaving the op interface itself to the kernel.

## LINUX KERNEL

### The function pointer struct and its host objects (include/sound/pcm.h)

- [`'\<struct snd_pcm_ops\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55): the fifteen-callback function pointer struct a driver fills in to service a PCM substream
- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): the per-direction stream instance whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer holds the function pointer struct and whose [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) holds the live state
- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the runtime record carrying the lifecycle [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the negotiated hw/sw parameters, the DMA area, and the [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) flag the [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op consults
- [`'\<struct snd_pcm\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534): the PCM device holding the [`streams[2]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) array of substreams that [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) walks
- [`'\<snd_pcm_state_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306): the bitwise int that types the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) field and the `SNDRV_PCM_STATE_*` constants

### Registration and dispatch (pcm_native.c, pcm_lib.c)

- [`'\<snd_pcm_set_ops\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510): store the function pointer struct into [`substream->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) for every substream of a direction
- [`'\<snd_pcm_common_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363): the per-stream ioctl dispatcher that routes `SNDRV_PCM_IOCTL_*` numbers to the core helpers
- [`'\<snd_pcm_ops_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L212): call the driver [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or fall back to [`snd_pcm_lib_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1856)
- [`'\<snd_pcm_lib_ioctl\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1856): the generic `SNDRV_PCM_IOCTL1_*` handler used when a driver leaves [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) NULL
- [`'\<snd_pcm_set_state\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) / [`'\<__snd_pcm_set_state\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725): write the new lifecycle value into [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) and the mmap copy

### Open and close (pcm_native.c)

- [`'\<snd_pcm_open_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767): attach the substream, build hw constraints, then run the [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and set [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464)
- [`'\<snd_pcm_release_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744): drop the stream, free hardware if still set up, then run the [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op

### Configuration path (pcm_native.c)

- [`'\<snd_pcm_hw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754): refine the parameters, call the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, copy the chosen values into [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), and set state SETUP on success or OPEN on error
- [`'\<snd_pcm_hw_params_user\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L889): copy the [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) from user space, call [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), copy the result back
- [`'\<snd_pcm_hw_free\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920): validate the state, run [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908), and set state OPEN
- [`'\<do_hw_free\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908): synchronise, call the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and free managed buffers
- [`'\<snd_pcm_sw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953): validate and store the software parameters into [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362); it calls no op in [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55)
- [`'\<snd_pcm_sw_params_user\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1006): copy the [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433) in, call [`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953), copy it back
- [`'\<snd_pcm_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997): drive the prepare action through [`snd_pcm_action_nonatomic()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416) with [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984)
- [`'\<snd_pcm_do_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965): synchronise and call the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op
- [`'\<snd_pcm_post_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976): set state PREPARED after the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op returns

### Running path (pcm_native.c, pcm_lib.c)

- [`'\<snd_pcm_do_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452): call the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op with `SNDRV_PCM_TRIGGER_START`, demoting to XRUN on `-EPIPE`
- [`'\<snd_pcm_do_stop\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530): call the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op with `SNDRV_PCM_TRIGGER_STOP`
- [`'\<snd_pcm_do_pause\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1628) / [`'\<snd_pcm_do_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) / [`'\<snd_pcm_do_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814): the pause, suspend, and resume trigger commands
- [`'\<snd_pcm_sync_stop\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639): call the [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op (or fall back to [`synchronize_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L145)) when [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is set
- [`'\<snd_pcm_update_hw_ptr0\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286): read the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and, when present, the [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op to update the hardware position and timestamps

### Data movement and mapping (pcm_lib.c, pcm_native.c)

- [`'\<__snd_pcm_lib_xfer\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271): the read/write loop that selects the [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op (or a default) and uses [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) for a NULL playback buffer
- [`'\<fill_silence\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2069): write silence through the [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or the generic silence helper
- [`'\<pcm_lib_apply_appl_ptr\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227): advance the application pointer and call the [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op
- [`'\<snd_pcm_mmap_data\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969): map the DMA buffer through the [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927)
- [`'\<snd_pcm_mmap_data_fault\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3872): resolve a fault page through the [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op when the driver supplies one
- [`'\<hw_support_mmap\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L262): report mmap capability based on the presence of the [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) or [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op

### ASoC boundary (soc-pcm.c)

- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): fill the soc-pcm [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and register it with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510)
- [`'\<soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917): the ASoC [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op forwarding to [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L860)
- [`'\<soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) / [`'\<__soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070): the ASoC [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op that calls [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on each DAI of the link
- [`'\<soc_pcm_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198): the ASoC [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op that orders component, CPU, and codec triggering with rollback

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM chapter that documents each [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback, the state machine, and the buffer and silence helpers
- [`Documentation/sound/designs/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/index.rst): the ALSA design notes covering the PCM timestamp and synchronization models the [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) ops support
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the soc-pcm front-end ops in [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) feed back-end DAIs

## OTHER SOURCES

- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Every callback below is a field of [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55). The PCM core dereferences each op pointer at a fixed file-operation entry point, and most entry points guard the call with an explicit NULL test, so an op a driver leaves unset is skipped. Only [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) are called unconditionally by their host functions and are therefore effectively mandatory for a working substream; the rest are optional. An op returns 0 on success and a negative errno on failure, except [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), which returns the current hardware position as an [`snd_pcm_uframes_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L147), and [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), which returns a [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) pointer. The mapping from the operation a userspace client requests to the op that runs and the resulting [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) state is fixed.

| userspace operation | snd_pcm_ops callback | invoked by | resulting PCM state |
|---------------------|----------------------|------------|---------------------|
| `open()` on the PCM node | [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) (OPEN on error) |
| `SNDRV_PCM_IOCTL_SW_PARAMS` | (none) | [`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953) | unchanged |
| `SNDRV_PCM_IOCTL_PREPARE` | [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) | [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309) |
| `SNDRV_PCM_IOCTL_START` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) (START) | [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |
| `SNDRV_PCM_IOCTL_PAUSE` (push) | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) (PAUSE_PUSH) | [`snd_pcm_do_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1628) | [`SNDRV_PCM_STATE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L313) |
| `SNDRV_PCM_IOCTL_DROP` | [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) (STOP) | [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530) | [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) | [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) |
| `read()`/`write()` transfer | [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) / [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`__snd_pcm_lib_xfer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271) | unchanged |
| `mmap()` of the buffer | [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) / [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) | unchanged |
| `close()` of the descriptor | [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) | [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) | (released) |

### open and close

[`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) runs once when the first reference to a substream is taken, called unconditionally by [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) after the hardware constraints are initialised, and it sets up the driver-private runtime and assigns the [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) capability record. [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) runs from [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) when the last reference is dropped, after any outstanding hardware has been freed, so it releases what [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) acquired. The state is OPEN for the whole window between these two ops.

### ioctl

[`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) handles the small set of driver-private `SNDRV_PCM_IOCTL1_*` requests, reached through [`snd_pcm_ops_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L212), which calls the op when set and otherwise runs the generic [`snd_pcm_lib_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1856). Most drivers leave it NULL and accept the default, which answers the channel-info, FIFO-size, sync-id, and reset queries. This op is internal to the core, distinct from the userspace `SNDRV_PCM_IOCTL_*` numbers handled in [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363).

### hw_params and hw_free

[`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) applies the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) (access mode, format, rate, channels, period and buffer sizes) to the hardware and, for managed buffers, may allocate the DMA area. It is called by [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) only after the parameter refinement succeeds, and a failure here forces the state back to OPEN. [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) reverses it, releasing whatever [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) claimed; [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) calls it under a NULL guard and then the state returns to OPEN. Both ops may run more than once across the life of a substream, since a client can re-negotiate parameters after an [`SNDRV_PCM_IOCTL_HW_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L682).

### prepare

[`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) readies the substream to be triggered, called unconditionally by [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) after a synchronising [`snd_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639), so the driver can program the controller, reset its FIFO, and zero its position counters. It runs at the [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) ioctl and again after an XRUN or a resume, and [`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976) sets the state to PREPARED once it returns.

### trigger

[`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) starts, stops, pauses, suspends, or resumes the data flow, taking one of the `SNDRV_PCM_TRIGGER_*` commands. It is called unconditionally from the action helpers, [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) for [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99), [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530) for stop, and the pause, suspend, and resume helpers for the others. According to the comment in [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452), "XRUN happened during the start", so a [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) returning `-EPIPE` moves the stream to XRUN rather than RUNNING. For most cards the op runs in atomic context under the PCM stream lock.

### sync_stop

[`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) waits for the hardware and any IRQ handler to quiesce after a stop, so a following [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) or [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) does not race in-flight DMA. [`snd_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639) calls it only when [`runtime->stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is set, and when the driver supplies no op it falls back to [`synchronize_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L145) on the card's shared IRQ.

### pointer

[`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) returns the current hardware position in frames within the ring buffer, called by [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) at every interrupt and timer tick to advance the buffer accounting. Its return type is [`snd_pcm_uframes_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L147), and a return of [`SNDRV_PCM_POS_XRUN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L106) signals an underrun or overrun. It is effectively mandatory, since the core dereferences it without a NULL check.

### get_time_info

[`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) supplies a precise correlated system and audio timestamp, queried inside [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) when the driver provides it, so a client can align audio frames to the system clock more accurately than the default jiffies estimate. It is optional; when absent the core derives timestamps from the buffer pointer and the wall clock.

### fill_silence and copy

[`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) moves one chunk of audio between the user [`struct iov_iter`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uio.h#L43) and the hardware buffer for a driver whose DMA area is not directly addressable, selected in [`__snd_pcm_lib_xfer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271) in place of the default memcpy path. [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) writes silence into a region, used by [`fill_silence()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2069) for under-run filling and for a NULL playback buffer. Both are optional; a driver with a plain DMA buffer omits them and the core uses generic copy and silence routines.

### page

[`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) returns the [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) backing a given byte offset of the buffer, called from the fault handler [`snd_pcm_mmap_data_fault()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3872) when a driver maps non-contiguous or vmalloc memory. It is optional; for a contiguous DMA buffer the default fault path computes the page directly.

### mmap

[`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) maps the DMA buffer into the client address space, called by [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) when present and otherwise replaced by [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927). A driver overrides it only when the buffer needs special VMA flags or a custom mapping, and the presence of either [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) or [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) is what [`hw_support_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L262) reports as mmap capability.

### ack

[`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) notifies the driver that the application pointer has moved, called from [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227) after each transfer so a driver that hands data to firmware can push the newly available bytes. It is optional; a DMA-driven driver that reads the pointer at interrupt time leaves it unset.

## DETAILS

### The function pointer struct

A driver describes its PCM hardware with one [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55). It is a plain function pointer struct, with one pointer per operation and no flags or version field, so the core distinguishes a supported operation from an unsupported one purely by whether the pointer is NULL:

```c
/* include/sound/pcm.h:55 */
struct snd_pcm_ops {
	int (*open)(struct snd_pcm_substream *substream);
	int (*close)(struct snd_pcm_substream *substream);
	int (*ioctl)(struct snd_pcm_substream * substream,
		     unsigned int cmd, void *arg);
	int (*hw_params)(struct snd_pcm_substream *substream,
			 struct snd_pcm_hw_params *params);
	int (*hw_free)(struct snd_pcm_substream *substream);
	int (*prepare)(struct snd_pcm_substream *substream);
	int (*trigger)(struct snd_pcm_substream *substream, int cmd);
	int (*sync_stop)(struct snd_pcm_substream *substream);
	snd_pcm_uframes_t (*pointer)(struct snd_pcm_substream *substream);
	int (*get_time_info)(struct snd_pcm_substream *substream,
			struct timespec64 *system_ts, struct timespec64 *audio_ts,
			struct snd_pcm_audio_tstamp_config *audio_tstamp_config,
			struct snd_pcm_audio_tstamp_report *audio_tstamp_report);
	int (*fill_silence)(struct snd_pcm_substream *substream, int channel,
			    unsigned long pos, unsigned long bytes);
	int (*copy)(struct snd_pcm_substream *substream, int channel,
		    unsigned long pos, struct iov_iter *iter, unsigned long bytes);
	struct page *(*page)(struct snd_pcm_substream *substream,
			     unsigned long offset);
	int (*mmap)(struct snd_pcm_substream *substream, struct vm_area_struct *vma);
	int (*ack)(struct snd_pcm_substream *substream);
};
```

Every op takes the [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) as its first argument, and the op reaches its own state through that handle. The substream holds the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer the core just dereferenced, alongside the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) record that carries the live parameters and the DMA area:

```c
/* include/sound/pcm.h:464 */
struct snd_pcm_substream {
	struct snd_pcm *pcm;
	struct snd_pcm_str *pstr;
	void *private_data;		/* copied from pcm->private_data */
	int number;
	char name[32];			/* substream name */
	int stream;			/* stream (direction) */
	struct pm_qos_request latency_pm_qos_req; /* pm_qos request */
	size_t buffer_bytes_max;	/* limit ring buffer size */
	struct snd_dma_buffer dma_buffer;
	size_t dma_max;
	/* -- hardware operations -- */
	const struct snd_pcm_ops *ops;
	/* -- runtime information -- */
	struct snd_pcm_runtime *runtime;
	...
	/* misc flags */
	unsigned int hw_opened: 1;
	unsigned int managed_buffer_alloc:1;
	...
};
```

The lifecycle [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) the configuration helpers advance is the first field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), and the [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) flag that gates [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) lives further down in the same record:

```c
/* include/sound/pcm.h:362 */
struct snd_pcm_runtime {
	/* -- Status -- */
	snd_pcm_state_t state;		/* stream state */
	snd_pcm_state_t suspended_state; /* suspended stream state */
	struct snd_pcm_substream *trigger_master;
	...
	/* -- locking / scheduling -- */
	...
	bool stop_operating;		/* sync_stop will be called */
	...
};
```

The [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) takes one of the `SNDRV_PCM_STATE_*` values defined in the ABI header. The configuration path moves a stream through OPEN, SETUP, and PREPARED in order, and a stop returns it to SETUP:

```c
/* include/uapi/sound/asound.h:307 */
#define	SNDRV_PCM_STATE_OPEN		((__force snd_pcm_state_t) 0) /* stream is open */
#define	SNDRV_PCM_STATE_SETUP		((__force snd_pcm_state_t) 1) /* stream has a setup */
#define	SNDRV_PCM_STATE_PREPARED	((__force snd_pcm_state_t) 2) /* stream is ready to start */
#define	SNDRV_PCM_STATE_RUNNING		((__force snd_pcm_state_t) 3) /* stream is running */
#define	SNDRV_PCM_STATE_XRUN		((__force snd_pcm_state_t) 4) /* stream reached an xrun */
#define	SNDRV_PCM_STATE_DRAINING	((__force snd_pcm_state_t) 5) /* stream is draining */
#define	SNDRV_PCM_STATE_PAUSED		((__force snd_pcm_state_t) 6) /* stream is paused */
#define	SNDRV_PCM_STATE_SUSPENDED	((__force snd_pcm_state_t) 7) /* hardware is suspended */
#define	SNDRV_PCM_STATE_DISCONNECTED	((__force snd_pcm_state_t) 8) /* hardware is disconnected */
```

The callbacks that carry a stream through those states group by phase, with a starred handful dereferenced under no NULL guard and so effectively mandatory:

```
    struct snd_pcm_ops: the 15 callbacks grouped by phase
    ──────────────────────────────────────────────────────
    (* = dereferenced with no NULL guard, effectively mandatory)

    ┌──────────────────────────────────────────────────────────┐
    │ ends         open *       close *                        │
    │ private      ioctl                                       │
    │ configure    hw_params    hw_free      prepare *         │
    │ running      trigger *    pointer *    sync_stop         │
    │              get_time_info                               │
    │ data move    copy         fill_silence                   │
    │ mapping      mmap         page                           │
    │ notify       ack                                         │
    └──────────────────────────────────────────────────────────┘

    one pointer per op and no flags field, so a NULL pointer means
    the op is unsupported and the core skips it
```

### The driver installs the ops with snd_pcm_set_ops

A PCM device owns two [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) lists, one per direction, in the [`streams[2]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) array of its [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534). [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) installs one function pointer struct for a whole direction by walking that list and writing the same pointer into every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) field:

```c
/* sound/core/pcm_lib.c:510 */
void snd_pcm_set_ops(struct snd_pcm *pcm, int direction,
		     const struct snd_pcm_ops *ops)
{
	struct snd_pcm_str *stream = &pcm->streams[direction];
	struct snd_pcm_substream *substream;
	
	for (substream = stream->substream; substream != NULL; substream = substream->next)
		substream->ops = ops;
}
```

From here the core has a non-NULL [`substream->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) on every substream, and each file-operation entry point dereferences it directly.

### Open runs the open op and records hw_opened

[`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) is the first place an op runs. After attaching the substream and initialising the hardware constraints, it calls the [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op without a NULL guard, then marks [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) so the release path knows the op ran:

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

	substream->hw_opened = 1;
	...
}
```

[`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) is the mirror. It frees any still-configured hardware with [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) and only then runs the [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, guarded by the [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) flag so [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) runs only against a substream whose [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) succeeded:

```c
/* sound/core/pcm_native.c:2744 */
void snd_pcm_release_substream(struct snd_pcm_substream *substream)
{
	substream->ref_count--;
	if (substream->ref_count > 0)
		return;

	snd_pcm_drop(substream);
	if (substream->hw_opened) {
		if (substream->runtime->state != SNDRV_PCM_STATE_OPEN)
			do_hw_free(substream);
		substream->ops->close(substream);
		substream->hw_opened = 0;
	}
	...
}
```

### snd_pcm_hw_params calls the hw_params op and sets the SETUP state

[`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) is the core of the configuration path. It first validates that the stream is in OPEN, SETUP, or PREPARED (any other state returns `-EBADFD`), refines the requested parameters against the hardware constraints, and allocates the managed buffer if the driver uses one. It then calls the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op under a NULL guard and copies the chosen values into [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362):

```c
/* sound/core/pcm_native.c:754 */
	if (substream->ops->hw_params != NULL) {
		err = substream->ops->hw_params(substream, params);
		if (err < 0)
			goto _error;
	}

	runtime->access = params_access(params);
	runtime->format = params_format(params);
	runtime->subformat = params_subformat(params);
	runtime->channels = params_channels(params);
	runtime->rate = params_rate(params);
	runtime->period_size = params_period_size(params);
	runtime->periods = params_periods(params);
	runtime->buffer_size = params_buffer_size(params);
	...
```

After the op succeeds it computes the byte and frame alignment and commits the state with [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621); the error tail forces the state back to OPEN and undoes a partial setup:

```c
/* sound/core/pcm_native.c:754 */
	snd_pcm_timer_resolution_change(substream);
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_SETUP);
	...
	err = 0;
 _error:
	if (err) {
		/* hardware might be unusable from this time,
		 * so we force application to retry to set
		 * the correct hardware parameter settings
		 */
		snd_pcm_set_state(substream, SNDRV_PCM_STATE_OPEN);
		if (substream->ops->hw_free != NULL)
			substream->ops->hw_free(substream);
		if (substream->managed_buffer_alloc)
			snd_pcm_lib_free_pages(substream);
	}
 unlock:
	snd_pcm_buffer_access_unlock(runtime);
	return err;
}
```

According to the comment in [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), "hardware might be unusable from this time, so we force application to retry to set the correct hardware parameter settings", which is why the error tail sets the state to OPEN and calls the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op to undo a partial setup. A success leaves the stream in SETUP; a failure leaves it in OPEN.

### do_hw_free calls the hw_free op and returns to OPEN

The teardown side is [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908), which synchronises against in-flight DMA, calls the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op under a NULL guard, and frees the managed buffer:

```c
/* sound/core/pcm_native.c:908 */
static int do_hw_free(struct snd_pcm_substream *substream)
{
	int result = 0;

	snd_pcm_sync_stop(substream, true);
	if (substream->ops->hw_free)
		result = substream->ops->hw_free(substream);
	if (substream->managed_buffer_alloc)
		snd_pcm_lib_free_pages(substream);
	return result;
}
```

[`snd_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920) wraps it for the ioctl path. It accepts only the SETUP or PREPARED state, runs [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908), and then sets the state back to OPEN. A non-zero [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) makes it return `-EBADFD`, since freeing a buffer still mapped by a process would leave a dangling mapping.

### snd_pcm_sw_params stores software parameters and calls no op

[`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953) handles the [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) request. Unlike the hardware path, it programs nothing in the driver. It validates the requested thresholds and copies them straight into the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) fields the core itself consults (the wakeup avail-min, the start and stop thresholds, and the silence parameters), so there is no callback in [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) for it to invoke and the lifecycle state does not change:

```c
/* sound/core/pcm_native.c:953 */
	err = 0;
	scoped_guard(pcm_stream_lock_irq, substream) {
		runtime->tstamp_mode = params->tstamp_mode;
		if (params->proto >= SNDRV_PROTOCOL_VERSION(2, 0, 12))
			runtime->tstamp_type = params->tstamp_type;
		runtime->period_step = params->period_step;
		runtime->control->avail_min = params->avail_min;
		runtime->start_threshold = params->start_threshold;
		runtime->stop_threshold = params->stop_threshold;
		runtime->silence_threshold = params->silence_threshold;
		runtime->silence_size = params->silence_size;
		params->boundary = runtime->boundary;
		if (snd_pcm_running(substream)) {
			...
			err = snd_pcm_update_state(substream, runtime);
		}
	}
	return err;
}
```

The one constraint it enforces is that the stream is past OPEN, since the software parameters describe a buffer whose geometry [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) has already fixed; a call in OPEN returns `-EBADFD`.

### The prepare op runs through the action machinery

[`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) reaches the driver op through the generic action framework rather than a direct call. [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) first reverses a pause or suspend, then dispatches the [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) action through [`snd_pcm_action_nonatomic()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416). The action's [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) and [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) bracket the do-step that calls the op. [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) synchronises and then calls the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op unconditionally:

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

[`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976) runs after the op returns and commits the PREPARED state:

```c
/* sound/core/pcm_native.c:1976 */
static void snd_pcm_post_prepare(struct snd_pcm_substream *substream,
				 snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	runtime->control->appl_ptr = runtime->status->hw_ptr;
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_PREPARED);
}
```

### The trigger op starts and stops the data flow

Once the stream is PREPARED, [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) runs the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op through the start action's do-step. [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) calls the op with [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) and treats the XRUN-during-start case specially:

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

The stop side, [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530), issues [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) to the same op, and the pause, suspend, and resume helpers issue the remaining `SNDRV_PCM_TRIGGER_*` commands. Because the same op receives every command, a driver reads the [`cmd`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) argument to decide what to do, and the start command moves the stream to RUNNING while a stop returns it to SETUP.

### The running path reads the pointer op

While the stream runs, [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) reads the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op at each interrupt to learn the hardware position, and queries the [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op when the driver provides one:

```c
/* sound/core/pcm_lib.c:286 */
	pos = substream->ops->pointer(substream);
	curr_jiffies = jiffies;
	if (runtime->tstamp_mode == SNDRV_PCM_TSTAMP_ENABLE) {
		if ((substream->ops->get_time_info) &&
			(runtime->audio_tstamp_config.type_requested != SNDRV_PCM_AUDIO_TSTAMP_TYPE_DEFAULT)) {
			substream->ops->get_time_info(substream, &curr_tstamp,
						&audio_tstamp,
						&runtime->audio_tstamp_config,
						&runtime->audio_tstamp_report);
			...
		}
	}
```

The [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is dereferenced with no NULL check, which is why a working substream has to supply it. The [`get_time_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is optional and only consulted when timestamping is enabled and a non-default type is requested.

### The transfer path selects copy and fill_silence

For read and write, [`__snd_pcm_lib_xfer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271) picks the transfer routine up front. A NULL playback buffer means write silence through [`fill_silence()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2069); otherwise it uses the driver [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op when present and a default memcpy routine when not:

```c
/* sound/core/pcm_lib.c:2271 */
	if (!data) {
		if (is_playback)
			transfer = fill_silence;
		else
			return -EINVAL;
	} else {
		if (substream->ops->copy)
			transfer = substream->ops->copy;
		else
			transfer = is_playback ?
				default_write_copy : default_read_copy;
	}
```

[`fill_silence()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2069) in turn calls the driver [`fill_silence`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op when one is set, falling back to the generic silence writer. After each chunk, [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227) advances the application pointer and calls the [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op so a firmware-driven driver can push the freshly produced bytes:

```c
/* sound/core/pcm_lib.c:2227 */
	if (substream->ops->ack) {
		ret = substream->ops->ack(substream);
		...
	}
```

### The mmap path selects mmap and page

When a client maps the buffer, [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) installs the PCM VMA operations and then either calls the driver [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or falls back to [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927):

```c
/* sound/core/pcm_native.c:3969 */
	area->vm_ops = &snd_pcm_vm_ops_data;
	area->vm_private_data = substream;
	if (substream->ops->mmap)
		err = substream->ops->mmap(substream, area);
	else
		err = snd_pcm_lib_default_mmap(substream, area);
	if (!err)
		atomic_inc(&substream->mmap_count);
	return err;
```

A page fault inside that mapping reaches [`snd_pcm_mmap_data_fault()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3872), which uses the driver [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op to resolve the backing [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) when one is set, and computes the page from the DMA area otherwise.

### The ioctl dispatch from snd_pcm_common_ioctl

The userspace numbers that drive all of the above arrive at [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363). It checks the runtime is live, waits for the card to be powered, and switches on the command into the per-operation helpers:

```c
/* sound/core/pcm_native.c:3363 */
	switch (cmd) {
	...
	case SNDRV_PCM_IOCTL_HW_PARAMS:
		return snd_pcm_hw_params_user(substream, arg);
	case SNDRV_PCM_IOCTL_HW_FREE:
		return snd_pcm_hw_free(substream);
	case SNDRV_PCM_IOCTL_SW_PARAMS:
		return snd_pcm_sw_params_user(substream, arg);
	...
	case SNDRV_PCM_IOCTL_PREPARE:
		return snd_pcm_prepare(substream, file);
	case SNDRV_PCM_IOCTL_RESET:
		return snd_pcm_reset(substream);
	case SNDRV_PCM_IOCTL_START:
		return snd_pcm_start_lock_irq(substream);
	...
	case SNDRV_PCM_IOCTL_DROP:
		return snd_pcm_drop(substream);
	case SNDRV_PCM_IOCTL_PAUSE:
		return snd_pcm_pause_lock_irq(substream, (unsigned long)arg);
	...
	}
	pcm_dbg(substream->pcm, "unknown ioctl = 0x%x\n", cmd);
	return -ENOTTY;
}
```

[`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) reaches [`snd_pcm_hw_params_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L889), which copies the parameter block from user space, calls [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), and copies the refined block back. The driver [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is a separate channel, reached not from this switch but from [`snd_pcm_ops_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L212) on the internal `SNDRV_PCM_IOCTL1_*` commands, which calls the op when set and otherwise runs [`snd_pcm_lib_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1856):

```c
/* sound/core/pcm_native.c:212 */
static int snd_pcm_ops_ioctl(struct snd_pcm_substream *substream,
			     unsigned cmd, void *arg)
{
	if (substream->ops->ioctl)
		return substream->ops->ioctl(substream, cmd, arg);
	else
		return snd_pcm_lib_ioctl(substream, cmd, arg);
}
```

### The ASoC boundary fills the ops in soc_new_pcm

For an ASoC card the driver that fills [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) is the soc-pcm layer. [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) populates a [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) embedded in the runtime with generic ASoC callbacks (one set for a regular PCM, a separate front-end set for Dynamic PCM), and registers it for both directions with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510):

```c
/* sound/soc/soc-pcm.c:2909 */
	} else {
		rtd->ops.open		= soc_pcm_open;
		rtd->ops.hw_params	= soc_pcm_hw_params;
		rtd->ops.prepare	= soc_pcm_prepare;
		rtd->ops.trigger	= soc_pcm_trigger;
		rtd->ops.hw_free	= soc_pcm_hw_free;
		rtd->ops.close		= soc_pcm_close;
		rtd->ops.pointer	= soc_pcm_pointer;
	}
	...
	if (playback)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK, &rtd->ops);

	if (capture)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE, &rtd->ops);
```

The generic ASoC [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), whose work is in [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070). When the PCM core calls this single op, it fans the request across every codec DAI and CPU DAI of the link by calling [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on each, so one [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) entry point drives the whole DAI chain underneath. From the PCM core's view the boundary is the [`substream->ops->hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) dereference in [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754).

### Userspace drives the ops vector through snd_pcm_common_ioctl

A userspace client, or alsa-lib on its behalf, never names a [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback. It opens the PCM character device, which runs the [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op through [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) and leaves the stream in OPEN, then issues a sequence of ioctls that each land on one arm of [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363). [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) runs the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and advances the stream to SETUP, [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) records the software thresholds with no op and no state change, [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) runs the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and advances to PREPARED, and [`SNDRV_PCM_IOCTL_HW_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L682) runs the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and returns to OPEN. The start, stop, pause, and transfer ioctls then drive the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) ops as the data flows. The [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is the visible record of how far through that sequence the stream has travelled, and each helper updates it through [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) so the next ioctl can validate its precondition.

### snd_pcm_common_ioctl is the full ioctl switch

The narrowed switch above is one arm of the complete dispatcher. [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) rejects a torn-down or disconnected runtime, waits for the card with [`snd_power_wait()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L506), and then routes every `SNDRV_PCM_IOCTL_*` number, the version and info queries, the configuration commands, the start, drop, pause, drain, resume, and xrun commands, and the in-kernel read/write/rewind/forward helpers, to one core function each. The driver [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is not on this path; it is the separate `SNDRV_PCM_IOCTL1_*` channel through [`snd_pcm_ops_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L212):

```c
/* sound/core/pcm_native.c:3363 */
static int snd_pcm_common_ioctl(struct file *file,
				 struct snd_pcm_substream *substream,
				 unsigned int cmd, void __user *arg)
{
	struct snd_pcm_file *pcm_file = file->private_data;
	int res;

	if (PCM_RUNTIME_CHECK(substream))
		return -ENXIO;

	if (substream->runtime->state == SNDRV_PCM_STATE_DISCONNECTED)
		return -EBADFD;

	res = snd_power_wait(substream->pcm->card);
	if (res < 0)
		return res;

	switch (cmd) {
	case SNDRV_PCM_IOCTL_PVERSION:
		return put_user(SNDRV_PCM_VERSION, (int __user *)arg) ? -EFAULT : 0;
	case SNDRV_PCM_IOCTL_INFO:
		return snd_pcm_info_user(substream, arg);
	...
	case SNDRV_PCM_IOCTL_HW_PARAMS:
		return snd_pcm_hw_params_user(substream, arg);
	case SNDRV_PCM_IOCTL_HW_FREE:
		return snd_pcm_hw_free(substream);
	case SNDRV_PCM_IOCTL_SW_PARAMS:
		return snd_pcm_sw_params_user(substream, arg);
	...
	case SNDRV_PCM_IOCTL_PREPARE:
		return snd_pcm_prepare(substream, file);
	case SNDRV_PCM_IOCTL_START:
		return snd_pcm_start_lock_irq(substream);
	case SNDRV_PCM_IOCTL_RESUME:
		return snd_pcm_resume(substream);
	case SNDRV_PCM_IOCTL_DRAIN:
		return snd_pcm_drain(substream, file);
	case SNDRV_PCM_IOCTL_DROP:
		return snd_pcm_drop(substream);
	case SNDRV_PCM_IOCTL_PAUSE:
		return snd_pcm_pause_lock_irq(substream, (unsigned long)arg);
	...
	}
	pcm_dbg(substream->pcm, "unknown ioctl = 0x%x\n", cmd);
	return -ENOTTY;
}
```

### snd_pcm_sw_params validates and stores the software parameters

[`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953) is shown above by its inner store; its full body opens with the state and range checks that gate the store. It rejects a stream still in OPEN with `-EBADFD`, then range-checks the timestamp mode, the avail-min, and the silence thresholds before taking the stream lock to copy the values into [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). It calls no op in [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55):

```c
/* sound/core/pcm_native.c:953 */
static int snd_pcm_sw_params(struct snd_pcm_substream *substream,
			     struct snd_pcm_sw_params *params)
{
	struct snd_pcm_runtime *runtime;
	int err;

	if (PCM_RUNTIME_CHECK(substream))
		return -ENXIO;
	runtime = substream->runtime;
	scoped_guard(pcm_stream_lock_irq, substream) {
		if (runtime->state == SNDRV_PCM_STATE_OPEN)
			return -EBADFD;
	}

	if (params->tstamp_mode < 0 ||
	    params->tstamp_mode > SNDRV_PCM_TSTAMP_LAST)
		return -EINVAL;
	if (params->proto >= SNDRV_PROTOCOL_VERSION(2, 0, 12) &&
	    params->tstamp_type > SNDRV_PCM_TSTAMP_TYPE_LAST)
		return -EINVAL;
	if (params->avail_min == 0)
		return -EINVAL;
	if (params->silence_size >= runtime->boundary) {
		if (params->silence_threshold != 0)
			return -EINVAL;
	} else {
		if (params->silence_size > params->silence_threshold)
			return -EINVAL;
		if (params->silence_threshold > runtime->buffer_size)
			return -EINVAL;
	}
	...
}
```

### The do-action helpers issue the remaining trigger commands

The [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op receives every `SNDRV_PCM_TRIGGER_*` command from a small family of do-step helpers that the action machinery runs alongside [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452). Each one gates on the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) so a linked group fires the op once. [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530) issues [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) only when the stream is running and then sets [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) so a later [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) will wait:

```c
/* sound/core/pcm_native.c:1530 */
static int snd_pcm_do_stop(struct snd_pcm_substream *substream,
			   snd_pcm_state_t state)
{
	if (substream->runtime->trigger_master == substream &&
	    snd_pcm_running(substream)) {
		substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_STOP);
		substream->runtime->stop_operating = true;
	}
	return 0; /* unconditionally stop all substreams */
}
```

[`snd_pcm_do_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1628) chooses [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) or [`SNDRV_PCM_TRIGGER_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L101) from the [`pause_pushed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1619) test on the target state, and pushes [`hw_ptr_jiffies`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) far back so the next hw_ptr update skips its jiffies check once:

```c
/* sound/core/pcm_native.c:1628 */
static int snd_pcm_do_pause(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state)
{
	if (substream->runtime->trigger_master != substream)
		return 0;
	/* The jiffies check in snd_pcm_update_hw_ptr*() is done by
	 * a delta between the current jiffies, this gives a large enough
	 * delta, effectively to skip the check once.
	 */
	substream->runtime->hw_ptr_jiffies = jiffies - HZ * 1000;
	return substream->ops->trigger(substream,
				       pause_pushed(state) ?
				       SNDRV_PCM_TRIGGER_PAUSE_PUSH :
				       SNDRV_PCM_TRIGGER_PAUSE_RELEASE);
}
```

[`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) issues [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) for a running stream and likewise arms [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), while [`snd_pcm_do_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814) issues [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) only if the [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) recorded a stream that was actually moving:

```c
/* sound/core/pcm_native.c:1713 */
static int snd_pcm_do_suspend(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->trigger_master != substream)
		return 0;
	if (! snd_pcm_running(substream))
		return 0;
	substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_SUSPEND);
	runtime->stop_operating = true;
	return 0; /* suspend unconditionally */
}
```

```c
/* sound/core/pcm_native.c:1814 */
static int snd_pcm_do_resume(struct snd_pcm_substream *substream,
			     snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->trigger_master != substream)
		return 0;
	/* DMA not running previously? */
	if (runtime->suspended_state != SNDRV_PCM_STATE_RUNNING &&
	    (runtime->suspended_state != SNDRV_PCM_STATE_DRAINING ||
	     substream->stream != SNDRV_PCM_STREAM_PLAYBACK))
		return 0;
	return substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_RESUME);
}
```

These helpers and the start, stop, and pause ones each pass a single command into the same trigger op, gated so a linked group fires it once:

```
    One trigger op, one command per do-step helper
    ───────────────────────────────────────────────
    (each helper acts only when trigger_master == substream)

    do-step helper        SNDRV_PCM_TRIGGER_*  effect
    ────────────────────  ───────────────────  ────────────────────
    snd_pcm_do_start      START                RUNNING; -EPIPE ▶ XRUN
    snd_pcm_do_stop       STOP                 SETUP; stop_operating
    snd_pcm_do_pause      PAUSE_PUSH           PAUSED
    snd_pcm_do_pause      PAUSE_RELEASE        resume from PAUSED
    snd_pcm_do_suspend    SUSPEND              stop_operating set
    snd_pcm_do_resume     RESUME               back to RUNNING
                            │  (all six funnel into the one op)
                            ▼
              substream->ops->trigger(substream, cmd)
```

### The transfer loop, the appl-ptr ack, and the hw_ptr update

[`__snd_pcm_lib_xfer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2271) is the full read/write loop whose transfer-select head appears above. After choosing the per-frame writer and the [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) or silence transfer, it loops over the available frames, taking and dropping the stream lock around each chunk, advancing the application pointer through [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227), and starting the stream once enough is buffered:

```c
/* sound/core/pcm_lib.c:2271 */
snd_pcm_sframes_t __snd_pcm_lib_xfer(struct snd_pcm_substream *substream,
				     void *data, bool interleaved,
				     snd_pcm_uframes_t size, bool in_kernel)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_uframes_t xfer = 0;
	snd_pcm_uframes_t offset = 0;
	snd_pcm_uframes_t avail;
	pcm_copy_f writer;
	pcm_transfer_f transfer;
	bool nonblock;
	bool is_playback;
	int err;

	err = pcm_sanity_check(substream);
	if (err < 0)
		return err;
	...
	while (size > 0) {
		...
		appl_ptr += frames;
		if (appl_ptr >= runtime->boundary)
			appl_ptr -= runtime->boundary;
		err = pcm_lib_apply_appl_ptr(substream, appl_ptr);
		if (err < 0)
			goto _end_unlock;
		...
	}
 _end_unlock:
	runtime->twake = 0;
	if (xfer > 0 && err >= 0)
		snd_pcm_update_state(substream, runtime);
	snd_pcm_stream_unlock_irq(substream);
	return xfer > 0 ? (snd_pcm_sframes_t)xfer : err;
}
```

[`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227) records the new application pointer and calls the [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and on an op failure it restores the old value, turning an `-EPIPE` into an xrun through [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L181):

```c
/* sound/core/pcm_lib.c:2227 */
int pcm_lib_apply_appl_ptr(struct snd_pcm_substream *substream,
			   snd_pcm_uframes_t appl_ptr)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_uframes_t old_appl_ptr = runtime->control->appl_ptr;
	snd_pcm_sframes_t diff;
	int ret;

	if (old_appl_ptr == appl_ptr)
		return 0;
	...
	runtime->control->appl_ptr = appl_ptr;
	if (substream->ops->ack) {
		ret = substream->ops->ack(substream);
		if (ret < 0) {
			runtime->control->appl_ptr = old_appl_ptr;
			if (ret == -EPIPE)
				__snd_pcm_xrun(substream);
			return ret;
		}
	}

	trace_applptr(substream, old_appl_ptr, appl_ptr);

	return 0;
}
```

[`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) is the long routine whose pointer read appears above; its head opens by snapshotting the old hardware position, reading the [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and jiffies together, and treating a [`SNDRV_PCM_POS_XRUN`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) return as an underrun before any of the delta accounting runs:

```c
/* sound/core/pcm_lib.c:286 */
static int snd_pcm_update_hw_ptr0(struct snd_pcm_substream *substream,
				  unsigned int in_interrupt)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_uframes_t pos;
	snd_pcm_uframes_t old_hw_ptr, new_hw_ptr, hw_base;
	snd_pcm_sframes_t hdelta, delta;
	unsigned long jdelta;
	unsigned long curr_jiffies;
	struct timespec64 curr_tstamp;
	struct timespec64 audio_tstamp;
	int crossed_boundary = 0;

	old_hw_ptr = runtime->status->hw_ptr;
	...
	pos = substream->ops->pointer(substream);
	curr_jiffies = jiffies;
	...
	if (pos == SNDRV_PCM_POS_XRUN) {
		__snd_pcm_xrun(substream);
		return -EPIPE;
	}
	...
	return snd_pcm_update_state(substream, runtime);
}
```

The position this read returns advances the hardware pointer that chases the application pointer around the buffer, both wrapping at the boundary:

```
    The PCM ring buffer: hw_ptr and appl_ptr chase around it
    ─────────────────────────────────────────────────────────
    (buffer_size frames, split into periods of period_size)

    ┌────────┬────────┬────────┬────────┬────────┬────────┐
    │ period │ period │ period │ period │ period │ period │
    │   0    │   1    │   2    │   3    │   4    │   5    │
    └────────┴───┬────┴────────┴────────┴────┬───┴────────┘
                 │                           │
                 ▼                           ▼
              hw_ptr                      appl_ptr
       pointer op reports it      pcm_lib_apply_appl_ptr moves it
       snd_pcm_update_hw_ptr0     after each copy / fill_silence chunk

    playback: appl_ptr leads (app fills ahead), hw_ptr trails (DMA)
    both wrap at runtime->boundary; ack op fires when appl_ptr moves
```

### The mmap capability check, the mapper, and the fault handler

[`hw_support_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L262) decides whether a substream can be mapped at all. It first requires the [`SNDRV_PCM_INFO_MMAP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L289) capability bit, then reports true when the driver supplies a [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) or [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and otherwise inspects the DMA buffer type to see whether the generic path can map it:

```c
/* sound/core/pcm_native.c:262 */
static bool hw_support_mmap(struct snd_pcm_substream *substream)
{
	struct snd_dma_buffer *dmabuf;

	if (!(substream->runtime->hw.info & SNDRV_PCM_INFO_MMAP))
		return false;

	if (substream->ops->mmap || substream->ops->page)
		return true;

	dmabuf = snd_pcm_get_dma_buf(substream);
	if (!dmabuf)
		dmabuf = &substream->dma_buffer;
	switch (dmabuf->dev.type) {
	case SNDRV_DMA_TYPE_UNKNOWN:
		/* we can't know the device, so just assume that the driver does
		 * everything right
		 */
		return true;
	case SNDRV_DMA_TYPE_CONTINUOUS:
	case SNDRV_DMA_TYPE_VMALLOC:
		return true;
	default:
		return dma_can_mmap(dmabuf->dev.dev);
	}
}
```

[`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) is shown above by its VMA install; its full body first validates the access mode, the OPEN state, the [`SNDRV_PCM_INFO_MMAP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L289) bit, and the requested region against the DMA byte count before installing the PCM data VMA operations and calling the [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927):

```c
/* sound/core/pcm_native.c:3969 */
int snd_pcm_mmap_data(struct snd_pcm_substream *substream, struct file *file,
		      struct vm_area_struct *area)
{
	struct snd_pcm_runtime *runtime;
	long size;
	unsigned long offset;
	size_t dma_bytes;
	int err;

	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		if (!(area->vm_flags & (VM_WRITE|VM_READ)))
			return -EINVAL;
	} else {
		if (!(area->vm_flags & VM_READ))
			return -EINVAL;
	}
	runtime = substream->runtime;
	if (runtime->state == SNDRV_PCM_STATE_OPEN)
		return -EBADFD;
	if (!(runtime->info & SNDRV_PCM_INFO_MMAP))
		return -ENXIO;
	...
	area->vm_ops = &snd_pcm_vm_ops_data;
	area->vm_private_data = substream;
	if (substream->ops->mmap)
		err = substream->ops->mmap(substream, area);
	else
		err = snd_pcm_lib_default_mmap(substream, area);
	if (!err)
		atomic_inc(&substream->mmap_count);
	return err;
}
```

A page fault inside the mapping reaches [`snd_pcm_mmap_data_fault()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3872), which converts the fault offset to a [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) through the driver [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op when one is set, and otherwise resolves the page from the DMA area or the scatter-gather buffer:

```c
/* sound/core/pcm_native.c:3872 */
static vm_fault_t snd_pcm_mmap_data_fault(struct vm_fault *vmf)
{
	struct snd_pcm_substream *substream = vmf->vma->vm_private_data;
	struct snd_pcm_runtime *runtime;
	unsigned long offset;
	struct page * page;
	size_t dma_bytes;
	
	if (substream == NULL)
		return VM_FAULT_SIGBUS;
	runtime = substream->runtime;
	offset = vmf->pgoff << PAGE_SHIFT;
	dma_bytes = PAGE_ALIGN(runtime->dma_bytes);
	if (offset > dma_bytes - PAGE_SIZE)
		return VM_FAULT_SIGBUS;
	if (substream->ops->page)
		page = substream->ops->page(substream, offset);
	else if (!snd_pcm_get_dma_buf(substream)) {
		if (WARN_ON_ONCE(!runtime->dma_area))
			return VM_FAULT_SIGBUS;
		page = virt_to_page(runtime->dma_area + offset);
	} else
		page = snd_sgbuf_get_page(snd_pcm_get_dma_buf(substream), offset);
	if (!page)
		return VM_FAULT_SIGBUS;
	get_page(page);
	vmf->page = page;
	return 0;
}
```

### The soc-pcm ops table and the fan-out hw_params op

The abbreviated assignment above is the regular branch of the full builder. [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) selects a Dynamic PCM front-end set or the regular set into the embedded [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1027), layers in the optional component-backed [`ioctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`copy`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`page`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) ops where a component driver provides them, and then registers the table for each active direction with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510):

```c
/* sound/soc/soc-pcm.c:2909 */
int soc_new_pcm(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_component *component;
	struct snd_pcm *pcm;
	int ret = 0, playback = 0, capture = 0;
	int i;
	...
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

	for_each_rtd_components(rtd, i, component) {
		const struct snd_soc_component_driver *drv = component->driver;

		if (drv->ioctl)
			rtd->ops.ioctl		= snd_soc_pcm_component_ioctl;
		if (drv->sync_stop)
			rtd->ops.sync_stop	= snd_soc_pcm_component_sync_stop;
		if (drv->copy)
			rtd->ops.copy		= snd_soc_pcm_component_copy;
		if (drv->page)
			rtd->ops.page		= snd_soc_pcm_component_page;
		if (drv->mmap)
			rtd->ops.mmap		= snd_soc_pcm_component_mmap;
		if (drv->ack)
			rtd->ops.ack            = snd_soc_pcm_component_ack;
	}

	if (playback)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK, &rtd->ops);

	if (capture)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE, &rtd->ops);
	...
}
```

The regular [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) entry is [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), and its body is [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070), the function that turns the single PCM-core call into a fan-out across the link. It applies symmetry, then calls [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) on each codec DAI and each CPU DAI, fixing up the per-DAI TDM and channel masks, and finishes with [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L538); any error unwinds through [`soc_pcm_hw_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1015):

```c
/* sound/soc/soc-pcm.c:1070 */
static int __soc_pcm_hw_params(struct snd_pcm_substream *substream,
			       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *cpu_dai;
	struct snd_soc_dai *codec_dai;
	struct snd_pcm_hw_params tmp_params;
	int i, ret = 0;

	snd_soc_dpcm_mutex_assert_held(rtd);

	ret = soc_pcm_params_symmetry(substream, params);
	if (ret)
		goto out;

	ret = snd_soc_link_hw_params(substream, params);
	if (ret < 0)
		goto out;

	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		unsigned int tdm_mask = snd_soc_dai_tdm_mask_get(codec_dai, substream->stream);
		...
		if (!snd_soc_dai_stream_valid(codec_dai, substream->stream))
			continue;

		/* copy params for each codec */
		tmp_params = *params;

		/* fixup params based on TDM slot masks */
		if (tdm_mask)
			soc_pcm_codec_params_fixup(&tmp_params, tdm_mask);

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

		/* store the parameters for each DAI */
		soc_pcm_set_dai_params(cpu_dai, &tmp_params);
		snd_soc_dapm_update_dai(substream, &tmp_params, cpu_dai);
	}

	ret = snd_soc_pcm_component_hw_params(substream, params);
out:
	if (ret < 0)
		soc_pcm_hw_clean(rtd, substream, 1);

	return soc_pcm_ret(rtd, ret);
}
```

The single op body walks the codec DAIs, the CPU DAIs, and the components in turn, so one entry point branches into three legs of the link:

```
    One soc_pcm_hw_params call fans out across the link
    ────────────────────────────────────────────────────

    PCM core: substream->ops->hw_params  (= soc_pcm_hw_params)
                          │
                          ▼
                  __soc_pcm_hw_params
                          │
        ┌─────────────────┼───────────────────┐
        ▼                 ▼                   ▼
    each codec DAI    each CPU DAI        component(s)
    snd_soc_dai_      snd_soc_dai_        snd_soc_pcm_
      hw_params         hw_params         component_hw_params
```
