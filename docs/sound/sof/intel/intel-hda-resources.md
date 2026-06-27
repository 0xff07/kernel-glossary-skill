# SOF Intel HDA stream resources

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The host-to-DSP audio path on an Intel x86-64 ACPI platform runs through the HD-Audio controller's host DMA engines, each represented by a [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) wrapped by a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) and again by the SOF-private [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576); [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) reads the controller GCAP register to build one such object per engine and links each onto the bus [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337), [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) and [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) hand one out at PCM open and return it at close, [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) programs the stream descriptor and the buffer-descriptor list (BDL) through [`hda_dsp_stream_setup_bdl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L112), and the SoundWire and DMIC back ends map their channels onto the same host stream tag through [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847).

```
    hdac_stream pool ─▶ assigned stream ─▶ host DMA / BDL  (Meteor / Lunar Lake)
    ────────────────────────────────────────────────────────────────────────

    bus->stream_list   (built once by hda_dsp_stream_init from GCAP)
    ┌───────────────────────────────────────────────────────────────────┐
    │ struct sof_intel_hda_stream  (one per host DMA engine)            │
    │   ┌────────────────────────────────────────────────────────────┐ │
    │   │ struct hdac_ext_stream hext_stream                         │ │
    │   │   pphc_addr ─▶ PP host regs   pplc_addr ─▶ PP link regs    │ │
    │   │   ┌──────────────────────────────────────────────────────┐ │ │
    │   │   │ struct hdac_stream hstream                           │ │ │
    │   │   │   sd_addr  stream_tag  index  direction  opened      │ │ │
    │   │   │   bdl (snd_dma_buffer)   posbuf                       │ │ │
    │   │   └───────────────────────────────────────────────────────┘│ │
    │   │   host_reserved   flags   ioc                              │ │
    │   └────────────────────────────────────────────────────────────┘ │
    └───────┬──────────────────────────────────────────────────────────┘
            │  hda_dsp_stream_get(direction)         (PCM open)
            ▼
    assigned hext_stream  ──▶  substream->runtime->private_data
            │  hda_dsp_stream_hw_params(hext_stream, dmab, params)
            ▼
    ┌──────────────────────┐        ┌───────────────────────────────────┐
    │ host DMA descriptor  │        │ BDL in hstream->bdl.area          │
    │ SDxBDPL/U ◀──────────┼────────┤ addr_l addr_h size ioc  (per BDLE)│
    │ SDxCBL = bufsize     │        │ entries cover dmab segments       │
    │ SDxFMT = format_val  │        └───────────────────────────────────┘
    │ SDxCTL.STRM = tag    │
    └──────────┬───────────┘
               │ stream split: host engine ◀──▶ link
               ▼
    ┌───────────────────────────┐   ┌────────────────────────────────────┐
    │ HDA codec / iDISP link    │   │ SoundWire / DMIC back end          │
    │ snd_hdac_ext_bus_link_    │   │ hdac_bus_eml_sdw_map_stream_ch     │
    │   set_stream_id(tag)      │   │   PCMSyCM: lchan hchan stream_id   │
    └───────────────────────────┘   └────────────────────────────────────┘
```

## SUMMARY

A SOF host DMA stream is three nested objects. The innermost is [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516), the generic HD-Audio core stream that records the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), the assigned [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), the stream-descriptor MMIO pointer [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), the BDL buffer [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518), and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L565) node on the bus [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337). The middle layer is [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47), which embeds the core stream as [`hstream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L48) and adds the processing-pipe host pointer [`pphc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L50) and link pointer [`pplc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L51) the DSP path uses to bind a host engine to a DSP pipeline. The outer layer is the SOF-private [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576), which embeds the ext stream as [`hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L578) and adds the [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) reservation flag and the [`ioc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L582) completion. The controller object, the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) that owns the [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) and is reached from a [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) through [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562), is owned by the sibling controller page; this page covers the per-stream DMA resources that hang off it.

The pool is built once at probe. [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) reads the controller GCAP register through [`snd_sof_dsp_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L73), extracts the playback and capture engine counts from bits 12 to 15 and 8 to 11, allocates the shared position buffer and CORB/RIRB rings with [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76), and then for each engine allocates a [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L36), sets the processing-pipe register pointers from the PP BAR, computes the stream-descriptor offset with [`SOF_STREAM_SD_OFFSET()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L591), assigns the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520) and [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), allocates the per-stream BDL, and links the core stream onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337). This is the SOF analog of the generic [`snd_hdac_ext_stream_init_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L90), which loops [`snd_hdac_ext_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L65) and in turn [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) for a legacy controller; SOF re-implements the loop so it can wrap each engine in its own [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) and place the descriptor pointers at the SOF BAR layout.

Assignment is by direction off the pool. At PCM open [`hda_dsp_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219) calls [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275), which forwards to [`_hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214) to walk [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) under [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364) and claim the first stream of the requested direction whose [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) flag is clear and whose [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) is zero, binding it into [`substream->runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437). At PCM hw_free the matching [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) forwards to [`_hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L287), which clears [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) on the stream matching the direction and tag.

The BDL and host-DMA setup is one function. [`hda_dsp_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L101) records the format, [`bufsize`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L522), and [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523) on the core stream, fetches the runtime DMA buffer from [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441), and calls [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554). That function resets the stream with [`hda_dsp_stream_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L353), builds the BDL with [`hda_dsp_stream_setup_bdl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L112) (which fills [`struct sof_intel_dsp_bdl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462) entries through [`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64)), programs the stream tag into SDxCTL, writes the cyclic buffer length SDxCBL, the format SDxFMT, the last-valid-index SDxLVI, and the BDL pointer SDxBDPL/SDxBDPU, and enables the position buffer. [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) starts and stops the DMA by toggling SDxCTL.RUN.

The link side reuses the same host stream tag. For a SoundWire back end, [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493) first allocates a host stream through the HDAudio path and then calls [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) to program the per-sublink PCMSyCM register with the channel range and the host [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) over the multi-link (eml/ALH) area of the same controller. The DMIC and SSP back ends route through [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372), which assigns a host stream the same way and carries the ALH node id into the DSP copier configuration.

## SPECIFICATIONS

The stream descriptor registers (SDxCTL, SDxSTS, SDxCBL, SDxLVI, SDxFMT, SDxBDPL, SDxBDPU), the GCAP global-capabilities field that reports the input and output stream counts, the buffer-descriptor list (BDL) with its address-low, address-high, length, and IOC fields, and the DMA position-in-buffer mechanism are defined by the Intel High Definition Audio Specification. The [`struct sof_intel_dsp_bdl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462) layout that [`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64) fills mirrors the BDL entry that specification describes, and the 4 KB BDLE boundary restriction the code enforces with [`align_bdle_4k`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L347) follows the same specification. The processing-pipe (PP) capability that supplies the [`pphc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L50) and [`pplc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L51) register windows and the multi-link (ML) capability that carries the PCMSyCM stream-channel-map register are Intel extensions to that specification. The SoundWire links whose channels map onto a host stream follow the MIPI SoundWire Specification, and the SOF DSP pipeline that the host stream feeds is defined by the Sound Open Firmware project rather than by a public hardware specification.

## LINUX KERNEL

### Stream resource types (hdaudio.h, hdaudio_ext.h, intel/hda.h)

- [`'\<struct hdac_stream\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516): one host DMA engine of the controller; carries the [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L517) back pointer, the BDL buffer [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518), the [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L519) position-buffer slot, the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), the [`bufsize`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L522) and [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523), the descriptor MMIO pointer [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), the assigned [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547), the [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550)/[`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551)/[`prepared`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L552) state bits, and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L565) node on [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337)
- [`'\<struct hdac_ext_stream\>':'include/sound/hdaudio_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47): wraps [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) as [`hstream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L48) and adds the processing-pipe host pointer [`pphc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L50), the link pointer [`pplc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L51), the [`decoupled`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L61) and [`link_locked`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L62)/[`link_prepared`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L63) flags, and the [`host_setup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L65) callback
- [`'\<struct sof_intel_hda_stream\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576): the SOF wrapper embedding [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) as [`hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L578); adds the [`sdev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L577) back pointer, the [`sof_intel_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L579) position-offset block, the [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) channel reservation, and the [`ioc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L582) completion
- [`'\<struct sof_intel_dsp_bdl\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462): one packed BDL entry with [`addr_l`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L463), [`addr_h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L464), [`size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L465), and [`ioc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L466) words
- [`'\<struct sof_intel_stream\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L209): the per-stream DSP position block holding [`posn_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L210), the mailbox offset at which the DSP reports the stream position

### Pool accessor macros (hdaudio_ext.h, intel/hda.h)

- [`'\<hdac_stream\>':'include/sound/hdaudio_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L70): reach the embedded [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) from a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47)
- [`'\<stream_to_hdac_ext_stream\>':'include/sound/hdaudio_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L71): the inverse container-of from a [`struct hdac_stream\>`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) back to its [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47)
- [`'\<hstream_to_sof_hda_stream\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L585): container-of from a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) to the enclosing [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576)
- [`'\<SOF_STREAM_SD_OFFSET\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L591): the stream-descriptor register offset for a stream of a given [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547)

### Generic HD-Audio core stream init (hda/core/stream.c, hda/core/ext/stream.c)

- [`'\<snd_hdac_stream_init\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94): the core library initializer; sets [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527) to `remap_addr + 0x20 * idx + 0x80`, sets [`sd_int_sta_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L536), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547), [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), and [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), and links the stream onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337)
- [`'\<snd_hdac_ext_stream_init\>':'sound/hda/core/ext/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L65): set [`pphc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L50) and [`pplc_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L51) from [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301) when present, then call [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94)
- [`'\<snd_hdac_ext_stream_init_all\>':'sound/hda/core/ext/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L90): allocate and initialize `num_stream` ext streams of one direction, choosing the host setup op by PCI device id; the loop SOF re-implements in [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895)

### SOF stream pool and assignment (intel/hda-stream.c)

- [`'\<hda_dsp_stream_init\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895): read GCAP for the playback/capture engine counts, allocate the position buffer and CORB/RIRB rings, and build one [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) per engine onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337); store the total in [`stream_max`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L524)
- [`'\<hda_dsp_stream_get\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) / [`'\<_hda_dsp_stream_get\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214): claim the first unused stream of a direction under [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364), skipping any with [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) set; mark it [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550)
- [`'\<hda_dsp_stream_put\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) / [`'\<_hda_dsp_stream_put\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L287): clear [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) on the stream matching the direction and tag, re-evaluating the DMI L1 gate across the remaining open streams
- [`'\<hda_dsp_stream_hw_params\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554): reset the stream, build the BDL, and program the stream descriptor (tag, SDxCBL, SDxFMT, SDxLVI, SDxBDPL/U) and the position buffer
- [`'\<hda_dsp_stream_setup_bdl\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L112): split the DMA buffer into periods and emit BDL entries through [`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64), forcing a two-period split when the firmware-load path passes a zero [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523)
- [`'\<hda_setup_bdle\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64): fill one or more [`struct sof_intel_dsp_bdl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462) entries for a buffer segment, capping each at the 4 KB boundary when [`align_bdle_4k`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L347) is set and advancing [`frags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L524)
- [`'\<hda_dsp_stream_reset\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L353): enter and exit stream reset by toggling SDxCTL.SRST and polling for the bit to set then clear
- [`'\<hda_dsp_stream_trigger\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392): start, stop, pause, and resume the host DMA by setting or clearing SDxCTL.RUN and the interrupt-enable bits, flipping [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551)
- [`'\<hda_dsp_stream_spib_config\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L187): program the software-position-in-buffer (SPIB) register from [`spib_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L529) when rewinds are disabled

### PCM and DAI consumers (intel/hda-pcm.c, intel/hda-dai.c, intel/hda-mlink.c)

- [`'\<hda_dsp_pcm_open\>':'sound/soc/sof/intel/hda-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219): the [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) op; call [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275), set period and format constraints, and store the assigned stream in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437)
- [`'\<hda_dsp_pcm_hw_params\>':'sound/soc/sof/intel/hda-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L101): the [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) op; record [`bufsize`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L522), [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523), and [`format_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L543), then call [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) and return the [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) to the core
- [`'\<sdw_hda_dai_hw_params\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493): the SoundWire back-end DAI hw_params; reset and then program the PCMSyCM channel map with [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) using the host stream tag
- [`'\<non_hda_dai_hw_params_data\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372): the shared non-HDA (SoundWire, DMIC, SSP) hw_params helper; assign a host stream via [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240) and fill the DSP copier DMA config with the [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546)
- [`'\<hdac_bus_eml_sdw_map_stream_ch\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847): write the multi-link PCMSyCM register for a SoundWire sublink, encoding the low and high channel and the host [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) and direction through [`hdaml_shim_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L360)

## KERNEL DOCUMENTATION

- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the HDAudio multi-link structure that carries the PCMSyCM stream-channel-map registers [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) programs for the SoundWire back ends
- [`Documentation/sound/hd-audio/notes.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/notes.rst): the HD-Audio controller and stream model the [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) pool implements
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end model that routes a host DMA stream through a DSP pipeline to an HDA, SoundWire, or DMIC back end
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM buffer and hw_params model the SOF [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) op sits under, including the External Hardware Buffers section
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the back-end DAI ops drive over the same controller

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware on the Linux kernel ASoC tree](https://github.com/thesofproject/linux)
- [Intel High Definition Audio Specification](https://www.intel.com/content/www/us/en/standards/high-definition-audio-specification.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The stream resources are created once at probe and then assigned per substream. The pool is the set of [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) objects on [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337), built by [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) and torn down with the device by [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L36) lifetime. An individual stream is loaned to a substream between [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) at open and [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) at hw_free, with its [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) bit acting as the in-use marker under [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364). The BDL and position buffer are owned by the stream for the device lifetime; only their contents change per hw_params.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) pool | [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) ([`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L36)) | probe to remove |
| per-stream BDL [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518) | [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) in [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) | probe to remove |
| shared position buffer [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L333) | [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) in [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) | probe to remove |
| stream assignment ([`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) set) | [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) at PCM open | until [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) at hw_free |
| BDL contents and descriptor program | [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) at hw_params | rewritten each hw_params |
| link channel map (PCMSyCM) | [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) from the back-end DAI | cleared and reprogrammed each hw_params |

The table below maps the substream action to the entry point and the stream-side effect.

| substream action | entry point | stream-side effect |
|------------------|-------------|--------------------|
| PCM open | [`hda_dsp_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219) | [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) claims a stream, binds it to [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`hda_dsp_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L101) | [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) builds the BDL and programs the descriptor |
| SoundWire/DMIC back-end hw_params | [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493) | [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) maps channels to the host tag |
| `SNDRV_PCM_TRIGGER_START` | [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) | set SDxCTL.RUN, mark [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343) | clear [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550), return the stream to the pool |

## DETAILS

### The three nested stream objects

The generic HD-Audio core stream is [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516). It is the unit the controller's host DMA engine corresponds to, and it carries the BDL buffer, the position-buffer slot, the direction, the descriptor MMIO pointer, the assigned stream tag and index, the state bits, and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L565) node by which it hangs off the bus:

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
	unsigned char stream_tag;	/* assigned stream */
	unsigned char index;		/* stream index */
	int assigned_key;		/* last device# key assigned to */

	bool opened:1;
	bool running:1;
	bool prepared:1;
	...
	struct list_head list;
	...
};
```

[`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518) is the per-stream buffer-descriptor list, a [`struct snd_dma_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L55) whose [`area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L57) holds the BDL entries and whose [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L58) is written into the SDxBDPL/SDxBDPU registers. [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L519) points into the shared position buffer the controller updates with the DMA position. [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527) is the base of this stream's descriptor register block. [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) is the in-use flag the get/put pair toggles.

The DSP path wraps each core stream in [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47), which adds the processing-pipe host (PPHC) and link (PPLC) register windows the controller uses to bind the host DMA stream to a DSP pipeline, plus the link-coupling state:

```c
/* include/sound/hdaudio_ext.h:47 */
struct hdac_ext_stream {
	struct hdac_stream hstream;

	void __iomem *pphc_addr;
	void __iomem *pplc_addr;

	u32 pphcllpl;
	u32 pphcllpu;
	u32 pphcldpl;
	u32 pphcldpu;

	u32 pplcllpl;
	u32 pplcllpu;

	bool decoupled:1;
	bool link_locked:1;
	bool link_prepared;

	int (*host_setup)(struct hdac_stream *, bool);

	struct snd_pcm_substream *link_substream;
};
```

Two macros walk between the two views. [`hdac_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L70) returns the embedded core stream, and [`stream_to_hdac_ext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L71) recovers the ext stream from a core-stream pointer, used wherever the PCM layer hands back the [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) it stashed:

```c
/* include/sound/hdaudio_ext.h:70 */
#define hdac_stream(s)		(&(s)->hstream)
#define stream_to_hdac_ext_stream(s) \
	container_of(s, struct hdac_ext_stream, hstream)
```

SOF wraps the ext stream once more in [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576), the object that actually populates [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337). It adds the [`sdev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L577) back pointer, the [`sof_intel_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L579) DSP-position block, the [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) channel reservation that fences a stream off from the get path, and a per-stream [`ioc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L582) completion:

```c
/* sound/soc/sof/intel/hda.h:576 */
struct sof_intel_hda_stream {
	struct snd_sof_dev *sdev;
	struct hdac_ext_stream hext_stream;
	struct sof_intel_stream sof_intel_stream;
	int host_reserved; /* reserve host DMA channel */
	u32 flags;
	struct completion ioc;
};
```

The container-of from the ext stream back to the SOF wrapper is [`hstream_to_sof_hda_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L585), the mirror of how [`_hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214) reaches the reservation flag from a list-walked core stream:

```c
/* sound/soc/sof/intel/hda.h:585 */
#define hstream_to_sof_hda_stream(hstream) \
	container_of(hstream, struct sof_intel_hda_stream, hext_stream)
```

### The generic core builds the pool with snd_hdac_stream_init

A legacy HD-Audio controller builds its pool through the core library. [`snd_hdac_ext_stream_init_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L90) loops over a direction's engines, allocates one [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) each, and assigns a setup op chosen by the PCI device id:

```c
/* sound/hda/core/ext/stream.c:90 */
int snd_hdac_ext_stream_init_all(struct hdac_bus *bus, int start_idx,
				 int num_stream, int dir)
{
	struct pci_dev *pci = to_pci_dev(bus->dev);
	int (*setup_op)(struct hdac_stream *, bool);
	int stream_tag = 0;
	int i, tag, idx = start_idx;

	if (pci->device == PCI_DEVICE_ID_INTEL_HDA_APL)
		setup_op = snd_hdac_apl_host_stream_setup;
	else
		setup_op = snd_hdac_stream_setup;

	for (i = 0; i < num_stream; i++) {
		struct hdac_ext_stream *hext_stream = kzalloc_obj(*hext_stream);
		if (!hext_stream)
			return -ENOMEM;
		tag = ++stream_tag;
		snd_hdac_ext_stream_init(bus, hext_stream, idx, dir, tag);
		idx++;
		hext_stream->host_setup = setup_op;
	}

	return 0;

}
```

Each pass calls [`snd_hdac_ext_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L65), which sets the processing-pipe register pointers from [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301) and then defers to [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) for the core fields:

```c
/* sound/hda/core/ext/stream.c:65 */
static void snd_hdac_ext_stream_init(struct hdac_bus *bus,
				     struct hdac_ext_stream *hext_stream,
				     int idx, int direction, int tag)
{
	if (bus->ppcap) {
		hext_stream->pphc_addr = bus->ppcap + AZX_PPHC_BASE +
				AZX_PPHC_INTERVAL * idx;

		hext_stream->pplc_addr = bus->ppcap + AZX_PPLC_BASE +
				AZX_PPLC_MULTI * bus->num_streams +
				AZX_PPLC_INTERVAL * idx;
	}

	hext_stream->decoupled = false;
	snd_hdac_stream_init(bus, &hext_stream->hstream, idx, direction, tag);
}
```

[`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) is where the core library computes the descriptor base from the remapped MMIO and links the stream onto the bus. According to the comment, the offset arithmetic is `SDI0=0x80, SDI1=0xa0, ... SDO3=0x160`:

```c
/* sound/hda/core/stream.c:94 */
void snd_hdac_stream_init(struct hdac_bus *bus, struct hdac_stream *azx_dev,
			  int idx, int direction, int tag)
{
	azx_dev->bus = bus;
	/* offset: SDI0=0x80, SDI1=0xa0, ... SDO3=0x160 */
	azx_dev->sd_addr = bus->remap_addr + (0x20 * idx + 0x80);
	/* int mask: SDI0=0x01, SDI1=0x02, ... SDO3=0x80 */
	azx_dev->sd_int_sta_mask = 1 << idx;
	azx_dev->index = idx;
	azx_dev->direction = direction;
	azx_dev->stream_tag = tag;
	snd_hdac_dsp_lock_init(azx_dev);
	list_add_tail(&azx_dev->list, &bus->stream_list);
	...
}
```

SOF does not call this loop. It re-implements the same per-engine construction inside [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) so it can wrap each engine in its own [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576) and place the descriptor and processing-pipe pointers at the SOF BAR layout rather than the legacy one.

### hda_dsp_stream_init reads GCAP and builds the SOF pool

[`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) reads the controller GCAP register through the HDA BAR, splits its capture (bits 8 to 11) and playback (bits 12 to 15) nibbles into engine counts, allocates the shared position buffer and the CORB/RIRB rings, and enters the per-engine loop:

```c
/* sound/soc/sof/intel/hda-stream.c:895 */
int hda_dsp_stream_init(struct snd_sof_dev *sdev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct hdac_ext_stream *hext_stream;
	struct hdac_stream *hstream;
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	struct sof_intel_hda_dev *sof_hda = bus_to_sof_hda(bus);
	int sd_offset;
	int i, num_playback, num_capture, num_total, ret;
	u32 gcap;

	gcap = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, SOF_HDA_GCAP);
	dev_dbg(sdev->dev, "hda global caps = 0x%x\n", gcap);

	/* get stream count from GCAP */
	num_capture = (gcap >> 8) & 0x0f;
	num_playback = (gcap >> 12) & 0x0f;
	num_total = num_playback + num_capture;
	...
	ret = snd_dma_alloc_pages(SNDRV_DMA_TYPE_DEV, &pci->dev,
				  SOF_HDA_DPIB_ENTRY_SIZE * num_total,
				  &bus->posbuf);
	...
	ret = snd_dma_alloc_pages(SNDRV_DMA_TYPE_DEV, &pci->dev,
				  PAGE_SIZE, &bus->rb);
	...
```

Each iteration allocates a [`struct sof_intel_hda_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L576), sets the processing-pipe register pointers from the PP BAR when present, computes the descriptor offset with [`SOF_STREAM_SD_OFFSET()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L591), assigns the direction and tag (capture engines take tags 1..num_capture and run first; playback engines follow), allocates the BDL, points [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L519) into the shared position buffer, and links the core stream onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337):

```c
/* sound/soc/sof/intel/hda-stream.c:895 (continued) */
	/* create capture and playback streams */
	for (i = 0; i < num_total; i++) {
		struct sof_intel_hda_stream *hda_stream;

		hda_stream = devm_kzalloc(sdev->dev, sizeof(*hda_stream),
					  GFP_KERNEL);
		if (!hda_stream)
			return -ENOMEM;

		hda_stream->sdev = sdev;
		init_completion(&hda_stream->ioc);

		hext_stream = &hda_stream->hext_stream;

		if (sdev->bar[HDA_DSP_PP_BAR]) {
			hext_stream->pphc_addr = sdev->bar[HDA_DSP_PP_BAR] +
				SOF_HDA_PPHC_BASE + SOF_HDA_PPHC_INTERVAL * i;

			hext_stream->pplc_addr = sdev->bar[HDA_DSP_PP_BAR] +
				SOF_HDA_PPLC_BASE + SOF_HDA_PPLC_MULTI * num_total +
				SOF_HDA_PPLC_INTERVAL * i;
		}

		hstream = &hext_stream->hstream;
		...
		hstream->bus = bus;
		hstream->sd_int_sta_mask = 1 << i;
		hstream->index = i;
		sd_offset = SOF_STREAM_SD_OFFSET(hstream);
		hstream->sd_addr = sdev->bar[HDA_DSP_HDA_BAR] + sd_offset;
		hstream->opened = false;
		hstream->running = false;

		if (i < num_capture) {
			hstream->stream_tag = i + 1;
			hstream->direction = SNDRV_PCM_STREAM_CAPTURE;
		} else {
			hstream->stream_tag = i - num_capture + 1;
			hstream->direction = SNDRV_PCM_STREAM_PLAYBACK;
		}

		/* mem alloc for stream BDL */
		ret = snd_dma_alloc_pages(SNDRV_DMA_TYPE_DEV, &pci->dev,
					  HDA_DSP_BDL_SIZE, &hstream->bdl);
		if (ret < 0) {
			dev_err(sdev->dev, "error: stream bdl dma alloc failed\n");
			return -ENOMEM;
		}

		hstream->posbuf = (__le32 *)(bus->posbuf.area +
			(hstream->index) * 8);

		list_add_tail(&hstream->list, &bus->stream_list);
	}

	/* store total stream count (playback + capture) from GCAP */
	sof_hda->stream_max = num_total;
	...
	return 0;
}
```

The descriptor offset is computed by [`SOF_STREAM_SD_OFFSET()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L591), which scales the stream [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547) by the per-stream descriptor size from a fixed base:

```c
/* sound/soc/sof/intel/hda.h:591 */
#define SOF_STREAM_SD_OFFSET(s) \
	(SOF_HDA_ADSP_SD_ENTRY_SIZE * ((s)->index) \
	 + SOF_HDA_ADSP_LOADER_BASE)
```

Back at the register that opened the function, GCAP carries the engine counts in two nibbles, the OSS field giving the playback count and the ISS field the capture count, their sum sizing the pool:

```
    GCAP global capabilities word (read by snd_sof_dsp_read)
    ──────────────────────────────────────────────────────────

    bit 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
       ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
       │    OSS    │    ISS    │       other..         │
       │  (15:12)  │  (11:8)   │         (7:0)         │
       └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘

    ISS (11:8)  ─▶ num_capture  = (gcap >>  8) & 0x0f
    OSS (15:12) ─▶ num_playback = (gcap >> 12) & 0x0f
    num_total  = num_playback + num_capture ─▶ sof_hda->stream_max
    one struct sof_intel_hda_stream is built per engine, 0..num_total-1
```

### hda_dsp_stream_get hands out a stream by direction

At PCM open [`hda_dsp_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L219) requests a stream of the substream direction. It sets the DMI L1 compatibility flag for playback and for capture streams marked d0i3-compatible, calls [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275), applies period and format constraints, and stores the assigned stream as the substream private data so hw_params can recover it:

```c
/* sound/soc/sof/intel/hda-pcm.c:219 */
int hda_dsp_pcm_open(struct snd_sof_dev *sdev,
		     struct snd_pcm_substream *substream)
{
	...
	if (hda_always_enable_dmi_l1 ||
	    direction == SNDRV_PCM_STREAM_PLAYBACK ||
	    spcm->stream[substream->stream].d0i3_compatible)
		flags |= SOF_HDA_STREAM_DMI_L1_COMPATIBLE;

	dsp_stream = hda_dsp_stream_get(sdev, direction, flags);
	if (!dsp_stream) {
		dev_err(sdev->dev, "error: no stream available\n");
		return -ENODEV;
	}
	...
	/* binding pcm substream to hda stream */
	substream->runtime->private_data = &dsp_stream->hstream;
	...
	return 0;
}
```

[`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) is a thin wrapper that forwards to [`_hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214) with `pair` false, the `pair` argument being the path that also locks a link stream for a coupled host-link transfer:

```c
/* sound/soc/sof/intel/hda-stream.c:275 */
struct hdac_ext_stream *
hda_dsp_stream_get(struct snd_sof_dev *sdev, int direction, u32 flags)
{
	return _hda_dsp_stream_get(sdev, direction, flags, false);
}
```

[`_hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214) walks [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) under [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364), takes the first stream of the requested direction whose [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) is clear, skips any whose [`host_reserved`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L580) flag fences it off, and marks the winner opened:

```c
/* sound/soc/sof/intel/hda-stream.c:214 */
static struct hdac_ext_stream *
_hda_dsp_stream_get(struct snd_sof_dev *sdev, int direction, u32 flags, bool pair)
{
	const struct sof_intel_dsp_desc *chip_info =  get_chip_info(sdev->pdata);
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct sof_intel_hda_stream *hda_stream;
	struct hdac_ext_stream *hext_stream = NULL;
	struct hdac_stream *s;

	spin_lock_irq(&bus->reg_lock);

	/* get an unused stream */
	list_for_each_entry(s, &bus->stream_list, list) {
		if (s->direction == direction && !s->opened) {
			hext_stream = stream_to_hdac_ext_stream(s);
			hda_stream = container_of(hext_stream,
						  struct sof_intel_hda_stream,
						  hext_stream);
			/* check if the host DMA channel is reserved */
			if (hda_stream->host_reserved)
				continue;

			if (pair && hext_stream->link_locked)
				continue;

			s->opened = true;

			if (pair)
				hext_stream->link_locked = true;

			break;
		}
	}

	spin_unlock_irq(&bus->reg_lock);
	...
	return hext_stream;
}
```

The release direction is [`hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L343), the symmetric wrapper over [`_hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L287):

```c
/* sound/soc/sof/intel/hda-stream.c:343 */
int hda_dsp_stream_put(struct snd_sof_dev *sdev, int direction, int stream_tag)
{
	return _hda_dsp_stream_put(sdev, direction, stream_tag, false);
}
```

[`_hda_dsp_stream_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L287) walks the list again under [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364), clears [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550) on the stream that matches both the direction and the [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), and in the same pass checks whether any remaining open stream is DMI-L1 incompatible so it can re-enable L1 when none is:

```c
/* sound/soc/sof/intel/hda-stream.c:287 */
static int _hda_dsp_stream_put(struct snd_sof_dev *sdev, int direction, int stream_tag, bool pair)
{
	...
	list_for_each_entry(s, &bus->stream_list, list) {
		hext_stream = stream_to_hdac_ext_stream(s);
		hda_stream = container_of(hext_stream, struct sof_intel_hda_stream, hext_stream);

		if (!s->opened)
			continue;

		if (s->direction == direction && s->stream_tag == stream_tag) {
			s->opened = false;
			found = true;
			if (pair)
				link_stream = hext_stream;
		} else if (!(hda_stream->flags & SOF_HDA_STREAM_DMI_L1_COMPATIBLE)) {
			dmi_l1_enable = false;
		}
	}
	...
	if (!found) {
		dev_err(sdev->dev, "%s: stream_tag %d not opened!\n",
			__func__, stream_tag);
		return -ENODEV;
	}
	...
	return 0;
}
```

### hw_params programs the descriptor and BDL

When the core delivers hw_params, [`hda_dsp_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-pcm.c#L101) recovers the assigned stream from [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L437) with [`stream_to_hdac_ext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L71), reads the managed DMA buffer from [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441), records the format, buffer size, and period size on the core stream, and calls [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554):

```c
/* sound/soc/sof/intel/hda-pcm.c:101 */
int hda_dsp_pcm_hw_params(struct snd_sof_dev *sdev,
			  struct snd_pcm_substream *substream,
			  struct snd_pcm_hw_params *params,
			  struct snd_sof_platform_stream_params *platform_params)
{
	struct hdac_stream *hstream = substream->runtime->private_data;
	struct hdac_ext_stream *hext_stream = stream_to_hdac_ext_stream(hstream);
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	struct snd_dma_buffer *dmab;
	int ret;

	hstream->substream = substream;

	dmab = substream->runtime->dma_buffer_p;
	...
	hstream->bufsize = params_buffer_bytes(params);
	hstream->period_bytes = params_period_bytes(params);
	hstream->no_period_wakeup  =
			(params->info & SNDRV_PCM_INFO_NO_PERIOD_WAKEUP) &&
			(params->flags & SNDRV_PCM_HW_PARAMS_NO_PERIOD_WAKEUP);

	ret = hda_dsp_stream_hw_params(sdev, hext_stream, dmab, params);
	if (ret < 0) {
		dev_err(sdev->dev, "error: hdac prepare failed: %d\n", ret);
		return ret;
	}
	...
	platform_params->stream_tag = hstream->stream_tag;

	return 0;
}
```

The managed DMA buffer comes from the ALSA-core PCM preallocation that the SOF [`pcm_construct`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L89) op sets up; this page consumes [`dma_buffer_p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L441) but does not own it.

[`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) is the program-the-hardware step. It optionally decouples host and link DMA in the PP control register, clears the stream status, resets the stream, builds the BDL, and then programs the stream descriptor. The first block clears state, decouples, and resets:

```c
/* sound/soc/sof/intel/hda-stream.c:554 */
int hda_dsp_stream_hw_params(struct snd_sof_dev *sdev,
			     struct hdac_ext_stream *hext_stream,
			     struct snd_dma_buffer *dmab,
			     struct snd_pcm_hw_params *params)
{
	const struct sof_intel_dsp_desc *chip = get_chip_info(sdev->pdata);
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct hdac_stream *hstream;
	int sd_offset, ret;
	u32 dma_start = SOF_HDA_SD_CTL_DMA_START;
	u32 mask;
	u32 run;
	...
	hstream = &hext_stream->hstream;
	sd_offset = SOF_STREAM_SD_OFFSET(hstream);
	mask = BIT(hstream->index);

	/* decouple host and link DMA if the DSP is used */
	if (!sdev->dspless_mode_selected)
		snd_sof_dsp_update_bits(sdev, HDA_DSP_PP_BAR, SOF_HDA_REG_PP_PPCTL,
					mask, mask);
	...
	/* stream reset */
	ret = hda_dsp_stream_reset(sdev, hstream);
	if (ret < 0)
		return ret;

	if (hstream->posbuf)
		*hstream->posbuf = 0;

	/* reset BDL address */
	snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
			  sd_offset + SOF_HDA_ADSP_REG_SD_BDLPL,
			  0x0);
	snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
			  sd_offset + SOF_HDA_ADSP_REG_SD_BDLPU,
			  0x0);
	...
```

The decouple write sets the PP control bit for this stream so the host DMA and the link run independently while the DSP processes the data between them; this is the split the diagram shows between the host engine and the link.

The second block builds the BDL and programs the descriptor with the stream tag, the cyclic buffer length, the format, the last-valid-index, and the BDL base address:

```c
/* sound/soc/sof/intel/hda-stream.c:554 (continued) */
	hstream->frags = 0;

	ret = hda_dsp_stream_setup_bdl(sdev, dmab, hstream);
	if (ret < 0) {
		dev_err(sdev->dev, "error: set up of BDL failed\n");
		return ret;
	}

	/* program stream tag to set up stream descriptor for DMA */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, sd_offset,
				SOF_HDA_CL_SD_CTL_STREAM_TAG_MASK,
				hstream->stream_tag <<
				SOF_HDA_CL_SD_CTL_STREAM_TAG_SHIFT);

	/* program cyclic buffer length */
	snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
			  sd_offset + SOF_HDA_ADSP_REG_SD_CBL,
			  hstream->bufsize);
	...
	/* program stream format */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
				sd_offset +
				SOF_HDA_ADSP_REG_SD_FORMAT,
				0xffff, hstream->format_val);
	...
	/* program last valid index */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
				sd_offset + SOF_HDA_ADSP_REG_SD_LVI,
				0xffff, (hstream->frags - 1));

	/* program BDL address */
	snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
			  sd_offset + SOF_HDA_ADSP_REG_SD_BDLPL,
			  (u32)hstream->bdl.addr);
	snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
			  sd_offset + SOF_HDA_ADSP_REG_SD_BDLPU,
			  upper_32_bits(hstream->bdl.addr));
	...
}
```

The SDxLVI value is `frags - 1`, the index of the last BDL entry, and [`hda_dsp_stream_setup_bdl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L112) sets [`frags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L524) as it emits entries, so the descriptor program depends on the BDL build having run first. The BDL base in [`hstream->bdl.addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518) is the bus address of the per-stream BDL buffer allocated at probe.

```
    Stream descriptor program at sd_offset = SOF_STREAM_SD_OFFSET(hstream)
    ───────────────────────────────────────────────────────────────────────

    register at sd_offset + ...        written value
    ────────────────────────────────   ───────────────────────────────
    sd_offset (CTL.STREAM_TAG)     ◀── hstream->stream_tag
    SOF_HDA_ADSP_REG_SD_CBL        ◀── hstream->bufsize
    SOF_HDA_ADSP_REG_SD_FORMAT     ◀── hstream->format_val
    SOF_HDA_ADSP_REG_SD_LVI        ◀── hstream->frags - 1
    SOF_HDA_ADSP_REG_SD_BDLPL      ◀── lower_32_bits(hstream->bdl.addr)
    SOF_HDA_ADSP_REG_SD_BDLPU      ◀── upper_32_bits(hstream->bdl.addr)

    data dependency: hda_dsp_stream_setup_bdl sets hstream->frags first,
    so SD_LVI (= frags - 1) is valid only after the BDL has been built
```

### hda_dsp_stream_setup_bdl splits the buffer into BDL entries

[`hda_dsp_stream_setup_bdl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L112) computes the period count from [`bufsize`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L522) and [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523), points a [`struct sof_intel_dsp_bdl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462) cursor at the BDL buffer area, and emits one period per loop iteration through [`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64). When [`period_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L523) is zero, which happens for firmware or library loading, it forces a single contiguous buffer into two periods so the descriptor has at least two BDL entries:

```c
/* sound/soc/sof/intel/hda-stream.c:112 */
int hda_dsp_stream_setup_bdl(struct snd_sof_dev *sdev,
			     struct snd_dma_buffer *dmab,
			     struct hdac_stream *hstream)
{
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	struct sof_intel_dsp_bdl *bdl;
	int i, offset, period_bytes, periods;
	int remain, ioc;

	period_bytes = hstream->period_bytes;
	...
	if (!period_bytes) {
		unsigned int chunk_size;

		chunk_size = snd_sgbuf_get_chunk_size(dmab, 0, hstream->bufsize);

		period_bytes = hstream->bufsize;
		...
		if (chunk_size == hstream->bufsize)
			period_bytes /= 2;
	}

	periods = hstream->bufsize / period_bytes;
	...
	remain = hstream->bufsize % period_bytes;
	if (remain)
		periods++;

	/* program the initial BDL entries */
	bdl = (struct sof_intel_dsp_bdl *)hstream->bdl.area;
	offset = 0;
	hstream->frags = 0;
	...
	for (i = 0; i < periods; i++) {
		if (i == (periods - 1) && remain)
			/* set the last small entry */
			offset = hda_setup_bdle(sdev, dmab,
						hstream, &bdl, offset,
						remain, 0);
		else
			offset = hda_setup_bdle(sdev, dmab,
						hstream, &bdl, offset,
						period_bytes, ioc);
	}

	return offset;
}
```

According to the comment on the zero-period branch, the HDA specification requires the SDxLVI value to be at least one, so a transfer needs at least two BDL entries, which is why a single contiguous firmware buffer is split in two.

Each [`struct sof_intel_dsp_bdl`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L462) entry is a packed quad of little-endian words, the address low and high, the segment length, and the interrupt-on-completion flag:

```c
/* sound/soc/sof/intel/hda.h:462 */
struct sof_intel_dsp_bdl {
	__le32 addr_l;
	__le32 addr_h;
	__le32 size;
	__le32 ioc;
} __attribute((packed));
```

[`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64) fills these entries for one buffer segment. It loops while the segment has bytes left, reads each chunk's bus address from the DMA buffer with [`snd_sgbuf_get_addr()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L97), caps a chunk at the 4 KB boundary when the controller sets [`align_bdle_4k`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L347), and sets the IOC bit only on the final entry of a period that needs a wakeup:

```c
/* sound/soc/sof/intel/hda-stream.c:64 */
static int hda_setup_bdle(struct snd_sof_dev *sdev,
			  struct snd_dma_buffer *dmab,
			  struct hdac_stream *hstream,
			  struct sof_intel_dsp_bdl **bdlp,
			  int offset, int size, int ioc)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct sof_intel_dsp_bdl *bdl = *bdlp;

	while (size > 0) {
		dma_addr_t addr;
		int chunk;

		if (hstream->frags >= HDA_DSP_MAX_BDL_ENTRIES) {
			dev_err(sdev->dev, "error: stream frags exceeded\n");
			return -EINVAL;
		}

		addr = snd_sgbuf_get_addr(dmab, offset);
		/* program BDL addr */
		bdl->addr_l = cpu_to_le32(lower_32_bits(addr));
		bdl->addr_h = cpu_to_le32(upper_32_bits(addr));
		/* program BDL size */
		chunk = snd_sgbuf_get_chunk_size(dmab, offset, size);
		/* one BDLE should not cross 4K boundary */
		if (bus->align_bdle_4k) {
			u32 remain = 0x1000 - (offset & 0xfff);

			if (chunk > remain)
				chunk = remain;
		}
		bdl->size = cpu_to_le32(chunk);
		/* only program IOC when the whole segment is processed */
		size -= chunk;
		bdl->ioc = (size || !ioc) ? 0 : cpu_to_le32(0x01);
		bdl++;
		hstream->frags++;
		offset += chunk;
	}

	*bdlp = bdl;
	return offset;
}
```

A single scatter-gather buffer can span multiple non-contiguous pages, so [`hda_setup_bdle()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L64) may emit several BDL entries for one period; [`frags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L524) counts the total entries written and bounds them at [`HDA_DSP_MAX_BDL_ENTRIES`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L417).

```
    BDL ring: DMA buffer split into period descriptor entries
    ────────────────────────────────────────────────────────────

    DMA buffer (dmab, hstream->bufsize bytes)
    ┌───────────┬───────────┬───────────┬───────────┐
    │ period 0  │ period 1  │ period 2  │ ...       │
    │period_byte│period_byte│period_byte│ (periods) │
    └─────┬─────┴─────┬─────┴─────┬─────┴─────┬─────┘
          │           │           │           │
          ▼           ▼           ▼           ▼
    BDL in hstream->bdl.area  (struct sof_intel_dsp_bdl[])
    ┌─────────────────────────────────────────────────────────┐
    │ BDLE = { addr_l, addr_h, size, ioc }   (one per chunk)   │
    │   a period may emit >1 BDLE when its pages are split     │
    │   align_bdle_4k caps each chunk at a 4 KB boundary       │
    │   ioc = 1 only on the last BDLE of a wakeup period       │
    └─────────────────────────────────────────────────────────┘

    periods = bufsize / period_bytes   (+1 when a remainder is left)
    hstream->frags = total BDLE written ;   SD_LVI = frags - 1
    period_bytes == 0 (fw load) ─▶ buffer forced into two periods
```

### hda_dsp_stream_reset and hda_dsp_stream_trigger move the DMA

Before the descriptor is reprogrammed, [`hda_dsp_stream_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L353) takes the stream through the SDxCTL.SRST reset handshake, setting the reset bit and polling until it reads back set, then clearing it and polling until it reads back clear:

```c
/* sound/soc/sof/intel/hda-stream.c:353 */
static int hda_dsp_stream_reset(struct snd_sof_dev *sdev, struct hdac_stream *hstream)
{
	int sd_offset = SOF_STREAM_SD_OFFSET(hstream);
	int timeout = HDA_DSP_STREAM_RESET_TIMEOUT;
	u32 val;

	/* enter stream reset */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, sd_offset, SOF_STREAM_SD_OFFSET_CRST,
				SOF_STREAM_SD_OFFSET_CRST);
	do {
		val = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, sd_offset);
		if (val & SOF_STREAM_SD_OFFSET_CRST)
			break;
	} while (--timeout);
	...
	/* exit stream reset and wait to read a zero before reading any other register */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, sd_offset, SOF_STREAM_SD_OFFSET_CRST, 0x0);

	/* wait for hardware to report that stream is out of reset */
	udelay(3);
	do {
		val = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, sd_offset);
		if ((val & SOF_STREAM_SD_OFFSET_CRST) == 0)
			break;
	} while (--timeout);
	...
	return 0;
}
```

Once the descriptor is programmed, [`hda_dsp_stream_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L392) starts and stops the host DMA. On start it sets the interrupt-enable in SOF_HDA_INTCTL and SDxCTL.RUN, polls for RUN to read back, and marks [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551); on stop it clears RUN, polls for it to clear, acknowledges the status, and clears [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551):

```c
/* sound/soc/sof/intel/hda-stream.c:392 */
int hda_dsp_stream_trigger(struct snd_sof_dev *sdev,
			   struct hdac_ext_stream *hext_stream, int cmd)
{
	struct hdac_stream *hstream = &hext_stream->hstream;
	int sd_offset = SOF_STREAM_SD_OFFSET(hstream);
	u32 dma_start = SOF_HDA_SD_CTL_DMA_START;
	int ret = 0;
	u32 run;

	/* cmd must be for audio stream */
	switch (cmd) {
	...
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
	...
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
					sd_offset,
					SOF_HDA_SD_CTL_DMA_START |
					SOF_HDA_CL_DMA_SD_INT_MASK, 0x0);
		...
		if (ret >= 0) {
			snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
					  sd_offset + SOF_HDA_ADSP_REG_SD_STS,
					  SOF_HDA_CL_DMA_SD_INT_MASK);

			hstream->running = false;
			snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
						SOF_HDA_INTCTL,
						1 << hstream->index, 0x0);
		}
		break;
	...
	}
	...
	return ret;
}
```

### The link side maps channels onto the host stream tag

A SoundWire or DMIC back end does not get its own host DMA stream pool; it borrows a host stream and tells the multi-link hardware which channels of that host stream tag belong to a given sublink. For SoundWire, [`sdw_hda_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L493) first resets the PCMSyCM map, then allocates a host stream through [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372), and finally programs the channel mask with the host [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) recovered with [`hdac_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L70):

```c
/* sound/soc/sof/intel/hda-dai.c:493 */
int sdw_hda_dai_hw_params(struct snd_pcm_substream *substream,
			  struct snd_pcm_hw_params *params,
			  struct snd_soc_dai *cpu_dai,
			  int link_id,
			  int intel_alh_id)
{
	...
	/*
	 * reset the PCMSyCM registers to handle a prepare callback when the PCM is restarted
	 * due to xruns or after a call to snd_pcm_drain/drop()
	 */
	ret = hdac_bus_eml_sdw_map_stream_ch(sof_to_bus(sdev), link_id, cpu_dai->id,
					     0, 0, substream->stream);
	...
	data.dai_index = (link_id << 8) | cpu_dai->id;
	data.dai_node_id = intel_alh_id;
	ret = non_hda_dai_hw_params_data(substream, params, cpu_dai, &data, flags);
	...
	hext_stream = ops->get_hext_stream(sdev, cpu_dai, substream);
	if (!hext_stream)
		return -ENODEV;
	...
	ch_mask = GENMASK(params_channels(params) - 1, 0);

	ret = hdac_bus_eml_sdw_map_stream_ch(sof_to_bus(sdev), link_id, cpu_dai->id,
					     ch_mask,
					     hdac_stream(hext_stream)->stream_tag,
					     substream->stream);
	...
	return 0;
}
```

The `intel_alh_id` argument is the Audio-Link-Hub (ALH) node id this back end uses; it is carried into [`data.dai_node_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L95) and on into the DSP copier configuration that [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) fills, so the firmware knows which ALH stream the host tag feeds. The two calls to [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) bracket the allocation, the first clearing any stale map, the second installing the real channel range and tag.

[`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) is the shared body for the non-HDA back ends. It assigns a host stream by calling [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240), recovers the [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546) from the resulting [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47), and records `stream_id - 1` as the DSP DMA channel id in the copier TLV:

```c
/* sound/soc/sof/intel/hda-dai.c:372 */
static int non_hda_dai_hw_params_data(struct snd_pcm_substream *substream,
				      struct snd_pcm_hw_params *params,
				      struct snd_soc_dai *cpu_dai,
				      struct snd_sof_dai_config_data *data,
				      unsigned int flags)
{
	...
	/* use HDaudio stream handling */
	ret = hda_dai_hw_params_data(substream, params, cpu_dai, data, flags);
	if (ret < 0) {
		dev_err(cpu_dai->dev, "%s: hda_dai_hw_params_data failed: %d\n", __func__, ret);
		return ret;
	}
	...
	hstream = &hext_stream->hstream;
	stream_id = hstream->stream_tag;
	...
	dma_config->dma_method = SOF_IPC4_DMA_METHOD_HDA;
	dma_config->pre_allocated_by_host = 1;
	dma_config->dma_channel_id = stream_id - 1;
	dma_config->stream_id = stream_id;
	...
	return 0;
}
```

The host-stream assignment those back ends share runs inside [`hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L240) and [`hda_link_dma_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L166), which obtain a host stream through the DAI widget ops (whose [`get_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1028) and [`assign_hext_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L1031) ultimately reach the same [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) pool) and set the link stream id for playback with [`snd_hdac_ext_bus_link_set_stream_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/controller.c#L278).

```
    One host stream tag T, many back ends (link side borrows the tag)
    ───────────────────────────────────────────────────────────────────

    hda_dsp_stream_get ─▶ host DMA stream, hstream->stream_tag = T
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ HDA codec /      │ │ SoundWire sublink│ │ DMIC / SSP       │
    │ iDISP link       │ │                  │ │ (DSP-offloaded)  │
    │ link_set_        │ │ PCMSyCM map:     │ │ copier DMA cfg:  │
    │   stream_id(T)   │ │   ch_mask + T    │ │   stream_id = T  │
    └──────────────────┘ └──────────────────┘ └──────────────────┘

    ch_mask = GENMASK(params_channels - 1, 0)
    dma_config->stream_id      = T
    dma_config->dma_channel_id = T - 1      (stream_id - 1)
```

### hdac_bus_eml_sdw_map_stream_ch programs the PCMSyCM register

[`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) finds the SoundWire multi-link descriptor, computes the address of the per-sublink PCMSyCM register, and writes the low and high channel and the host stream id and direction through [`hdaml_shim_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L360). The `y` argument is the PDI (FIFO) index from the PCMSyCM register naming:

```c
/* sound/soc/sof/intel/hda-mlink.c:847 */
int hdac_bus_eml_sdw_map_stream_ch(struct hdac_bus *bus, int sublink, int y,
				   int channel_mask, int stream_id, int dir)
{
	struct hdac_ext2_link *h2link;
	u16 __iomem *pcmsycm;
	int hchan;
	int lchan;
	u16 val;

	h2link = find_ext2_link(bus, true, AZX_REG_ML_LEPTR_ID_SDW);
	if (!h2link)
		return -ENODEV;

	pcmsycm = h2link->base_ptr + h2link->shim_offset +
		h2link->instance_offset * sublink +
		AZX_REG_SDW_SHIM_PCMSyCM(y);

	if (channel_mask) {
		hchan = __fls(channel_mask);
		lchan = __ffs(channel_mask);
	} else {
		hchan = 0;
		lchan = 0;
	}

	scoped_guard(mutex, &h2link->eml_lock)
		hdaml_shim_map_stream_ch(pcmsycm, lchan, hchan, stream_id, dir);
	...
	return 0;
}
```

The register offset comes from [`AZX_REG_SDW_SHIM_PCMSyCM()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L80), which steps by 4 bytes per PDI index `y`:

```c
/* sound/soc/sof/intel/hda-mlink.c:80 */
#define AZX_REG_SDW_SHIM_PCMSyCM(y)			(0x16 + 0x4 * (y))
```

[`find_ext2_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L469) is how the SoundWire sublink is located. It walks the bus [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378) (the multi-link list the controller page describes) for the alternate link whose element id is the SoundWire id, so the channel map is written into the SoundWire area of the same controller's multi-link block:

```c
/* sound/soc/sof/intel/hda-mlink.c:469 */
static struct hdac_ext2_link *
find_ext2_link(struct hdac_bus *bus, bool alt, int elid)
{
	struct hdac_ext_link *hlink;

	list_for_each_entry(hlink, &bus->hlink_list, list) {
		struct hdac_ext2_link *h2link = hdac_ext_link_to_ext2(hlink);

		if (h2link->alt == alt && h2link->elid == elid)
			return h2link;
	}

	return NULL;
}
```

[`hdaml_shim_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L360) packs the PCMSyCM register's four fields, the low channel in bits 0 to 3, the high channel in bits 4 to 7, the stream id in bits 8 to 13, and the direction in bit 15:

```c
/* sound/soc/sof/intel/hda-mlink.c:360 */
static void hdaml_shim_map_stream_ch(u16 __iomem *pcmsycm, int lchan, int hchan,
				     int stream_id, int dir)
{
	u16 val;

	val = readw(pcmsycm);

	u16p_replace_bits(&val, lchan, GENMASK(3, 0));
	u16p_replace_bits(&val, hchan, GENMASK(7, 4));
	u16p_replace_bits(&val, stream_id, GENMASK(13, 8));
	u16p_replace_bits(&val, dir, BIT(15));

	writew(val, pcmsycm);
}
```

The stream id written here is the host stream tag the host DMA engine carries, so the PCMSyCM register is what couples the SoundWire sublink's channel range to the host DMA stream the get/hw_params path set up. On a platform built without the multi-link support, [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) is the inline stub in [`include/sound/hda-mlink.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda-mlink.h#L166) that returns 0.

```
    PCMSyCM stream-channel-map register (u16, per SoundWire sublink)
    ───────────────────────────────────────────────────────────────────

    bit 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
       ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
       │d │--│    stream_id    │   hchan   │   lchan   │
       │15│  │     (13:8)      │   (7:4)   │   (3:0)   │
       └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘

    lchan = __ffs(channel_mask)        ─▶ bits 3:0    GENMASK(3, 0)
    hchan = __fls(channel_mask)        ─▶ bits 7:4    GENMASK(7, 4)
    stream_id = host stream tag        ─▶ bits 13:8   GENMASK(13, 8)
    dir                                ─▶ bit 15      BIT(15)

    register address (per sublink, PDI index y):
      pcmsycm = base_ptr + shim_offset
              + instance_offset * sublink
              + AZX_REG_SDW_SHIM_PCMSyCM(y)     where = 0x16 + 0x4 * y
```

### Reference platform: Meteor Lake and Lunar Lake

On Meteor Lake (ACE 1.0) and Lunar Lake (ACE 2.0) the pool is built the same way; the GCAP-reported engine counts and the descriptor program are identical, and the [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) versus [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) IP version only changes details around the stream path rather than the stream objects. [`_hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L214) reads the version through [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213) and skips the DMI Link L1 disable on the ACE generations, since the capture xrun workaround it guards is not needed there:

```c
/* sound/soc/sof/intel/hda-stream.c:214 (tail) */
	if (chip_info->hw_ip_version < SOF_INTEL_ACE_1_0 &&
	    !(flags & SOF_HDA_STREAM_DMI_L1_COMPATIBLE)) {
		snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
					HDA_VS_INTEL_EM2,
					HDA_VS_INTEL_EM2_L1SEN, 0);
		hda->l1_disabled = true;
	}
```

The difference that matters for the link side is which back ends use the PCMSyCM map at all. On Lunar Lake the SoundWire registers are mapped in the HDAudio multi-link areas, so [`hdac_bus_eml_sdw_map_stream_ch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L847) writes the eml/ALH PCMSyCM register described above, and the DMIC and SSP back ends are offloaded to the DSP and reach the host stream through the same [`non_hda_dai_hw_params_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L372) path. On Meteor Lake the SoundWire path uses the same multi-link channel map, while the DMIC and SSP back ends keep the default ASoC handling rather than the DSP-offloaded host-stream path. In every case the host stream tag assigned by [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275) and programmed into the descriptor by [`hda_dsp_stream_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L554) is the identifier the link side maps its channels onto, so one host DMA engine drives a back end on an HDA codec link, a SoundWire sublink, or a DMIC endpoint without the stream pool itself changing.
