# PCM userspace interface

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A process drives an ALSA PCM stream through the character device `/dev/snd/pcmC<card>D<device><p|c>`, and the kernel binds that descriptor to one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) and one [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) at `open()`. The ABI is three memory-mapped pages and one ioctl set. The status page [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) maps read-only and carries the hardware pointer [`hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) the kernel advances, the control page [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) maps read-write and carries the application pointer [`appl_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) the process advances, and the data area maps the DMA ring buffer. The two pointers chase each other around the ring, and the distance between them is the available count a process consults before each transfer.

```
    three mmapped regions of one open substream
    ───────────────────────────────────────────

    STATUS  (offset 0x82000000, read-only)   CONTROL (offset 0x83000000, RW)
    ┌───────────────────────────────┐        ┌───────────────────────────────┐
    │ state                         │        │ appl_ptr   (app advances)     │
    │ hw_ptr   (kernel advances)    │        │ avail_min  (wakeup threshold) │
    │ tstamp, suspended_state       │        └───────────────────────────────┘
    └───────────────────────────────┘

    DATA  (offset 0x00000000)  =  runtime->dma_area, the ring buffer
    0                                                        buffer_size
    ├────────────┬──────────────────────────┬───────────────────────────┤
    │  consumed  │      valid audio         │       free / silence      │
    └────────────┴──────────────────────────┴───────────────────────────┘
                 ▲                          ▲
                 │ hw_ptr (status page)     │ appl_ptr (control page)
                 │                          │
                 └──── playback avail ──────┘   (free space ahead of hw)

    playback:  app writes at appl_ptr, hardware drains at hw_ptr
    capture:   hardware fills at hw_ptr, app reads at appl_ptr
    avail = appl_ptr and hw_ptr distance; poll() wakes at avail_min
```

## SUMMARY

A process opens `/dev/snd/pcmC<card>D<device><p|c>`, the node [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) names. The open lands first in [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143), the shared sound-core character-device entry, which looks up the minor, swaps the file operations to the PCM set [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206) with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), and re-dispatches `open()`. That reaches [`snd_pcm_playback_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2841) or [`snd_pcm_capture_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2855), each forwarding to [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which takes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and through [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) and [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) binds a free substream and allocates its runtime. The substream and runtime objects this descriptor binds are described separately; this page follows the ABI surface bound to them.

Every subsequent request is an ioctl on the descriptor. [`snd_pcm_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3472) checks the `'A'` magic and forwards to [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363), a switch that routes each `SNDRV_PCM_IOCTL_*` number into a core helper. The setup numbers ([`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680), [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), [`SNDRV_PCM_IOCTL_HW_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L682), [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683)) negotiate and store parameters, the control numbers ([`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692), [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694), [`SNDRV_PCM_IOCTL_DROP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L695), [`SNDRV_PCM_IOCTL_DRAIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L696), [`SNDRV_PCM_IOCTL_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L697)) drive the state machine, and the transfer numbers ([`SNDRV_PCM_IOCTL_WRITEI_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L702), [`SNDRV_PCM_IOCTL_READI_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L703)) move audio for the read/write access mode. The [`mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) op routes by page offset to [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743), [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781), or [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969). When an architecture cannot coherently map the status and control pages, [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689) handled by [`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118) copies [`hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) out and [`appl_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) in over one call. A driver IRQ handler calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) each period to advance [`hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) and wake the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) queue that [`snd_pcm_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665) sleeps on, so `poll()`, `select()`, and `epoll` on the fd return when [`avail`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_local.h#L36) reaches [`avail_min`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540).

## SPECIFICATIONS

The PCM userspace interface is defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). That header is normative for this page. It declares the ioctl numbers ([`SNDRV_PCM_IOCTL_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L675)), the protocol version [`SNDRV_PCM_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L145), the mmap page layouts [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) and [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540), the mmap offsets ([`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319) and the status/control offsets), and the [`struct snd_pcm_sync_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L549) exchange structure. The underlying audio controller (Intel High Definition Audio, USB Audio Class, a SoundWire codec, or a SoC link) carries its own specification and sits below the PCM layer.

## LINUX KERNEL

### The ABI header (include/uapi/sound/asound.h)

- [`'\<struct __snd_pcm_mmap_status\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531): the read-only status page (`state`, `hw_ptr`, `tstamp`, `suspended_state`, `audio_tstamp`), reached as the public type [`snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L520)
- [`'\<struct __snd_pcm_mmap_control\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540): the read-write control page (`appl_ptr`, `avail_min`), reached as [`snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L521)
- [`'\<struct __snd_pcm_sync_ptr\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L549): the `flags` plus status and control unions [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689) exchanges, reached as [`snd_pcm_sync_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L522)
- [`'\<struct snd_pcm_hw_params\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408): the hardware-parameter mask set [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) and [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) negotiate
- [`'\<struct snd_pcm_sw_params\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433): the software-parameter block [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) stores, including `avail_min` and the start/stop thresholds
- [`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319): the `mmap` page offsets `DATA` (0), [`SNDRV_PCM_MMAP_OFFSET_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L325) (0x82000000), and [`SNDRV_PCM_MMAP_OFFSET_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L326) (0x83000000)
- [`SNDRV_PCM_SYNC_PTR_HWSYNC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L545): the sync-ptr flags `HWSYNC`, [`SNDRV_PCM_SYNC_PTR_APPL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L546), and [`SNDRV_PCM_SYNC_PTR_AVAIL_MIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L547) that select transfer direction per field

### Device node, fops, open and release (sound.c, pcm_native.c)

- [`'\<snd_open\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143): the sound-core character-device open; finds [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48), swaps in the per-type [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L219) with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), and re-invokes `open()`
- [`'snd_pcm_f_ops':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206): the two [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), index 0 for playback and index 1 for capture, naming the read/write, poll, ioctl, and mmap handlers
- [`'\<snd_pcm_playback_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2841) / [`'\<snd_pcm_capture_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2855): look up the PCM by minor and call [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) with the direction
- [`'\<snd_pcm_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869): take [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544), wait on [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) for a free substream, and run [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816)
- [`'\<snd_pcm_open_file\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816): run [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767), allocate the [`struct snd_pcm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L237), and store it in [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h)
- [`'\<snd_pcm_release\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2926): the `release` fop; under [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) runs [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744), frees the [`struct snd_pcm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L237), and wakes [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545)

### The ioctl dispatch (pcm_native.c)

- [`'\<snd_pcm_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3472): the `unlocked_ioctl` fop; rejects any command whose magic byte is not `'A'`, then calls [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363)
- [`'\<snd_pcm_common_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363): the per-stream switch routing every `SNDRV_PCM_IOCTL_*` number to a core helper
- [`'\<snd_pcm_hw_params_user\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L889): copy the [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) in, call [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), copy the result back
- [`'\<snd_pcm_sw_params_user\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1006): copy the [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433) in, call [`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953), copy it back
- [`'\<snd_pcm_xferi_frames_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3280): the interleaved transfer ioctl reaching [`snd_pcm_lib_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1187) or [`snd_pcm_lib_read()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1194)
- [`'\<snd_pcm_link\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) / [`'\<snd_pcm_unlink\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336): join or split substreams into a shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) for synchronized start
- [`'\<snd_pcm_drain\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2105): block until every linked playback stream empties its buffer
- [`'\<snd_pcm_hwsync\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3073): the [`SNDRV_PCM_IOCTL_HWSYNC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L686) handler, a [`snd_pcm_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3058) call with no result pointer

### mmap of the three regions (pcm_native.c)

- [`'\<snd_pcm_mmap\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013): the `mmap` fop; switches on `vm_pgoff << PAGE_SHIFT` to the status, control, or data handler
- [`'\<snd_pcm_mmap_status\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743): map the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page and strip write permission with [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h)
- [`'\<snd_pcm_mmap_control\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781): map the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page read-write
- [`'\<snd_pcm_mmap_data\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969): map the [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) ring buffer through the driver [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927), raising [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491)

### The sync-ptr fast path and poll (pcm_native.c, pcm_lib.c)

- [`'\<snd_pcm_sync_ptr\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118): the [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689) handler; apply the incoming `appl_ptr`/`avail_min` and copy `hw_ptr`/`state`/`tstamp` out in one call
- [`'\<pcm_lib_apply_appl_ptr\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227): write the application pointer into [`runtime->control->appl_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) and call the driver [`ack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op
- [`'\<snd_pcm_poll\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665): the `poll` fop; register [`runtime->sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) and report readiness once [`snd_pcm_avail()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_local.h#L36) reaches [`avail_min`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540)
- [`'\<snd_pcm_avail\>':'sound/core/pcm_local.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_local.h#L36): the [`appl_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) to [`hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) distance, computed per direction by [`snd_pcm_playback_avail()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L824) or [`snd_pcm_capture_avail()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L842)

### The period wakeup from the driver IRQ (pcm_lib.c)

- [`'\<snd_pcm_period_elapsed\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933): the IRQ-time entry a driver calls each period; takes the stream lock and forwards to [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900)
- [`'\<snd_pcm_period_elapsed_under_stream_lock\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900): update [`hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) via [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286), run the timer, and signal `SIGIO`
- [`'\<snd_pcm_update_hw_ptr0\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286): read the driver [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, advance the hardware position, and wake [`runtime->sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) through [`snd_pcm_update_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L209)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM Interface chapter describes the runtime [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) records a process mmaps, the [`appl_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) update model, and the operator and atomicity rules behind the ioctls
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): the meaning of the `tstamp` and `audio_tstamp` fields a process reads from the status page
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the `/proc/asound/cardX/pcm*` entries that report the same hardware and software parameters the ioctls negotiate
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated PCM Core API reference for [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933) and the helper functions the ioctls reach

## OTHER SOURCES

- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [ALSA project PCM (digital audio) interface reference](https://www.alsa-project.org/alsa-doc/alsa-lib/group___p_c_m.html)
- [aplay and arecord manual page](https://manpages.debian.org/bookworm/alsa-utils/aplay.1.en.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A process reaches one PCM substream through the character device `/dev/snd/pcmC<card>D<device><p|c>`. The userspace entry points are the file operations in [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206), with the bulk of the ABI carried by [`snd_pcm_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3472) and its dispatch [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363), the page mappings established by [`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) at three fixed offsets, the readiness reported by [`snd_pcm_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665), and the pointer exchange [`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118).

| userspace operation | kernel entry point | effect |
|---------------------|--------------------|--------|
| `open("/dev/snd/pcmC0D0p")` | [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) then [`snd_pcm_playback_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2841) | swaps to PCM fops, binds a substream, allocates the runtime |
| `ioctl(SNDRV_PCM_IOCTL_HW_PARAMS)` | [`snd_pcm_hw_params_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L889) | negotiates format/rate/channels, state to SETUP |
| `ioctl(SNDRV_PCM_IOCTL_SW_PARAMS)` | [`snd_pcm_sw_params_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1006) | stores `avail_min` and the thresholds |
| `ioctl(SNDRV_PCM_IOCTL_PREPARE)` | [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) | runs the driver [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, state to PREPARED |
| `ioctl(SNDRV_PCM_IOCTL_START)` | [`snd_pcm_start_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1511) | runs [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) START, state to RUNNING |
| `mmap(..., 0x82000000)` | [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743) | maps the status page read-only |
| `mmap(..., 0x83000000)` | [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781) | maps the control page read-write |
| `mmap(..., 0)` | [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) | maps the DMA ring buffer |
| `ioctl(SNDRV_PCM_IOCTL_SYNC_PTR)` | [`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118) | copies `hw_ptr` out, `appl_ptr` in |
| `poll()` / `epoll` on the fd | [`snd_pcm_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665) | sleeps on [`runtime->sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417), wakes at `avail_min` |
| `ioctl(SNDRV_PCM_IOCTL_WRITEI_FRAMES)` | [`snd_pcm_xferi_frames_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3280) | interleaved write transfer |
| `close()` | [`snd_pcm_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2926) | releases the substream, frees the runtime |

## DETAILS

### The device node and the open path through snd_open

The per-direction device node is named by [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) as `pcmC%iD%i%c`, the trailing character `p` for playback and `c` for capture, and appears under `/dev/snd`. The first kernel code an `open()` reaches is not PCM-specific. Every ALSA character device shares one minor table, and [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) is the common entry registered for all of them:

```c
/* sound/core/sound.c:143 */
static int snd_open(struct inode *inode, struct file *file)
{
	unsigned int minor = iminor(inode);
	struct snd_minor *mptr = NULL;
	const struct file_operations *new_fops;
	int err = 0;

	if (minor >= ARRAY_SIZE(snd_minors))
		return -ENODEV;
	scoped_guard(mutex, &sound_mutex) {
		mptr = snd_minors[minor];
		if (mptr == NULL) {
			mptr = autoload_device(minor);
			if (!mptr)
				return -ENODEV;
		}
		new_fops = fops_get(mptr->f_ops);
	}
	if (!new_fops)
		return -ENODEV;
	replace_fops(file, new_fops);

	if (file->f_op->open)
		err = file->f_op->open(inode, file);
	return err;
}
```

[`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) looks up the [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) for the minor, takes the file operations it registered, installs them on the open file with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), and then calls the freshly installed `open` op. For a PCM playback minor the installed operations are index 0 of [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206), so the re-dispatched `open` is [`snd_pcm_playback_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2841):

```c
/* sound/core/pcm_native.c:4206 */
const struct file_operations snd_pcm_f_ops[2] = {
	{
		.owner =		THIS_MODULE,
		.write =		snd_pcm_write,
		.write_iter =		snd_pcm_writev,
		.open =			snd_pcm_playback_open,
		.release =		snd_pcm_release,
		.poll =			snd_pcm_poll,
		.unlocked_ioctl =	snd_pcm_ioctl,
		.compat_ioctl = 	snd_pcm_ioctl_compat,
		.mmap =			snd_pcm_mmap,
		.fasync =		snd_pcm_fasync,
		.get_unmapped_area =	snd_pcm_get_unmapped_area,
	},
	{
		.owner =		THIS_MODULE,
		.read =			snd_pcm_read,
		.read_iter =		snd_pcm_readv,
		.open =			snd_pcm_capture_open,
		.release =		snd_pcm_release,
		.poll =			snd_pcm_poll,
		.unlocked_ioctl =	snd_pcm_ioctl,
		.compat_ioctl = 	snd_pcm_ioctl_compat,
		.mmap =			snd_pcm_mmap,
		.fasync =		snd_pcm_fasync,
		.get_unmapped_area =	snd_pcm_get_unmapped_area,
	}
};
```

[`snd_pcm_playback_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2841) resolves the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) from the minor and hands off to [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) with [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167); [`snd_pcm_capture_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2855) is the mirror with [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168):

```c
/* sound/core/pcm_native.c:2841 */
static int snd_pcm_playback_open(struct inode *inode, struct file *file)
{
	struct snd_pcm *pcm;
	int err = nonseekable_open(inode, file);
	if (err < 0)
		return err;
	pcm = snd_lookup_minor_data(iminor(inode),
				    SNDRV_DEVICE_TYPE_PCM_PLAYBACK);
	err = snd_pcm_open(file, pcm, SNDRV_PCM_STREAM_PLAYBACK);
	if (pcm)
		snd_card_unref(pcm->card);
	return err;
}
```

[`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) serializes against [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and loops on [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816), sleeping on [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) when every subdevice is busy and the open is blocking. [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) runs [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) to attach a free substream and allocate its runtime with the two mmap pages, then records the binding in a [`struct snd_pcm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L237) stored in [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h):

```c
/* sound/core/pcm_native.c:2816 */
static int snd_pcm_open_file(struct file *file,
			     struct snd_pcm *pcm,
			     int stream)
{
	struct snd_pcm_file *pcm_file;
	struct snd_pcm_substream *substream;
	int err;

	err = snd_pcm_open_substream(pcm, stream, file, &substream);
	if (err < 0)
		return err;

	pcm_file = kzalloc_obj(*pcm_file);
	if (pcm_file == NULL) {
		snd_pcm_release_substream(substream);
		return -ENOMEM;
	}
	pcm_file->substream = substream;
	if (substream->ref_count == 1)
		substream->pcm_release = pcm_release_private;
	file->private_data = pcm_file;

	return 0;
}
```

Every later operation reads [`pcm_file->substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L237) back out of [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h) to reach the runtime. The mirror at `close()` is [`snd_pcm_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2926), which under [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) runs [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) to free the runtime, frees the [`struct snd_pcm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L237), and wakes [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) so a blocked opener can proceed.

### The ioctl dispatch table

After open, the descriptor carries the ABI through its `unlocked_ioctl` op. [`snd_pcm_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3472) is the thin outer layer. It reads the substream back from [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), checks that the command's magic byte is `'A'` (every `SNDRV_PCM_IOCTL_*` number is built with `_IO*('A', ...)`), and forwards the rest:

```c
/* sound/core/pcm_native.c:3472 */
static long snd_pcm_ioctl(struct file *file, unsigned int cmd,
			  unsigned long arg)
{
	struct snd_pcm_file *pcm_file;

	pcm_file = file->private_data;

	if (((cmd >> 8) & 0xff) != 'A')
		return -ENOTTY;

	return snd_pcm_common_ioctl(file, pcm_file->substream, cmd,
				     (void __user *)arg);
}
```

Both directions share this one op, with no separate playback and capture ioctl wrappers, and the same [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) handles both, branching on [`substream->stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) inside the per-command helpers where direction matters. The dispatch is one switch. It first rejects a runtime that is gone or disconnected, waits for the card to leave a low-power state, then routes each number to its helper:

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
	case SNDRV_PCM_IOCTL_HW_REFINE:
		return snd_pcm_hw_refine_user(substream, arg);
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
	case SNDRV_PCM_IOCTL_LINK:
		return snd_pcm_link(substream, (int)(unsigned long) arg);
	case SNDRV_PCM_IOCTL_UNLINK:
		return snd_pcm_unlink(substream);
	case SNDRV_PCM_IOCTL_RESUME:
		return snd_pcm_resume(substream);
	case SNDRV_PCM_IOCTL_XRUN:
		return snd_pcm_xrun(substream);
	case SNDRV_PCM_IOCTL_HWSYNC:
		return snd_pcm_hwsync(substream);
	case SNDRV_PCM_IOCTL_DELAY:
	{
		snd_pcm_sframes_t delay = 0;
		snd_pcm_sframes_t __user *res = arg;
		int err;

		err = snd_pcm_delay(substream, &delay);
		if (err)
			return err;
		if (put_user(delay, res))
			return -EFAULT;
		return 0;
	}
	case __SNDRV_PCM_IOCTL_SYNC_PTR32:
		return snd_pcm_ioctl_sync_ptr_compat(substream, arg);
	case __SNDRV_PCM_IOCTL_SYNC_PTR64:
		return snd_pcm_sync_ptr(substream, arg);
	...
	case SNDRV_PCM_IOCTL_DRAIN:
		return snd_pcm_drain(substream, file);
	case SNDRV_PCM_IOCTL_DROP:
		return snd_pcm_drop(substream);
	case SNDRV_PCM_IOCTL_PAUSE:
		return snd_pcm_pause_lock_irq(substream, (unsigned long)arg);
	case SNDRV_PCM_IOCTL_WRITEI_FRAMES:
	case SNDRV_PCM_IOCTL_READI_FRAMES:
		return snd_pcm_xferi_frames_ioctl(substream, arg);
	case SNDRV_PCM_IOCTL_WRITEN_FRAMES:
	case SNDRV_PCM_IOCTL_READN_FRAMES:
		return snd_pcm_xfern_frames_ioctl(substream, arg);
	case SNDRV_PCM_IOCTL_REWIND:
		return snd_pcm_rewind_ioctl(substream, arg);
	case SNDRV_PCM_IOCTL_FORWARD:
		return snd_pcm_forward_ioctl(substream, arg);
	}
	pcm_dbg(substream->pcm, "unknown ioctl = 0x%x\n", cmd);
	return -ENOTTY;
}
```

The numbers group by function. The setup group [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680), [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), [`SNDRV_PCM_IOCTL_HW_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L682), and [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) negotiate and store parameters. The control group [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692), [`SNDRV_PCM_IOCTL_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L693), [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694), [`SNDRV_PCM_IOCTL_DROP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L695), [`SNDRV_PCM_IOCTL_DRAIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L696), [`SNDRV_PCM_IOCTL_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L697), [`SNDRV_PCM_IOCTL_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L699), and [`SNDRV_PCM_IOCTL_XRUN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L700) drive the PCM state machine. The sync group [`SNDRV_PCM_IOCTL_HWSYNC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L686), [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689), [`SNDRV_PCM_IOCTL_DELAY`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L685), [`SNDRV_PCM_IOCTL_REWIND`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L698), and [`SNDRV_PCM_IOCTL_FORWARD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L701) move and report the pointers. The transfer group [`SNDRV_PCM_IOCTL_WRITEI_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L702), [`SNDRV_PCM_IOCTL_READI_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L703), [`SNDRV_PCM_IOCTL_WRITEN_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L704), and [`SNDRV_PCM_IOCTL_READN_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L705) carry audio in the read/write access mode. The link group [`SNDRV_PCM_IOCTL_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L706) and [`SNDRV_PCM_IOCTL_UNLINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L707) join substreams for a synchronized start, with [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) moving both substreams into one shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) so a single trigger reaches them together.

```
    snd_pcm_common_ioctl routes each number group to a helper
    ────────────────────────────────────────────────────────────
    setup     HW_REFINE / HW_PARAMS    ──▶ snd_pcm_hw_params_user
              HW_FREE / SW_PARAMS      ──▶ snd_pcm_sw_params_user
    control   PREPARE / RESET / START  ──▶ snd_pcm_prepare / _start
              DROP / DRAIN / PAUSE     ──▶ snd_pcm_drop / _drain
              RESUME / XRUN            ──▶ snd_pcm_resume / _xrun
    sync      HWSYNC / DELAY           ──▶ snd_pcm_hwsync / _delay
              SYNC_PTR                 ──▶ snd_pcm_sync_ptr
              REWIND / FORWARD         ──▶ snd_pcm_rewind/forward_ioctl
    transfer  WRITEI / READI           ──▶ snd_pcm_xferi_frames_ioctl
              WRITEN / READN           ──▶ snd_pcm_xfern_frames_ioctl
    link      LINK / UNLINK            ──▶ snd_pcm_link / _unlink
```

### hw_params and sw_params from userspace

Parameter negotiation runs in two passes. [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) narrows the masks in a [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) against the driver's constraints without committing, and [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) commits a single chosen configuration. [`snd_pcm_hw_params_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L889) is the ioctl wrapper, copying the parameter set in from the process, running the core [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754), and copying the resolved values back:

```c
/* sound/core/pcm_native.c:889 */
static int snd_pcm_hw_params_user(struct snd_pcm_substream *substream,
				  struct snd_pcm_hw_params __user * _params)
{
	int err;
	struct snd_pcm_hw_params *params __free(kfree) =
		memdup_user(_params, sizeof(*params));

	if (IS_ERR(params))
		return PTR_ERR(params);

	err = snd_pcm_hw_params(substream, params);
	if (err < 0)
		return err;

	if (copy_to_user(_params, params, sizeof(*params)))
		return -EFAULT;
	return err;
}
```

The core [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) refines the masks, invokes the driver [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and writes the chosen values into the runtime. The same call seeds the software side from the negotiated buffer, so the control page's threshold has a default the moment parameters are set:

```c
/* sound/core/pcm_native.c:754 (excerpt) */
	runtime->access = params_access(params);
	runtime->format = params_format(params);
	...
	runtime->buffer_size = params_buffer_size(params);
	...
	/* Default sw params */
	runtime->tstamp_mode = SNDRV_PCM_TSTAMP_NONE;
	runtime->period_step = 1;
	runtime->control->avail_min = runtime->period_size;
	runtime->start_threshold = 1;
	runtime->stop_threshold = runtime->buffer_size;
	...
	runtime->boundary = runtime->buffer_size;
	while (runtime->boundary * 2 <= LONG_MAX - runtime->buffer_size)
		runtime->boundary *= 2;
```

[`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) then overrides those defaults. [`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953) calls no driver op, it only validates and stores the values into the runtime, and the value a process cares about most is `avail_min`, which it writes straight into the control page so the poll path reads the new threshold:

```c
/* sound/core/pcm_native.c:953 (excerpt) */
	scoped_guard(pcm_stream_lock_irq, substream) {
		runtime->tstamp_mode = params->tstamp_mode;
		...
		runtime->control->avail_min = params->avail_min;
		runtime->start_threshold = params->start_threshold;
		runtime->stop_threshold = params->stop_threshold;
		...
	}
```

### The mmap status, control, and data pages and the appl_ptr/hw_ptr contract

A process that wants the lowest overhead maps three regions of the substream into its own address space, so it reads the hardware pointer and writes the application pointer without a system call per period. [`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) is the single `mmap` fop, and it selects the region by the page offset the process passed:

```c
/* sound/core/pcm_native.c:4013 */
static int snd_pcm_mmap(struct file *file, struct vm_area_struct *area)
{
	struct snd_pcm_file * pcm_file;
	struct snd_pcm_substream *substream;	
	unsigned long offset;
	
	pcm_file = file->private_data;
	substream = pcm_file->substream;
	if (PCM_RUNTIME_CHECK(substream))
		return -ENXIO;
	if (substream->runtime->state == SNDRV_PCM_STATE_DISCONNECTED)
		return -EBADFD;

	offset = area->vm_pgoff << PAGE_SHIFT;
	switch (offset) {
	case SNDRV_PCM_MMAP_OFFSET_STATUS_OLD:
		if (pcm_file->no_compat_mmap || !IS_ENABLED(CONFIG_64BIT))
			return -ENXIO;
		fallthrough;
	case SNDRV_PCM_MMAP_OFFSET_STATUS_NEW:
		if (!pcm_status_mmap_allowed(pcm_file))
			return -ENXIO;
		return snd_pcm_mmap_status(substream, file, area);
	case SNDRV_PCM_MMAP_OFFSET_CONTROL_OLD:
		if (pcm_file->no_compat_mmap || !IS_ENABLED(CONFIG_64BIT))
			return -ENXIO;
		fallthrough;
	case SNDRV_PCM_MMAP_OFFSET_CONTROL_NEW:
		if (!pcm_control_mmap_allowed(pcm_file))
			return -ENXIO;
		return snd_pcm_mmap_control(substream, file, area);
	default:
		return snd_pcm_mmap_data(substream, file, area);
	}
	return 0;
}
```

The offsets are fixed constants in the ABI header. [`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319) is 0, and the status and control offsets carry distinct high bits, with [`SNDRV_PCM_MMAP_OFFSET_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L325) and [`SNDRV_PCM_MMAP_OFFSET_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L326) resolving to the `NEW` variant under a 64-bit time layout and the `OLD` variant otherwise:

```c
/* include/uapi/sound/asound.h:318 */
enum {
	SNDRV_PCM_MMAP_OFFSET_DATA = 0x00000000,
	SNDRV_PCM_MMAP_OFFSET_STATUS_OLD = 0x80000000,
	SNDRV_PCM_MMAP_OFFSET_CONTROL_OLD = 0x81000000,
	SNDRV_PCM_MMAP_OFFSET_STATUS_NEW = 0x82000000,
	SNDRV_PCM_MMAP_OFFSET_CONTROL_NEW = 0x83000000,
#ifdef __SND_STRUCT_TIME64
	SNDRV_PCM_MMAP_OFFSET_STATUS = SNDRV_PCM_MMAP_OFFSET_STATUS_NEW,
	SNDRV_PCM_MMAP_OFFSET_CONTROL = SNDRV_PCM_MMAP_OFFSET_CONTROL_NEW,
#else
	SNDRV_PCM_MMAP_OFFSET_STATUS = SNDRV_PCM_MMAP_OFFSET_STATUS_OLD,
	SNDRV_PCM_MMAP_OFFSET_CONTROL = SNDRV_PCM_MMAP_OFFSET_CONTROL_OLD,
#endif
};
```

The status page is the read-only side. [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743) maps the [`runtime->status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page and clears `VM_WRITE` and `VM_MAYWRITE` through [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h), so a process can never write the hardware pointer the kernel owns:

```c
/* sound/core/pcm_native.c:3743 */
static int snd_pcm_mmap_status(struct snd_pcm_substream *substream, struct file *file,
			       struct vm_area_struct *area)
{
	long size;
	if (!(area->vm_flags & VM_READ))
		return -EINVAL;
	size = area->vm_end - area->vm_start;
	if (size != PAGE_ALIGN(sizeof(struct snd_pcm_mmap_status)))
		return -EINVAL;
	area->vm_ops = &snd_pcm_vm_ops_status;
	area->vm_private_data = substream;
	vm_flags_mod(area, VM_DONTEXPAND | VM_DONTDUMP,
		     VM_WRITE | VM_MAYWRITE);

	return 0;
}
```

The page that backs this mapping is [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) (declared as `__snd_pcm_mmap_status` and reached through the public `#define`). Its comments mark each field read-only, and `hw_ptr` is the running buffer position in frames modulo the boundary:

```c
/* include/uapi/sound/asound.h:531 */
struct __snd_pcm_mmap_status {
	snd_pcm_state_t state;		/* RO: state - SNDRV_PCM_STATE_XXXX */
	int pad1;			/* Needed for 64 bit alignment */
	snd_pcm_uframes_t hw_ptr;	/* RO: hw ptr (0...boundary-1) */
	struct __snd_timespec tstamp;	/* Timestamp */
	snd_pcm_state_t suspended_state; /* RO: suspended stream state */
	struct __snd_timespec audio_tstamp; /* from sample counter or wall clock */
};
```

The control page is the read-write side. [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781) maps the [`runtime->control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page with write permission left intact:

```c
/* sound/core/pcm_native.c:3781 */
static int snd_pcm_mmap_control(struct snd_pcm_substream *substream, struct file *file,
				struct vm_area_struct *area)
{
	long size;
	if (!(area->vm_flags & VM_READ))
		return -EINVAL;
	size = area->vm_end - area->vm_start;
	if (size != PAGE_ALIGN(sizeof(struct snd_pcm_mmap_control)))
		return -EINVAL;
	area->vm_ops = &snd_pcm_vm_ops_control;
	area->vm_private_data = substream;
	vm_flags_set(area, VM_DONTEXPAND | VM_DONTDUMP);
	return 0;
}
```

Its backing page [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) holds the two values a process writes, the application pointer it advances after each transfer and the wakeup threshold:

```c
/* include/uapi/sound/asound.h:540 */
struct __snd_pcm_mmap_control {
	snd_pcm_uframes_t appl_ptr;	/* RW: appl ptr (0...boundary-1) */
	snd_pcm_uframes_t avail_min;	/* RW: min available frames for wakeup */
};
```

The data region is the DMA buffer itself, the same ring buffer the data area maps. [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) validates the size against [`runtime->dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439), rejects the request when the access mode is read/write rather than mmap, then maps [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) through the driver [`mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or the default, and raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491):

```c
/* sound/core/pcm_native.c:3969 (excerpt) */
	if (runtime->access == SNDRV_PCM_ACCESS_RW_INTERLEAVED ||
	    runtime->access == SNDRV_PCM_ACCESS_RW_NONINTERLEAVED)
		return -EINVAL;
	size = area->vm_end - area->vm_start;
	offset = area->vm_pgoff << PAGE_SHIFT;
	dma_bytes = PAGE_ALIGN(runtime->dma_bytes);
	if ((size_t)size > dma_bytes)
		return -EINVAL;
	if (offset > dma_bytes - size)
		return -EINVAL;

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

The contract that binds the three pages is the relationship of the two pointers on the ring. `hw_ptr` in the status page is where the hardware has reached, `appl_ptr` in the control page is where the application has reached, and the available count is the signed distance between them, computed per direction by [`snd_pcm_avail()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_local.h#L36). For playback the available count is the free space ahead of the hardware that the process may still fill; for capture it is the captured frames behind the hardware that the process may still read. A process advances `appl_ptr` after each transfer and consults `avail` before the next, never overtaking `hw_ptr`.

```
    snd_pcm_mmap dispatches the page offset to one handler
    ───────────────────────────────────────────────────────────
    vm_pgoff << PAGE_SHIFT       handler                page (perm)

    0x82000000 STATUS_NEW  ─┐
    0x80000000 STATUS_OLD  ─┴─▶ snd_pcm_mmap_status   status   (RO)
    0x83000000 CONTROL_NEW ─┐
    0x81000000 CONTROL_OLD ─┴─▶ snd_pcm_mmap_control  control  (RW)
    0x00000000 DATA        ───▶ snd_pcm_mmap_data     dma_area (ring)
```

### The SYNC_PTR fast path

Coherent mmap of the status and control pages is not available on every architecture, and a process can also disable it. [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689) is the fallback that exchanges the same two pointers over one ioctl. The exchange structure [`struct snd_pcm_sync_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L549) carries a flags word and copies of both pages:

```c
/* include/uapi/sound/asound.h:549 */
struct __snd_pcm_sync_ptr {
	unsigned int flags;
	union {
		struct __snd_pcm_mmap_status status;
		unsigned char reserved[64];
	} s;
	union {
		struct __snd_pcm_mmap_control control;
		unsigned char reserved[64];
	} c;
};
```

[`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118) reads the flags and the incoming control values, optionally runs a hardware sync first, applies the application pointer with [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227) unless the [`SNDRV_PCM_SYNC_PTR_APPL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L546) flag asks to read it back instead, then copies the status page out:

```c
/* sound/core/pcm_native.c:3118 */
static int snd_pcm_sync_ptr(struct snd_pcm_substream *substream,
			    struct snd_pcm_sync_ptr __user *_sync_ptr)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	volatile struct snd_pcm_mmap_status *status;
	volatile struct snd_pcm_mmap_control *control;
	u32 sflags;
	struct snd_pcm_mmap_control scontrol;
	struct snd_pcm_mmap_status sstatus;
	int err;

	if (snd_pcm_sync_ptr_get_user(sflags, scontrol, _sync_ptr))
		return -EFAULT;
	status = runtime->status;
	control = runtime->control;
	if (sflags & SNDRV_PCM_SYNC_PTR_HWSYNC) {
		err = snd_pcm_hwsync(substream);
		if (err < 0)
			return err;
	}
	scoped_guard(pcm_stream_lock_irq, substream) {
		if (!(sflags & SNDRV_PCM_SYNC_PTR_APPL)) {
			err = pcm_lib_apply_appl_ptr(substream, scontrol.appl_ptr);
			if (err < 0)
				return err;
		} else {
			scontrol.appl_ptr = control->appl_ptr;
		}
		if (!(sflags & SNDRV_PCM_SYNC_PTR_AVAIL_MIN))
			control->avail_min = scontrol.avail_min;
		else
			scontrol.avail_min = control->avail_min;
		sstatus.state = status->state;
		sstatus.hw_ptr = status->hw_ptr;
		sstatus.tstamp = status->tstamp;
		sstatus.suspended_state = status->suspended_state;
		sstatus.audio_tstamp = status->audio_tstamp;
	}
	if (!(sflags & SNDRV_PCM_SYNC_PTR_APPL))
		snd_pcm_dma_buffer_sync(substream, SNDRV_DMA_SYNC_DEVICE);
	if (snd_pcm_sync_ptr_put_user(sstatus, scontrol, _sync_ptr))
		return -EFAULT;
	return 0;
}
```

The three flags select direction per field. Without [`SNDRV_PCM_SYNC_PTR_APPL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L546) the call writes the process's `appl_ptr` into the kernel through [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227); with it the call reads the kernel's `appl_ptr` back out. Likewise [`SNDRV_PCM_SYNC_PTR_AVAIL_MIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L547) chooses whether the call sets or reads `avail_min`, and [`SNDRV_PCM_SYNC_PTR_HWSYNC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L545) forces a fresh hardware pointer read before the status copy. The `hw_ptr`, `state`, and timestamp fields always copy out, so one ioctl gives the process the same view the status mmap would and pushes the same update the control mmap would. [`pcm_lib_apply_appl_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2227) writes the new pointer and notifies a driver that wants the change:

```c
/* sound/core/pcm_lib.c:2227 (excerpt) */
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
```

That apply helper is one direction of the wider exchange, where each flag points one field either into the kernel or back out while state, hw_ptr, and the timestamp always copy out:

```
    SYNC_PTR carries both pages, flags pick direction per field
    ──────────────────────────────────────────────────────────────
    struct snd_pcm_sync_ptr
    ┌──────────────────────────────────┐
    │ flags                            │
    │ s.status   (snd_pcm_mmap_status) │
    │ c.control  (snd_pcm_mmap_control)│
    └──────────────────────────────────┘

    flag           field      direction
    APPL clear     appl_ptr   app to kernel    (apply_appl_ptr)
    APPL set       appl_ptr   kernel to app    (read back)
    AVAIL_MIN      avail_min  clear: set   set: read back
    HWSYNC        (hw_ptr)    fresh pointer read before copy-out
    always         state, hw_ptr, tstamp        copied out
```

### Period wakeups and poll

A process that waits for buffer space sleeps in `poll()`, `select()`, or `epoll` on the descriptor rather than spinning on the pointers. The wakeup originates in the driver. Each time the hardware finishes one period, its IRQ handler calls [`snd_pcm_period_elapsed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1933), which takes the stream lock and forwards to [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900):

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

According to the comment on [`snd_pcm_period_elapsed_under_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1900), the call "updates the status of runtime with the latest position of audio data transmission, checks overrun and underrun over buffer, awaken user processes from waiting for available audio data frames". It reads the driver [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op through [`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) and signals `SIGIO` to any process that armed `fasync`:

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

[`snd_pcm_update_hw_ptr0()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L286) writes the new value into [`runtime->status->hw_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531), which is the same field the status mmap exposes, and finishes through [`snd_pcm_update_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L209), which wakes [`runtime->sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) once the available count reaches the threshold. The waiter side is [`snd_pcm_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665), which registers that same wait queue and reports readiness:

```c
/* sound/core/pcm_native.c:3665 (excerpt) */
	poll_wait(file, &runtime->sleep, wait);

	mask = 0;
	guard(pcm_stream_lock_irq)(substream);
	avail = snd_pcm_avail(substream);
	switch (runtime->state) {
	case SNDRV_PCM_STATE_RUNNING:
	case SNDRV_PCM_STATE_PREPARED:
	case SNDRV_PCM_STATE_PAUSED:
		if (avail >= runtime->control->avail_min)
			mask = ok;
		break;
```

[`snd_pcm_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3665) computes [`snd_pcm_avail()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_local.h#L36) and returns `EPOLLOUT` for playback or `EPOLLIN` for capture once the available count reaches [`avail_min`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540), the same control-page field the process set through [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683). The period interrupt that advanced `hw_ptr` is what changes the available count past the threshold, so the wakeup and the pointer the process reads come from the one IRQ.

```
    Period IRQ and poll() rendezvous on shared runtime state
    ───────────────────────────────────────────────────────────
                       shared runtime state
                ┌──────────────────────────────┐
    IRQ  ──────▶│ status->hw_ptr               │◀──────  poll()
    advances    │ runtime->sleep  (wait queue) │  computes avail,
    hw_ptr and  └──────────────────────────────┘  sleeps on queue
    wakes queue
                avail = appl_ptr to hw_ptr distance
                wake and return once avail >= avail_min
```

### The alsa-lib, aplay, and procfs surface

Few applications issue the raw ioctls. The user-space library libasound (alsa-lib) wraps them behind the `snd_pcm_*` API, and an application opens a stream with `snd_pcm_open()`, configures it with `snd_pcm_hw_params()` and `snd_pcm_sw_params()`, and moves audio with `snd_pcm_writei()` and `snd_pcm_readi()` for interleaved frames or `snd_pcm_writen()` and `snd_pcm_readn()` for non-interleaved. Each of those maps onto the matching ioctl: `snd_pcm_hw_params()` issues [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), `snd_pcm_writei()` issues [`SNDRV_PCM_IOCTL_WRITEI_FRAMES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L702), and `snd_pcm_prepare()` issues [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692).

The two access models the library exposes correspond directly to the kernel paths above. In the read/write model the library calls the transfer ioctls and the kernel copies through [`snd_pcm_xferi_frames_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3280) into the DMA buffer, so the data area is never mapped. In the mmap model the library maps all three regions, and an application uses `snd_pcm_mmap_begin()` to obtain a pointer into the data area at the current `appl_ptr`, writes or reads frames directly, calls `snd_pcm_mmap_commit()` to advance `appl_ptr` in the control page, and reads `snd_pcm_avail_update()` to refresh the available count from `hw_ptr`. When the control and status pages cannot be coherently mapped the library falls back to [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689) for every pointer exchange, which is why [`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118) carries both pointers in one structure.

The command-line tools aplay and arecord from alsa-utils are thin front ends over the same library, opening the PCM by name, setting the format from the WAV header or the command line, and looping over `snd_pcm_writei()` or `snd_pcm_readi()`. The kernel exposes the same negotiated parameters through procfs, and `/proc/asound/cardX/pcm<device><p|c>/sub0/hw_params` and `.../sw_params` report the format, rate, channels, buffer and period sizes, and `avail_min` of the open substream, the same values the [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) and [`SNDRV_PCM_IOCTL_SW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L683) ioctls negotiated. The HD Audio and SOF controllers reach this ABI through the PCM device a driver creates with [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), and from a process's view the interface is identical regardless of the controller underneath.
