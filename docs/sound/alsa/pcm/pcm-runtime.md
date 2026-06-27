# PCM runtime (snd_pcm_runtime)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is the per-open state of a PCM substream, allocated when a process opens the substream and freed when the last reference closes it, so it exists only while a stream is in use. It gathers eight field groups, the status block (the lifecycle [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the hardware-pointer bookkeeping), the hardware parameters the driver's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op fixed ([`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L379), [`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L380), [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L382), [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L383), [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386)), the software parameters a client set ([`start_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L399), [`stop_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L400), [`silence_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L402), [`boundary`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L403)), the two mmap pages [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413), the locking and scheduling fields ([`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417), [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422)), the hardware description ([`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) and [`hw_constraints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L430)), and the DMA pointers ([`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439)). [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) allocates the record and its two mmap pages, and [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) frees them.

```
    struct snd_pcm_runtime  (one per open substream)
    ────────────────────────────────────────────────
    ┌───────────────────────────────────────────────────┐
    │ Status      state, suspended_state,               │
    │             hw_ptr_base, hw_ptr_interrupt, delay   │
    ├───────────────────────────────────────────────────┤
    │ HW params   access, format, rate, channels,       │
    │             period_size, periods, buffer_size,     │
    │             frame_bits, sample_bits, rate_num/den  │
    ├──────────────────────────────────────────────────┤
    │ SW params   start/stop/silence thresholds,         │
    │             boundary, period_step, tstamp_mode     │
    ├──────────────────────────────────────────────────┤
    │ mmap        status  ─▶ RO page (state, hw_ptr)     │
    │             control ─▶ RW page (appl_ptr, avail)   │
    ├──────────────────────────────────────────────────┤
    │ locking     sleep, tsleep, buffer_mutex,           │
    │             buffer_accessing, stop_operating       │
    ├──────────────────────────────────────────────────┤
    │ hw desc     hw (snd_pcm_hardware), hw_constraints  │
    ├──────────────────────────────────────────────────┤
    │ DMA         dma_area, dma_addr, dma_bytes,         │
    │             dma_buffer_p, buffer_changed           │
    └──────────────────────────────────────────────────┘
       allocated by snd_pcm_attach_substream() at open
       freed by snd_pcm_detach_substream() at close
```

## SUMMARY

A free substream has a NULL [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478). Opening it allocates one [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) in [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), which also allocates the two page-aligned mmap areas [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413), initializes [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) and the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) wait queue, and sets the initial [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307). The fields then fill in stages. The driver's [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op copies its [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) capability set into [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) and seeds [`hw_constraints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L430), the `SNDRV_PCM_IOCTL_HW_PARAMS` path writes the negotiated [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L379), [`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L380), [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L382), [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L383), [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), [`periods`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385), and [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386), and the `SNDRV_PCM_IOCTL_SW_PARAMS` path writes the [`start_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L399), [`stop_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L400), and silence fields from a [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433). On an x86-64 ACPI machine that [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op is ASoC's [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), which fills [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) from the merged capabilities of the link's CPU and codec DAIs through [`soc_pcm_init_runtime_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L701).

During the running stream, the status block tracks the hardware pointer ([`hw_ptr_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L371), [`hw_ptr_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L372), [`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L375)) and mirrors the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) into the read-only [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page through [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725). The DMA group ([`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437), [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438), [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439), [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441)) is filled by [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263) at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) and cleared at [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77). Close runs [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980), which frees the two pages, destroys [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), and frees the record so the substream returns to its NULL-runtime state.

## SPECIFICATIONS

The runtime record is an internal Linux kernel object and has no standalone hardware specification. Two of its members are part of the ALSA userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h): the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page is a [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) and the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page is a [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540), both of which a client may mmap. The negotiated parameters mirror the [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) and [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433) the ioctls carry. The sample formats and rates the runtime holds follow the codec and bus standards of the hardware behind the card.

## LINUX KERNEL

### The runtime record and its field groups (include/sound/pcm.h)

- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the per-open record holding the eight field groups
- [`'state':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) / [`'suspended_state':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) / [`'trigger_master':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366): the status block's lifecycle value, the saved resume state, and the linked-group trigger owner
- [`'hw_ptr_base':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L371) / [`'hw_ptr_interrupt':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L372) / [`'delay':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L375): the hardware-pointer accounting the running path updates
- [`'access':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L379) / [`'format':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L380) / [`'rate':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L382) / [`'channels':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L383) / [`'period_size':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384) / [`'periods':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385) / [`'buffer_size':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386): the HW-params group fixed by [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77)
- [`'frame_bits':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389) / [`'sample_bits':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L390) / [`'rate_num':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L392) / [`'rate_den':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L393): the derived frame and rate geometry
- [`'start_threshold':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L399) / [`'stop_threshold':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L400) / [`'silence_threshold':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L401) / [`'silence_size':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L402) / [`'boundary':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L403): the SW-params group the core consults
- [`'status':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) / [`'control':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413): the read-only and read-write mmap pages
- [`'twake':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L416) / [`'sleep':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) / [`'tsleep':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L418) / [`'stop_operating':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L420) / [`'buffer_mutex':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) / [`'buffer_accessing':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422): the locking and scheduling group
- [`'hw':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) / [`'hw_constraints':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L430): the [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) capability snapshot and the [`struct snd_pcm_hw_constraints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L347) rule set
- [`'dma_area':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) / [`'dma_addr':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) / [`'dma_bytes':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) / [`'dma_buffer_p':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441): the active DMA buffer

### Related types

- [`'\<struct snd_pcm_hardware\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32): the driver-declared capability set copied into [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429)
- [`'\<struct snd_pcm_hw_constraints\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L347): the parameter masks, intervals, and rules the refinement walks
- [`'\<struct snd_pcm_sw_params\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433): the userspace software-parameter block copied into the SW-params fields
- [`'\<struct snd_pcm_mmap_status\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531): the layout of the read-only [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page
- [`'\<struct snd_pcm_mmap_control\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540): the layout of the read-write [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page

### Lifecycle and state helpers

- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): allocate the runtime and its two mmap pages at open
- [`'\<snd_pcm_detach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980): free the pages and the runtime at close
- [`'\<__snd_pcm_set_state\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725): write [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and its [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page copy together
- [`'\<snd_pcm_set_runtime_buffer\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263): set or clear the [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437)/[`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438)/[`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439)/[`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441) DMA group
- [`'\<snd_pcm_hw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754): write the HW-params group from the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408)
- [`'\<snd_pcm_sw_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953): write the SW-params group from the [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Runtime Pointer chapter describing each runtime field group a driver reads and writes
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): the audio-timestamp config and report fields and the hardware-pointer model
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated reference for the runtime and parameter-constraint helpers

## OTHER SOURCES

- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The runtime record itself has no character device; a driver reaches it through [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) and a userspace client maps the two shared pages. The constituent objects come up and go away at distinct points in the open.

| object | created by | lifetime |
|--------|------------|----------|
| [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) | [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) at open | freed by [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) at the last close |
| [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page, a [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) | [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) with [`alloc_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5063) | mapped read-only by the client, freed at detach |
| [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) page, a [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) | [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) with [`alloc_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5063) | mapped read-write by the client, freed at detach |
| [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) / [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) / [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) buffer fields | [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263) at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) | cleared at [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77), the owning [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) freed there |

## DETAILS

### The full record and its eight groups

The runtime gathers its fields into commented groups, each serving one stage of the stream's life:

```c
/* include/sound/pcm.h:362 */
struct snd_pcm_runtime {
	/* -- Status -- */
	snd_pcm_state_t state;		/* stream state */
	snd_pcm_state_t suspended_state; /* suspended stream state */
	struct snd_pcm_substream *trigger_master;
	struct timespec64 trigger_tstamp;	/* trigger timestamp */
	bool trigger_tstamp_latched;     /* trigger timestamp latched in low-level driver/hardware */
	int overrange;
	snd_pcm_uframes_t avail_max;
	snd_pcm_uframes_t hw_ptr_base;	/* Position at buffer restart */
	snd_pcm_uframes_t hw_ptr_interrupt; /* Position at interrupt time */
	unsigned long hw_ptr_jiffies;	/* Time when hw_ptr is updated */
	unsigned long hw_ptr_buffer_jiffies; /* buffer time in jiffies */
	snd_pcm_sframes_t delay;	/* extra delay; typically FIFO size */
	u64 hw_ptr_wrap;                /* offset for hw_ptr due to boundary wrap-around */

	/* -- HW params -- */
	snd_pcm_access_t access;	/* access mode */
	snd_pcm_format_t format;	/* SNDRV_PCM_FORMAT_* */
	snd_pcm_subformat_t subformat;	/* subformat */
	unsigned int rate;		/* rate in Hz */
	unsigned int channels;		/* channels */
	snd_pcm_uframes_t period_size;	/* period size */
	unsigned int periods;		/* periods */
	snd_pcm_uframes_t buffer_size;	/* buffer size */
	snd_pcm_uframes_t min_align;	/* Min alignment for the format */
	size_t byte_align;
	unsigned int frame_bits;
	unsigned int sample_bits;
	unsigned int info;
	unsigned int rate_num;
	unsigned int rate_den;
	unsigned int no_period_wakeup: 1;

	/* -- SW params; see struct snd_pcm_sw_params for comments -- */
	int tstamp_mode;
	unsigned int period_step;
	snd_pcm_uframes_t start_threshold;
	snd_pcm_uframes_t stop_threshold;
	snd_pcm_uframes_t silence_threshold;
	snd_pcm_uframes_t silence_size;
	snd_pcm_uframes_t boundary;
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

	/* -- private section -- */
	void *private_data;
	void (*private_free)(struct snd_pcm_runtime *runtime);

	/* -- hardware description -- */
	struct snd_pcm_hardware hw;
	struct snd_pcm_hw_constraints hw_constraints;
	...
	/* -- DMA -- */
	unsigned char *dma_area;	/* DMA area */
	dma_addr_t dma_addr;		/* physical bus address (not accessible from main CPU) */
	size_t dma_bytes;		/* size of DMA area */

	struct snd_dma_buffer *dma_buffer_p;	/* allocated buffer */
	unsigned int buffer_changed:1;	/* buffer allocation changed; set only in managed mode */

	/* -- audio timestamp config -- */
	struct snd_pcm_audio_tstamp_config audio_tstamp_config;
	struct snd_pcm_audio_tstamp_report audio_tstamp_report;
	struct timespec64 driver_tstamp;
	...
};
```

### The status group tracks the stream and its position

The first group holds the lifecycle [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), the [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) saved across a suspend, the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366) elected by a transition, and the hardware-pointer accounting. The running path updates [`hw_ptr_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L371) at each buffer restart and [`hw_ptr_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L372) at each interrupt, and [`delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L375) carries the extra latency a driver reports (typically the FIFO size). The [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) is the only field written through a dedicated helper, [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725), which copies it into the mmap [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) page in the same store:

```c
/* include/sound/pcm.h:725 */
static inline void __snd_pcm_set_state(struct snd_pcm_runtime *runtime,
				       snd_pcm_state_t state)
{
	runtime->state = state;
	runtime->status->state = state; /* copy for mmap */
}
```

The single store lands in both copies at once, the kernel-side field and the read-only mmap page a client reads without a syscall:

```
    __snd_pcm_set_state(): one write, two readers
    ─────────────────────────────────────────────
              snd_pcm_state_t state
                       │ single store
            ┌──────────┴──────────┐
            ▼                     ▼
       runtime->state        status->state
       (kernel reads)        (RO mmap page; the
                              client sees it with
                              no syscall)
```

### The HW-params group is fixed at hw_params

The hardware-parameter group records the format the stream runs at, written by [`snd_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L754) after the parameter refinement chooses a value for each. The same function fills [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L379), [`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L380), [`subformat`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L381), [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L383), [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L382), [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), [`periods`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385), and [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386) straight from the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408):

```c
/* sound/core/pcm_native.c:754 */
	runtime->access = params_access(params);
	runtime->format = params_format(params);
	runtime->subformat = params_subformat(params);
	runtime->channels = params_channels(params);
	runtime->rate = params_rate(params);
	runtime->period_size = params_period_size(params);
	runtime->periods = params_periods(params);
	runtime->buffer_size = params_buffer_size(params);
```

It then derives the geometry the core uses everywhere, the [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389) and [`sample_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L390) word sizes, the [`min_align`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L387) alignment, and the [`rate_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L392)/[`rate_den`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L393) exact-rate fraction. These fields stay fixed until a [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) returns the stream to OPEN.

```
    HW-params: negotiated values land in the runtime
    ───────────────────────────────────────────────────
    struct snd_pcm_hw_params
    ┌────────────────────────┐
    │ negotiated params      │──┐ params_xxx()
    └────────────────────────┘  │
                                ▼  snd_pcm_hw_params()
    runtime HW-params group
    ┌──────────────────────────────────────────────┐
    │ copied:  access, format, subformat,          │
    │          channels, rate, period_size,        │
    │          periods, buffer_size                │
    │ derived: frame_bits, sample_bits,            │
    │          min_align, rate_num / rate_den      │
    └──────────────────────────────────────────────┘
       fixed until hw_free returns the stream to OPEN
```

### The SW-params group is set without a driver op

The software parameters are the thresholds the core itself acts on, with no driver callback. [`snd_pcm_sw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L953) copies them out of a [`struct snd_pcm_sw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L433) into the runtime. [`start_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L399) is how much data must be queued before an implicit start, [`stop_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L400) is the available-bytes level that triggers an XRUN, and [`silence_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L401) with [`silence_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L402) control the auto-silencer that pre-fills the unplayed part of the ring:

```c
/* sound/core/pcm_native.c:953 */
		runtime->tstamp_mode = params->tstamp_mode;
		...
		runtime->period_step = params->period_step;
		runtime->control->avail_min = params->avail_min;
		runtime->start_threshold = params->start_threshold;
		runtime->stop_threshold = params->stop_threshold;
		runtime->silence_threshold = params->silence_threshold;
		runtime->silence_size = params->silence_size;
		params->boundary = runtime->boundary;
```

The [`boundary`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L403) is the wrap value of the application and hardware pointers, a large power-of-two multiple of the buffer size the core computes once so the pointers can advance monotonically before wrapping.

```
    PCM ring buffer: buffer_size split into periods
    ──────────────────────────────────────────────────────
    periods = buffer_size / period_size; pointers wrap at boundary

             hw_ptr              appl_ptr
               ▼                    ▼
    ┌──────┬──────┬──────┬──────┬──────┬──────┐
    │  P0  │  P1  │  P2  │  P3  │  P4  │  P5  │
    └──────┴──────┴──────┴──────┴──────┴──────┘
    hw_ptr → appl_ptr : filled, awaiting playback (hw drains)
    appl_ptr → hw_ptr : avail, free space the app fills
    stop_threshold   : avail level that signals an XRUN
    silence_size     : unplayed span the core pre-fills
```

### The mmap pages, the locking group, and the hardware description

The [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) and [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L413) pointers address the two page-aligned areas a client maps, the read-only [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) (carrying the state and hardware pointer) and the read-write [`struct snd_pcm_mmap_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L540) (carrying the application pointer and avail-min). The locking group serializes access: [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421) paired with the [`buffer_accessing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L422) counter keeps a buffer change from racing an in-flight transfer, the [`sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L417) and [`tsleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L418) wait queues block a polling and a transferring task, and [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L420) records that a [`sync_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) is owed. The hardware-description group is the [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) capability snapshot the driver's [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) op fills and the [`hw_constraints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L430) rule set the refinement walks to choose the HW-params values.

```
    The two mmap pages a client maps with no syscall
    ──────────────────────────────────────────────────
    runtime->status (read-only)    runtime->control (read-write)
    struct snd_pcm_mmap_status     struct snd_pcm_mmap_control
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │ state                    │   │ appl_ptr                 │
    │ hw_ptr                   │   │ avail_min                │
    └──────────────────────────┘   └──────────────────────────┘
       kernel writes, app reads       app writes, kernel reads
```

### The DMA group binds the active buffer

The DMA group is the runtime's view of the transfer buffer. [`snd_pcm_set_runtime_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1263) writes all four fields together at [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77) and clears them at [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L77), so [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) is the kernel virtual address the CPU and the userspace mmap use, [`dma_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L438) is the bus address the controller programs, [`dma_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L439) is the size, and [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441) points at the owning [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55). The [`buffer_changed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L442) bit is set in managed mode when the allocation moved, so a driver can re-derive any cached descriptor.

```
    The DMA group: one buffer, four views
    ────────────────────────────────────────────────
    set together by snd_pcm_set_runtime_buffer()
    ┌──────────────┬────────────────────────────────┐
    │ dma_area     │ CPU virtual addr (also mmap'd) │
    │ dma_addr     │ bus addr the controller uses   │
    │ dma_bytes    │ size of the DMA area           │
    │ dma_buffer_p │ owning struct snd_dma_buffer   │
    └──────────────┴────────────────────────────────┘
       written at hw_params, cleared at hw_free
```

### Allocation at attach and free at detach

The whole record is per-open. [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) allocates it on the open path, allocates the two mmap pages with [`alloc_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5063), initializes the locking group, and seeds the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307):

```c
/* sound/core/pcm.c:875 */
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
```

[`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) reverses it at close, freeing the two pages with [`free_pages_exact()`](https://elixir.bootlin.com/linux/v7.0/source/mm/page_alloc.c#L5481), destroying [`buffer_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L421), and freeing the record, after which [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478) is NULL again:

```c
/* sound/core/pcm.c:980 */
	free_pages_exact(runtime->status,
		       PAGE_ALIGN(sizeof(struct snd_pcm_mmap_status)));
	free_pages_exact(runtime->control,
		       PAGE_ALIGN(sizeof(struct snd_pcm_mmap_control)));
	kfree(runtime->hw_constraints.rules);
	...
	mutex_destroy(&runtime->buffer_mutex);
	snd_fasync_free(runtime->fasync);
	kfree(runtime);
```

So the runtime, and with it every negotiated parameter, mmap page, and DMA binding, lives exactly as long as one open of the substream. A driver reaches all of it through [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), and a userspace client reads the status and control halves directly through the two mmap pages without a syscall.

### ASoC fills the hardware description from the link's DAIs

On an x86-64 ACPI machine the [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) capability snapshot is not declared by a single driver but computed by the ASoC layer from the CPU and codec DAIs of the link. When a substream opens, ASoC's [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) calls [`soc_pcm_init_runtime_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L701), which takes the address of [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) and writes into it directly:

```c
/* sound/soc/soc-pcm.c:701 */
static void soc_pcm_init_runtime_hw(struct snd_pcm_substream *substream)
{
	struct snd_pcm_hardware *hw = &substream->runtime->hw;
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	u64 formats = hw->formats;
	...
	snd_soc_runtime_calc_hw(rtd, hw, substream->stream);

	if (formats)
		hw->formats &= formats;
}
```

[`snd_soc_runtime_calc_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L641) walks the link's CPU DAIs and then its codec DAIs, intersecting each DAI's supported channel counts, rates, and formats into the one [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32), so the [`hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L429) the core then uses to seed the constraint refinement is the subset both ends of the link can carry. The result is the same [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) a non-ASoC driver would copy in from a static capability table, only built at open from the merged DAI capabilities instead.
