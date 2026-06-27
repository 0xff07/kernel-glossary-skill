# Legacy HDA controller (azx)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The legacy azx controller is the classic [`snd_hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2841) PCI driver path that wraps an Intel HD-Audio controller in [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) (which embeds the core [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) through a codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38)), driving the same controller silicon as SOF but exposing it directly as ALSA PCM devices. The PCI [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback [`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) allocates the chip with [`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769), maps the BAR and brings up the chip in [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) through [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552) and [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018), builds the codecs with [`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186), and binds host DMA streams to PCM substreams in [`azx_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574) by way of [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44). This is the non-SOF path; modern Intel platforms boot Sound Open Firmware and bring the same controller up through the SOF Intel driver instead, but the azx controller documented here remains the driver for codec-only HD-Audio hardware and for parts where the DSP is not enabled.

```
    Legacy azx controller object (one PCI device, x86-64 ACPI)
    ──────────────────────────────────────────────────────────

    struct azx                                  (the legacy wrapper)
    ┌───────────────────────────────────────────────────────────────┐
    │  driver_type   driver_caps   num_streams   ops                │
    │  pcm_list ─▶ azx_pcm                                          │
    │  struct hda_bus bus       (codec list, pci back pointer)      │
    │  ┌────────────────────────────────────────────────────────┐  │
    │  │  struct hdac_bus core   (host HD-Audio controller)     │  │
    │  │    remap_addr   ppcap   mlcap   codec_mask             │  │
    │  │    corb / rirb   stream_list   ops ─▶ bus_core_ops     │  │
    │  └──┬──────────────────┬─────────────────────┬────────────┘ │
    └─────┼──────────────────┼─────────────────────┼──────────────┘
          │ codec_mask       │ stream_list         │ ops.command
          ▼                  ▼                     ▼
    ┌───────────┐      ┌───────────────┐    ┌──────────────────┐
    │ hda_codec │      │ struct azx_dev│    │ azx_send_cmd /   │
    │ per slot  │      │  embeds       │    │ azx_get_response │
    │ (codec    │      │  hdac_stream  │    │ (CORB/RIRB verb  │
    │  page)    │      │  core[N]      │    │  transport)      │
    └───────────┘      └───────────────┘    └──────────────────┘

    bring-up order (off the PCI .probe, deferred to a work item):
      azx_probe ─▶ azx_create ─▶ schedule probe_work
      probe_work ─▶ azx_probe_continue ─▶ azx_first_init
      azx_first_init ─▶ azx_init_streams ─▶ hda_intel_init_chip ─▶ azx_init_chip
      azx_probe_continue ─▶ azx_probe_codecs ─▶ azx_codec_configure ─▶ register
```

## SUMMARY

The legacy azx controller is the in-memory image of one HD-Audio PCI function as the [`snd_hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2841) driver sees it. [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) holds the chip-type fields [`driver_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L103) and [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104), the stream counts [`playback_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L105), [`capture_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L107) and [`num_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L109), the register-access function pointer struct [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L113), the [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L123) of allocated PCM devices, and an embedded [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) named [`bus`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L96) whose [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member is the core [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291). The macro [`azx_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L155) reaches that nested bus, and [`bus_to_azx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L156) is the inverse [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) used in the bus callbacks. Each host DMA engine the driver hands to a PCM is a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57), a thin wrapper that embeds the core [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L58) member and adds two legacy flag bits, [`irq_pending`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L60) and [`insufficient`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L66).

The PCI bind runs in two stages. The [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback [`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) creates the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L92), allocates the chip with [`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769) (which calls [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150) to set up the embedded bus over [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) with the [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928) verb function pointer struct), and then defers the rest to a work item. [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333) runs [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852), which maps BAR0 with [`pcim_iomap_region()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h), reads the GCAP stream counts, builds one [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) per engine with [`azx_init_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276), and resets the controller through [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552) and [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018), the wrapper over the core [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609). [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333) then enumerates codecs with [`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186) (which calls [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947) for every bit set in [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320)), configures them with [`azx_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243), and registers the card with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c).

The PCM side binds a host DMA stream to each substream. The codec layer attaches a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470) for every codec PCM through [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692), installing the [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L669) function pointer struct on each direction with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510). At open time [`azx_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574) calls [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44), which wraps the core [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361) and converts the returned [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) back to a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) with [`stream_to_azx_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L70); [`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152) programs the SDn registers with [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257); [`azx_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L201) starts and stops the engine with [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) and [`snd_hdac_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c); and [`azx_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L91) gives the stream back with [`azx_release_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L55). The reference platform is an Intel azx controller on x86-64 ACPI, bound through the [`struct pci_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h) [`azx_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2841).

## SPECIFICATIONS

The controller register set, the GCAP stream-count fields, the buffer-descriptor list (BDL), the position buffer, the CORB/RIRB command rings, and the per-stream descriptor (SDn) blocks the azx driver programs are defined by the Intel High Definition Audio Specification. [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) reads the stream counts straight out of the GCAP register and masks 64-bit DMA support with [`AZX_GCAP_64OK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L15) per that specification, and the SDn programming the PCM ops drive runs through the core [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) and [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130). The codec verb protocol the [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928) function pointer struct implements is the command/response transport of the same specification.

- Intel High Definition Audio Specification, section 3.3: controller register set (GCAP, GCTL, INTCTL, INTSTS, CORB/RIRB, stream descriptors) read and programmed by [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) and [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018)
- Intel High Definition Audio Specification, section 3.3.2: global capabilities (GCAP), whose ISS/OSS fields [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) decodes into [`capture_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L107) and [`playback_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L105)
- Intel High Definition Audio Specification, section 3.3.36: stream descriptor (SDn) register block programmed by [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) on behalf of [`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152)
- Intel High Definition Audio Specification, section 4.4.1: command output ring buffer (CORB) and response input ring buffer (RIRB) driven by the [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928) [`command`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L245) and [`get_response`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L247) callbacks

## LINUX KERNEL

### Legacy controller objects (sound/hda/common/hda_controller.h)

- [`'\<struct azx\>':'sound/hda/common/hda_controller.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95): the legacy controller wrapper; embeds [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) as [`bus`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L96) and holds [`driver_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L103), [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104), [`num_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L109), the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L113) function pointer struct, the [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L123), and the position callbacks [`get_position`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L116)
- [`'\<struct azx_dev\>':'sound/hda/common/hda_controller.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57): a host DMA engine; embeds [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) as [`core`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L58) and adds the [`irq_pending`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L60) and [`insufficient`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L66) flag bits
- [`'\<struct azx_pcm\>':'sound/hda/common/hda_controller.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84): the per-PCM record on [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L123), tying a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470) to its [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) and [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164)
- [`'\<struct hda_controller_ops\>':'sound/hda/common/hda_controller.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L75): the bus-glue function pointer struct with [`disable_msi_reset_irq`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L77), [`position_check`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L79), and [`link_power`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L81)
- [`'\<struct hda_intel\>':'sound/hda/controllers/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L9): the Intel-specific outer struct embedding [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) as [`chip`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L10) and carrying the deferred-probe [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17) and [`vga_switcheroo`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L28) state
- [`azx_bus`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L155) / [`bus_to_azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L156): reach the embedded [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) from a [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) and recover the chip from a bus pointer
- [`azx_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L69) / [`stream_to_azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L70): convert between a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) and its embedded [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516)

### PCI probe and chip bring-up (sound/hda/controllers/intel.c)

- [`'\<azx_probe\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127): the [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback of [`azx_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2841); create the card, call [`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769), and schedule [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17)
- [`'\<azx_create\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769): allocate the [`struct hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L9), fill the chip-type fields, call [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150), and register the [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h)
- [`'\<azx_probe_continue\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333): the deferred remainder; run [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852), [`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186), [`azx_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243), and [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c)
- [`'\<azx_first_init\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852): map BAR0, read GCAP, set the DMA mask, build the streams with [`azx_init_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276), and bring the chip up through [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552)
- [`'\<hda_intel_init_chip\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552): the Intel chip-init wrapper that toggles the codec wakeup and the SKL clock-gating bit around [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018)
- [`'\<azx_probe_work\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1726): the [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17) handler that calls [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333)
- [`azx_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2841): the [`struct pci_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h) bound to the [`azx_ids`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2473) id table, naming [`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) and [`azx_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2429)
- [`pci_hda_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2120): the [`struct hda_controller_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L75) the Intel driver installs in [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L113)

### Shared controller glue (sound/hda/common/controller.c)

- [`'\<azx_init_chip\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018): wrap [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609) and apply the CXT RINTCNT workaround when the chip was actually reset
- [`'\<azx_bus_init\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150): initialise the embedded [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) over [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) with [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928) and apply the [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104)-derived bus flags
- [`'\<azx_init_streams\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276): allocate [`num_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L109) [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) objects and call [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) on each
- [`'\<azx_probe_codecs\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186): probe each populated slot of [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) and create a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) for each with [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947)
- [`'\<azx_codec_configure\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243): walk the bus codec list and call [`snd_hda_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c) on each, unregistering any that fail
- [`'\<azx_interrupt\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1059): the shared HD-Audio IRQ handler reading [`AZX_REG_INTSTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L37) and dispatching per-stream interrupts
- [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928): the [`struct hdac_bus_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L243) verb function pointer struct naming [`azx_send_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L902) and [`azx_get_response()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L915)
- [`'\<azx_send_cmd\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L902): the [`command`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L245) op routing a verb to [`snd_hdac_bus_send_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c) or the single-command path

### PCM ops and stream binding (sound/hda/common/controller.c)

- [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L669): the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) function pointer struct installed on every azx PCM substream
- [`'\<snd_hda_attach_pcm_stream\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692): create a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470) for a codec PCM, allocate the [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84), and install [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L669) with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510)
- [`'\<azx_pcm_open\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574): the [`.open`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L670) op; assign a host DMA stream with [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44), seed [`runtime->hw`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h) from [`azx_pcm_hw`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L548), and call the codec [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h) op
- [`'\<azx_assign_device\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44): wrap [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361) and convert the result to a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57)
- [`'\<azx_pcm_prepare\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152): the [`.prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L674) op; compute the format value, set the stream params, and program SDn with [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257)
- [`'\<azx_pcm_trigger\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L201): the [`.trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L675) op; run [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) or [`snd_hdac_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c) under the SYNC bit protocol
- [`'\<azx_pcm_close\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L91): the [`.close`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L671) op; release the stream with [`azx_release_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L55)
- [`'\<azx_pcm_pointer\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L319): the [`.pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L676) op; report the buffer position from [`azx_get_position()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L286)
- [`'\<azx_get_position\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L286): read the playback position, by LPIB with [`azx_get_pos_lpib()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L274) or the position buffer with [`azx_get_pos_posbuf()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L280)

### Core layer reached by the controller (sound/hda/core, sound/hda/common/codec.c)

- [`'\<snd_hdac_bus_init\>':'sound/hda/core/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31): the core bus constructor [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150) calls on the embedded [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291)
- [`'\<snd_hdac_bus_init_chip\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609): the core chip bring-up [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018) wraps
- [`'\<snd_hdac_stream_assign\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361): the core stream allocator [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44) wraps
- [`'\<snd_hdac_stream_setup\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257): the core SDn programming [`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152) calls
- [`'\<snd_hda_codec_new\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947): create a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) on the bus; called from [`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186)

## KERNEL DOCUMENTATION

- [`Documentation/sound/hd-audio/notes.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/notes.rst): the HD-Audio driver design, the controller and codec split that [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) and [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) implement, and the module options the [`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) path reads
- [`Documentation/sound/hd-audio/models.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/models.rst): the codec model quirks the [`model`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c) option (passed into [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150)) selects
- [`Documentation/sound/hd-audio/dp-mst.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/dp-mst.rst): DisplayPort Multi-Stream on the HDMI/DP codecs an Intel azx controller exposes
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the MultiLink capability the [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointer addresses, parsed by the core for the SKL-class controllers the azx driver also covers

## OTHER SOURCES

- [Intel High Definition Audio Specification (Revision 1.0a)](https://www.intel.com/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)
- [ALSA project: HD-Audio](https://www.alsa-project.org/wiki/Main_Page)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The controller comes up through one PCI bind whose remainder is deferred to a work item, then exposes its host DMA streams to the PCM layer. The [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback allocates the chip and schedules [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17); the deferred [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333) maps the BAR, builds the streams and codecs, and registers the card; and the per-substream [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L669) hand a host DMA stream to each open. The objects below have one creator each, so a reader can follow a link from the PCI bind down into the embedded bus object and out to the streams and codecs.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L9) (contains [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95)) | [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) in [`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769) | the PCI device (devm) |
| [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) [`bus`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L96) | embedded; set up by [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150) | embedded in [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) |
| [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) | embedded; initialised by [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) | embedded in [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) |
| [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) on [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) | [`azx_init_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276) | the controller |
| [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) per slot | [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947) in [`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186) | the controller |
| [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84) on [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L123) | [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692) | the codec PCM |
| stream assigned to a substream | [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44) at open | until [`azx_release_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L55) at close |

### azx_probe allocates the chip and defers the rest

The [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback [`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) screens the device against the denylist, creates the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L92), and calls [`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769). On x86-64 ACPI it first consults [`snd_intel_dsp_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/intel-dsp-config.c) so that when SOF should own the device the azx driver aborts and leaves the controller to SOF. The substance of the rest of the bind is deferred to [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17) because it may trigger a request-module.

### azx_first_init maps the BAR and brings up the chip

The deferred [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333) runs [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852), which maps BAR0 into [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298), reads the GCAP stream counts into [`capture_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L107) and [`playback_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L105), builds the streams with [`azx_init_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276), and resets the controller through [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552).

### azx_probe_codecs enumerates the codec slots

[`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186) walks [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) and creates a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) for each populated slot with [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947), then [`azx_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243) parses each codec. The codec layer is documented separately; this page treats codec creation as a single call.

### azx_pcm_open binds a host DMA stream

[`azx_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574) assigns a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) with [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44), records it in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h), and seeds the hardware constraints from [`azx_pcm_hw`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L548). The matching [`azx_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L91) returns the stream with [`azx_release_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L55).

## DETAILS

### The azx wrapper and its embedded bus

A [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) is the legacy driver's image of one HD-Audio PCI function. It does not re-declare the controller's transport state; it embeds the codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) (whose [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member is the core [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291)) and adds the chip-type fields, the stream counts, the register-access function pointer struct, and the list of PCM devices:

```c
/* sound/hda/common/hda_controller.h:95 */
struct azx {
	struct hda_bus bus;

	struct snd_card *card;
	struct pci_dev *pci;
	int dev_index;

	/* chip type specific */
	int driver_type;
	unsigned int driver_caps;
	int playback_streams;
	int playback_index_offset;
	int capture_streams;
	int capture_index_offset;
	int num_streams;
	int jackpoll_interval; /* jack poll interval in jiffies */

	/* Register interaction. */
	const struct hda_controller_ops *ops;

	/* position adjustment callbacks */
	azx_get_pos_callback_t get_position[2];
	azx_get_delay_callback_t get_delay[2];

	/* locks */
	struct mutex open_mutex; /* Prevents concurrent open/close operations */

	/* PCM */
	struct list_head pcm_list; /* azx_pcm list */
	...
	/* flags */
	int bdl_pos_adj;
	unsigned int running:1;
	...
	unsigned int snoop:1;
	...
};
```

The [`driver_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L103) selects the chipset variant (the `AZX_DRIVER_*` enumerators), and [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104) is the bitmask of the `AZX_DCAPS_*` quirk flags that the bus-init and chip-init paths consult. The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L113) is a small function pointer struct of register-level glue distinct from the core verb [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293) on the bus:

```c
/* sound/hda/common/hda_controller.h:75 */
struct hda_controller_ops {
	/* Disable msi if supported, PCI only */
	int (*disable_msi_reset_irq)(struct azx *);
	/* Check if current position is acceptable */
	int (*position_check)(struct azx *chip, struct azx_dev *azx_dev);
	/* enable/disable the link power */
	int (*link_power)(struct azx *chip, bool enable);
};
```

Two macros bridge the wrapper and the core bus. [`azx_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L155) returns the address of the doubly-nested [`bus.core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39), and [`bus_to_azx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L156) is the inverse [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) the verb callbacks use to recover the chip from a [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) pointer:

```c
/* sound/hda/common/hda_controller.h:155 */
#define azx_bus(chip)	(&(chip)->bus.core)
#define bus_to_azx(_bus)	container_of(_bus, struct azx, bus.core)
```

The Intel driver wraps [`struct azx`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L95) once more. [`struct hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L9) embeds it as [`chip`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L10) and adds the deferred-probe machinery and the vga_switcheroo bookkeeping the PCI path needs:

```c
/* sound/hda/controllers/intel.h:9 */
struct hda_intel {
	struct azx chip;

	/* for pending irqs */
	struct work_struct irq_pending_work;

	/* sync probing */
	struct completion probe_wait;
	struct delayed_work probe_work;

	/* card list (for power_save trigger) */
	struct list_head list;
	...
	bool need_i915_power:1; /* the hda controller needs i915 power */

	int probe_retry;	/* being probe-retry */
};
```

### A host DMA stream wrapper

Each engine the driver hands to a PCM is a [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57). It embeds the core [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) (which carries the SDn register pointer, the BDL, the direction, the stream tag, and the positions) and adds only the two legacy flag bits:

```c
/* sound/hda/common/hda_controller.h:57 */
struct azx_dev {
	struct hdac_stream core;

	unsigned int irq_pending:1;
	/*
	 * For VIA:
	 *  A flag to ensure DMA position is 0
	 *  when link position is not greater than FIFO size
	 */
	unsigned int insufficient:1;
};

#define azx_stream(dev)		(&(dev)->core)
#define stream_to_azx_dev(s)	container_of(s, struct azx_dev, core)
```

[`azx_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L69) returns the embedded core stream so the PCM ops can call the core stream functions, and [`stream_to_azx_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L70) recovers the wrapper from a core stream pointer, which is exactly what [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44) does with the stream the core hands back.

### azx_probe creates the card and defers the bind

[`azx_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2127) is the [`.probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2844) callback of the [`struct pci_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h). It checks the denylists, allocates a card slot, and (on a build with the Intel DSP-config helper) calls [`snd_intel_dsp_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/intel-dsp-config.c) to decide whether the legacy driver should claim this device at all:

```c
/* sound/hda/controllers/intel.c:2127 */
static int azx_probe(struct pci_dev *pci,
		     const struct pci_device_id *pci_id)
{
	const struct dmi_system_id *dmi;
	struct snd_card *card;
	struct hda_intel *hda;
	struct azx *chip;
	bool schedule_probe;
	int dev;
	int err;
	...
	/*
	 * stop probe if another Intel's DSP driver should be activated
	 */
	if (dmic_detect) {
		err = snd_intel_dsp_driver_probe(pci);
		if (err != SND_INTEL_DSP_DRIVER_ANY && err != SND_INTEL_DSP_DRIVER_LEGACY) {
			dev_dbg(&pci->dev, "HDAudio driver not selected, aborting probe\n");
			return -ENODEV;
		}
	}
	...
	err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
			   0, &card);
	if (err < 0) {
		dev_err(&pci->dev, "Error creating card!\n");
		return err;
	}

	err = azx_create(card, pci, dev, pci_id->driver_data, &chip);
	if (err < 0)
		goto out_free;
	card->private_data = chip;
	hda = container_of(chip, struct hda_intel, chip);
	...
	schedule_probe = !chip->disabled;
	...
	if (schedule_probe)
		schedule_delayed_work(&hda->probe_work, 0);

	set_bit(dev, probed_devs);
	...
	return 0;
	...
}
```

According to the comment, the [`snd_intel_dsp_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/intel-dsp-config.c) check exists to "stop probe if another Intel's DSP driver should be activated", so on a modern Intel platform configured for SOF the legacy azx driver returns `-ENODEV` here and the same controller is bound by the SOF Intel driver instead. The driver-data argument [`pci_id->driver_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2473) is the combined [`driver_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L103) and [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104) from the [`azx_ids`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2473) table:

```c
/* sound/hda/controllers/intel.c:2473 */
static const struct pci_device_id azx_ids[] = {
	/* CPT */
	{ PCI_DEVICE_DATA(INTEL, HDA_CPT, AZX_DRIVER_PCH | AZX_DCAPS_INTEL_PCH_NOPM) },
	/* PBG */
	{ PCI_DEVICE_DATA(INTEL, HDA_PBG, AZX_DRIVER_PCH | AZX_DCAPS_INTEL_PCH_NOPM) },
	/* Panther Point */
	{ PCI_DEVICE_DATA(INTEL, HDA_PPT, AZX_DRIVER_PCH | AZX_DCAPS_INTEL_PCH_NOPM) },
	...
};
```

```c
/* sound/hda/controllers/intel.c:2841 */
static struct pci_driver azx_driver = {
	.name = KBUILD_MODNAME,
	.id_table = azx_ids,
	.probe = azx_probe,
	.remove = azx_remove,
	.shutdown = azx_shutdown,
	.driver = {
		.pm = pm_ptr(&azx_pm),
	},
};

module_pci_driver(azx_driver);
```

The actual remainder of the bind runs in [`azx_probe_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1726), the [`probe_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L17) handler, which recovers the chip and calls [`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333):

```c
/* sound/hda/controllers/intel.c:1726 */
static void azx_probe_work(struct work_struct *work)
{
	struct hda_intel *hda = container_of(work, struct hda_intel, probe_work.work);
	azx_probe_continue(&hda->chip);
}
```

### azx_create allocates the chip and the embedded bus

[`azx_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1769) allocates the [`struct hda_intel`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.h#L9) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48), fills the chip-type fields from the driver-data, installs the [`pci_hda_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2120) function pointer struct, and calls [`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150) to set up the embedded bus before registering a low-level [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h):

```c
/* sound/hda/controllers/intel.c:1769 */
static int azx_create(struct snd_card *card, struct pci_dev *pci,
		      int dev, unsigned int driver_caps,
		      struct azx **rchip)
{
	static const struct snd_device_ops ops = {
		.dev_disconnect = azx_dev_disconnect,
		.dev_free = azx_dev_free,
	};
	struct hda_intel *hda;
	struct azx *chip;
	int err;

	*rchip = NULL;

	err = pcim_enable_device(pci);
	if (err < 0)
		return err;

	hda = devm_kzalloc(&pci->dev, sizeof(*hda), GFP_KERNEL);
	if (!hda)
		return -ENOMEM;

	chip = &hda->chip;
	mutex_init(&chip->open_mutex);
	chip->card = card;
	chip->pci = pci;
	chip->ops = &pci_hda_ops;
	chip->driver_caps = driver_caps;
	chip->driver_type = driver_caps & 0xff;
	check_msi(chip);
	chip->dev_index = dev;
	...
	INIT_LIST_HEAD(&chip->pcm_list);
	...
	err = azx_bus_init(chip, model[dev]);
	if (err < 0)
		return err;
	...
	err = snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);
	if (err < 0) {
		dev_err(card->dev, "Error creating device [card]!\n");
		azx_free(chip);
		return err;
	}

	/* continue probing in work context as may trigger request module */
	INIT_DELAYED_WORK(&hda->probe_work, azx_probe_work);

	*rchip = chip;

	return 0;
}
```

[`azx_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1150) initialises the embedded [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) over the core constructor [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31), passing the verb function pointer struct [`bus_core_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L928), then translates the [`driver_caps`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L104) quirk bits into the corresponding bus flags:

```c
/* sound/hda/common/controller.c:1150 */
int azx_bus_init(struct azx *chip, const char *model)
{
	struct hda_bus *bus = &chip->bus;
	int err;

	err = snd_hdac_bus_init(&bus->core, chip->card->dev, &bus_core_ops);
	if (err < 0)
		return err;

	bus->card = chip->card;
	mutex_init(&bus->prepare_mutex);
	bus->pci = chip->pci;
	bus->modelname = model;
	bus->mixer_assigned = -1;
	bus->core.snoop = azx_snoop(chip);
	if (chip->get_position[0] != azx_get_pos_lpib ||
	    chip->get_position[1] != azx_get_pos_lpib)
		bus->core.use_posbuf = true;
	bus->core.bdl_pos_adj = chip->bdl_pos_adj;
	if (chip->driver_caps & AZX_DCAPS_CORBRP_SELF_CLEAR)
		bus->core.corbrp_self_clear = true;
	...
	/* enable sync_write flag for stable communication as default */
	bus->core.sync_write = 1;

	return 0;
}
```

The verb function pointer struct it installs routes a codec command and its response through the legacy transport, which falls back to a single-command path when CORB/RIRB DMA is disabled or PIO is requested:

```c
/* sound/hda/common/controller.c:928 */
static const struct hdac_bus_ops bus_core_ops = {
	.command = azx_send_cmd,
	.get_response = azx_get_response,
};
```

```c
/* sound/hda/common/controller.c:902 */
static int azx_send_cmd(struct hdac_bus *bus, unsigned int val)
{
	struct azx *chip = bus_to_azx(bus);

	if (chip->disabled)
		return 0;
	if (chip->single_cmd || bus->use_pio_for_commands)
		return azx_single_send_cmd(bus, val);
	else
		return snd_hdac_bus_send_cmd(bus, val);
}
```

[`azx_send_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L902) recovers the chip with [`bus_to_azx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L156) and forwards a normal verb to the core [`snd_hdac_bus_send_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c), so the CORB/RIRB command rings the core sets up at chip init carry every codec verb the azx driver issues.

### azx_first_init maps the BAR, reads GCAP, and starts the chip

[`azx_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L2333) runs the deferred steps in order. It requests the display power well, calls [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852), builds the codecs, configures them, and registers the card. The codec-build retry loop is bounded by the [`AZX_DCAPS_RETRY_PROBE`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L44) quirk:

```c
/* sound/hda/controllers/intel.c:2333 */
static int azx_probe_continue(struct azx *chip)
{
	struct hda_intel *hda = container_of(chip, struct hda_intel, chip);
	struct hdac_bus *bus = azx_bus(chip);
	struct pci_dev *pci = chip->pci;
	int dev = chip->dev_index;
	int err;
	...
	err = azx_first_init(chip);
	if (err < 0)
		goto out_free;
	...
	/* create codec instances */
	if (bus->codec_mask) {
		err = azx_probe_codecs(chip, azx_max_codecs[chip->driver_type]);
		if (err < 0)
			goto out_free;
	}
	...
 probe_retry:
	if (bus->codec_mask && !(probe_only[dev] & 1)) {
		err = azx_codec_configure(chip);
		if (err) {
			...
		}
	}

	err = snd_card_register(chip->card);
	if (err < 0)
		goto out_free;
	...
	chip->running = 1;
	...
	return 0;
}
```

[`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) is the controller bring-up proper. It maps BAR0 into [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298) with [`pcim_iomap_region()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h), records the physical base in [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L297), reads the GCAP register, and decodes its ISS and OSS fields straight into [`capture_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L107) and [`playback_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L105):

```c
/* sound/hda/controllers/intel.c:1852 */
static int azx_first_init(struct azx *chip)
{
	int dev = chip->dev_index;
	struct pci_dev *pci = chip->pci;
	struct snd_card *card = chip->card;
	struct hdac_bus *bus = azx_bus(chip);
	int err;
	unsigned short gcap;
	unsigned int dma_bits = 64;
	...
	bus->remap_addr = pcim_iomap_region(pci, 0, "ICH HD audio");
	if (IS_ERR(bus->remap_addr))
		return PTR_ERR(bus->remap_addr);

	bus->addr = pci_resource_start(pci, 0);

	if (chip->driver_type == AZX_DRIVER_SKL)
		snd_hdac_bus_parse_capabilities(bus);
	...
	pci_set_master(pci);

	gcap = azx_readw(chip, GCAP);
	dev_dbg(card->dev, "chipset global capabilities = 0x%x\n", gcap);
	...
	/* allow 64bit DMA address if supported by H/W */
	if (!(gcap & AZX_GCAP_64OK))
		dma_bits = 32;
	if (dma_set_mask_and_coherent(&pci->dev, DMA_BIT_MASK(dma_bits)))
		dma_set_mask_and_coherent(&pci->dev, DMA_BIT_MASK(32));
	dma_set_max_seg_size(&pci->dev, UINT_MAX);
	...
	/* read number of streams from GCAP register instead of using
	 * hardcoded value
	 */
	chip->capture_streams = (gcap >> 8) & 0x0f;
	chip->playback_streams = (gcap >> 12) & 0x0f;
	...
	chip->capture_index_offset = 0;
	chip->playback_index_offset = chip->capture_streams;
	chip->num_streams = chip->playback_streams + chip->capture_streams;
	...
	/* initialize streams */
	err = azx_init_streams(chip);
	if (err < 0)
		return err;

	err = azx_alloc_stream_pages(chip);
	if (err < 0)
		return err;

	/* initialize chip */
	azx_init_pci(chip);

	snd_hdac_i915_set_bclk(bus);

	hda_intel_init_chip(chip, (probe_only[dev] & 2) == 0);

	/* codec detection */
	if (!azx_bus(chip)->codec_mask) {
		dev_err(card->dev, "no codecs found!\n");
		/* keep running the rest for the runtime PM */
	}

	if (azx_acquire_irq(chip, 0) < 0)
		return -EBUSY;
	...
	return 0;
}
```

The SKL-class controllers call [`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406) here to discover the extended capability pointers, the same walk SOF performs, so on those parts the [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointer is populated and [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552) can bring up the link-control register. The stream allocation runs in two steps: [`azx_init_streams()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1276) builds one [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) per engine and links it onto the core [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337), then [`azx_alloc_stream_pages()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L196) allocates the BDL and position-buffer pages:

```c
/* sound/hda/common/controller.c:1276 */
int azx_init_streams(struct azx *chip)
{
	int i;
	int stream_tags[2] = { 0, 0 };

	/* initialize each stream (aka device)
	 * assign the starting bdl address to each stream (device)
	 * and initialize
	 */
	for (i = 0; i < chip->num_streams; i++) {
		struct azx_dev *azx_dev = kzalloc_obj(*azx_dev);
		int dir, tag;

		if (!azx_dev)
			return -ENOMEM;

		dir = stream_direction(chip, i);
		...
		if (chip->driver_caps & AZX_DCAPS_SEPARATE_STREAM_TAG)
			tag = ++stream_tags[dir];
		else
			tag = i + 1;
		snd_hdac_stream_init(azx_bus(chip), azx_stream(azx_dev),
				     i, dir, tag);
	}

	return 0;
}
```

Each [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) is heap-allocated, and [`azx_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L69) passes its embedded core stream to [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94), which computes the SDn register offset (`remap_addr + 0x20 * idx + 0x80`) and links the stream onto the bus. The stream-tag assignment depends on the [`AZX_DCAPS_SEPARATE_STREAM_TAG`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L47) quirk, which the driver also forces on when [`num_streams`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L109) exceeds the 4-bit SDxCTL.STRM field.

```
    GCAP register decode in azx_first_init (16-bit word)
    ──────────────────────────────────────────────────────

    bit 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
       ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
       │    OSS    │    ISS    │       other..         │
       │  (15:12)  │  (11:8)   │         (7:0)         │
       └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘

    OSS (15:12) ─▶ playback_streams = (gcap >> 12) & 0x0f
    ISS (11:8)  ─▶ capture_streams  = (gcap >>  8) & 0x0f
    num_streams      = playback_streams + capture_streams
    capture_index_offset  = 0
    playback_index_offset = capture_streams
    AZX_GCAP_64OK clear ─▶ dma_bits = 32 (else 64)
```

### Chip init layers the Intel wrapper over the core

[`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552) is the Intel-specific chip-init step. It raises the codec-wakeup line, clears the SKL clock-gating bit around the reset, calls the shared [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018), and, when the MultiLink capability is present, initialises the link-control register:

```c
/* sound/hda/controllers/intel.c:552 */
static void hda_intel_init_chip(struct azx *chip, bool full_reset)
{
	struct hdac_bus *bus = azx_bus(chip);
	struct pci_dev *pci = chip->pci;
	u32 val;

	snd_hdac_set_codec_wakeup(bus, true);
	if (chip->driver_type == AZX_DRIVER_SKL) {
		pci_read_config_dword(pci, INTEL_HDA_CGCTL, &val);
		val = val & ~INTEL_HDA_CGCTL_MISCBDCGE;
		pci_write_config_dword(pci, INTEL_HDA_CGCTL, val);
	}
	azx_init_chip(chip, full_reset);
	if (chip->driver_type == AZX_DRIVER_SKL) {
		pci_read_config_dword(pci, INTEL_HDA_CGCTL, &val);
		val = val | INTEL_HDA_CGCTL_MISCBDCGE;
		pci_write_config_dword(pci, INTEL_HDA_CGCTL, val);
	}

	snd_hdac_set_codec_wakeup(bus, false);
	...
	if (bus->mlcap != NULL)
		intel_init_lctl(chip);
}
```

The shared [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018) is a thin wrapper over the core [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609), which resets the link, programs the CORB/RIRB rings, enables interrupts, and reads the codec bitmap. It applies one chipset workaround when the boolean return reports the chip was actually initialised:

```c
/* sound/hda/common/controller.c:1018 */
void azx_init_chip(struct azx *chip, bool full_reset)
{
	if (snd_hdac_bus_init_chip(azx_bus(chip), full_reset)) {
		/* correct RINTCNT for CXT */
		if (chip->driver_caps & AZX_DCAPS_CTX_WORKAROUND)
			azx_writew(chip, RINTCNT, 0xc0);
	}
}
```

After [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609) returns, the core bus has set [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) from the STATESTS read, so [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) can log "no codecs found!" when the mask is empty and still keep the controller running for runtime PM. This wrapper is reached from eight call sites across the HD-Audio controller drivers; the Intel path enters it through [`hda_intel_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L552), while the ACPI, Tegra, and CIX controllers call [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018) directly.

### azx_probe_codecs builds one hda_codec per slot

[`azx_probe_codecs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1186) makes two passes over the codec slots. The first probes each bit set in both [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) and the driver's [`codec_probe_mask`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L126), resetting the controller if a probe disturbs it; the second creates a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) for each surviving slot with [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947):

```c
/* sound/hda/common/controller.c:1186 */
int azx_probe_codecs(struct azx *chip, unsigned int max_slots)
{
	struct hdac_bus *bus = azx_bus(chip);
	int c, codecs, err;

	codecs = 0;
	if (!max_slots)
		max_slots = AZX_DEFAULT_CODECS;

	/* First try to probe all given codec slots */
	for (c = 0; c < max_slots; c++) {
		if ((bus->codec_mask & (1 << c)) & chip->codec_probe_mask) {
			if (probe_codec(chip, c) < 0) {
				...
				bus->codec_mask &= ~(1 << c);
				...
				azx_stop_chip(chip);
				azx_init_chip(chip, true);
			}
		}
	}

	/* Then create codec instances */
	for (c = 0; c < max_slots; c++) {
		if ((bus->codec_mask & (1 << c)) & chip->codec_probe_mask) {
			struct hda_codec *codec;
			err = snd_hda_codec_new(&chip->bus, chip->card, c, &codec);
			if (err < 0)
				continue;
			codec->jackpoll_interval = chip->jackpoll_interval;
			codec->beep_mode = chip->beep_mode;
			codec->ctl_dev_id = chip->ctl_dev_id;
			codecs++;
		}
	}
	if (!codecs) {
		dev_err(chip->card->dev, "no codecs initialized\n");
		return -ENXIO;
	}
	return 0;
}
```

[`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947) calls the codec-layer constructor [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885), which in turn calls the core [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) on the embedded [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52); the codec layer itself is documented separately. [`azx_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243) then walks the bus codec list and parses each codec, which is what causes the codec to build its PCMs and attach them through the controller.

### snd_hda_attach_pcm_stream installs the PCM ops

When a codec builds its PCMs, the codec layer calls back into the controller through [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692) (reached from [`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300)). It creates the ALSA [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470), allocates an [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84) onto [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L123), and installs the [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L669) function pointer struct on each populated direction:

```c
/* sound/hda/common/controller.c:692 */
int snd_hda_attach_pcm_stream(struct hda_bus *_bus, struct hda_codec *codec,
			      struct hda_pcm *cpcm)
{
	struct hdac_bus *bus = &_bus->core;
	struct azx *chip = bus_to_azx(bus);
	struct snd_pcm *pcm;
	struct azx_pcm *apcm;
	int pcm_dev = cpcm->device;
	...
	err = snd_pcm_new(chip->card, cpcm->name, pcm_dev,
			  cpcm->stream[SNDRV_PCM_STREAM_PLAYBACK].substreams,
			  cpcm->stream[SNDRV_PCM_STREAM_CAPTURE].substreams,
			  &pcm);
	if (err < 0)
		return err;
	...
	apcm = kzalloc_obj(*apcm);
	if (apcm == NULL) {
		snd_device_free(chip->card, pcm);
		return -ENOMEM;
	}
	apcm->chip = chip;
	apcm->pcm = pcm;
	apcm->codec = codec;
	apcm->info = cpcm;
	pcm->private_data = apcm;
	pcm->private_free = azx_pcm_free;
	...
	list_add_tail(&apcm->list, &chip->pcm_list);
	cpcm->pcm = pcm;
	for (s = 0; s < 2; s++) {
		if (cpcm->stream[s].substreams)
			snd_pcm_set_ops(pcm, s, &azx_pcm_ops);
	}
	...
}
```

The [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84) carries the back pointers each PCM op needs, holding the chip, the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L470), the owning [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178), and the codec's [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) description:

```c
/* sound/hda/common/hda_controller.h:84 */
struct azx_pcm {
	struct azx *chip;
	struct snd_pcm *pcm;
	struct hda_codec *codec;
	struct hda_pcm *info;
	struct list_head list;
};
```

The function pointer struct it installs names the eight PCM ops the azx controller implements:

```c
/* sound/hda/common/controller.c:669 */
static const struct snd_pcm_ops azx_pcm_ops = {
	.open = azx_pcm_open,
	.close = azx_pcm_close,
	.hw_params = azx_pcm_hw_params,
	.hw_free = azx_pcm_hw_free,
	.prepare = azx_pcm_prepare,
	.trigger = azx_pcm_trigger,
	.pointer = azx_pcm_pointer,
	.get_time_info =  azx_get_time_info,
};
```

Every op in that table recovers the record from pcm->private_data and reads its back-pointers to reach the chip, the codec, and the PCM description:

```
    struct azx_pcm back-pointers each PCM op follows
    ──────────────────────────────────────────────────
    (allocated by snd_hda_attach_pcm_stream, parked in
     pcm->private_data; azx_pcm_ops installed per direction)

                    ┌───────────────────────┐
                    │ struct azx_pcm        │
                    │   chip ───────────────┼──▶ struct azx
                    │   pcm  ───────────────┼──▶ struct snd_pcm
                    │   codec ──────────────┼──▶ struct hda_codec
                    │   info ───────────────┼──▶ struct hda_pcm
                    │   list (on pcm_list)  │
                    └───────────┬───────────┘
                                ▲
              pcm->private_data │ (recovered by
                                │  snd_pcm_substream_chip)
                    ┌───────────┴───────────┐
                    │ azx_pcm_ops:          │
                    │  open close hw_params │
                    │  prepare trigger      │
                    │  pointer ...          │
                    └───────────────────────┘
```

### azx_pcm_open assigns a host DMA stream

[`azx_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574) is the [`.open`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L670) op. It recovers the [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L84) with [`snd_pcm_substream_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L21), assigns a host DMA stream with [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44), records it in [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h), seeds the hardware constraints from [`azx_pcm_hw`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L548), and forwards to the codec's open op:

```c
/* sound/hda/common/controller.c:574 */
static int azx_pcm_open(struct snd_pcm_substream *substream)
{
	struct azx_pcm *apcm = snd_pcm_substream_chip(substream);
	struct hda_pcm_stream *hinfo = to_hda_pcm_stream(substream);
	struct azx *chip = apcm->chip;
	struct azx_dev *azx_dev;
	struct snd_pcm_runtime *runtime = substream->runtime;
	int err;
	int buff_step;

	snd_hda_codec_pcm_get(apcm->info);
	mutex_lock(&chip->open_mutex);
	azx_dev = azx_assign_device(chip, substream);
	trace_azx_pcm_open(chip, azx_dev);
	if (azx_dev == NULL) {
		err = -EBUSY;
		goto unlock;
	}
	runtime->private_data = azx_dev;

	runtime->hw = azx_pcm_hw;
	if (chip->gts_present)
		runtime->hw.info |= SNDRV_PCM_INFO_HAS_LINK_SYNCHRONIZED_ATIME;
	runtime->hw.channels_min = hinfo->channels_min;
	runtime->hw.channels_max = hinfo->channels_max;
	runtime->hw.formats = hinfo->formats;
	runtime->hw.rates = hinfo->rates;
	...
	snd_hda_power_up(apcm->codec);
	if (hinfo->ops.open)
		err = hinfo->ops.open(hinfo, apcm->codec, substream);
	else
		err = -ENODEV;
	if (err < 0) {
		azx_release_device(azx_dev);
		goto powerdown;
	}
	...
	snd_pcm_set_sync(substream);
	mutex_unlock(&chip->open_mutex);
	return 0;
	...
}
```

The hardware template seeds the format and rate constraints before the codec narrows them. The defaults restrict to stereo S16_LE at 48 kHz, which the codec's open op then widens to the codec's true capabilities:

```c
/* sound/hda/common/controller.c:548 */
static const struct snd_pcm_hardware azx_pcm_hw = {
	.info =			(SNDRV_PCM_INFO_MMAP |
				 SNDRV_PCM_INFO_INTERLEAVED |
				 SNDRV_PCM_INFO_BLOCK_TRANSFER |
				 SNDRV_PCM_INFO_MMAP_VALID |
				 SNDRV_PCM_INFO_PAUSE |
				 SNDRV_PCM_INFO_SYNC_START |
				 SNDRV_PCM_INFO_HAS_WALL_CLOCK | /* legacy */
				 SNDRV_PCM_INFO_HAS_LINK_ATIME |
				 SNDRV_PCM_INFO_NO_PERIOD_WAKEUP),
	.formats =		SNDRV_PCM_FMTBIT_S16_LE,
	.rates =		SNDRV_PCM_RATE_48000,
	.rate_min =		48000,
	.rate_max =		48000,
	.channels_min =		2,
	.channels_max =		2,
	...
};
```

The stream assignment itself is one indirection over the core. [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L44) calls [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361), which walks the core [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) for an unused engine of the right direction, and converts the returned [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) back to the wrapper with [`stream_to_azx_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L70):

```c
/* sound/hda/common/controller.c:44 */
static inline struct azx_dev *
azx_assign_device(struct azx *chip, struct snd_pcm_substream *substream)
{
	struct hdac_stream *s;

	s = snd_hdac_stream_assign(azx_bus(chip), substream);
	if (!s)
		return NULL;
	return stream_to_azx_dev(s);
}
```

The matching close path [`azx_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L91) gives the engine back with [`azx_release_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L55), the one-line wrapper over [`snd_hdac_stream_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L417):

```c
/* sound/hda/common/controller.c:55 */
static inline void azx_release_device(struct azx_dev *azx_dev)
{
	snd_hdac_stream_release(azx_stream(azx_dev));
}
```

### azx_pcm_prepare programs the SDn registers

[`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152) is the [`.prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L674) op. It resets the assigned stream, computes the HD-Audio format value from the runtime rate, channel count, and sample width, and programs the stream descriptor registers through the core [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) before handing the stream tag to the codec:

```c
/* sound/hda/common/controller.c:152 */
static int azx_pcm_prepare(struct snd_pcm_substream *substream)
{
	struct azx_pcm *apcm = snd_pcm_substream_chip(substream);
	struct azx *chip = apcm->chip;
	struct azx_dev *azx_dev = get_azx_dev(substream);
	struct hda_pcm_stream *hinfo = to_hda_pcm_stream(substream);
	struct snd_pcm_runtime *runtime = substream->runtime;
	unsigned int format_val, stream_tag, bits;
	int err;
	...
	snd_hdac_stream_reset(azx_stream(azx_dev));
	bits = snd_hdac_stream_format_bits(runtime->format, SNDRV_PCM_SUBFORMAT_STD, hinfo->maxbps);

	format_val = snd_hdac_spdif_stream_format(runtime->channels, bits, runtime->rate, ctls);
	if (!format_val) {
		dev_err(chip->card->dev,
			"invalid format_val, rate=%d, ch=%d, format=%d\n",
			runtime->rate, runtime->channels, runtime->format);
		return -EINVAL;
	}

	err = snd_hdac_stream_set_params(azx_stream(azx_dev), format_val);
	if (err < 0)
		return err;

	snd_hdac_stream_setup(azx_stream(azx_dev), false);

	stream_tag = azx_dev->core.stream_tag;
	...
	err = snd_hda_codec_prepare(apcm->codec, hinfo, stream_tag,
				     azx_dev->core.format_val, substream);
	if (err < 0)
		return err;

	azx_stream(azx_dev)->prepared = 1;
	return 0;
}
```

[`get_azx_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L184) reads the [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) back out of [`runtime->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h) that [`azx_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L574) stored, and [`azx_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L69) hands the embedded core stream to [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257), so the SDn programming (stream tag, cyclic buffer length, format, last-valid-index, and BDL base) runs once per PCM prepare for a legacy HD-Audio stream. The codec is told the same stream tag so it routes its converter widget output to the matching link stream.

```
    Per-stream SDn register blocks (one per host DMA engine)
    ──────────────────────────────────────────────────────────
    SDn block base = remap_addr + 0x80 + 0x20 * idx   (stride 0x20)

      idx        SDn block base
      ───        ──────────────
       0   ───▶  remap_addr + 0x80     ┌──────────────────────┐
       1   ───▶  remap_addr + 0xA0     │ SDn descriptor:      │
       2   ───▶  remap_addr + 0xC0     │   stream tag         │
       .                               │   cyclic buf length  │
       .                               │   format value       │
       n   ───▶  remap_addr            │   last-valid-index   │
                  + 0x80 + 0x20*n      │   BDL base address   │
                                       └──────────────────────┘

    snd_hdac_stream_setup() programs the block for the assigned idx
    idx split: capture  = [0 .. capture_streams)
               playback = [capture_streams .. num_streams)
```

### azx_pcm_trigger starts and stops the engine

[`azx_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L201) is the [`.trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L675) op. It gathers the SYNC bit mask of every substream in the trigger group, then under the bus register lock sets the SYNC bits, starts or stops each engine, and clears the SYNC bits so the streams begin together:

```c
/* sound/hda/common/controller.c:201 */
static int azx_pcm_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct azx_pcm *apcm = snd_pcm_substream_chip(substream);
	struct azx *chip = apcm->chip;
	struct hdac_bus *bus = azx_bus(chip);
	struct azx_dev *azx_dev;
	struct snd_pcm_substream *s;
	struct hdac_stream *hstr;
	bool start;
	int sbits = 0;
	int sync_reg;

	azx_dev = get_azx_dev(substream);
	...
	hstr = azx_stream(azx_dev);
	if (chip->driver_caps & AZX_DCAPS_OLD_SSYNC)
		sync_reg = AZX_REG_OLD_SSYNC;
	else
		sync_reg = AZX_REG_SSYNC;

	if (dsp_is_locked(azx_dev) || !hstr->prepared)
		return -EPIPE;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_RESUME:
		start = true;
		break;
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		start = false;
		break;
	default:
		return -EINVAL;
	}

	snd_pcm_group_for_each_entry(s, substream) {
		if (s->pcm->card != substream->pcm->card)
			continue;
		azx_dev = get_azx_dev(s);
		sbits |= 1 << azx_dev->core.index;
		snd_pcm_trigger_done(s, substream);
	}

	scoped_guard(spinlock, &bus->reg_lock) {
		/* first, set SYNC bits of corresponding streams */
		snd_hdac_stream_sync_trigger(hstr, true, sbits, sync_reg);

		snd_pcm_group_for_each_entry(s, substream) {
			if (s->pcm->card != substream->pcm->card)
				continue;
			azx_dev = get_azx_dev(s);
			if (start) {
				azx_dev->insufficient = 1;
				snd_hdac_stream_start(azx_stream(azx_dev));
			} else {
				snd_hdac_stream_stop(azx_stream(azx_dev));
			}
		}
	}
	...
}
```

The start branch sets the legacy [`insufficient`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L66) flag before calling the core [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130), which writes the run bit and the per-stream interrupt enable into the SDn control register; the stop branch calls [`snd_hdac_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c). The SYNC register differs by chipset, with the [`AZX_DCAPS_OLD_SSYNC`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L37) quirk selecting [`AZX_REG_OLD_SSYNC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L39) on old ICH parts.

```
    azx_pcm_trigger START: ordered SYNC-bit group start
    ──────────────────────────────────────────────────────
    (whole step runs under bus->reg_lock so the group is atomic)

    build sbits: each stream sets bit (1 << core.index) in sbits
                                  │
                                  ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 1. set SYNC bits           snd_hdac_stream_sync_trigger  │
    │      (sbits ─▶ sync_reg)    (..., true, sbits, sync_reg) │
    ├──────────────────────────────────────────────────────────┤
    │ 2. per stream in group     snd_hdac_stream_start, _stop  │
    │      start ─▶ run bit, per-stream IRQ enable in SDn      │
    ├──────────────────────────────────────────────────────────┤
    │ 3. clear SYNC bits         engines leave reset together  │
    └──────────────────────────────────────────────────────────┘

    sync_reg = AZX_REG_OLD_SSYNC if AZX_DCAPS_OLD_SSYNC else AZX_REG_SSYNC
```

### azx_pcm_pointer reads the buffer position

[`azx_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L319) is the [`.pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L676) op the PCM core polls. It converts the byte position from [`azx_get_position()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L286) into frames:

```c
/* sound/hda/common/controller.c:319 */
static snd_pcm_uframes_t azx_pcm_pointer(struct snd_pcm_substream *substream)
{
	struct azx_pcm *apcm = snd_pcm_substream_chip(substream);
	struct azx *chip = apcm->chip;
	struct azx_dev *azx_dev = get_azx_dev(substream);
	return bytes_to_frames(substream->runtime,
			       azx_get_position(chip, azx_dev));
}
```

[`azx_get_position()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L286) reads the position either from the SD_LPIB link-position register with [`azx_get_pos_lpib()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L274) or from the DMA position buffer with [`azx_get_pos_posbuf()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L280), the choice driven by the [`get_position`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L116) callbacks the driver wired up at create time from the position-fix module option and the [`AZX_DCAPS_POSFIX_LPIB`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L33) quirk.

### The IRQ handler dispatches per-stream completions

The shared [`azx_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1059) is the IRQ handler the Intel driver installs through [`azx_acquire_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c). It reads the controller [`AZX_REG_INTSTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L37) register, dispatches each per-stream completion through the core stream-interrupt helper, and notifies the codec layer on a RIRB or unsolicited-response interrupt. The handler reaches each [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57) by its core stream's [`sd_int_sta_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L536), the same per-stream bit [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) enabled in the interrupt-control register, so an [`AZX_REG_INTSTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L37) bit identifies which stream raised the interrupt.

```
    azx_interrupt fans INTSTS bits out to per-stream handling
    ────────────────────────────────────────────────────────────

                       ┌─────────────────────────┐
                       │   azx_interrupt reads   │
                       │ AZX_REG_INTSTS register │
                       └────────────┬────────────┘
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │per-stream[0] │    │per-stream[1] │    │ RIRB / unsol │
        │  completion  │    │  completion  │    │ response ─▶  │
        │ via sd_int_  │    │ via sd_int_  │    │ notify codec │
        │   sta_mask   │    │   sta_mask   │    │    layer     │
        └──────────────┘    └──────────────┘    └──────────────┘

    each azx_dev->core.sd_int_sta_mask is the per-stream bit
    snd_hdac_stream_start enabled in the interrupt-control reg
```
