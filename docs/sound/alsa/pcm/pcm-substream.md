# PCM substream (snd_pcm_substream)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) is one open-able PCM stream instance, the per-direction per-subdevice object a process binds when it opens `/dev/snd/pcmC<card>D<dev>[pc]`. It sits one level below the PCM device, where one [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) owns two [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) direction containers and each container holds a singly linked list of substreams threaded through the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484) field. [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) allocates the whole array once at [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) time, so a substream exists for the life of the card and carries no transfer state until a process attaches. The substream holds the back-pointers [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L465) and [`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L466), the driver callback set [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476), the per-open [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473) it transfers through, the linking fields [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) and [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488), and the open accounting [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491). At creation [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) points at the substream's own embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), a one-member [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) that carries the per-stream lock, and [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) repoints several substreams at one shared group so a single trigger acts on all of them at once.

```
    unlinked: each substream is its own group of one
    ─────────────────────────────────────────────────
    snd_pcm_substream A          snd_pcm_substream B
    ┌──────────────────┐         ┌──────────────────┐
    │ group ───┐       │         │ group ───┐       │
    │ self_group ◀─────┘ lock    │ self_group ◀─────┘ lock
    └──────────────────┘         └──────────────────┘

    after snd_pcm_link(A, B): one shared group, one lock
    ────────────────────────────────────────────────────
    snd_pcm_substream A          snd_pcm_substream B
    ┌──────────────────┐         ┌──────────────────┐
    │ group ───┐       │         │ group ───┐       │
    └──────────┼───────┘         └──────────┼───────┘
               └────────────┬───────────────┘
                            ▼
                   struct snd_pcm_group  (kzalloc, refs=2)
                   ┌───────────────────────────────┐
                   │ lock   mutex                  │
                   │ substreams ─▶ A.link_list ▶ B │
                   └───────────────────────────────┘
```

## SUMMARY

A substream is allocated at device-creation time and stays unopened until a process attaches. [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) runs once per non-empty direction from [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697), allocates [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) instances of [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) with [`kzalloc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1190), threads them onto the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) list through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484), numbers each in [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468), names it `subdevice #%i` in [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L469), sets [`buffer_bytes_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L472) to `UINT_MAX`, and seeds the linking state by pointing [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) at the embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) and calling [`snd_pcm_group_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78) on it. The driver wires its [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback set into every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510).

The open lifecycle binds one substream to one process. [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) calls [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), which scans the list for a free substream (one whose [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is zero, tested by [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510)), honors [`prefer_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158) and `O_APPEND` sharing, allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) with its status and control mmap pages, sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1, records [`f_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L492) and [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494), and bumps [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518). [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) then runs [`snd_pcm_hw_constraints_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2531), invokes the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and sets [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L503). Close is the inverse. [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), and on the last reference drops any running transfer, runs the driver [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and calls [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) to free the runtime and clear [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) back to NULL. Synchronized start across several substreams is expressed by repointing [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488). [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) moves the linked substreams onto a shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) under [`snd_pcm_group_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1323), and [`snd_pcm_unlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336) restores each to its own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) through [`relink_to_local()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2329). On an x86-64 ACPI machine each substream of an ASoC card is associated with a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) reached through [`snd_soc_substream_to_rtd()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1200), and ASoC's [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) op operates on the substream through that runtime. A substream is also what userspace addresses as a subdevice. The [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) is identified from userspace by its [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) within a device and direction, and the core selects a free one at each open, so the substream object and the subdevice an application picks are one and the same. The addressing and selection of that subdevice form the subdevice side, drawing on the device and subdevice numbering and the open count rather than the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), linking, and locking of the substream side.

## SPECIFICATIONS

The [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) object is a Linux kernel software construct and has no standalone hardware specification. The userspace-visible surface is the ALSA character-device ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h): the [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167) and [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168) direction selectors, the [`SNDRV_PCM_IOCTL_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L706) and [`SNDRV_PCM_IOCTL_UNLINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L707) ioctls that build and tear down a group, and the two mmap pages a substream's runtime exports. The underlying audio transport (HD Audio, USB Audio, or a SoC link) carries its own specification, and the substream sits above it.

## LINUX KERNEL

### Substream and container types (pcm.h)

- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): one open-able PCM stream instance; holds the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L465)/[`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L466) back-pointers, [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476), [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473), the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484) list link, the linking fields [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487)/[`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488), and the open counts [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490)/[`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491)
- [`'\<struct snd_pcm_str\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513): the per-direction container; holds [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518), the head [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) of the list, the [`chmap_kctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L530) channel-map control, and the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L531)
- [`'\<struct snd_pcm_group\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455): the lock holder for one or more linked substreams; holds the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) spinlock, the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L457) used in the nonatomic case, the [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L458) member list, and the [`refs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L459) refcount
- [`'\<SUBSTREAM_BUSY\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510): the free-or-busy test, true when [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is greater than zero
- [`'\<struct snd_pcm_ops\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55): the driver callback set [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) points at
- [`'\<struct snd_dma_buffer\>':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55): the descriptor of the substream's [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473)

### Creation at device time (sound/core/pcm.c)

- [`'\<snd_pcm_new_stream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627): allocates the substream array for one direction; sets [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L465)/[`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L466)/[`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468)/[`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470), threads [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484), and initializes each [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487)
- [`'\<snd_pcm_set_ops\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510): stores the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) pointer in every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field for one direction
- [`'\<snd_pcm_substream_proc_init\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L547): creates the `sub%i` procfs subdirectory under the per-direction node for each substream

### Per-open attach and detach (sound/core/pcm.c, pcm_native.c)

- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): selects a free substream by [`prefer_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158)/`O_APPEND`, allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) with its status and control pages, sets [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), and sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1
- [`'\<snd_pcm_detach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980): frees the runtime and its status/control pages, calls [`put_pid()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/pid.c#L88) on [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494), clears [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), and decrements [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518)
- [`'\<snd_pcm_open_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767): wraps the attach with [`snd_pcm_hw_constraints_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2531), the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L503); returns the shared substream early when [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is greater than 1
- [`'\<snd_pcm_release_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744): decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), runs [`snd_pcm_drop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2233), the driver [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) on the last reference

### Linking and grouping (sound/core/pcm_native.c)

- [`'\<snd_pcm_group_init\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78): initializes a [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) spinlock, mutex, list, and refcount
- [`'\<snd_pcm_stream_linked\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L632): true when [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) no longer equals the embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487)
- [`'\<snd_pcm_group_assign\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1323): repoints [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) and moves [`link_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L486) onto the new group's [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L458) list
- [`'\<snd_pcm_stream_group_ref\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1352): locks and references the current [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488), returning NULL for an unlinked substream so the action runs on the [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) lock alone
- [`'\<snd_pcm_link\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279): merges two substreams into one shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455), the body behind [`SNDRV_PCM_IOCTL_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L706)
- [`'\<snd_pcm_unlink\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336) / [`'\<relink_to_local\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2329): restore a substream to its own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), the body behind [`SNDRV_PCM_IOCTL_UNLINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L707)

### Per-stream lock and state accessors (pcm_native.c, pcm.h)

- [`'\<snd_pcm_stream_lock\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114) / [`'\<snd_pcm_stream_lock_irq\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L140): take the lock in [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), choosing spinlock or mutex by [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549)
- [`'DEFINE_PCM_GROUP_LOCK':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L87): generates the `snd_pcm_group_lock` family that branches on [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549)
- [`'\<snd_pcm_running\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L711): true when the substream's [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) is [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310), or draining for playback
- [`'\<snd_pcm_substream_chip\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L21): reads the driver state out of [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L467)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM Interface chapter explains that a PCM stream consists of one or more substreams, a free one is chosen at each open, and the middle layer handles the selection
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated PCM Core API reference covering the substream attach, open, and release functions
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the per-substream procfs entries created under each [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513)

## OTHER SOURCES

- [ALSA project library documentation: PCM (digital audio) interface](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [aplay and arecord manual page](https://man7.org/linux/man-pages/man1/aplay.1.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A process never names a substream directly. It opens the per-direction character device `/dev/snd/pcmC<card>D<device><p|c>` that [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) created, and the kernel binds one free substream from the matching [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) list. The helper set below allocates the substreams, attaches one at open, links and unlinks them into shared groups, and reads back their state.

| operation | kernel entry point | substream effect |
|-----------|--------------------|------------------|
| device creation | [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) | allocates the substream array, [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) = 0, [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) = [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) |
| ops binding | [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) | stores the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) pointer in every [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) |
| `open("...p")` | [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) | binds one substream, allocates [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) = 1 |
| `SNDRV_PCM_IOCTL_LINK` | [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) | repoints [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) at a shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) |
| `SNDRV_PCM_IOCTL_UNLINK` | [`snd_pcm_unlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336) | restores [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) to [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) |
| `close()` | [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) | drops [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), frees [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) at zero, detaches |

## DETAILS

### A substream and a subdevice are the same object

A substream is one kernel object, the [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), an open-able stream instance. The open lifecycle, the per-open [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the linking into a shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455), and the per-stream lock all act on it. Userspace addresses the same object under a different name, as a subdevice, by its [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) within a [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) direction, and the core selects a free one at each open through [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875). The [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) field gives the subdevice side its identity, and [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), tested by [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510), marks the instance busy so a later open skips it. The object is one and the same, where the substream name is the open-able stream instance and the subdevice name is how it is addressed, counted, and selected. Addressing and counting draw on a different set of fields (the device and subdevice numbering, the [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) and [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) counters, and the control-device queries), distinct from the open lifecycle, the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the linking and grouping, and the per-stream lock.

```
    One object, two names: which fields each name draws on
    ────────────────────────────────────────────────────────
                  struct snd_pcm_substream

    substream side                  subdevice side
    (open-able instance)            (how it is addressed)
    ┌──────────────────────────┐    ┌──────────────────────────┐
    │ runtime    (per-open)    │    │ number     (identity)    │
    │ group / self_group       │    │ ref_count  → SUBSTREAM_  │
    │ self_group.lock          │    │              BUSY        │
    │ ops        (callbacks)   │    │ substream_count  (total) │
    │ ref_count  (open count)  │    │ substream_opened (open)  │
    └──────────────────────────┘    └──────────────────────────┘
       open / link / lock              address / count / select
```

### One subdevice under snd_pcm_str under snd_pcm

A substream is the leaf of a three-level tree. One [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) device owns a [`streams[2]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L543) pair of [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) direction containers. Each container threads its subdevices on a singly linked list rooted at [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) and walked through the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484) pointer of each [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464):

The substream definition groups its fields by role. The first block is the back-pointers and identity, then the hardware section with [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) and the [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473), the runtime pointer, the list link [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484), the linking trio [`link_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L486)/[`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487)/[`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488), and finally the assigned-files block with [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491), [`f_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L492), and [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494):

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
        /* -- timer section -- */
	struct snd_timer *timer;		/* timer */
	unsigned timer_running: 1;	/* time is running */
	long wait_time;	/* time in ms for R/W to wait for avail */
	/* -- next substream -- */
	struct snd_pcm_substream *next;
	/* -- linked substreams -- */
	struct list_head link_list;	/* linked list member */
	struct snd_pcm_group self_group;	/* fake group for non linked substream (with substream lock inside) */
	struct snd_pcm_group *group;		/* pointer to current group */
	/* -- assigned files -- */
	int ref_count;
	atomic_t mmap_count;
	unsigned int f_flags;
	void (*pcm_release)(struct snd_pcm_substream *);
	struct pid *pid;
	...
	/* misc flags */
	unsigned int hw_opened: 1;
	unsigned int managed_buffer_alloc:1;
	...
};
```

The container the substream points back at through [`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L466) records how many subdevices exist in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) and how many are currently open in [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518), and holds the head of the list in [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519):

```c
/* include/sound/pcm.h:513 */
struct snd_pcm_str {
	int stream;				/* stream (direction) */
	struct snd_pcm *pcm;
	/* -- substreams -- */
	unsigned int substream_count;
	unsigned int substream_opened;
	struct snd_pcm_substream *substream;
	...
	struct snd_kcontrol *chmap_kctl; /* channel-mapping controls */
	struct device *dev;
};
```

The container's count and list head reach each substream, whose own fields the map below groups by role before the tree under it threads the three subdevices on their next links:

```
    struct snd_pcm_substream field groups
    ──────────────────────────────────────────────
    ┌──────────────────────────────────────────────┐
    │ identity      pcm, pstr, private_data,       │
    │               number, name, stream           │
    ├──────────────────────────────────────────────┤
    │ hardware ops  ops, dma_buffer                │
    ├──────────────────────────────────────────────┤
    │ runtime       runtime  (NULL until open)     │
    ├──────────────────────────────────────────────┤
    │ timer         timer, timer_running           │
    ├──────────────────────────────────────────────┤
    │ next          next  (singly linked list link)│
    ├──────────────────────────────────────────────┤
    │ linking       link_list, self_group, group   │
    ├──────────────────────────────────────────────┤
    │ assigned      ref_count, mmap_count,         │
    │ files         f_flags, pid                   │
    ├──────────────────────────────────────────────┤
    │ misc flags    hw_opened, managed_buffer_alloc│
    └──────────────────────────────────────────────┘
```

```
    snd_pcm.streams[SNDRV_PCM_STREAM_PLAYBACK]
    ┌────────────────────┐
    │ snd_pcm_str        │
    │ substream_count=3  │
    │ substream ─┐       │
    └────────────┼───────┘
                 ▼   next       next
       substream #0 ────▶ #1 ────▶ #2 ────▶ NULL
       ┌────────────┐
       │ number=0   │
       │ ops        │
       │ runtime    │ (NULL until open)
       │ self_group │
       │ ref_count  │
       └────────────┘
```

### snd_pcm_new_stream allocates the substream array

The substreams come into existence at device-creation time rather than at open. [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) runs once per direction from [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697). It fills the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) header, returns early for a zero count, and otherwise allocates the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L531) named `pcmC%iD%i%c` from the card number, the device index, and the direction character:

```c
/* sound/core/pcm.c:627 */
int snd_pcm_new_stream(struct snd_pcm *pcm, int stream, int substream_count)
{
	int idx, err;
	struct snd_pcm_str *pstr = &pcm->streams[stream];
	struct snd_pcm_substream *substream, *prev;
	...
	pstr->stream = stream;
	pstr->pcm = pcm;
	pstr->substream_count = substream_count;
	if (!substream_count)
		return 0;

	err = snd_device_alloc(&pstr->dev, pcm->card);
	if (err < 0)
		return err;
	dev_set_name(pstr->dev, "pcmC%iD%i%c", pcm->card->number, pcm->device,
		     stream == SNDRV_PCM_STREAM_PLAYBACK ? 'p' : 'c');
```

The loop allocates one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice with [`kzalloc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1190), sets the back-pointers and identity, names it `subdevice #%i`, caps [`buffer_bytes_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L472) at `UINT_MAX`, links it onto the list through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484), points [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) at the embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), and runs [`snd_pcm_group_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78) so the per-stream lock exists before any process can open the substream:

```c
/* sound/core/pcm.c:659 */
	for (idx = 0, prev = NULL; idx < substream_count; idx++) {
		substream = kzalloc_obj(*substream);
		if (!substream)
			return -ENOMEM;
		substream->pcm = pcm;
		substream->pstr = pstr;
		substream->number = idx;
		substream->stream = stream;
		sprintf(substream->name, "subdevice #%i", idx);
		substream->buffer_bytes_max = UINT_MAX;
		if (prev == NULL)
			pstr->substream = substream;
		else
			prev->next = substream;
		...
		substream->group = &substream->self_group;
		snd_pcm_group_init(&substream->self_group);
		list_add_tail(&substream->link_list, &substream->self_group.substreams);
		atomic_set(&substream->mmap_count, 0);
		prev = substream;
	}
	return 0;
}
```

[`snd_pcm_group_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78) sets up the lock, the mutex, the member list, and a refcount of 1 in the [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455). The same routine initializes both an embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) here and a freshly allocated shared group later in [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279):

```c
/* sound/core/pcm_native.c:78 */
void snd_pcm_group_init(struct snd_pcm_group *group)
{
	spin_lock_init(&group->lock);
	mutex_init(&group->mutex);
	INIT_LIST_HEAD(&group->substreams);
	refcount_set(&group->refs, 1);
}
```

### snd_pcm_attach_substream binds one substream at open

The substreams persist for the device lifetime, and an open binds exactly one of them to a process. [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) reads the [`prefer_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158) hint, handles the [`SNDRV_PCM_INFO_HALF_DUPLEX`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L288) and `O_APPEND` cases, and then walks the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list for the first entry that is free under [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) and matches the preferred subdevice if one was requested:

```c
/* sound/core/pcm.c:929 */
	for (substream = pstr->substream; substream; substream = substream->next) {
		if (!SUBSTREAM_BUSY(substream) &&
		    (prefer_subdevice == -1 ||
		     substream->number == prefer_subdevice))
			break;
	}
	if (substream == NULL)
		return -EAGAIN;
```

[`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) is the one-line predicate on [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) that separates a free substream from an open one:

```c
/* include/sound/pcm.h:510 */
#define SUBSTREAM_BUSY(substream) ((substream)->ref_count > 0)
```

Once a free substream is chosen, the attach allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), allocates the two page-aligned mmap areas for the status and control pages, initializes the runtime locks, sets [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), and wires the runtime into the substream. The accounting fields are set here, where [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) is published, [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L467) is copied from the device, [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is set to 1, [`f_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L492) is taken from the open file, [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494) records the opener, and [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) rises by one:

```c
/* sound/core/pcm.c:938 */
	runtime = kzalloc_obj(*runtime);
	if (runtime == NULL)
		return -ENOMEM;

	size = PAGE_ALIGN(sizeof(struct snd_pcm_mmap_status));
	runtime->status = alloc_pages_exact(size, GFP_KERNEL);
	...
	size = PAGE_ALIGN(sizeof(struct snd_pcm_mmap_control));
	runtime->control = alloc_pages_exact(size, GFP_KERNEL);
	...
	__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_OPEN);
	mutex_init(&runtime->buffer_mutex);
	atomic_set(&runtime->buffer_accessing, 0);

	substream->runtime = runtime;
	substream->private_data = pcm->private_data;
	substream->ref_count = 1;
	substream->f_flags = file->f_flags;
	substream->pid = get_pid(task_pid(current));
	pstr->substream_opened++;
	*rsubstream = substream;
	...
	return 0;
}
```

[`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) is the layer above the attach. It calls [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), returns the substream straight back when [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) came back greater than 1 (an `O_APPEND` reopen of an already-open substream, which shares the existing runtime), and otherwise initializes the hardware constraints, invokes the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) callback through [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476), and marks [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L503) so the close path knows the driver-side open ran:

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
	if (substream->ref_count > 1) {
		*rsubstream = substream;
		return 0;
	}

	err = snd_pcm_hw_constraints_init(substream);
	if (err < 0) {
		pcm_dbg(pcm, "snd_pcm_hw_constraints_init failed\n");
		goto error;
	}

	err = substream->ops->open(substream);
	if (err < 0)
		goto error;

	substream->hw_opened = 1;

	err = snd_pcm_hw_constraints_complete(substream);
	...
	*rsubstream = substream;
	return 0;

 error:
	snd_pcm_release_substream(substream);
	return err;
}
```

### snd_pcm_release_substream frees the runtime

Close runs the attach in reverse and is reference counted. [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) first and returns early while any reference remains, so an `O_APPEND` co-opener releasing its handle leaves the substream open. On the last reference it drops any running transfer with [`snd_pcm_drop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2233), and when [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L503) is set it releases the hardware parameters through [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) (unless the runtime is still in the OPEN state), runs the driver [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and clears [`hw_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L503):

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
	snd_pcm_detach_substream(substream);
}
```

[`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) reverses the allocation. It frees the status and control pages, releases [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494) with [`put_pid()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/pid.c#L88), frees the runtime, and decrements [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518). The matching [`free_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5481) calls undo the [`alloc_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gfp.h#L375) calls from the attach, and clearing [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) returns the substream to its free state for the next open:

```c
/* sound/core/pcm.c:980 */
void snd_pcm_detach_substream(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime;

	if (PCM_RUNTIME_CHECK(substream))
		return;
	runtime = substream->runtime;
	...
	free_pages_exact(runtime->status,
		       PAGE_ALIGN(sizeof(struct snd_pcm_mmap_status)));
	free_pages_exact(runtime->control,
		       PAGE_ALIGN(sizeof(struct snd_pcm_mmap_control)));
	...
	mutex_destroy(&runtime->buffer_mutex);
	snd_fasync_free(runtime->fasync);
	kfree(runtime);
	put_pid(substream->pid);
	substream->pid = NULL;
	substream->pstr->substream_opened--;
}
```

After detach the substream is back to its post-creation shape with [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) at zero and [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) NULL, ready to be picked again by the next [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875).

### The ops vector is bound once into every substream

The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field is a pointer to the driver's [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback set, and it is the same pointer in every substream of one direction. [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) walks the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list and stores the pointer in each one, so the [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77), `hw_params`, `trigger`, and `pointer` callbacks are reachable the moment a process attaches:

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

The open and close paths above invoke [`substream->ops->open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) and [`substream->ops->close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) directly. The full callback set and the wrappers that drive the remaining ops at each ioctl are out of scope here; this page treats [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) only as the field that binds them to the substream.

### The runtime is the per-open state the substream points at

[`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) is NULL on a free substream and points at a fresh [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) for the duration of one open. That separation lets a substream exist for the whole card lifetime while the negotiated format, the stream [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), the two mmap pages, and the DMA pointers all come and go with each open. The substream exposes its current state through a small inline accessor. [`snd_pcm_running()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L711) reads [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and reports true for a substream that is actively moving samples, which the interrupt and pointer paths consult before touching the hardware pointer:

```c
/* include/sound/pcm.h:711 */
static inline int snd_pcm_running(struct snd_pcm_substream *substream)
{
	return (substream->runtime->state == SNDRV_PCM_STATE_RUNNING ||
		(substream->runtime->state == SNDRV_PCM_STATE_DRAINING &&
		 substream->stream == SNDRV_PCM_STREAM_PLAYBACK));
}
```

That state lives behind one of the two pointers the substream holds, the ops vector staying for every open while the runtime and its state come and go with each:

```
    What the substream points at: ops persist, runtime per-open
    ─────────────────────────────────────────────────────────────
    struct snd_pcm_substream
    ┌──────────────────────────┐
    │ ops     ─────────────────┼────▶ struct snd_pcm_ops
    │                          │      (set once for all opens)
    │ runtime ─────────────────┼──┐
    └──────────────────────────┘  │   NULL until open
                                  ▼
                       struct snd_pcm_runtime  (per-open)
                       ┌────────────────────────────┐
                       │ state                      │
                       │ status   (mmap page)       │
                       │ control  (mmap page)       │
                       └────────────────────────────┘
```

### Linking merges several substreams under one group lock

Every substream starts as a group of one. [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) points at the embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), whose comment names it the "fake group for non linked substream (with substream lock inside)", and the per-stream lock that serializes the substream's trigger and pointer updates is the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) field of that embedded [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455):

```c
/* include/sound/pcm.h:455 */
struct snd_pcm_group {		/* keep linked substreams */
	spinlock_t lock;
	struct mutex mutex;
	struct list_head substreams;
	refcount_t refs;
};
```

[`snd_pcm_stream_linked()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L632) is the test for whether a substream is still its own group, a single pointer comparison where a substream is linked exactly when [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) no longer points at [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487):

```c
/* include/sound/pcm.h:632 */
static inline int snd_pcm_stream_linked(struct snd_pcm_substream *substream)
{
	return substream->group != &substream->self_group;
}
```

A process links two open substreams for synchronized start with [`SNDRV_PCM_IOCTL_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L706), dispatched to [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279). The function allocates one fresh [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455), rejects substreams that are in different states or use a different [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) mode, assigns the first substream to the new group if it was not already linked, then assigns the second substream to that target group and bumps its [`refs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L459):

```c
/* sound/core/pcm_native.c:2279 */
static int snd_pcm_link(struct snd_pcm_substream *substream, int fd)
{
	...
	struct snd_pcm_group *group __free(kfree) =
		kzalloc(sizeof(*group), GFP_KERNEL);
	if (!group)
		return -ENOMEM;
	snd_pcm_group_init(group);

	guard(rwsem_write)(&snd_pcm_link_rwsem);
	if (substream->runtime->state == SNDRV_PCM_STATE_OPEN ||
	    substream->runtime->state != substream1->runtime->state ||
	    substream->pcm->nonatomic != substream1->pcm->nonatomic)
		return -EBADFD;
	if (snd_pcm_stream_linked(substream1))
		return -EALREADY;

	scoped_guard(pcm_stream_lock_irq, substream) {
		if (!snd_pcm_stream_linked(substream)) {
			snd_pcm_group_assign(substream, group);
			group = NULL; /* assigned, don't free this one below */
		}
		target_group = substream->group;
	}

	snd_pcm_group_lock_irq(target_group, nonatomic);
	snd_pcm_stream_lock_nested(substream1);
	snd_pcm_group_assign(substream1, target_group);
	refcount_inc(&target_group->refs);
	snd_pcm_stream_unlock(substream1);
	snd_pcm_group_unlock_irq(target_group, nonatomic);
	return 0;
}
```

[`snd_pcm_group_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1323) is the one operation that moves a substream between groups. It repoints [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) and uses [`list_move()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L304) to take [`link_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L486) off its current group's member list and add it to the new one:

```c
/* sound/core/pcm_native.c:1323 */
static void snd_pcm_group_assign(struct snd_pcm_substream *substream,
				 struct snd_pcm_group *new_group)
{
	substream->group = new_group;
	list_move(&substream->link_list, &new_group->substreams);
}
```

Once linked, an action on any member acquires the shared group lock so it covers the whole set. [`snd_pcm_stream_group_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1352) is the helper the action path calls to lock and reference the current [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488). It returns NULL for an unlinked substream, signalling that the [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) lock already held is enough, and for a linked substream it bumps [`refs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L459), trylocks the group, and re-locks in group-then-stream order to avoid an ABBA deadlock when the trylock fails:

```c
/* sound/core/pcm_native.c:1352 */
snd_pcm_stream_group_ref(struct snd_pcm_substream *substream)
{
	bool nonatomic = substream->pcm->nonatomic;
	struct snd_pcm_group *group;
	bool trylock;

	for (;;) {
		if (!snd_pcm_stream_linked(substream))
			return NULL;
		group = substream->group;
		/* block freeing the group object */
		refcount_inc(&group->refs);

		trylock = nonatomic ? mutex_trylock(&group->mutex) :
			spin_trylock(&group->lock);
		if (trylock)
			break; /* OK */

		/* re-lock for avoiding ABBA deadlock */
		snd_pcm_stream_unlock(substream);
		snd_pcm_group_lock(group, nonatomic);
		snd_pcm_stream_lock(substream);

		/* check the group again; the above opens a small race window */
		if (substream->group == group)
			break; /* OK */
		/* group changed, try again */
		snd_pcm_group_unref(group, substream);
	}
	return group;
}
```

The per-stream lock itself is reached through [`snd_pcm_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114), which always locks the substream's own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), choosing spinlock or mutex by the device [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) flag. The group lock from [`snd_pcm_stream_group_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1352) sits on top of that self-group lock, so a linked action holds both the member's stream lock and the shared group lock.

[`SNDRV_PCM_IOCTL_UNLINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L707) reverses the link through [`snd_pcm_unlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336). It returns the substream to its own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) with [`relink_to_local()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2329), drops a [`refs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L459) reference, and when only one member is left it relocates that last member back to its own group and frees the shared group object:

```c
/* sound/core/pcm_native.c:2336 */
static int snd_pcm_unlink(struct snd_pcm_substream *substream)
{
	struct snd_pcm_group *group;
	bool nonatomic = substream->pcm->nonatomic;
	bool do_free = false;

	guard(rwsem_write)(&snd_pcm_link_rwsem);

	if (!snd_pcm_stream_linked(substream))
		return -EALREADY;

	group = substream->group;
	snd_pcm_group_lock_irq(group, nonatomic);

	relink_to_local(substream);
	refcount_dec(&group->refs);

	/* detach the last stream, too */
	if (list_is_singular(&group->substreams)) {
		relink_to_local(list_first_entry(&group->substreams,
						 struct snd_pcm_substream,
						 link_list));
		do_free = refcount_dec_and_test(&group->refs);
	}

	snd_pcm_group_unlock_irq(group, nonatomic);
	if (do_free)
		kfree(group);
	return 0;
}
```

[`relink_to_local()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2329) is the inverse of the link's assign step, calling [`snd_pcm_group_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1323) with the substream's own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) under the nested stream lock:

```c
/* sound/core/pcm_native.c:2329 */
static void relink_to_local(struct snd_pcm_substream *substream)
{
	snd_pcm_stream_lock_nested(substream);
	snd_pcm_group_assign(substream, &substream->self_group);
	snd_pcm_stream_unlock(substream);
}
```

### Reference counting and shared opens

The [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) fields track two different kinds of sharing. [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) counts open file handles bound to the substream. A normal open sets it to 1 in [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), and an `O_APPEND` open of an already-open substream takes the `O_APPEND` branch instead, which finds the busy substream and increments [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) so two file descriptors share one runtime:

```c
/* sound/core/pcm.c:909 */
	if (file->f_flags & O_APPEND) {
		...
		if (! SUBSTREAM_BUSY(substream))
			return -EBADFD;
		substream->ref_count++;
		*rsubstream = substream;
		return 0;
	}
```

[`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) is the atomic count of active user mappings of the runtime pages and the DMA buffer, set to zero at creation in [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) and raised by each successful mmap. It gates teardown so the pages stay alive while a process still maps them, separate from [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), which gates the runtime allocation itself.

```
    Two counts, two kinds of sharing
    ──────────────────────────────────────────────────────────
                     ref_count               mmap_count
    ┌──────────────┬───────────────────────┬──────────────────┐
    │ counts       │ open file handles     │ active mappings  │
    │ type         │ int                   │ atomic_t         │
    │ at creation  │ 0                     │ 0                │
    │ normal open  │ set to 1              │ unchanged        │
    │ O_APPEND     │ incremented           │ unchanged        │
    │ each mmap    │ unchanged             │ incremented      │
    │ gates        │ runtime allocation    │ page teardown    │
    └──────────────┴───────────────────────┴──────────────────┘
```

### A process opens, links, maps, and closes the substream

A process reaches a substream through the per-direction node `/dev/snd/pcmC<card>D<dev>[pc]`, the name [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) assigned, where the trailing `p` or `c` selects the direction. The alsa-lib `snd_pcm_open` call opens that node, and the kernel `open()` reaches [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767), which binds one free substream chosen by [`prefer_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158) and allocates its [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). The opener is recorded in [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L494) and the open flags are copied into [`f_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L492), so a later non-blocking or append behavior follows the descriptor that opened the substream.

A process that drives two devices in lockstep, such as a duplex loop or a multi-card playback, opens both substreams and issues [`SNDRV_PCM_IOCTL_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L706) with the second descriptor's file. [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) merges them into one shared [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455), so a single `SNDRV_PCM_IOCTL_START` on either descriptor triggers both at once under the group lock. [`SNDRV_PCM_IOCTL_UNLINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L707) calls [`snd_pcm_unlink()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2336) to split the group back into one-member self-groups. Both ioctls are dispatched from the PCM ioctl handler:

```c
/* sound/core/pcm_native.c:3418 */
	case SNDRV_PCM_IOCTL_LINK:
		return snd_pcm_link(substream, (int)(unsigned long) arg);
	case SNDRV_PCM_IOCTL_UNLINK:
		return snd_pcm_unlink(substream);
```

After negotiating parameters, the process maps the runtime's status and control pages and the DMA buffer, and each mapping raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) on the substream. When the process closes the descriptor, [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and, at zero, frees the runtime through [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980), leaving the substream and its [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) lock in place for the next open. Each substream also carries a `sub%i` procfs subdirectory created by [`snd_pcm_substream_proc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L547) under `/proc/asound/card<X>/pcm<dev><p|c>/`, where the number matches [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) and the entries report the substream's negotiated parameters and current state.

### ASoC reaches its runtime descriptor through the substream

On an x86-64 ACPI machine the substream belongs to a PCM the ASoC layer built, so its [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L467) is the link's [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) that [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) copied down from the pcm. ASoC reads it back with [`snd_soc_substream_to_rtd()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1200), a thin wrapper over the core [`snd_pcm_substream_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L21) accessor that returns [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L467):

```c
/* include/sound/soc.h:1200 */
static inline struct snd_soc_pcm_runtime *
snd_soc_substream_to_rtd(const struct snd_pcm_substream *substream)
{
	return snd_pcm_substream_chip(substream);
}
```

The substream [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) that [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) installed point the open callback at [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), which recovers the runtime from the substream and hands both to [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) under the DPCM mutex:

```c
/* sound/soc/soc-pcm.c:917 */
static int soc_pcm_open(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret;

	snd_soc_dpcm_mutex_lock(rtd);
	ret = __soc_pcm_open(rtd, substream);
	snd_soc_dpcm_mutex_unlock(rtd);
	return ret;
}
```

[`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) then walks every CPU and codec DAI of the link with [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217) and runs [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) on each, so a single core open of the one substream opens the whole DAI link the runtime describes.
