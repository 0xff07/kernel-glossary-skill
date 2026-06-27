# PCM device objects (snd_pcm, substream, runtime)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ALSA PCM device is one [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) a driver creates with [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), owning a fixed pair of direction containers in its [`streams[2]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L543) array, one [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) for [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167) and one for [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168). Each [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) holds a singly linked list of [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) objects (the subdevices), pre-allocated at creation and counted by [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517). A substream carries no transfer state until a process opens it. At open the core allocates one [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), points [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) at it, and the runtime holds the negotiated hardware and software parameters, the two mmap-exported pages [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413), and the DMA buffer pointers [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), and [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439). Three locks guard the object at three granularities. [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) on the device serializes open and close, the per-stream spinlock or mutex inside [`substream->self_group.lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) reached through [`snd_pcm_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114) guards the running stream, and [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) with [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) guards the DMA buffer against a concurrent free.

```
    snd_pcm  (device, snd_pcm_new)
    ┌────────────────────────────────────────────────────────┐
    │ open_mutex, open_wait, nonatomic                       │
    │ streams[2]                                             │
    └──────────┬─────────────────────────────┬───────────────┘
               │                             │
        [PLAYBACK]                      [CAPTURE]
               ▼                             ▼
    snd_pcm_str                     snd_pcm_str
    ┌────────────────────┐          ┌────────────────────┐
    │ substream_count    │          │ substream_count    │
    │ substream ─┐       │          │ substream ─┐       │
    └────────────┼───────┘          └────────────┼───────┘
                 ▼                               ▼
       snd_pcm_substream  ─next▶  snd_pcm_substream  ...
       ┌──────────────────────┐
       │ ops, ref_count       │
       │ self_group.lock      │
       │ mmap_count           │
       │ runtime ─┐           │  (NULL until open)
       └──────────┼───────────┘
                  ▼
       snd_pcm_runtime  (one per open substream)
       ┌───────────────────────────────────────────┐
       │ state, hw/sw params                       │
       │ buffer_mutex, buffer_accessing            │
       │ status  ─▶ mmap page (RO)                 │
       │ control ─▶ mmap page (RW)                 │
       │ dma_area / dma_addr / dma_bytes           │
       └───────────────────────────────────────────┘
```

## SUMMARY

A driver creates one PCM device per logical audio function by calling [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) with a playback substream count and a capture substream count. The call allocates one [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), initializes its [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) wait queue, and for each non-zero direction count runs [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627), which fills the matching [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) and links one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice onto its [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list. [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) names the per-direction device `pcmC%iD%i%c`, the trailing character `p` for playback or `c` for capture, and gives every substream its own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) so the per-stream lock exists from creation. The driver then attaches its [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback set through [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510), which stores the pointer in every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field. On an x86-64 ACPI machine an ASoC card is one such driver, where [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) builds one [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) per DAI link, stashes its [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) in the pcm [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L546), and installs its own operators with the same [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510).

The substreams exist for the life of the device, while a [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is per open. When a process opens `/dev/snd/pcmC%iD%i%c`, [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) takes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and reaches [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), which finds a free substream, allocates the runtime with the two mmap pages, and sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1. The runtime keeps the stream [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), the negotiated parameters, the read-only [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page and read-write [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page that map into the process, and the DMA pointers. Close runs the inverse, where [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and on the last reference calls [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) to free the runtime and its pages, returning the substream to its free state. Locking is layered, where [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) serializes the open and close transitions, the per-stream lock in [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) (a spinlock when [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) is false, the group [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L457) when true) serializes trigger and pointer updates, and [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) paired with the [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) counter keeps a buffer free from racing an in-flight read or write.

## SPECIFICATIONS

The PCM device objects are Linux kernel software constructs and have no standalone hardware specification. The sample formats, rates, and the read-only and read-write mmap pages they expose are part of the ALSA userspace ABI defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The underlying audio transport (HD Audio, USB Audio, or a SoC link) carries its own specification, and the PCM layer sits above it.

## LINUX KERNEL

### Device and direction container types (pcm.h)

- [`'\<struct snd_pcm\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534): one PCM device; holds the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L535) back pointer, the [`streams[2]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L543) direction array, [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544), [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545), and the [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) flag that selects the per-stream lock type
- [`'\<struct snd_pcm_str\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513): one direction; holds [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518), and the head [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) of the subdevice list, plus the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L531) named `pcmC%iD%i%c`
- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): one subdevice; holds the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) callback pointer, the per-open [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) carrying the per-stream lock, the current [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) pointer, the open [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), and the [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) of active user mappings
- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): per-open transfer state; holds [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), the HW and SW parameters, the mmap pages [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413), the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) poll wait queue, [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422), and the DMA pointers
- [`'\<struct snd_pcm_hardware\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32): the driver-declared capability set (`info`, `formats`, rate and channel bounds, buffer and period byte limits, `fifo_size`) copied into [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) at open
- [`'\<struct snd_pcm_group\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455): the lock holder for one or more linked substreams; holds the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) spinlock, the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L457) used in the nonatomic case, the [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L458) list, and the [`refs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L459) refcount

### Creation and teardown (sound/core/pcm.c)

- [`'\<snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767): public constructor; forwards to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) with `internal` false
- [`'\<_snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697): allocates the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), initializes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545), builds both streams, and registers the device via [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29)
- [`'\<snd_pcm_new_stream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627): fills one [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), names the per-direction device `pcmC%iD%i%c`, allocates each [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), and calls [`snd_pcm_group_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78) on each [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487)
- [`'\<snd_pcm_set_ops\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510): stores the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) pointer in every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field for one direction
- [`'\<snd_pcm_free\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L854): releases the device, freeing both streams through [`snd_pcm_free_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L814) and the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) itself

### Per-open attach and detach (sound/core/pcm.c, pcm_native.c)

- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): selects a free substream, allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) with its [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) pages, sets [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to `SNDRV_PCM_STATE_OPEN`, and sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1
- [`'\<snd_pcm_detach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980): frees the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) pages, destroys [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), frees the runtime, and clears [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478)
- [`'\<snd_pcm_open\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869): the character-device open; takes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544), waits on [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) for a busy device, and calls [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816)
- [`'\<snd_pcm_open_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767): runs [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), initializes constraints, and invokes the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op
- [`'\<snd_pcm_release_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744): decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), runs the driver [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op on the last reference, and calls [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980)

### Per-stream and buffer locking (sound/core/pcm_native.c)

- [`'\<snd_pcm_group_init\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L78): initializes a [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455) spinlock, mutex, list, and refcount
- [`'\<snd_pcm_stream_lock\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114) / [`'\<snd_pcm_stream_unlock\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L126): take and release the per-stream lock in [`substream->self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), choosing spinlock or mutex by [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549)
- [`'\<snd_pcm_stream_lock_irq\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L140): the IRQ-disabling variant used on the interrupt and trigger paths
- [`'DEFINE_PCM_GROUP_LOCK':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L87): generates `snd_pcm_group_lock`, `snd_pcm_group_unlock`, and the `_irq` forms that branch on `nonatomic`
- [`'\<snd_pcm_buffer_access_lock\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L717): blocks DMA-buffer changes by testing [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) and taking [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421)

### mmap of the runtime pages (sound/core/pcm_native.c)

- [`'\<snd_pcm_mmap\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013): the file `mmap` op; dispatches by `vm_pgoff` offset to the status, control, or data mapping
- [`'\<snd_pcm_mmap_status\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743): maps the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page and strips write permission with [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987)
- [`'\<snd_pcm_mmap_control\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781): maps the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page read-write
- [`'\<struct __snd_pcm_mmap_status\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531): the read-only page layout (`state`, `hw_ptr`, `tstamp`) reached as [`snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L520)
- [`'\<struct __snd_pcm_mmap_control\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540): the read-write page layout (`appl_ptr`, `avail_min`) reached as [`snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L521)

### Worked example (sound/hda/common/controller.c)

- [`'\<snd_hda_attach_pcm_stream\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692): the HD Audio bus callback that calls [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) with the per-direction substream counts from its [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) and then [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM Interface chapter walks [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510), and the runtime structure a driver fills
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated PCM Core API reference for the device and substream functions
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): the meaning of the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page fields a process reads through the read-only mmap
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the per-substream procfs entries created alongside each [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513)

## OTHER SOURCES

- [ALSA project PCM library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A process reaches a PCM substream through the character device `/dev/snd/pcmC<card>D<device><p|c>`, the name [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) assigns. The kernel-side entry points map one to one onto the file operations a userspace client issues, with [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) binding one substream and one [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the parameter ioctls advancing the runtime [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), and [`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) exposing the runtime pages.

| userspace operation | kernel entry point | object effect |
|---------------------|--------------------|---------------|
| `open("/dev/snd/pcmC0D0p")` | [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) | binds one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) = 1 |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | driver [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op | fills the runtime parameters, sets [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) `SNDRV_PCM_STATE_SETUP` |
| `mmap(..., STATUS offset)` | [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743) | maps [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) read-only, raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) |
| `mmap(..., CONTROL offset)` | [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781) | maps [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) read-write, raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) |
| `SNDRV_PCM_IOCTL_START` | driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op under [`snd_pcm_stream_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L140) | [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) `SNDRV_PCM_STATE_RUNNING` |
| `close()` | [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) | drops [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), frees the runtime at zero |

## DETAILS

### The device owns a fixed pair of direction containers

A [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) is the device. It carries a back pointer to its [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L535), the device index, an id and name, the [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545) used during open, the [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) flag that selects the per-stream lock type, and the two-element [`streams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L543) array indexed by direction:

```c
/* include/sound/pcm.h:534 */
struct snd_pcm {
	struct snd_card *card;
	struct list_head list;
	int device; /* device number */
	unsigned int info_flags;
	unsigned short dev_class;
	unsigned short dev_subclass;
	char id[64];
	char name[80];
	struct snd_pcm_str streams[2];
	struct mutex open_mutex;
	wait_queue_head_t open_wait;
	void *private_data;
	void (*private_free) (struct snd_pcm *pcm);
	bool internal; /* pcm is for internal use only */
	bool nonatomic; /* whole PCM operations are in non-atomic context */
	bool no_device_suspend; /* don't invoke device PM suspend */
#if IS_ENABLED(CONFIG_SND_PCM_OSS)
	struct snd_pcm_oss oss;
#endif
};
```

Each element of [`streams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L543) is a [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), one direction's container. It records the direction in [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L514), how many subdevices exist in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), how many are currently open in [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518), and the head of the subdevice list in [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519). The [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L531) field is the per-direction device that becomes the `/dev/snd/pcmC%iD%i%c` node:

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

The device that holds these containers is the snd_pcm, its fixed streams pair indexing one snd_pcm_str for playback and one for capture next to the open_mutex and the nonatomic flag:

```
    snd_pcm                          one device, snd_pcm_new()
    ┌──────────────────────────────────────────────────────┐
    │ card, device, id, name                               │
    │ open_mutex   open_wait   nonatomic                   │
    │ streams[SNDRV_PCM_STREAM_PLAYBACK] ┐                 │
    │ streams[SNDRV_PCM_STREAM_CAPTURE]  ┘ snd_pcm_str     │
    └──────────────────────────────────────────────────────┘
```

### snd_pcm_new builds the device and both streams

[`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) is a one-line forward to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) with `internal` set false. According to the comment on [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), "The pcm operators have to be set afterwards to the new instance via snd_pcm_set_ops()", so the constructor builds the object graph and the driver wires its callbacks in a second step. [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) allocates the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), initializes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) and [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545), runs [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) once per direction, and on success registers the device with [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29). A zero count for a direction leaves that [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) with no substreams:

```c
/* sound/core/pcm.c:697 */
static int _snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, bool internal,
		struct snd_pcm **rpcm)
{
	struct snd_pcm *pcm;
	int err;
	...
	pcm = kzalloc_obj(*pcm);
	if (!pcm)
		return -ENOMEM;
	pcm->card = card;
	pcm->device = device;
	pcm->internal = internal;
	mutex_init(&pcm->open_mutex);
	init_waitqueue_head(&pcm->open_wait);
	INIT_LIST_HEAD(&pcm->list);
	if (id)
		strscpy(pcm->id, id, sizeof(pcm->id));

	err = snd_pcm_new_stream(pcm, SNDRV_PCM_STREAM_PLAYBACK,
				 playback_count);
	if (err < 0)
		goto free_pcm;

	err = snd_pcm_new_stream(pcm, SNDRV_PCM_STREAM_CAPTURE, capture_count);
	if (err < 0)
		goto free_pcm;

	err = snd_device_new(card, SNDRV_DEV_PCM, pcm,
			     internal ? &internal_ops : &ops);
	if (err < 0)
		goto free_pcm;

	if (rpcm)
		*rpcm = pcm;
	return 0;

free_pcm:
	snd_pcm_free(pcm);
	return err;
}
```

### snd_pcm_new_stream names the device and seeds the substreams

[`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) populates one [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), allocates a [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L531) for it, and names it `pcmC%iD%i%c` from the card number, the device index, and a direction character that is `p` for playback or `c` for capture. This is the name a process sees under `/dev/snd`:

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

The loop allocates one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice, links each onto the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list through the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484) pointer, points [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) at the substream's own [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), and initializes that group so the per-stream lock exists before any open:

```c
/* sound/core/pcm.c:627 (continued) */
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

The substream is the subdevice. It points back at its [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L465) and [`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L466), holds the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) callback pointer and the per-open [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), keeps its embedded [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) and the current [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) pointer, and tracks the open [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and the [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) of user mappings:

```c
/* include/sound/pcm.h:464 */
struct snd_pcm_substream {
	struct snd_pcm *pcm;
	struct snd_pcm_str *pstr;
	void *private_data;		/* copied from pcm->private_data */
	int number;
	char name[32];			/* substream name */
	int stream;			/* stream (direction) */
	...
	/* -- hardware operations -- */
	const struct snd_pcm_ops *ops;
	/* -- runtime information -- */
	struct snd_pcm_runtime *runtime;
	...
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
};
```

According to the comment on [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), it is the "fake group for non linked substream (with substream lock inside)", so an unlinked substream is its own group of one and the lock that serializes its trigger and pointer updates is the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) field of that embedded [`struct snd_pcm_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L455). When userspace links two substreams for synchronized start, [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L488) is repointed at a shared group and the lock then covers the whole set.

```
    Each substream is its own group of one at creation
    ──────────────────────────────────────────────────

    ┌──────────────────────────────────┐
    │ struct snd_pcm_substream         │
    │   next ─▶ next substream         │
    │   self_group  (embedded group)   │
    │   group ─┐  (points at own       │
    └──────────┼──── self_group)───────┘
               ▼
    ┌──────────────────────────────────┐
    │ struct snd_pcm_group  self_group │
    │   lock   (spinlock)              │
    │   mutex  (nonatomic case)        │
    │   substreams ─▶ link_list        │
    └──────────────────────────────────┘

    on snd_pcm_link, group is repointed at a shared
    snd_pcm_group, so one lock then covers the whole set
```

### snd_pcm_set_ops wires the callbacks into every substream

[`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) walks the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list of one direction and stores the same [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) pointer in each substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) field, so the open, hw_params, trigger, and pointer callbacks are reachable once a process attaches:

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

### The runtime is allocated per open

The substreams persist for the device lifetime, while the transfer state is per open. [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) is reached from [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) under [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544). It scans the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list for a free entry (one whose [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is zero), allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), allocates the two page-aligned mmap areas for [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) with [`alloc_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5063), initializes the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) wait queue and [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), sets [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), and sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1.

The prologue resolves the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) for the requested direction, returns `-ENODEV` when that direction has no substreams, and reads the preferred subdevice. The `O_APPEND` branch is the reopen case that bumps [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) on an already busy substream rather than allocating a new runtime, which is why a second handle on the same subdevice can share one [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362):

```c
/* sound/core/pcm.c:875 */
int snd_pcm_attach_substream(struct snd_pcm *pcm, int stream,
			     struct file *file,
			     struct snd_pcm_substream **rsubstream)
{
	struct snd_pcm_str * pstr;
	struct snd_pcm_substream *substream;
	struct snd_pcm_runtime *runtime;
	struct snd_card *card;
	int prefer_subdevice;
	size_t size;
	...
	*rsubstream = NULL;
	pstr = &pcm->streams[stream];
	if (pstr->substream == NULL || pstr->substream_count == 0)
		return -ENODEV;

	card = pcm->card;
	prefer_subdevice = snd_ctl_get_preferred_subdevice(card, SND_CTL_SUBDEV_PCM);
	...
	if (file->f_flags & O_APPEND) {
		...
		substream->ref_count++;
		*rsubstream = substream;
		return 0;
	}
```

The default path then runs the free-entry scan and the runtime and mmap-page allocation:

```c
/* sound/core/pcm.c:875 (continued) */
	for (substream = pstr->substream; substream; substream = substream->next) {
		if (!SUBSTREAM_BUSY(substream) &&
		    (prefer_subdevice == -1 ||
		     substream->number == prefer_subdevice))
			break;
	}
	if (substream == NULL)
		return -EAGAIN;

	runtime = kzalloc_obj(*runtime);
	if (runtime == NULL)
		return -ENOMEM;

	size = PAGE_ALIGN(sizeof(struct snd_pcm_mmap_status));
	runtime->status = alloc_pages_exact(size, GFP_KERNEL);
	if (runtime->status == NULL) {
		kfree(runtime);
		return -ENOMEM;
	}
	memset(runtime->status, 0, size);

	size = PAGE_ALIGN(sizeof(struct snd_pcm_mmap_control));
	runtime->control = alloc_pages_exact(size, GFP_KERNEL);
	...
	init_waitqueue_head(&runtime->sleep);
	init_waitqueue_head(&runtime->tsleep);

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

The [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) holds the whole transfer state. The status block carries the stream [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and hardware-pointer bookkeeping, the HW and SW param blocks carry the negotiated format, the mmap section carries the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page pointers, the locking section carries the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) wait queue, [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), and [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422), and the DMA section carries [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), and [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439):

```c
/* include/sound/pcm.h:362 */
struct snd_pcm_runtime {
	/* -- Status -- */
	snd_pcm_state_t state;		/* stream state */
	snd_pcm_state_t suspended_state; /* suspended stream state */
	...
	/* -- HW params -- */
	snd_pcm_access_t access;	/* access mode */
	snd_pcm_format_t format;	/* SNDRV_PCM_FORMAT_* */
	...
	/* -- mmap -- */
	struct snd_pcm_mmap_status *status;
	struct snd_pcm_mmap_control *control;

	/* -- locking / scheduling -- */
	snd_pcm_uframes_t twake; 	/* do transfer (!poll) wakeup if non-zero */
	wait_queue_head_t sleep;	/* poll sleep */
	wait_queue_head_t tsleep;	/* transfer sleep */
	struct snd_fasync *fasync;
	bool stop_operating;		/* sync_stop will be called */
	struct mutex buffer_mutex;	/* protect for buffer changes */
	atomic_t buffer_accessing;	/* >0: in r/w operation, <0: blocked */
	...
	/* -- hardware description -- */
	struct snd_pcm_hardware hw;
	struct snd_pcm_hw_constraints hw_constraints;
	...
	/* -- DMA -- */           
	unsigned char *dma_area;	/* DMA area */
	dma_addr_t dma_addr;		/* physical bus address (not accessible from main CPU) */
	size_t dma_bytes;		/* size of DMA area */
	...
};
```

The [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) member is a [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32), the capability set a driver declares and the core copies into the runtime at open to seed the constraints a process negotiates against:

```c
/* include/sound/pcm.h:32 */
struct snd_pcm_hardware {
	unsigned int info;		/* SNDRV_PCM_INFO_* */
	u64 formats;			/* SNDRV_PCM_FMTBIT_* */
	u32 subformats;			/* for S32_LE, SNDRV_PCM_SUBFMTBIT_* */
	unsigned int rates;		/* SNDRV_PCM_RATE_* */
	unsigned int rate_min;		/* min rate */
	unsigned int rate_max;		/* max rate */
	unsigned int channels_min;	/* min channels */
	unsigned int channels_max;	/* max channels */
	size_t buffer_bytes_max;	/* max buffer size */
	size_t period_bytes_min;	/* min period size */
	size_t period_bytes_max;	/* max period size */
	unsigned int periods_min;	/* min # of periods */
	unsigned int periods_max;	/* max # of periods */
	size_t fifo_size;		/* fifo size in bytes */
};
```

That capability block sits in the HW-params section of the runtime, which gathers the stream state, the negotiated parameters, the read-only status and read-write control pages, the buffer locking fields, and the DMA pointers in one per-open allocation:

```
    struct snd_pcm_runtime  (one allocation per open)
    ─────────────────────────────────────────────────

    ┌──────────────────────────────────────────────┐
    │ -- Status --   state, hw_ptr bookkeeping     │
    ├──────────────────────────────────────────────┤
    │ -- HW / SW params --   format, rate, ...     │
    │                        hw (snd_pcm_hardware) │
    ├──────────────────────────────────────────────┤
    │ -- mmap --                                   │
    │   status  ─▶ page exported read-only         │
    │   control ─▶ page exported read-write        │
    ├──────────────────────────────────────────────┤
    │ -- locking --   sleep, buffer_mutex,         │
    │                 buffer_accessing             │
    ├──────────────────────────────────────────────┤
    │ -- DMA --   dma_area, dma_addr, dma_bytes    │
    └──────────────────────────────────────────────┘
       freed by detach on the last close, runtime ─▶ NULL
```

### Three locks at three granularities

[`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) serializes open and close of the device. [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869) registers the file, adds itself to [`open_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L545), takes [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544), and retries [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) until a substream is free or the open is non-blocking. A busy device returns `-EAGAIN` from the attach, and a blocking open sleeps on the wait queue until a close wakes it:

```c
/* sound/core/pcm_native.c:2869 */
static int snd_pcm_open(struct file *file, struct snd_pcm *pcm, int stream)
{
	int err;
	wait_queue_entry_t wait;
	...
	init_waitqueue_entry(&wait, current);
	add_wait_queue(&pcm->open_wait, &wait);
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
	remove_wait_queue(&pcm->open_wait, &wait);
	mutex_unlock(&pcm->open_mutex);
	...
}
```

The per-stream lock sits in [`substream->self_group.lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) and is reached only through [`snd_pcm_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114), which forwards to the generated [`snd_pcm_group_lock`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L101) with the device [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) flag:

```c
/* sound/core/pcm_native.c:114 */
void snd_pcm_stream_lock(struct snd_pcm_substream *substream)
{
	snd_pcm_group_lock(&substream->self_group, substream->pcm->nonatomic);
}
```

[`snd_pcm_stream_unlock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L126) is the matching release, forwarding to the generated [`snd_pcm_group_unlock`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L101) with the same [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) flag so it drops whichever of the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L457) or [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) [`snd_pcm_stream_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L114) took on the [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) of the same substream:

```c
/* sound/core/pcm_native.c:126 */
void snd_pcm_stream_unlock(struct snd_pcm_substream *substream)
{
	snd_pcm_group_unlock(&substream->self_group, substream->pcm->nonatomic);
}
```

The group lock helpers are generated by [`DEFINE_PCM_GROUP_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L87), which takes the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L457) when [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) is set and the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) spinlock otherwise. A driver whose trigger and pointer callbacks may sleep sets [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) and runs under the mutex, while a classic interrupt-driven driver leaves it clear and runs under the spinlock with IRQs disabled through [`snd_pcm_stream_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L140):

```c
/* sound/core/pcm_native.c:87 */
#define DEFINE_PCM_GROUP_LOCK(action, bh_lock, bh_unlock, mutex_action) \
static void snd_pcm_group_ ## action(struct snd_pcm_group *group, bool nonatomic) \
{ \
	if (nonatomic) { \
		mutex_ ## mutex_action(&group->mutex); \
	} else { \
		if (IS_ENABLED(CONFIG_PREEMPT_RT) && bh_lock)   \
			local_bh_disable();			\
		spin_ ## action(&group->lock);			\
		if (IS_ENABLED(CONFIG_PREEMPT_RT) && bh_unlock) \
			local_bh_enable();                      \
	}							\
}

DEFINE_PCM_GROUP_LOCK(lock, false, false, lock);
DEFINE_PCM_GROUP_LOCK(unlock, false, false, unlock);
DEFINE_PCM_GROUP_LOCK(lock_irq, true, false, lock);
DEFINE_PCM_GROUP_LOCK(unlock_irq, false, true, unlock);
```

[`snd_pcm_stream_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L140) is the variant taken on the interrupt and trigger paths. It forwards to the generated `snd_pcm_group_lock_irq` on the same [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487), so in the atomic case it takes the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L456) spinlock with local IRQs disabled, and in the [`nonatomic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L549) case it degrades to the plain mutex acquisition since a sleeping section can never run with IRQs off:

```c
/* sound/core/pcm_native.c:140 */
void snd_pcm_stream_lock_irq(struct snd_pcm_substream *substream)
{
	snd_pcm_group_lock_irq(&substream->self_group,
			       substream->pcm->nonatomic);
}
```

[`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) and [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) together guard the DMA buffer against a free that races an in-flight read or write. [`snd_pcm_buffer_access_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L717) decrements [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) only when it is not already positive, so a transfer in progress (holding a positive count) makes the buffer-change path return `-EBUSY`, and otherwise it takes [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) to block further transfers:

```c
/* sound/core/pcm_native.c:717 */
static int snd_pcm_buffer_access_lock(struct snd_pcm_runtime *runtime)
{
	if (!atomic_dec_unless_positive(&runtime->buffer_accessing))
		return -EBUSY;
	mutex_lock(&runtime->buffer_mutex);
	return 0; /* keep buffer_mutex, unlocked by below */
}
```

That buffer guard is the narrowest of three nested scopes, the device open_mutex serializing open and close at the top, the per-stream self_group lock covering trigger and pointer in the middle, and buffer_mutex with buffer_accessing guarding the DMA buffer at the bottom:

```
    Three locks, three granularities (widest scope first)
    ─────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ DEVICE   open_mutex                                      │
    │   serializes open() and close() of the snd_pcm           │
    ├──────────────────────────────────────────────────────────┤
    │ STREAM   self_group.lock  (spinlock)                     │
    │          self_group.mutex (when nonatomic)               │
    │   serializes trigger and pointer for one substream       │
    ├──────────────────────────────────────────────────────────┤
    │ BUFFER   buffer_mutex + buffer_accessing                 │
    │   blocks a DMA-buffer free while a read/write is live    │
    └──────────────────────────────────────────────────────────┘
       nonatomic selects spinlock vs mutex for the STREAM lock
```

### Close frees the runtime and returns the substream

Close is the inverse of attach. [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and returns early while any reference remains. On the last reference it drops any running transfer, runs the driver [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, and calls [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980):

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

[`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) frees the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) pages with [`free_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5481), destroys [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), frees the runtime, and clears [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) back to NULL so the substream is free for the next open, decrementing [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518):

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
	kfree(runtime->hw_constraints.rules);
	...
	mutex_destroy(&runtime->buffer_mutex);
	snd_fasync_free(runtime->fasync);
	kfree(runtime);
	put_pid(substream->pid);
	substream->pid = NULL;
	substream->pstr->substream_opened--;
}
```

The whole device is torn down by [`snd_pcm_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L854), which frees both streams through [`snd_pcm_free_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L814) and then the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) allocation:

```c
/* sound/core/pcm.c:854 */
static int snd_pcm_free(struct snd_pcm *pcm)
{
	if (!pcm)
		return 0;
	if (!pcm->internal)
		pcm_call_notify(pcm, n_unregister);
	if (pcm->private_free)
		pcm->private_free(pcm);
	snd_pcm_lib_preallocate_free_for_all(pcm);
	snd_pcm_free_stream(&pcm->streams[SNDRV_PCM_STREAM_PLAYBACK]);
	snd_pcm_free_stream(&pcm->streams[SNDRV_PCM_STREAM_CAPTURE]);
	kfree(pcm);
	return 0;
}
```

### Worked example: HD Audio attaches a PCM device

The HD Audio controller creates each PCM device from [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692), the bus callback invoked once per [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) a codec builds. It passes the per-direction substream counts straight into [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), stores its private state in [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L546), and calls [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) for each direction that has substreams:

```c
/* sound/hda/common/controller.c:692 */
int snd_hda_attach_pcm_stream(struct hda_bus *_bus, struct hda_codec *codec,
			      struct hda_pcm *cpcm)
{
	struct hdac_bus *bus = &_bus->core;
	struct azx *chip = bus_to_azx(bus);
	struct snd_pcm *pcm;
	...
	err = snd_pcm_new(chip->card, cpcm->name, pcm_dev,
			  cpcm->stream[SNDRV_PCM_STREAM_PLAYBACK].substreams,
			  cpcm->stream[SNDRV_PCM_STREAM_CAPTURE].substreams,
			  &pcm);
	if (err < 0)
		return err;
	strscpy(pcm->name, cpcm->name, sizeof(pcm->name));
	...
	pcm->private_data = apcm;
	pcm->private_free = azx_pcm_free;
	...
	for (s = 0; s < 2; s++) {
		if (cpcm->stream[s].substreams)
			snd_pcm_set_ops(pcm, s, &azx_pcm_ops);
	}
	/* buffer pre-allocation */
	size = CONFIG_SND_HDA_PREALLOC_SIZE * 1024;
	...
	snd_pcm_set_managed_buffer_all(pcm, type, chip->card->dev,
				       size, MAX_PREALLOC_SIZE);
	return 0;
}
```

### A process opens, maps, and closes the device

A process interacts with the device through `/dev/snd/pcmC%iD%i%c`, where the trailing `p` or `c` selects the direction. `open()` on that node reaches [`snd_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2869), which under [`open_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L544) calls [`snd_pcm_open_file()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2816) and then [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767), binding exactly one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) to the open file and allocating its [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). The bind is reference counted through [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490), which starts at 1 and rises only when the same substream is reopened through an `O_APPEND` handle.

[`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) is the per-substream half of open. It calls [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) to claim the substream and build the runtime, returns straight away on the `O_APPEND` reopen where [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) rose above 1, and otherwise seeds the hardware constraints and invokes the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op through the substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) pointer. Any failure after the attach unwinds through [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744):

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
	...
	*rsubstream = substream;
	return 0;

 error:
	snd_pcm_release_substream(substream);
	return err;
}
```

After negotiating parameters, the process maps the runtime pages. [`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) dispatches on the page offset, sending the status offset to [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743) and the control offset to [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781). The status mapping clears the write bits with [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) so the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page is read-only to the process, which reads the stream [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L532) and hardware pointer from it without a syscall.

[`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) is the file `mmap` op installed for the PCM character device. It recovers the bound [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) from the open file, rejects a disconnected device, and switches on the page offset so the status offset reaches [`snd_pcm_mmap_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3743), the control offset reaches [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781), and any other offset maps the DMA data buffer:

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
	...
	case SNDRV_PCM_MMAP_OFFSET_STATUS_NEW:
		if (!pcm_status_mmap_allowed(pcm_file))
			return -ENXIO;
		return snd_pcm_mmap_status(substream, file, area);
	...
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

The control mapping keeps write permission through [`snd_pcm_mmap_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3781), so the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page is read-write and the process advances its application pointer there directly. The page the status mapping exports is the [`struct __snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) ABI layout, reached through the [`snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L520) name in [`runtime->status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412), its comments marking each field read-only:

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

The page the control mapping exports is the [`struct __snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) layout, reached as [`snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L521) through [`runtime->control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413). Its two read-write fields are the application pointer the process advances as it produces or consumes frames and the wakeup threshold it sets, so the control page is the writable counterpart to the read-only status page:

```c
/* include/uapi/sound/asound.h:540 */
struct __snd_pcm_mmap_control {
	snd_pcm_uframes_t appl_ptr;	/* RW: appl ptr (0...boundary-1) */
	snd_pcm_uframes_t avail_min;	/* RW: min available frames for wakeup */
};
```

Each active mapping raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491), and the count gates teardown so the runtime pages stay alive while a process still maps them. When the process closes the file, [`snd_pcm_release_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2744) decrements [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and, at zero, frees the runtime through [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980), leaving the substream and its [`self_group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L487) lock in place for the next open.

### ASoC builds and owns the snd_pcm for each DAI link

On an x86-64 ACPI machine the sound card is assembled by the ASoC layer in [`sound/soc/`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc), and the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) is created there rather than by a standalone driver. [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) runs once per [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), reaching [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) through its helper [`soc_create_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2867), then publishes the link's [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) in the pcm [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L546) and installs ASoC's own operators with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510):

```c
/* sound/soc/soc-pcm.c:2909 */
int soc_new_pcm(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_component *component;
	struct snd_pcm *pcm;
	int ret = 0, playback = 0, capture = 0;
	int i;
	...
	ret = soc_create_pcm(&pcm, rtd, playback, capture);
	if (ret < 0)
		return ret;
	...
	rtd->pcm = pcm;
	pcm->nonatomic = rtd->dai_link->nonatomic;
	pcm->private_data = rtd;
	pcm->no_device_suspend = true;
	...
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
	...
}
```

The [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) the ASoC card surfaces is therefore an ordinary core PCM device built by [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), and the only ASoC-specific part is the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1147) table held in the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) and the back pointer to that runtime in [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L546). When a process opens the pcm node, the core invokes [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) through the substream [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476) pointer, which recovers the runtime and opens every CPU and codec DAI of the link.
