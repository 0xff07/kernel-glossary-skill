# PCM DMA buffers

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A PCM substream moves audio through a DMA buffer the ALSA core preallocates from a pool established when the device is created and exposes to the driver as three fields of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the kernel virtual address [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), the bus address [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), and the size [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439). The pool is one [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) attached to each substream at PCM creation through [`snd_pcm_lib_preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341) or, in the mode almost every modern driver uses, [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380), which both call the internal [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261) and differ only in whether they set [`substream->managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504). In managed mode the core allocates the runtime buffer just before the driver's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op in [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) and frees it just after [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) in [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) by calling [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) and [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482), which populate the runtime fields through [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263). The ASoC platform DMA bridge that drives the data movement is out of scope here; this page covers the ALSA-core preallocation and managed-buffer helpers in [`sound/core/pcm_memory.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c) and the underlying allocator in [`sound/core/memalloc.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c).

```
    PCM DMA buffer lifecycle in time
    ────────────────────────────────

    snd_pcm_new ───▶ pcm_construct (driver)
                       │  snd_pcm_set_managed_buffer[_all]()
                       ▼
                 ┌────────────────────────────────────┐
       t0        │ prealloc pool: substream.dma_buffer│  managed_buffer_alloc=1
                 │ snd_dma_buffer { area, addr, bytes}│
                 └────────────────────────────────────┘
                       │  (substream opened; runtime exists)
       open            ▼
       HW_PARAMS  snd_pcm_hw_params()
                  ├─ snd_pcm_lib_malloc_pages()    ◀── alloc, before
       t1         │     snd_pcm_set_runtime_buffer()    driver hw_params op
                  │        runtime->dma_area  = area
                  │        runtime->dma_addr  = addr
                  │        runtime->dma_bytes = size
                  └─ driver ops->hw_params(...)
                       │  (RUNNING: DMA reads/writes dma_area)
       HW_FREE         ▼
                  do_hw_free()
                  ├─ driver ops->hw_free(...)
       t2         └─ snd_pcm_lib_free_pages()      ◀── free, after
                        snd_pcm_set_runtime_buffer(NULL)  driver hw_free op
                          runtime->dma_area/addr/bytes = 0
       close           │
                       ▼
                 prealloc pool persists until snd_pcm_free
```

## SUMMARY

A driver gives each PCM substream a DMA buffer in two stages. At PCM creation it preallocates a pool, one [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) stored in [`substream->dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473), and at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) time the actual transfer buffer is bound into the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) DMA fields. Preallocation runs through [`snd_pcm_lib_preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L322) for one substream or [`snd_pcm_lib_preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341) for the whole PCM, and both forward to the internal [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261) with the managed flag cleared. [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401) call the same internal function with the flag set, which records [`substream->managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504). The buffer is described by a DMA type constant such as [`SNDRV_DMA_TYPE_DEV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L34) or [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45) and a backing [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), and the pages are obtained by [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63) and released by [`snd_dma_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L127).

The managed mode removes the explicit allocate and free from the driver. According to the kernel-doc on [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380), "PCM core will allocate a buffer automatically before PCM hw_params ops call, and release the buffer after PCM hw_free ops call as well, so that the driver doesn't need to invoke the allocation and the release explicitly in its callback". [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) tests the flag and calls [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) before the driver op, recording the result in [`runtime->buffer_changed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L442), and [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) calls [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482) after the driver op. Both helpers move the buffer into and out of [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), and [`runtime->dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) through [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263), which also tracks the managing buffer in [`runtime->dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441). A driver that manages the buffer itself uses [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) and [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482) from its own [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) callbacks. On Intel x86-64 Sound Open Firmware platforms the SOF [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) op [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) preallocates with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45), while the HD Audio core allocates its own descriptor and position buffers with [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) in [`snd_hdac_bus_alloc_stream_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L703).

## SPECIFICATIONS

The PCM DMA buffer model is a Linux kernel software contract with no standalone hardware specification. The buffer is reached from userspace through the data-area mmap at offset [`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319), defined in the ALSA userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h), which together with the read-only status and read-write control pages is the part of the model exposed to applications. The kernel DMA mapping the allocator sits on is described in [`Documentation/core-api/dma-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/dma-api.rst), and the buffer preallocation and managed mode are documented in the Buffer and Memory Management chapter of [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst). The underlying audio transport (HD Audio, USB Audio, or a SoC link) carries its own specification, and the buffer layer sits above it.

## LINUX KERNEL

### Buffer descriptor and DMA types (memalloc.h)

- [`'\<struct snd_dma_buffer\>':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55): one allocated buffer; holds the [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L56) type descriptor, the virtual pointer [`area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L57), the bus [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L58), the [`bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L59) size, and an allocator-private pointer
- [`'\<struct snd_dma_device\>':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L22): the buffer's [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L23), DMA [`dir`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L24), and backing [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L26)
- [`'SNDRV_DMA_TYPE_DEV':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L34): generic device coherent contiguous memory, the default audio buffer type
- [`'SNDRV_DMA_TYPE_DEV_SG':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45): scatter-gather pages (falls back to [`SNDRV_DMA_TYPE_DEV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L34) without `CONFIG_SND_DMA_SGBUF`)
- [`'SNDRV_DMA_TYPE_DEV_WC':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L35): write-combined contiguous memory
- [`'SNDRV_DMA_TYPE_VMALLOC':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L41): vmalloc'ed buffer for software-only paths
- [`'SNDRV_DMA_TYPE_NONCONTIG':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L42): non-coherent scatter-gather buffer
- [`'SNDRV_DMA_TYPE_DEV_IRAM':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L37): on-chip IRAM buffer (falls back to [`SNDRV_DMA_TYPE_DEV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L34) without `CONFIG_GENERIC_ALLOCATOR`)

### Allocator (memalloc.c)

- [`'\<snd_dma_alloc_dir_pages\>':'sound/core/memalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63): allocate pages for the given type and direction into a [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55), page-aligning the size and dispatching by type
- [`'\<snd_dma_alloc_pages\>':'include/sound/memalloc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76): the `DMA_BIDIRECTIONAL` inline wrapper over [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63)
- [`'\<snd_dma_alloc_pages_fallback\>':'sound/core/memalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L102): retry with a halved size until the allocation succeeds or one page is reached
- [`'\<snd_dma_free_pages\>':'sound/core/memalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L127): release a buffer through its type-specific free op
- [`'\<snd_dma_buffer_mmap\>':'sound/core/memalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L186): map a buffer's pages into a userspace VMA, used by the default PCM data mmap

### Preallocation and managed mode (pcm_memory.c)

- [`'\<snd_pcm_lib_preallocate_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L322): preallocate one substream's pool with the managed flag cleared
- [`'\<snd_pcm_lib_preallocate_pages_for_all\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341): preallocate every substream of a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), unmanaged
- [`'\<snd_pcm_set_managed_buffer\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380): preallocate one substream and set [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504)
- [`'\<snd_pcm_set_managed_buffer_all\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401): the same for every substream of a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534)
- [`'\<preallocate_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261): the internal primitive every public helper wraps; records the type and device, preallocates when `preallocate_dma` is set, and sets [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) when `managed` is true
- [`'\<preallocate_pages_for_all\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L297): loop [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261) over every substream
- [`'\<preallocate_pcm_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L98): the loop that asks [`do_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L51) for the largest page run down to [`snd_minimum_buffer`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L27)
- [`'\<snd_pcm_lib_preallocate_free\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L129): release one substream's preallocated pool
- [`'\<snd_pcm_lib_preallocate_free_for_all\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L140): release every substream's pool

### Explicit allocate and free (pcm_memory.c)

- [`'\<snd_pcm_lib_malloc_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420): bind the transfer buffer into the runtime; reuse the prealloc pool when it is large enough, otherwise allocate a fresh [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55), then call [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263)
- [`'\<snd_pcm_lib_free_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482): free a separately allocated buffer (leaving the prealloc pool intact) and clear the runtime fields with [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263)
- [`'\<do_alloc_pages\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L51): reserve against the per-card `max_alloc_per_card` budget, pick the DMA direction by stream, and call [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63)

### Runtime fields and the runtime-buffer setter (pcm.h)

- [`'dma_area':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437): the kernel virtual address of the active buffer
- [`'dma_addr':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438): the buffer's bus address for the DMA engine
- [`'dma_bytes':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439): the active buffer size
- [`'dma_buffer_p':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441): the [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) backing the active buffer (the prealloc pool or a fresh allocation)
- [`'buffer_changed':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L442): set in managed mode when the allocation changed, so a driver can re-derive hardware parameters
- [`'\<snd_pcm_set_runtime_buffer\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263): copy a [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) into the runtime DMA fields, or clear them when passed NULL
- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): holds the prealloc pool [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473), the [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) preallocation ceiling, and the [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) flag

### The auto alloc/free contract (pcm_native.c)

- [`'\<snd_pcm_hw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754): in managed mode calls [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) before the driver [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op and sets [`buffer_changed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L442)
- [`'\<do_hw_free\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908): runs the driver [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op then, in managed mode, calls [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482)
- [`'\<snd_pcm_hw_free\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920): the ioctl wrapper that takes the buffer-access lock and calls [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908)
- [`'\<snd_pcm_buffer_access_lock\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L717): block a buffer change while a read or write is in flight

### Data-area mmap (pcm_native.c)

- [`'\<snd_pcm_mmap\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013): the file `mmap` op; routes the default offset [`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319) to [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969)
- [`'\<snd_pcm_mmap_data\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969): bound-check the request against [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439), install the VMA ops, and raise [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491)
- [`'\<snd_pcm_lib_default_mmap\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927): map the buffer pages with [`snd_dma_buffer_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L186) on the runtime's [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441)

### /proc preallocation tuning (pcm_memory.c)

- [`'\<snd_pcm_lib_preallocate_proc_read\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L156): print the current preallocated size in kB for the `prealloc` proc file
- [`'\<snd_pcm_lib_preallocate_max_proc_read\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L168): print the [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) ceiling in kB for the `prealloc_max` proc file
- [`'\<snd_pcm_lib_preallocate_proc_write\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L180): reallocate the pool to a user-written size, bounded by [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474), refused while a substream is open
- [`'\<preallocate_info_init\>':'sound/core/pcm_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L233): create the `prealloc` and `prealloc_max` proc entries under the substream

### SOF and HDA consumers (sof/pcm.c, hda/core/controller.c)

- [`'\<sof_pcm_new\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637): the SOF [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) op; preallocates the playback and capture buffers with [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45)
- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): wires [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) into the SOF component driver's [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) field
- [`'\<snd_hdac_bus_alloc_stream_pages\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L703): allocate the per-stream BDL and the shared position buffer with [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Buffer and Memory Management chapter covers [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401), the managed mode, and the External Hardware Buffers section that uses [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45)
- [`Documentation/core-api/dma-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/dma-api.rst): the DMA mapping API that [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63) builds on, including coherent and streaming allocations
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated PCM and memory-management API reference for the preallocation and managed-buffer helpers
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the per-substream procfs entries, including the `prealloc` and `prealloc_max` files

## OTHER SOURCES

- [ALSA project library documentation (PCM mmap access)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A driver chooses one of two buffer-management contracts when it constructs the PCM, and the choice fixes which kernel entry points touch the runtime DMA fields. Managed mode is the common case, where [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) (or [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401)) preallocates and arms the auto alloc/free, and the unmanaged case calls [`snd_pcm_lib_preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341) at construct time and then [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) and [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482) from the driver's own callbacks. The mapping from the userspace PCM action to the core entry point and the buffer effect is the same for every ALSA driver.

| userspace action | kernel entry point | buffer effect |
|------------------|--------------------|---------------|
| PCM device creation | driver [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) calls [`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401) | preallocate [`substream->dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473), set [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) (managed) | [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) sets [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437)/[`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438)/[`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) before the driver op |
| `mmap(..., DATA offset)` | [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) | map [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) into the process, raise [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) (managed) | [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482) clears the runtime DMA fields after the driver op |
| `echo N > .../prealloc` | [`snd_pcm_lib_preallocate_proc_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L180) | reallocate [`substream->dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473) to N kB, bounded by [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) |
| device teardown | [`snd_pcm_lib_preallocate_free_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L140) | release every substream's prealloc pool |

### snd_dma_buffer: the allocated buffer

[`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) is the unit the allocator fills and every consumer reads back. The [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L56) member names the DMA type and the backing device, [`area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L57) is the kernel virtual pointer, [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L58) is the bus address the hardware uses, and [`bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L59) is the actual allocated size, which can exceed the requested size:

```c
/* include/sound/memalloc.h:55 */
struct snd_dma_buffer {
	struct snd_dma_device dev;	/* device type */
	unsigned char *area;	/* virtual pointer */
	dma_addr_t addr;	/* physical address */
	size_t bytes;		/* buffer size in bytes */
	void *private_data;	/* private for allocator; don't touch */
};
```

The [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L56) member is a [`struct snd_dma_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L22) carrying the type constant, the DMA direction, and the generic device the pages are allocated against:

```c
/* include/sound/memalloc.h:22 */
struct snd_dma_device {
	int type;			/* SNDRV_DMA_TYPE_XXX */
	enum dma_data_direction dir;	/* DMA direction */
	bool need_sync;			/* explicit sync needed? */
	struct device *dev;		/* generic device */
};
```

The [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L23) is one of the `SNDRV_DMA_TYPE_*` constants, and several of them collapse to a coherent device buffer when the matching config option is off:

```c
/* include/sound/memalloc.h:32 */
#define SNDRV_DMA_TYPE_UNKNOWN		0	/* not defined */
#define SNDRV_DMA_TYPE_CONTINUOUS	1	/* continuous no-DMA memory */
#define SNDRV_DMA_TYPE_DEV		2	/* generic device continuous */
#define SNDRV_DMA_TYPE_DEV_WC		5	/* continuous write-combined */
#ifdef CONFIG_GENERIC_ALLOCATOR
#define SNDRV_DMA_TYPE_DEV_IRAM		4	/* generic device iram-buffer */
#else
#define SNDRV_DMA_TYPE_DEV_IRAM	SNDRV_DMA_TYPE_DEV
#endif
#define SNDRV_DMA_TYPE_VMALLOC		7	/* vmalloc'ed buffer */
#define SNDRV_DMA_TYPE_NONCONTIG	8	/* non-coherent SG buffer */
#define SNDRV_DMA_TYPE_NONCOHERENT	9	/* non-coherent buffer */
#ifdef CONFIG_SND_DMA_SGBUF
#define SNDRV_DMA_TYPE_DEV_SG		3	/* S/G pages */
#define SNDRV_DMA_TYPE_DEV_WC_SG	6	/* SG write-combined */
#else
#define SNDRV_DMA_TYPE_DEV_SG	SNDRV_DMA_TYPE_DEV /* no SG-buf support */
#define SNDRV_DMA_TYPE_DEV_WC_SG	SNDRV_DMA_TYPE_DEV_WC
#endif
```

## DETAILS

### The runtime DMA fields and the buffer descriptor

The transfer buffer is reached at run time through three fields of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) is the kernel virtual address the CPU and the userspace mmap see, [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) is the bus address the DMA engine programs, and [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) is the size. A fourth field, [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441), points at the [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) that owns those pages, either the substream's prealloc pool or a fresh allocation:

```c
/* include/sound/pcm.h:436 */
	/* -- DMA -- */           
	unsigned char *dma_area;	/* DMA area */
	dma_addr_t dma_addr;		/* physical bus address (not accessible from main CPU) */
	size_t dma_bytes;		/* size of DMA area */

	struct snd_dma_buffer *dma_buffer_p;	/* allocated buffer */
	unsigned int buffer_changed:1;	/* buffer allocation changed; set only in managed mode */
```

The prealloc pool itself is the embedded [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473) of the [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), alongside the [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) ceiling and the [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) flag that records which contract the substream uses:

```c
/* include/sound/pcm.h:464 */
struct snd_pcm_substream {
	...
	struct snd_dma_buffer dma_buffer;
	size_t dma_max;
	...
	/* misc flags */
	unsigned int hw_opened: 1;
	unsigned int managed_buffer_alloc:1;
	...
};
```

[`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263) is the one place the four runtime DMA fields are written together. It copies [`area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L57), [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L58), and [`bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L59) out of a [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) and stores the pointer, or zeroes all four when passed NULL:

```c
/* include/sound/pcm.h:1263 */
static inline void snd_pcm_set_runtime_buffer(struct snd_pcm_substream *substream,
					      struct snd_dma_buffer *bufp)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (bufp) {
		runtime->dma_buffer_p = bufp;
		runtime->dma_area = bufp->area;
		runtime->dma_addr = bufp->addr;
		runtime->dma_bytes = bufp->bytes;
	} else {
		runtime->dma_buffer_p = NULL;
		runtime->dma_area = NULL;
		runtime->dma_addr = 0;
		runtime->dma_bytes = 0;
	}
}
```

The pages behind a [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) come from [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63), which page-aligns the request, records the type and device on the buffer, dispatches to the type-specific allocator through [`__snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L39), and stores the actual allocated size in [`bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L59):

```c
/* sound/core/memalloc.c:63 */
int snd_dma_alloc_dir_pages(int type, struct device *device,
			    enum dma_data_direction dir, size_t size,
			    struct snd_dma_buffer *dmab)
{
	if (WARN_ON(!size))
		return -ENXIO;
	if (WARN_ON(!dmab))
		return -ENXIO;

	size = PAGE_ALIGN(size);
	dmab->dev.type = type;
	dmab->dev.dev = device;
	dmab->dev.dir = dir;
	dmab->bytes = 0;
	dmab->addr = 0;
	dmab->private_data = NULL;
	dmab->area = __snd_dma_alloc_pages(dmab, size);
	if (!dmab->area)
		return -ENOMEM;
	dmab->bytes = size;
	return 0;
}
```

[`snd_dma_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L127) releases a buffer by calling the type-specific free op selected from the same dispatch table.

```
    Buffer descriptor feeds the runtime DMA fields
    ───────────────────────────────────────────────
    (snd_pcm_set_runtime_buffer copies one struct into the runtime)

    struct snd_pcm_substream            fresh struct snd_dma_buffer
    ┌──────────────────────────────┐    (when pool too small)
    │ dma_buffer (prealloc pool):  │    ┌──────────────────────────┐
    │   struct snd_dma_buffer      │    │ area  (virtual pointer)  │
    │     area / addr / bytes      │    │ addr  (bus address)      │
    │ dma_max                      │    │ bytes (allocated size)   │
    │ managed_buffer_alloc         │    └─────────────┬────────────┘
    └──────────────┬───────────────┘                  │
                   │   snd_pcm_set_runtime_buffer(bufp)│
                   └────────────────┬─────────────────┘
                                    ▼
    struct snd_pcm_runtime
    ┌─────────────────────────────────────────────────────────┐
    │ dma_buffer_p ─▶ the backing snd_dma_buffer (pool/fresh)  │
    │ dma_area  = bufp->area   (kernel virtual address)        │
    │ dma_addr  = bufp->addr   (bus address for the DMA)       │
    │ dma_bytes = bufp->bytes  (active buffer size)            │
    └─────────────────────────────────────────────────────────┘
```

### The allocator entry points and the mmap helper

[`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) is the thin inline wrapper most callers reach for. It pins the direction to `DMA_BIDIRECTIONAL` and forwards to [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63), so a caller that does not care about the DMA direction gets the same page-aligning, type-dispatching allocation shown above:

```c
/* include/sound/memalloc.h:76 */
static inline int snd_dma_alloc_pages(int type, struct device *dev,
				      size_t size, struct snd_dma_buffer *dmab)
{
	return snd_dma_alloc_dir_pages(type, dev, DMA_BIDIRECTIONAL, size, dmab);
}
```

[`snd_dma_alloc_pages_fallback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L102) wraps that call in a retry loop. On `-ENOMEM` it halves the request and rounds it back up to an order boundary, looping until the allocation succeeds or it is already down to a single page, which lets a caller obtain a smaller-than-ideal buffer rather than fail outright:

```c
/* sound/core/memalloc.c:102 */
int snd_dma_alloc_pages_fallback(int type, struct device *device, size_t size,
				 struct snd_dma_buffer *dmab)
{
	int err;

	while ((err = snd_dma_alloc_pages(type, device, size, dmab)) < 0) {
		if (err != -ENOMEM)
			return err;
		if (size <= PAGE_SIZE)
			return -ENOMEM;
		size >>= 1;
		size = PAGE_SIZE << get_order(size);
	}
	if (! dmab->area)
		return -ENOMEM;
	return 0;
}
```

[`snd_dma_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L127) is the matching release, a one-line dispatch that looks up the buffer's allocator ops with [`snd_dma_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L52) and calls the type-specific `free`:

```c
/* sound/core/memalloc.c:127 */
void snd_dma_free_pages(struct snd_dma_buffer *dmab)
{
	const struct snd_malloc_ops *ops = snd_dma_get_ops(dmab);

	if (ops && ops->free)
		ops->free(dmab);
}
```

[`snd_dma_buffer_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L186) maps a buffer's pages into a userspace VMA the same way, by dispatching to the type-specific `mmap` op, and is the call the default PCM data-area mmap path uses to expose [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) to an application:

```c
/* sound/core/memalloc.c:191 */
int snd_dma_buffer_mmap(struct snd_dma_buffer *dmab,
			struct vm_area_struct *area)
{
	const struct snd_malloc_ops *ops;

	if (!dmab)
		return -ENOENT;
	ops = snd_dma_get_ops(dmab);
	if (ops && ops->mmap)
		return ops->mmap(dmab, area);
	else
		return -ENOENT;
}
```

### Preallocation establishes the pool at pcm_new

A driver preallocates the pool when it constructs the PCM, before any substream is opened. The unmanaged entry point [`snd_pcm_lib_preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341) walks every substream and forwards to the internal [`preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L297) with the managed flag cleared, and [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261) is the primitive both contracts share. It records the DMA type and backing device on the substream's pool, preallocates the pages through [`preallocate_pcm_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L98) when `preallocate_dma` is set and the substream index is within `maximum_substreams`, captures the [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) ceiling, creates the proc files, and sets [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) only when `managed` is true:

```c
/* sound/core/pcm_memory.c:261 */
static int preallocate_pages(struct snd_pcm_substream *substream,
			      int type, struct device *data,
			      size_t size, size_t max, bool managed)
{
	int err;

	if (snd_BUG_ON(substream->dma_buffer.dev.type))
		return -EINVAL;

	substream->dma_buffer.dev.type = type;
	substream->dma_buffer.dev.dev = data;

	if (size > 0) {
		if (!max) {
			/* no fallback, only also inform -ENOMEM */
			err = preallocate_pcm_pages(substream, size, true);
			if (err < 0)
				return err;
		} else if (preallocate_dma &&
			   substream->number < maximum_substreams) {
			err = preallocate_pcm_pages(substream, size, false);
			if (err < 0 && err != -ENOMEM)
				return err;
		}
	}

	if (substream->dma_buffer.bytes > 0)
		substream->buffer_bytes_max = substream->dma_buffer.bytes;
	substream->dma_max = max;
	if (max > 0)
		preallocate_info_init(substream);
	if (managed)
		substream->managed_buffer_alloc = 1;
	return 0;
}
```

[`preallocate_pcm_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L98) asks [`do_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L51) for the requested size and, unless `no_fallback` is set, halves the size on `-ENOMEM` down to [`snd_minimum_buffer`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L27) (16 kB), so a card short on contiguous memory still gets a usable pool. [`do_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L51) reserves the size against the per-card `max_alloc_per_card` budget under `card->memory_mutex`, picks `DMA_TO_DEVICE` for playback and `DMA_FROM_DEVICE` for capture, and then calls [`snd_dma_alloc_dir_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L63).

The public unmanaged helpers are thin shells over [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261) and [`preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L297) with `managed` passed false. [`snd_pcm_lib_preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L322) sets the pool on one substream:

```c
/* sound/core/pcm_memory.c:322 */
void snd_pcm_lib_preallocate_pages(struct snd_pcm_substream *substream,
				  int type, struct device *data,
				  size_t size, size_t max)
{
	preallocate_pages(substream, type, data, size, max, false);
}
```

[`snd_pcm_lib_preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L341) does the same for the whole PCM by delegating to the loop helper:

```c
/* sound/core/pcm_memory.c:341 */
void snd_pcm_lib_preallocate_pages_for_all(struct snd_pcm *pcm,
					  int type, void *data,
					  size_t size, size_t max)
{
	preallocate_pages_for_all(pcm, type, data, size, max, false);
}
```

[`preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L297) is the shared loop that walks every substream of the PCM with [`for_each_pcm_substream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L580) and applies [`preallocate_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L261); both the unmanaged and managed all-substream entry points funnel through it, differing only in the `managed` argument:

```c
/* sound/core/pcm_memory.c:297 */
static int preallocate_pages_for_all(struct snd_pcm *pcm, int type,
				      void *data, size_t size, size_t max,
				      bool managed)
{
	struct snd_pcm_substream *substream;
	int stream, err;

	for_each_pcm_substream(pcm, stream, substream) {
		err = preallocate_pages(substream, type, data, size, max, managed);
		if (err < 0)
			return err;
	}
	return 0;
}
```

The pool is released at PCM teardown. [`snd_pcm_lib_preallocate_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L129) frees one substream's embedded [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473) through [`do_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L42), which also returns the bytes to the per-card budget, and [`snd_pcm_lib_preallocate_free_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L140) loops it over the PCM, the call the core makes from [`snd_pcm_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1029) so a driver never has to release the preallocation itself:

```c
/* sound/core/pcm_memory.c:129 */
void snd_pcm_lib_preallocate_free(struct snd_pcm_substream *substream)
{
	do_free_pages(substream->pcm->card, &substream->dma_buffer);
}
```

```c
/* sound/core/pcm_memory.c:140 */
void snd_pcm_lib_preallocate_free_for_all(struct snd_pcm *pcm)
{
	struct snd_pcm_substream *substream;
	int stream;

	for_each_pcm_substream(pcm, stream, substream)
		snd_pcm_lib_preallocate_free(substream);
}
```

### Managed mode auto-allocates around hw_params and hw_free

[`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) and its all-substream form are the same internal call as the unmanaged helpers with `managed` set true, which is the only difference between the two contracts:

```c
/* sound/core/pcm_memory.c:380 */
int snd_pcm_set_managed_buffer(struct snd_pcm_substream *substream, int type,
				struct device *data, size_t size, size_t max)
{
	return preallocate_pages(substream, type, data, size, max, true);
}
```

[`snd_pcm_set_managed_buffer_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L401) is the all-substream form, the one most drivers call from their construct path, and it routes through the same [`preallocate_pages_for_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L297) loop with `managed` set true:

```c
/* sound/core/pcm_memory.c:401 */
int snd_pcm_set_managed_buffer_all(struct snd_pcm *pcm, int type,
				   struct device *data,
				   size_t size, size_t max)
{
	return preallocate_pages_for_all(pcm, type, data, size, max, true);
}
```

The [`managed_buffer_alloc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L504) flag set by that call is read on the ioctl paths. [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) refines and chooses the parameters, then, before it invokes the driver's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op, allocates the buffer with [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) and records whether the allocation changed in [`runtime->buffer_changed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L442):

```c
/* sound/core/pcm_native.c:792 */
	err = snd_pcm_hw_params_choose(substream, params);
	if (err < 0)
		goto _error;

	err = fixup_unreferenced_params(substream, params);
	if (err < 0)
		goto _error;

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
```

The release side mirrors it. [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908), reached from [`snd_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920), runs the driver's [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op first and only then, in managed mode, frees the buffer:

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

The ordering is the contract the kernel-doc on [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380) promises, "PCM core will allocate a buffer automatically before PCM hw_params ops call, and release the buffer after PCM hw_free ops call as well, so that the driver doesn't need to invoke the allocation and the release explicitly in its callback". By the time the driver's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) runs, [`runtime->dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) and [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) are valid, so the op programs the DMA descriptor against a buffer the core owns, and by the time [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) returns the buffer is still present for the driver to quiesce its hardware before the core releases it. Both [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) and [`snd_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920) hold the buffer-access lock taken by [`snd_pcm_buffer_access_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L717), so the allocation change cannot race an in-flight read or write.

[`snd_pcm_buffer_access_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L717) is the guard both ioctl handlers acquire first. It decrements [`runtime->buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L444) only when no reader or writer holds it positive, returning `-EBUSY` if one does, and otherwise takes [`runtime->buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L443) so the buffer cannot be reallocated under an active transfer:

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

[`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) also cleans up the buffer on its own error path. If a later step fails after the managed allocation, the `_error` tail runs the driver [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op and, in managed mode, calls [`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482), so a half-configured substream never keeps a buffer the core believes it released:

```c
/* sound/core/pcm_native.c:874 */
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

[`snd_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L920) is the ioctl entry point for `SNDRV_PCM_IOCTL_HW_FREE`. It takes the buffer-access lock, checks the substream is in `SETUP` or `PREPARED` and not still mmap'd, then calls [`do_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L908) to run the driver op and release the managed buffer before returning the substream to the `OPEN` state:

```c
/* sound/core/pcm_native.c:920 */
static int snd_pcm_hw_free(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime;
	int result = 0;

	if (PCM_RUNTIME_CHECK(substream))
		return -ENXIO;
	runtime = substream->runtime;
	result = snd_pcm_buffer_access_lock(runtime);
	if (result < 0)
		return result;
	scoped_guard(pcm_stream_lock_irq, substream) {
		switch (runtime->state) {
		case SNDRV_PCM_STATE_SETUP:
		case SNDRV_PCM_STATE_PREPARED:
			if (atomic_read(&substream->mmap_count))
				result = -EBADFD;
			break;
		default:
			result = -EBADFD;
			break;
		}
	}
	if (result)
		goto unlock;
	result = do_hw_free(substream);
	snd_pcm_set_state(substream, SNDRV_PCM_STATE_OPEN);
	cpu_latency_qos_remove_request(&substream->latency_pm_qos_req);
 unlock:
	snd_pcm_buffer_access_unlock(runtime);
	return result;
}
```

### The explicit malloc/free path for non-managed drivers

A driver that did not arm managed mode calls [`snd_pcm_lib_malloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L420) from its own [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) callback. The function reuses the prealloc pool when it is at least the requested size, allocates a fresh [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) otherwise, and binds the result into the runtime with [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263), returning 1 when the buffer changed and 0 when the pool was reused unchanged:

```c
/* sound/core/pcm_memory.c:444 */
	if (substream->dma_buffer.area != NULL &&
	    substream->dma_buffer.bytes >= size) {
		dmab = &substream->dma_buffer; /* use the pre-allocated buffer */
	} else {
		/* dma_max=0 means the fixed size preallocation */
		if (substream->dma_buffer.area && !substream->dma_max)
			return -ENOMEM;
		dmab = kzalloc_obj(*dmab);
		if (! dmab)
			return -ENOMEM;
		dmab->dev = substream->dma_buffer.dev;
		if (do_alloc_pages(card,
				   substream->dma_buffer.dev.type,
				   substream->dma_buffer.dev.dev,
				   substream->stream,
				   size, dmab) < 0) {
			kfree(dmab);
			...
			return -ENOMEM;
		}
	}
	snd_pcm_set_runtime_buffer(substream, dmab);
	runtime->dma_bytes = size;
	return 1;			/* area was changed */
```

[`snd_pcm_lib_free_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L482) is the inverse. It frees the buffer only when the runtime points at a separately allocated one (when [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441) differs from the embedded pool), leaving the prealloc pool intact for the next [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77), and then clears the runtime fields:

```c
/* sound/core/pcm_memory.c:482 */
int snd_pcm_lib_free_pages(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime;

	if (PCM_RUNTIME_CHECK(substream))
		return -EINVAL;
	runtime = substream->runtime;
	if (runtime->dma_area == NULL)
		return 0;
	if (runtime->dma_buffer_p != &substream->dma_buffer) {
		struct snd_card *card = substream->pcm->card;

		/* it's a newly allocated buffer.  release it now. */
		do_free_pages(card, runtime->dma_buffer_p);
		kfree(runtime->dma_buffer_p);
	}
	snd_pcm_set_runtime_buffer(substream, NULL);
	return 0;
}
```

The size decides the allocate path and the dma_buffer_p pointer decides the free path, one reusing the pool when it already fits and the other keeping it whenever the runtime still points at it:

```
    Which buffer backs the runtime, and what free releases
    ───────────────────────────────────────────────────────

    snd_pcm_lib_malloc_pages(size)
    condition                            backing buffer
    ───────────────────────────────────  ───────────────────────────
    pool.area set and pool.bytes >= size reuse pool (&dma_buffer)
    pool.area set and dma_max == 0       reject: -ENOMEM (fixed pool)
    otherwise                            kzalloc a fresh snd_dma_buffer
                                         then do_alloc_pages()
    result: snd_pcm_set_runtime_buffer(dmab); return 1 changed / 0 same

    snd_pcm_lib_free_pages()
    runtime->dma_buffer_p value          action
    ───────────────────────────────────  ───────────────────────────
    == &dma_buffer  (the prealloc pool)  keep pool; clear runtime fields
    != &dma_buffer  (a fresh allocation) do_free_pages + kfree; clear
```

### The data-area mmap reaches the same buffer from userspace

The buffer the core allocated is handed to an application by mapping its pages into the process. [`snd_pcm_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4013) is the file `mmap` op; it dispatches on the page offset, routing the status and control pages to their own handlers and the default offset [`SNDRV_PCM_MMAP_OFFSET_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L319) to [`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969):

```c
/* sound/core/pcm_native.c:4013 */
static int snd_pcm_mmap(struct file *file, struct vm_area_struct *area)
{
	struct snd_pcm_file * pcm_file;
	struct snd_pcm_substream *substream;	
	unsigned long offset;
	
	pcm_file = file->private_data;
	substream = pcm_file->substream;
	...
	offset = area->vm_pgoff << PAGE_SHIFT;
	switch (offset) {
	...
	default:
		return snd_pcm_mmap_data(substream, file, area);
	}
	return 0;
}
```

[`snd_pcm_mmap_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3969) checks the request against the substream's access mode and bounds the mapping length and offset against the page-aligned [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439), installs the data VMA ops, calls the driver's own `mmap` op or [`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927), and raises [`mmap_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L491) on success so a later [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) is refused while the mapping is live:

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
	...
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
}
```

[`snd_pcm_lib_default_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3927) is the default handler used when the driver supplies no `mmap` op. It maps the runtime's [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441) pages with [`snd_dma_buffer_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/memalloc.c#L186), falling back to a fault handler when the buffer type cannot be mapped in one shot:

```c
/* sound/core/pcm_native.c:3927 */
int snd_pcm_lib_default_mmap(struct snd_pcm_substream *substream,
			     struct vm_area_struct *area)
{
	vm_flags_set(area, VM_DONTEXPAND | VM_DONTDUMP);
	if (!substream->ops->page &&
	    !snd_dma_buffer_mmap(snd_pcm_get_dma_buf(substream), area))
		return 0;
	/* mmap with fault handler */
	area->vm_ops = &snd_pcm_vm_ops_data_fault;
	return 0;
}
```

That mapping is one of three windows onto the same pages, the kernel reaching them by dma_area, the DMA engine by dma_addr, and the process through the data mmap:

```
    One snd_dma_buffer, three views of the same pages
    ──────────────────────────────────────────────────

              struct snd_dma_buffer   (runtime->dma_buffer_p)
              ┌────────────────────────────────────────┐
              │   the allocated DMA pages (dma_bytes)   │
              └────┬──────────────┬──────────────┬──────┘
                   │              │              │
       dma_area    │   dma_addr   │    mmap of   │
       kernel va   │   bus addr   │  same pages  │
                   ▼              ▼              ▼
       ┌──────────────┐ ┌──────────────┐ ┌───────────────────┐
       │ CPU / kernel │ │ DMA engine   │ │ userspace VMA     │
       │ reads/writes │ │ reads/writes │ │ snd_pcm_mmap_data │
       │ via          │ │ via          │ │ snd_pcm_lib_      │
       │ dma_area     │ │ dma_addr     │ │   default_mmap    │
       └──────────────┘ └──────────────┘ └───────────────────┘

       the mmap length and offset are bounded by dma_bytes
```

### Retuning the pool size through procfs

Each substream with a nonzero [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) gets `prealloc` and `prealloc_max` proc files created by [`preallocate_info_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L233). [`snd_pcm_lib_preallocate_proc_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L156) reports the current pool size in kB, and [`snd_pcm_lib_preallocate_max_proc_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L168) reports the [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474) ceiling:

```c
/* sound/core/pcm_memory.c:156 */
static void snd_pcm_lib_preallocate_proc_read(struct snd_info_entry *entry,
					      struct snd_info_buffer *buffer)
{
	struct snd_pcm_substream *substream = entry->private_data;
	snd_iprintf(buffer, "%lu\n", (unsigned long) substream->dma_buffer.bytes / 1024);
}
```

```c
/* sound/core/pcm_memory.c:168 */
static void snd_pcm_lib_preallocate_max_proc_read(struct snd_info_entry *entry,
						  struct snd_info_buffer *buffer)
{
	struct snd_pcm_substream *substream = entry->private_data;
	snd_iprintf(buffer, "%lu\n", (unsigned long) substream->dma_max / 1024);
}
```

[`snd_pcm_lib_preallocate_proc_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L180) reallocates the pool to a user-written size in kB. It refuses while the substream is open, validates the size against [`dma_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L474), allocates a replacement with [`do_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L51), and only after that succeeds frees the old [`dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L473) and swaps the new one in:

```c
/* sound/core/pcm_memory.c:180 */
static void snd_pcm_lib_preallocate_proc_write(struct snd_info_entry *entry,
					       struct snd_info_buffer *buffer)
{
	struct snd_pcm_substream *substream = entry->private_data;
	struct snd_card *card = substream->pcm->card;
	char line[64], str[64];
	unsigned long size;
	struct snd_dma_buffer new_dmab;

	guard(mutex)(&substream->pcm->open_mutex);
	if (substream->runtime) {
		buffer->error = -EBUSY;
		return;
	}
	if (!snd_info_get_line(buffer, line, sizeof(line))) {
		snd_info_get_str(str, line, sizeof(str));
		buffer->error = kstrtoul(str, 10, &size);
		if (buffer->error != 0)
			return;
		size *= 1024;
		if ((size != 0 && size < 8192) || size > substream->dma_max) {
			buffer->error = -EINVAL;
			return;
		}
		if (substream->dma_buffer.bytes == size)
			return;
		memset(&new_dmab, 0, sizeof(new_dmab));
		new_dmab.dev = substream->dma_buffer.dev;
		if (size > 0) {
			if (do_alloc_pages(card,
					   substream->dma_buffer.dev.type,
					   substream->dma_buffer.dev.dev,
					   substream->stream,
					   size, &new_dmab) < 0) {
				buffer->error = -ENOMEM;
				...
				return;
			}
			substream->buffer_bytes_max = size;
		} else {
			substream->buffer_bytes_max = UINT_MAX;
		}
		if (substream->dma_buffer.area)
			do_free_pages(card, &substream->dma_buffer);
		substream->dma_buffer = new_dmab;
	} else {
		buffer->error = -EINVAL;
	}
}
```

### SOF preallocates with the same managed contract

On Intel x86-64 the Sound Open Firmware platform component preallocates the host buffer in its [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) op. [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) locates the SOF PCM for the runtime with [`snd_sof_find_spcm_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L24) and then, for each direction the topology declares, calls [`snd_pcm_set_managed_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_memory.c#L380):

```c
/* sound/soc/sof/pcm.c:637 */
static int sof_pcm_new(struct snd_soc_component *component,
		       struct snd_soc_pcm_runtime *rtd)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pcm *spcm;
	struct snd_pcm *pcm = rtd->pcm;
	struct snd_soc_tplg_stream_caps *caps;
	int stream = SNDRV_PCM_STREAM_PLAYBACK;

	/* find SOF PCM for this RTD */
	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm) {
		dev_warn(component->dev, "warn: can't find PCM with DAI ID %d\n",
			 rtd->dai_link->id);
		return 0;
	}
	...
```

Each direction passes [`SNDRV_DMA_TYPE_DEV_SG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L45), a size of 0, and the topology-supplied maximum, so the buffer is allocated lazily at the first [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77):

```c
/* sound/soc/sof/pcm.c:668 */
	/* pre-allocate playback audio buffer pages */
	spcm_dbg(spcm, stream, "allocate %s playback DMA buffer size 0x%x max 0x%x\n",
		 caps->name, caps->buffer_size_min, caps->buffer_size_max);

	snd_pcm_set_managed_buffer(pcm->streams[stream].substream,
				   SNDRV_DMA_TYPE_DEV_SG, sdev->dev,
				   0, le32_to_cpu(caps->buffer_size_max));
```

[`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) wires the op into the SOF component driver by setting the [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) field of the embedded [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L60) to [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637), alongside the rest of the PCM ops:

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
	...
	pd->hw_params = sof_pcm_hw_params;
	pd->prepare = sof_pcm_prepare;
	pd->hw_free = sof_pcm_hw_free;
	...
	pd->pcm_construct = sof_pcm_new;
	...
}
```

Because [`sof_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L637) arms managed mode, the core runs the alloc-before-hw_params and free-after-hw_free contract above, and the SOF [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op sees a ready [`runtime->dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) it hands to the firmware. The HD Audio core, by contrast, allocates the per-stream descriptor and position buffers directly rather than through the managed PCM contract. [`snd_hdac_bus_alloc_stream_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L703) calls [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) once per stream for the buffer descriptor list, once for the shared position buffer sized to eight bytes per stream, and once for the ring-buffer page:

```c
/* sound/hda/core/controller.c:703 */
int snd_hdac_bus_alloc_stream_pages(struct hdac_bus *bus)
{
	struct hdac_stream *s;
	int num_streams = 0;
	int dma_type = bus->dma_type ? bus->dma_type : SNDRV_DMA_TYPE_DEV;
	int err;

	list_for_each_entry(s, &bus->stream_list, list) {
		/* allocate memory for the BDL for each stream */
		err = snd_dma_alloc_pages(dma_type, bus->dev,
					  BDL_SIZE, &s->bdl);
		num_streams++;
		if (err < 0)
			return -ENOMEM;
	}

	if (WARN_ON(!num_streams))
		return -EINVAL;
	/* allocate memory for the position buffer */
	err = snd_dma_alloc_pages(dma_type, bus->dev,
				  num_streams * 8, &bus->posbuf);
	if (err < 0)
		return -ENOMEM;
	list_for_each_entry(s, &bus->stream_list, list)
		s->posbuf = (__le32 *)(bus->posbuf.area + s->index * 8);

	/* single page (at least 4096 bytes) must suffice for both ringbuffes */
	return snd_dma_alloc_pages(dma_type, bus->dev, PAGE_SIZE, &bus->rb);
}
```
