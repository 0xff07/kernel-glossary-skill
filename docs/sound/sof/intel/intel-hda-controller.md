# SOF Intel HDA controller

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an Intel x86-64 ACPI platform the audio DSP and the HD-Audio controller that hosts it are two PCI functions of one device, so Sound Open Firmware (SOF) brings up an HD-Audio controller for itself and reaches the DSP, the HDA codec links, the SoundWire links, and the digital-microphone (DMIC) endpoints all through that one controller; the host side of it is the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) that the core HD-Audio library uses everywhere, wrapped by the codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) and embedded in the SOF-private [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), reached from a [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) through the [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562), [`sof_to_hbus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L569), and inverse [`bus_to_sof_hda()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588) accessors. [`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) checks the PCI class and calls [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489) to map the controller registers and read its capability chain with [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58), [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) builds the host DMA engines and then calls [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607), and [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) resets the controller with [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) and enumerates the multi-link block with [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) that carries both the HDA codec links and the SoundWire links.

```
    SOF Intel HDA controller object (one PCI device, x86-64 ACPI)
    ─────────────────────────────────────────────────────────────

    struct sof_intel_hda_dev
    ┌───────────────────────────────────────────────────────────────┐
    │  struct hda_bus hbus      (codec list, pci back pointer)      │
    │  ┌────────────────────────────────────────────────────────┐  │
    │  │  struct hdac_bus core   (host HD-Audio controller)     │  │
    │  │    remap_addr   ppcap   mlcap   spbcap   gtscap        │  │
    │  │    codec_mask   stream_list   hlink_list               │  │
    │  └──┬─────────────┬──────────────┬─────────────┬──────────┘  │
    └─────┼─────────────┼──────────────┼─────────────┼─────────────┘
          │ ppcap       │ codec_mask   │ stream_list │ mlcap
          ▼             ▼              ▼             ▼
    ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────────┐
    │ DSP       │ │ HDA codec │ │ host DMA  │ │ multi-link:    │
    │ processing│ │ links     │ │ streams   │ │ HDA link #0,   │
    │ pipe (PP) │ │ link #0,  │ │ hdac_     │ │ iDISP link #1, │
    │ capability│ │ iDISP #1  │ │ stream[N] │ │ SoundWire,DMIC │
    └───────────┘ └───────────┘ └───────────┘ └────────────────┘
       owned by    (this page)   (sibling      hlink_list
       intel-mtl    via codec     stream page)  via hda_bus_ml_init
       -lnl page    enumeration

    bring-up order (off the PCI probe, two function-pointer-struct ops):
      probe_early ─▶ hda_init ─▶ sof_hda_bus_init ─▶ hda_dsp_ctrl_get_caps
      probe ──────▶ hda_dsp_stream_init ─▶ hda_init_caps
      hda_init_caps ─▶ ctrl_init_chip ─▶ ml_init ─▶ sdw_probe ─▶ codec_probe
```

## SUMMARY

The SOF Intel HDA controller is the host-side HD-Audio controller object that SOF allocates and programs directly, so the same [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) base object the core HD-Audio library defines is what SOF shares across the DSP, the HDA codec links, the SoundWire links, and the DMIC endpoints. SOF nests that base object twice. The codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) embeds it as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member and adds the codec list and the PCI back pointer, and the SOF-private [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) embeds that in turn as [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512). The two-line accessors [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562) and [`sof_to_hbus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L569) read down the SOF private data into the embedded structs, and [`bus_to_sof_hda()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588) is the [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) that recovers the outer struct from a bus pointer.

Bring-up runs in two ops of the platform function pointer struct, both off the PCI probe. [`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) reads the PCI class to confirm the DSP function is enabled, allocates the [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), and calls [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489), which calls [`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69) to initialise the embedded [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) through [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29), maps BAR0 with [`pci_ioremap_bar()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h), and reads the controller capability chain with [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58) so the [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), and [`gtscap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L304) pointers are populated. The main op [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) maps the DSP BAR, calls [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) to build the host DMA streams, claims the shared IRQ, and then calls [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607).

[`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) brings up the controller and everything hanging off it. It runs [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) to reset the controller and detect the codec bitmask, runs [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) to enumerate the HDAudio multi-link block, scans SoundWire with [`hda_sdw_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L137) when the interface mask includes [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) and allocates SoundWire resources with [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159), and finally enumerates HDA codecs with [`hda_codec_probe_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L217). The host DMA streams that [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) builds (one [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) per engine, on [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337), handed out at PCM open by [`hda_dsp_stream_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275)) are the subject of the sibling Intel HDA resources page and are referenced here by name only. The worked example is Intel Meteor Lake, whose [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31) descriptor selects [`sof_mtl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L24); the body of [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) that fills it over [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) is covered by the sibling Intel MTL/LNL dsp_ops page.

## SPECIFICATIONS

The host controller register layout, the GCAP stream-count fields, the buffer-descriptor list (BDL), the position buffer, and the CORB/RIRB command rings are defined by the Intel High Definition Audio Specification. The extended capability chain that [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58) walks, which includes the processing-pipe (PP) capability used by the DSP and the multi-link (ML) capability used by the HDA and SoundWire links, is an Intel extension to that specification, described in this kernel from the multi-link kernel documentation and the capability-id macros in [`hda.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h). The SoundWire links carried on the same controller follow the MIPI Alliance SoundWire (Serial Low-power Inter-chip Media Bus) specification, which is membership-gated and is referenced here only from the kernel source.

## LINUX KERNEL

### Bus object and accessors (hdaudio.h, hda_codec.h, hda.h)

- [`'\<struct hdac_bus\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291): the host HD-Audio controller base object; holds the remapped MMIO base [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), the capability pointers ([`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), [`gtscap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L304), [`drsmcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L305)), the [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320), the [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340) flag, and the [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) and [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378) heads
- [`'\<struct hda_bus\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38): codec-aware wrapper embedding [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member, adding the [`pci`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L43) back pointer, the [`prepare_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L46), and the per-bus PCM device bitmap [`pcm_dev_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L49)
- [`'\<struct sof_intel_hda_dev\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496): SOF-private controller state embedding [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) as [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512); also holds the chip descriptor [`desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L515), the maximum stream count [`stream_max`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L524), the DMIC platform device [`dmic_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L530), the SoundWire scan result [`info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L536), and the SoundWire context [`sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L539)
- [`'\<sof_to_bus\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562): inline accessor returning the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) base object from a [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), reading `hw_pdata` then `&hda->hbus.core`
- [`'\<sof_to_hbus\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L569): inline accessor returning the codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) wrapper from a [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547)
- [`'bus_to_sof_hda':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588): the inverse [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) macro recovering [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) from a [`hbus.core`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512) bus pointer

### Controller mapping and bus init (hda.c, hda-bus.c, ext/bus.c)

- [`'\<hda_init\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489): resolve both bus views, call [`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69), map BAR0 into [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), record it as the HDA BAR, init the i915/HDMI codec path, and read the controller capabilities (the SOF controller mapping, distinct from the unrelated board widget helper of the same name in `sound/soc/intel/boards/`)
- [`'\<sof_hda_bus_init\>':'sound/soc/sof/intel/hda-bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69): initialise the embedded [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), deferring to [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29) when HDA-link support is built in, otherwise zeroing the bus and setting up the stream list, the IRQ field, the index, and the register lock directly
- [`'\<snd_hdac_ext_bus_init\>':'sound/hda/core/ext/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29): the core HD-Audio library entry that chains to [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) and records the extended ops on [`ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291)
- [`'\<hda_dsp_ctrl_get_caps\>':'sound/soc/sof/intel/hda-ctrl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58): reset once, then walk the controller extended-capability chain from the [`SOF_HDA_LLCH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L42) register, setting the per-capability pointers and the matching DSP BAR offsets
- [`'\<hda_dsp_ctrl_init_chip\>':'sound/soc/sof/intel/hda-ctrl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186): reset the controller, exit reset, accept unsolicited responses, optionally detect the codec bitmask with [`hda_codec_detect_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L255), and set [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340)
- [`'\<hda_init_caps\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607): reset the chip and bring up the multi-link block, SoundWire, and the HDA codecs on the controller

### PCI probe entry (hda.c, hda-common-ops.c, pci-mtl.c)

- [`'\<hda_dsp_probe_early\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744): the [`probe_early`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L168) op wired into [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L19); verify the DSP PCI class, allocate [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), and call [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489)
- [`'\<hda_dsp_probe\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793): the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169) op wired into [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L20); register the DMIC platform device, map the DSP BAR, run [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895), claim the IRQ, and call [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607)
- [`'\<hda_pci_intel_probe\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1744): the `.probe` callback of the per-platform PCI driver; forwards to [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190)
- [`'sof_hda_common_ops':'sound/soc/sof/intel/hda-common-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17): the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) shared by every Intel HDA-controller SOF platform, naming the probe, stream, and machine callbacks
- [`'mtl_desc':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31): the Meteor Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L173) is [`sof_mtl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L24), whose [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L150) is [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), and whose [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L156) is `BIT(SOF_IPC_TYPE_4)`
- [`'sof_pci_ids':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L122): the PCI id table binding the `HDA_MTL` and `HDA_ARL` device ids to their descriptors

### Multi-link block, SoundWire, and codecs (hda-mlink.c, hda.c, hda-codec.c)

- [`'\<hda_bus_ml_init\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426): read the multi-link capability count from [`AZX_REG_ML_MLCD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L261) and allocate one host-to-link descriptor per link with [`hda_ml_alloc_h2link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L389)
- [`'\<hda_ml_alloc_h2link\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L389): allocate one [`struct hdac_ext2_link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L48), set its index and `ml_addr`, enumerate it, and add its [`struct hdac_ext_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L95) onto [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378)
- [`'\<hda_bus_ml_put_all\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L883): drop the runtime-PM refcount on every multi-link descriptor once codec probing is done
- [`'\<hda_sdw_acpi_scan\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L137): resolve the DSP ACPI handle and scan the DSDT for SoundWire controller information into [`info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L536)
- [`'\<hda_sdw_probe\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159): build a [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h) and call [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333), selecting the Cannon Lake or Lunar Lake SoundWire hardware ops by the chip IP version
- [`'\<hda_codec_probe_bus\>':'sound/soc/sof/intel/hda-codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L217): probe an HDA codec in each populated slot of [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) via [`hda_codec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L149)
- [`'\<enum sof_ipc_dai_type\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76): the SOF DAI type enum whose values [`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80) and [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) gate the HDA-link and SoundWire bring-up

### Host DMA streams referenced by name (hdaudio.h, hda-stream.c)

- [`'\<struct hdac_stream\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516): one host DMA engine of the controller; built and managed by the sibling Intel HDA resources page, listed here because the [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) head it links onto is a field of the controller object
- [`'\<struct hdac_ext_stream\>':'include/sound/hdaudio_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47): wraps [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) as [`hstream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L48) and adds the processing-pipe register pointers; owned by the sibling resources page
- [`'\<hda_dsp_stream_init\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895): read GCAP for the stream counts and build one stream object per engine; called from [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793), detailed on the sibling resources page
- [`'\<hda_dsp_stream_get\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L275): hand out an unused stream of a direction at PCM open; detailed on the sibling resources page

## KERNEL DOCUMENTATION

- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the HDAudio multi-link structure on Intel platforms, the link mapping (HDA link #0, iDISP link #1), and the SoundWire link extensions that [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) parses
- [`Documentation/sound/hd-audio/notes.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/notes.rst): the HD-Audio controller and codec model that the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) base object implements
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end/back-end model SOF uses to route a host DMA stream to a DSP pipeline and then to an HDA, SoundWire, or DMIC back end
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle on the links that [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) brings up on the same controller

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Intel High Definition Audio Specification](https://www.intel.com/content/www/us/en/standards/high-definition-audio-specification.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The controller comes up through one PCI bind that runs in two ops of the platform function pointer struct, then exposes its host DMA streams to the PCM layer. The early op maps the controller and reads its capabilities, the main op builds the streams and brings up the links and codecs, and the per-substream op (owned by the sibling resources page) hands out a host DMA stream. The objects below have one creator each, so a reader can follow a link from the PCI bind down into the embedded bus object and out to the multi-link descriptors and codecs.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) | [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) in [`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) | the DSP device (devm) |
| [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512) | embedded; initialised by [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489) | embedded in [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) |
| [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) | embedded; set up by [`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69) | embedded in [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) |
| capability pointers ([`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303), ...) | [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58) | the controller |
| multi-link descriptors on [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378) | [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) | the controller |
| [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) on [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) | [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) (sibling page) | the controller |

### hda_dsp_probe_early maps the controller

The early op [`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) is the first pass that may return `-EPROBE_DEFER`, so it runs outside the probe workqueue. It reads the PCI class to confirm the DSP function is present, allocates the [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48), and calls [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489), which maps BAR0 and reads the capability chain.

### hda_dsp_probe builds streams and brings up the links

The main op [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) maps the DSP BAR, runs [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) to build one [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) per host DMA engine, claims the shared IRQ, and calls [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) to reset the chip and bring up the multi-link block, SoundWire, and the codecs.

### hda_init_caps resets the chip and enumerates every link type

[`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) resets the controller with [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186), enumerates the multi-link block with [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426), conditionally scans and probes SoundWire, and creates HDA codec instances with [`hda_codec_probe_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L217).

## DETAILS

### The controller is the bus base object SOF embeds

The host side of the HD-Audio controller is [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), the base object the core HD-Audio library uses for every HD-Audio controller in the kernel. SOF does not re-declare the controller's fields; it embeds the existing object and reuses the whole core library on top of it. The capability pointers, the codec bitmask, the [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340) flag, and the two list heads that the rest of this page refers to are all fields of this one struct:

```c
/* include/sound/hdaudio.h:291 */
struct hdac_bus {
	struct device *dev;
	const struct hdac_bus_ops *ops;
	const struct hdac_ext_bus_ops *ext_ops;

	/* h/w resources */
	unsigned long addr;
	void __iomem *remap_addr;
	int irq;

	void __iomem *ppcap;
	void __iomem *spbcap;
	void __iomem *mlcap;
	void __iomem *gtscap;
	void __iomem *drsmcap;

	/* codec linked list */
	struct list_head codec_list;
	unsigned int num_codecs;
	...
	/* bit flags of detected codecs */
	unsigned long codec_mask;
	...
	/* hdac_stream linked list */
	struct list_head stream_list;

	/* operation state */
	bool chip_init:1;		/* h/w initialized */
	...
	/* link management */
	struct list_head hlink_list;
	bool cmd_dma_state;
	...
};
```

[`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301) is the processing-pipe capability pointer, non-NULL only when the DSP function is present, and [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) is the multi-link capability pointer that the HDA and SoundWire links sit behind. [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) is the bitmask of HDA codec slots that responded after reset. [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) holds the host DMA streams that the sibling resources page builds, and [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378) holds the multi-link descriptors that [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) builds.

SOF wraps that base object twice. The codec-aware [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) embeds it as [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) and adds the [`pci`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L42) back pointer the controller needs along with the codec-list bookkeeping:

```c
/* include/sound/hda_codec.h:38 */
struct hda_bus {
	struct hdac_bus core;

	struct snd_card *card;

	struct pci_dev *pci;
	const char *modelname;

	struct mutex prepare_mutex;

	/* assigned PCMs */
	DECLARE_BITMAP(pcm_dev_bits, SNDRV_PCM_DEVICES);
	...
	unsigned int mixer_assigned;	/* codec addr for mixer name */
};
```

That, in turn, is embedded as [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512) inside the SOF-private [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), which adds the chip descriptor, the maximum stream count, the DMIC platform device, the SoundWire scan result, and the SoundWire context:

```c
/* sound/soc/sof/intel/hda.h:496 */
struct sof_intel_hda_dev {
	...
	struct hda_bus hbus;

	/* hw config */
	const struct sof_intel_dsp_desc *desc;

	/* trace */
	struct hdac_ext_stream *dtrace_stream;
	...
	/* the maximum number of streams (playback + capture) supported */
	u32 stream_max;
	...
	/* DMIC device */
	struct platform_device *dmic_dev;
	...
	/* ACPI information stored between scan and probe steps */
	struct sdw_intel_acpi_info info;

	/* sdw context allocated by SoundWire driver */
	struct sdw_intel_ctx *sdw;
	...
	/* Intel NHLT information */
	struct nhlt_acpi_table *nhlt;
	...
};
```

The two nestings let SOF reach any layer from a [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547). [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562) returns the controller base object and [`sof_to_hbus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L569) returns the codec-aware wrapper, both reading the SOF hardware private data and then walking into the embedded structs:

```c
/* sound/soc/sof/intel/hda.h:562 */
static inline struct hdac_bus *sof_to_bus(struct snd_sof_dev *s)
{
	struct sof_intel_hda_dev *hda = s->pdata->hw_pdata;

	return &hda->hbus.core;
}

static inline struct hda_bus *sof_to_hbus(struct snd_sof_dev *s)
{
	struct sof_intel_hda_dev *hda = s->pdata->hw_pdata;

	return &hda->hbus;
}
```

The inverse direction uses [`bus_to_sof_hda()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588), a [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) from a bus pointer back to the enclosing SOF struct, used where a callback receives the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) but needs the SOF-private fields:

```c
/* sound/soc/sof/intel/hda.h:588 */
#define bus_to_sof_hda(bus) \
	container_of(bus, struct sof_intel_hda_dev, hbus.core)
```

### hda_init maps the controller and reads its capability chain

[`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489) is the first controller-specific step, called from [`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744). The name is reused in the tree (an unrelated DAPM-widget helper in `sound/soc/intel/boards/sof_board_helpers.c` is also named `hda_init`); the one here is the SOF controller mapping. It resolves both bus views through the accessors, calls [`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69), maps BAR0 of the PCI device into [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), records that mapping as the HDA BAR, brings up the i915/HDMI codec path, and reads the controller capabilities:

```c
/* sound/soc/sof/intel/hda.c:489 */
static int hda_init(struct snd_sof_dev *sdev)
{
	struct hda_bus *hbus;
	struct hdac_bus *bus;
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	int ret;

	hbus = sof_to_hbus(sdev);
	bus = sof_to_bus(sdev);

	/* HDA bus init */
	sof_hda_bus_init(sdev, &pci->dev);
	...
	mutex_init(&hbus->prepare_mutex);
	hbus->pci = pci;
	hbus->mixer_assigned = -1;
	hbus->modelname = hda_model;

	/* initialise hdac bus */
	bus->addr = pci_resource_start(pci, 0);
	bus->remap_addr = pci_ioremap_bar(pci, 0);
	if (!bus->remap_addr) {
		dev_err(bus->dev, "error: ioremap error\n");
		return -ENXIO;
	}

	/* HDA base */
	sdev->bar[HDA_DSP_HDA_BAR] = bus->remap_addr;

	/* init i915 and HDMI codecs */
	ret = hda_codec_i915_init(sdev);
	if (ret < 0 && ret != -ENODEV) {
		dev_err_probe(sdev->dev, ret, "init of i915 and HDMI codec failed\n");
		goto out;
	}

	/* get controller capabilities */
	ret = hda_dsp_ctrl_get_caps(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "error: get caps error\n");
		hda_codec_i915_exit(sdev);
	}

out:
	if (ret < 0)
		iounmap(sof_to_bus(sdev)->remap_addr);

	return ret;
}
```

[`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69) is the bus initialiser, and its body is selected at compile time by the HDA-link and HDA-codec config options. According to the comment, it "can be used for both with/without hda link support". When HDA-link support is built in it defers to the core library entry [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29); otherwise it zeroes the bus and sets up the stream list, the IRQ field, the bus index, and the register lock by hand:

```c
/* sound/soc/sof/intel/hda-bus.c:69 */
void sof_hda_bus_init(struct snd_sof_dev *sdev, struct device *dev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);

#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_LINK)
#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_AUDIO_CODEC)
	const struct sof_intel_dsp_desc *chip = get_chip_info(sdev->pdata);

	snd_hdac_ext_bus_init(bus, dev, &bus_core_ops, sof_hda_ext_ops);

	if (chip && chip->hw_ip_version >= SOF_INTEL_ACE_2_0)
		bus->use_pio_for_commands = true;
#else
	snd_hdac_ext_bus_init(bus, dev, NULL, NULL);
#endif
#else

	memset(bus, 0, sizeof(*bus));
	bus->dev = dev;

	INIT_LIST_HEAD(&bus->stream_list);

	bus->irq = -1;
	...
	bus->idx = 0;

	spin_lock_init(&bus->reg_lock);
#endif /* CONFIG_SND_SOC_SOF_HDA_LINK */
}
```

The core library entry [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29) chains to [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) and then records the extended ops, so the SOF-driven controller and a legacy HD-Audio controller share the same base initialisation:

```c
/* sound/hda/core/ext/bus.c:29 */
int snd_hdac_ext_bus_init(struct hdac_bus *bus, struct device *dev,
			const struct hdac_bus_ops *ops,
			const struct hdac_ext_bus_ops *ext_ops)
{
	int ret;

	ret = snd_hdac_bus_init(bus, dev, ops);
	if (ret < 0)
		return ret;

	bus->ext_ops = ext_ops;
	...
	bus->idx = 0;
	bus->cmd_dma_state = true;

	return 0;
}
```

### hda_dsp_ctrl_get_caps parses the extended capability chain

[`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58) reads the extended-capability linked list starting from the [`SOF_HDA_LLCH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L42) register and, for each capability id, stores the remapped capability pointer into the matching field of the bus and (for some) the matching DSP BAR slot. The capability id is extracted with [`SOF_HDA_CAP_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L62) and the next-capability offset with [`SOF_HDA_CAP_NEXT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L64); the loop bounds the walk at [`SOF_HDA_MAX_CAPS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L60) iterations:

```c
/* sound/soc/sof/intel/hda-ctrl.c:58 */
int hda_dsp_ctrl_get_caps(struct snd_sof_dev *sdev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	u32 cap, offset, feature;
	int count = 0;
	int ret;

	/*
	 * On some devices, one reset cycle is necessary before reading
	 * capabilities
	 */
	ret = hda_dsp_ctrl_link_reset(sdev, true);
	if (ret < 0)
		return ret;
	ret = hda_dsp_ctrl_link_reset(sdev, false);
	if (ret < 0)
		return ret;

	offset = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, SOF_HDA_LLCH);

	do {
		...
		cap = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, offset);

		if (cap == -1) {
			dev_dbg(bus->dev, "Invalid capability reg read\n");
			break;
		}

		feature = (cap & SOF_HDA_CAP_ID_MASK) >> SOF_HDA_CAP_ID_OFF;

		switch (feature) {
		case SOF_HDA_PP_CAP_ID:
			dev_dbg(sdev->dev, "found DSP capability at 0x%x\n",
				offset);
			bus->ppcap = bus->remap_addr + offset;
			sdev->bar[HDA_DSP_PP_BAR] = bus->ppcap;
			break;
		case SOF_HDA_SPIB_CAP_ID:
			...
			bus->spbcap = bus->remap_addr + offset;
			sdev->bar[HDA_DSP_SPIB_BAR] = bus->spbcap;
			break;
		case SOF_HDA_DRSM_CAP_ID:
			...
			bus->drsmcap = bus->remap_addr + offset;
			sdev->bar[HDA_DSP_DRSM_BAR] = bus->drsmcap;
			break;
		case SOF_HDA_GTS_CAP_ID:
			...
			bus->gtscap = bus->remap_addr + offset;
			break;
		case SOF_HDA_ML_CAP_ID:
			dev_dbg(sdev->dev, "found ML capability at 0x%x\n",
				offset);
			bus->mlcap = bus->remap_addr + offset;
			break;
		default:
			...
			break;
		}

		offset = cap & SOF_HDA_CAP_NEXT_MASK;
	} while (count++ <= SOF_HDA_MAX_CAPS && offset);

	return 0;
}
```

The processing-pipe (PP) capability id [`SOF_HDA_PP_CAP_ID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L69) yields [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301) and the DSP processing-pipe BAR, and the multi-link (ML) capability id [`SOF_HDA_ML_CAP_ID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L67) yields [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303). The presence of [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301) is what tells SOF the DSP is reachable through this same controller, and [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) reads it back to log that the DSP will be probed later.

```
    Capability-id walk: each id stores a bus pointer and a BAR slot
    ───────────────────────────────────────────────────────────────

    offset = read SOF_HDA_LLCH; loop: id = cap & SOF_HDA_CAP_ID_MASK

    ┌──────────────────────┬───────────────┬───────────────────┐
    │ capability id        │ bus pointer   │ DSP BAR slot      │
    ├──────────────────────┼───────────────┼───────────────────┤
    │ SOF_HDA_PP_CAP_ID    │ ppcap         │ HDA_DSP_PP_BAR    │
    │ SOF_HDA_SPIB_CAP_ID  │ spbcap        │ HDA_DSP_SPIB_BAR  │
    │ SOF_HDA_DRSM_CAP_ID  │ drsmcap       │ HDA_DSP_DRSM_BAR  │
    │ SOF_HDA_GTS_CAP_ID   │ gtscap        │ (none)            │
    │ SOF_HDA_ML_CAP_ID    │ mlcap         │ (none)            │
    └──────────────────────┴───────────────┴───────────────────┘

    pointer = remap_addr + offset
    offset  = cap & SOF_HDA_CAP_NEXT_MASK   (next link; 0 ends walk)
    bounded by SOF_HDA_MAX_CAPS iterations
```

### hda_dsp_probe_early and hda_dsp_probe split the bring-up

The controller comes up across two ops of the function pointer struct, both members of [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17):

```c
/* sound/soc/sof/intel/hda-common-ops.c:17 */
const struct snd_sof_dsp_ops sof_hda_common_ops = {
	/* probe/remove/shutdown */
	.probe_early	= hda_dsp_probe_early,
	.probe		= hda_dsp_probe,
	...
};
```

[`hda_dsp_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) confirms the DSP function is enabled by reading the PCI class/subclass/prog-if, allocates the [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), and calls [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489). According to the comment, class `0x040300` means "no DSP, legacy driver is required", class `0x040100` means "DSP is present", and class `0x040380` means "either of DSP or legacy mode works", so SOF aborts the probe on the legacy-only class and on any other unknown class:

```c
/* sound/soc/sof/intel/hda.c:744 */
int hda_dsp_probe_early(struct snd_sof_dev *sdev)
{
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	struct sof_intel_hda_dev *hdev;
	const struct sof_intel_dsp_desc *chip;
	int ret = 0;

	if (!sdev->dspless_mode_selected) {
		/*
		 * detect DSP by checking class/subclass/prog-id information
		 * class=04 subclass 03 prog-if 00: no DSP, legacy driver is required
		 * class=04 subclass 01 prog-if 00: DSP is present
		 *   (and may be required e.g. for DMIC or SSP support)
		 * class=04 subclass 03 prog-if 80: either of DSP or legacy mode works
		 */
		if (pci->class == 0x040300) {
			dev_err(sdev->dev, "the DSP is not enabled on this platform, aborting probe\n");
			return -ENODEV;
		} else if (pci->class != 0x040100 && pci->class != 0x040380) {
			dev_err(sdev->dev, "unknown PCI class/subclass/prog-if 0x%06x found, aborting probe\n",
				pci->class);
			return -ENODEV;
		}
		...
	}

	chip = get_chip_info(sdev->pdata);
	...
	hdev = devm_kzalloc(sdev->dev, sizeof(*hdev), GFP_KERNEL);
	if (!hdev)
		return -ENOMEM;
	sdev->pdata->hw_pdata = hdev;
	hdev->desc = chip;
	ret = hda_init(sdev);

err:
	return ret;
}
```

[`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) is the main op. It registers the DMIC platform device, maps the DSP BAR, sets the DMA mask, calls [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) to build the host DMA streams (the sibling resources page owns that function), requests the shared IRQ, and then calls [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607):

```c
/* sound/soc/sof/intel/hda.c:793 */
int hda_dsp_probe(struct snd_sof_dev *sdev)
{
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	struct sof_intel_hda_dev *hdev = sdev->pdata->hw_pdata;
	...
	hdev->dmic_dev = platform_device_register_data(sdev->dev, "dmic-codec",
						       PLATFORM_DEVID_NONE,
						       NULL, 0);
	...
	/* DSP base */
	sdev->bar[HDA_DSP_BAR] = pci_ioremap_bar(pci, HDA_DSP_BAR);
	...
	/* init streams */
	ret = hda_dsp_stream_init(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "error: failed to init streams\n");
		...
		goto free_streams;
	}
	...
	/* init HDA capabilities */
	ret = hda_init_caps(sdev);
	if (ret < 0)
		goto free_ipc_irq;
	...
}
```

The order is fixed. [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) needs the DSP BAR offsets that [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58) populated during the early stage, and [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) resets the controller only after the streams and the IRQ are in place.

```
    PCI class/subclass/prog-if decoded by hda_dsp_probe_early
    ─────────────────────────────────────────────────────────

    ┌────────────┬────────────────────────────┬──────────────────┐
    │ pci->class │ meaning                    │ probe action     │
    ├────────────┼────────────────────────────┼──────────────────┤
    │ 0x040300   │ no DSP, legacy driver only │ return -ENODEV   │
    │ 0x040100   │ DSP is present             │ continue probe   │
    │ 0x040380   │ DSP or legacy both work    │ continue probe   │
    │ other      │ unknown class              │ return -ENODEV   │
    └────────────┴────────────────────────────┴──────────────────┘

    04 = multimedia, 03 = HD-Audio (legacy), 01 = DSP signal processor
```

### hda_init_caps resets the controller and brings up everything on it

[`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) is the controller bring-up proper. It logs the DSP presence from [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), resets the controller with [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186), enumerates the multi-link block with [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426), then conditionally brings up SoundWire and unconditionally probes the HDA codecs:

```c
/* sound/soc/sof/intel/hda.c:607 */
static int hda_init_caps(struct snd_sof_dev *sdev)
{
	u32 interface_mask = hda_get_interface_mask(sdev);
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct snd_sof_pdata *pdata = sdev->pdata;
	struct sof_intel_hda_dev *hdev = pdata->hw_pdata;
	u32 link_mask;
	int ret = 0;

	/* check if dsp is there */
	if (bus->ppcap)
		dev_dbg(sdev->dev, "PP capability, will probe DSP later.\n");

	/* Init HDA controller after i915 init */
	ret = hda_dsp_ctrl_init_chip(sdev, true);
	if (ret < 0) {
		dev_err(bus->dev, "error: init chip failed with ret: %d\n",
			ret);
		return ret;
	}

	hda_bus_ml_init(bus);

	/* Skip SoundWire if it is not supported */
	if (!(interface_mask & BIT(SOF_DAI_INTEL_ALH)))
		goto skip_soundwire;
	...
	/* scan SoundWire capabilities exposed by DSDT */
	ret = hda_sdw_acpi_scan(sdev);
	if (ret < 0) {
		dev_dbg(sdev->dev, "skipping SoundWire, not detected with ACPI scan\n");
		goto skip_soundwire;
	}

	link_mask = hdev->info.link_mask;
	if (!link_mask) {
		dev_dbg(sdev->dev, "skipping SoundWire, no links enabled\n");
		goto skip_soundwire;
	}
	...
	ret = hda_sdw_probe(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "error: SoundWire probe error\n");
		return ret;
	}

skip_soundwire:

	/* create codec instances */
	hda_codec_probe_bus(sdev);

	if (!HDA_IDISP_CODEC(bus->codec_mask))
		hda_codec_i915_display_power(sdev, false);

	hda_bus_ml_put_all(bus);

	return 0;
}
```

The SoundWire branch is gated on `interface_mask & BIT(SOF_DAI_INTEL_ALH)`, where [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) is the Audio-Link-Hub DAI type the SoundWire path uses, distinct from [`SOF_DAI_INTEL_HDA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L80) for HDA-link codecs. According to the comment in [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607), "It's entirely possible to have a mix of I2S/DMIC/SoundWire devices, so we allocate the resources in all cases", which is why a single controller can carry HDA codecs, SoundWire peripherals, and DMIC endpoints at once. The closing [`hda_bus_ml_put_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L883) drops the runtime-PM refcount on the multi-link descriptors once the codecs have been probed.

[`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) does the controller reset itself. It short-circuits if [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340) is already set, takes the controller into and out of link reset, accepts unsolicited responses by setting [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27), and when its `detect_codec` argument is true detects the codec bitmask with [`hda_codec_detect_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L255):

```c
/* sound/soc/sof/intel/hda-ctrl.c:186 */
int hda_dsp_ctrl_init_chip(struct snd_sof_dev *sdev, bool detect_codec)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct hdac_stream *stream;
	int sd_offset, ret = 0;
	u32 gctl;

	if (bus->chip_init)
		return 0;
	...
	/* reset HDA controller */
	ret = hda_dsp_ctrl_link_reset(sdev, true);
	if (ret < 0) {
		dev_err(sdev->dev, "error: failed to reset HDA controller\n");
		goto err;
	}

	usleep_range(500, 1000);

	/* exit HDA controller reset */
	ret = hda_dsp_ctrl_link_reset(sdev, false);
	if (ret < 0) {
		dev_err(sdev->dev, "error: failed to exit HDA controller reset\n");
		goto err;
	}
	usleep_range(1000, 1200);

	/* Accept unsolicited responses */
	snd_hdac_chip_updatel(bus, GCTL, AZX_GCTL_UNSOL, AZX_GCTL_UNSOL);

	if (detect_codec)
		hda_codec_detect_mask(sdev);
	...
	bus->chip_init = true;

err:
	...
	return ret;
}
```

### The multi-link block carries both HDA and SoundWire links

[`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) enumerates the multi-link block once [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) is set. It reads the link count from the multi-link capability descriptor register [`AZX_REG_ML_MLCD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L261) (a zero-based count, so the read is incremented by one) and allocates one host-to-link descriptor per link with [`hda_ml_alloc_h2link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L389):

```c
/* sound/soc/sof/intel/hda-mlink.c:426 */
int hda_bus_ml_init(struct hdac_bus *bus)
{
	u32 link_count;
	int ret;
	int i;

	if (!bus->mlcap)
		return 0;

	link_count = readl(bus->mlcap + AZX_REG_ML_MLCD) + 1;

	dev_dbg(bus->dev, "HDAudio Multi-Link count: %d\n", link_count);

	for (i = 0; i < link_count; i++) {
		ret = hda_ml_alloc_h2link(bus, i);
		if (ret < 0) {
			hda_bus_ml_free(bus);
			return ret;
		}
	}
	return 0;
}
```

Each [`hda_ml_alloc_h2link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L389) call allocates a descriptor, computes the per-link register window from [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303), enumerates the link, and links the resulting [`struct hdac_ext_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L95) onto [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378):

```c
/* sound/soc/sof/intel/hda-mlink.c:389 */
static int hda_ml_alloc_h2link(struct hdac_bus *bus, int index)
{
	struct hdac_ext2_link *h2link;
	struct hdac_ext_link *hlink;
	int ret;

	h2link = kzalloc_obj(*h2link);
	if (!h2link)
		return -ENOMEM;

	/* basic initialization */
	hlink = &h2link->hext_link;

	hlink->index = index;
	hlink->bus = bus;
	hlink->ml_addr = bus->mlcap + AZX_ML_BASE + (AZX_ML_INTERVAL * index);

	ret = hdaml_lnk_enum(bus->dev, h2link, bus->remap_addr, hlink->ml_addr, index);
	if (ret < 0) {
		kfree(h2link);
		return ret;
	}

	mutex_init(&h2link->eml_lock);

	list_add_tail(&hlink->list, &bus->hlink_list);
	...
	return 0;
}
```

According to [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst), "External HDAudio codecs are handled with link #0, while iDISP codec for HDMI/DisplayPort is handled with link #1", and the SoundWire links are further entries in the same multi-link structure, so [`hda_bus_ml_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L426) is the single point that discovers every link type the controller exposes.

SoundWire bring-up follows when the ACPI scan finds links. [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) selects the SoundWire hardware ops by the chip IP version, using the older Cannon Lake ops for pre-ACE parts and the Lunar Lake (extended multi-link) ops for ACE 2.0 and later, where the SoundWire registers are mapped in the HDAudio multi-link areas of the same controller; the SoundWire controller itself is the subject of the Intel SoundWire controller page and is not re-derived here:

```c
/* sound/soc/sof/intel/hda.c:159 */
static int hda_sdw_probe(struct snd_sof_dev *sdev)
{
	const struct sof_intel_dsp_desc *chip;
	struct sof_intel_hda_dev *hdev;
	struct sdw_intel_res res;
	void *sdw;

	hdev = sdev->pdata->hw_pdata;

	memset(&res, 0, sizeof(res));

	chip = get_chip_info(sdev->pdata);
	if (chip->hw_ip_version < SOF_INTEL_ACE_2_0) {
		res.mmio_base = sdev->bar[HDA_DSP_BAR];
		res.hw_ops = &sdw_intel_cnl_hw_ops;
		res.shim_base = hdev->desc->sdw_shim_base;
		res.alh_base = hdev->desc->sdw_alh_base;
		res.ext = false;
		res.ops = &sdw_callback;
	} else {
		/*
		 * retrieve eml_lock needed to protect shared registers
		 * in the HDaudio multi-link areas
		 */
		res.eml_lock = hdac_bus_eml_get_mutex(sof_to_bus(sdev), true,
						      AZX_REG_ML_LEPTR_ID_SDW);
		...
		res.mmio_base = sdev->bar[HDA_DSP_HDA_BAR];
		...
	}
	...
}
```

The same multi-link block the SoundWire registers live in lays each link descriptor at mlcap plus a per-index stride, link #0 carrying the HDA codecs and link #1 the iDISP display, all chained on hlink_list:

```
    Multi-link register window: one descriptor per link at base+stride
    ──────────────────────────────────────────────────────────────────

    ml_addr = mlcap + AZX_ML_BASE + AZX_ML_INTERVAL * index
    link_count = readl(mlcap + AZX_REG_ML_MLCD) + 1

           mlcap
             │
             ▼  + AZX_ML_BASE
    ┌────────────────────┐  index 0   HDA codecs (link #0)
    │  hdac_ext_link[0]  │  ml_addr = mlcap + AZX_ML_BASE
    ├────────────────────┤  index 1   iDISP HDMI/DP (link #1)
    │  hdac_ext_link[1]  │  ml_addr += AZX_ML_INTERVAL
    ├────────────────────┤  index 2   SoundWire / DMIC links
    │  hdac_ext_link[2]  │  ml_addr += AZX_ML_INTERVAL
    ├────────────────────┤
    │        ...         │  each enumerated, linked on hlink_list
    └────────────────────┘
```

### HDA codec enumeration walks the detected bitmask

[`hda_codec_probe_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L217) is the last step. It walks every bit of [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) (the mask [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) detected) and probes a codec in each populated slot through [`hda_codec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L149), clearing the bit if the probe fails:

```c
/* sound/soc/sof/intel/hda-codec.c:217 */
void hda_codec_probe_bus(struct snd_sof_dev *sdev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	int i, ret;
	...
	/* probe codecs in avail slots */
	for (i = 0; i < HDA_MAX_CODECS; i++) {

		if (!(bus->codec_mask & (1 << i)))
			continue;

		ret = hda_codec_probe(sdev, i);
		if (ret < 0) {
			dev_warn(bus->dev, "codec #%d probe error, ret: %d\n",
				 i, ret);
			bus->codec_mask &= ~BIT(i);
		}
	}
}
```

### The Meteor Lake descriptor selects the function pointer struct

The worked example is Intel Meteor Lake. Its PCI id binds through [`sof_pci_ids`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L122) to [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31), the [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L173) is [`sof_mtl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L24), whose [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L150) is [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), and which advertises IPC4 only:

```c
/* sound/soc/sof/intel/pci-mtl.c:31 */
static const struct sof_dev_desc mtl_desc = {
	.use_acpi_target_states	= true,
	.machines               = snd_soc_acpi_intel_mtl_machines,
	.alt_machines		= snd_soc_acpi_intel_mtl_sdw_machines,
	...
	.chip_info = &mtl_chip_info,
	.ipc_supported_mask	= BIT(SOF_IPC_TYPE_4),
	.ipc_default		= SOF_IPC_TYPE_4,
	.dspless_mode_supported	= true,		/* Only supported for HDaudio */
	...
	.ops = &sof_mtl_ops,
	.ops_init = sof_mtl_ops_init,
	.ops_free = hda_ops_free,
};
```

The [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L174) hook [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) calls [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702), which copies [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) (the base that names [`hda_dsp_probe_early`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L744) and [`hda_dsp_probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793)) into [`sof_mtl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L24) and applies the MTL IPC, firmware, and core-power overrides. The body of that fill is covered by the sibling Intel MTL/LNL dsp_ops page; this page stops at the probe and capability surface that the common ops reach.

### The HDA controller bus object and its bring-up order

This figure shows the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) nested inside [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) and [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), the DSP, HDA-link, host-DMA-stream, and multi-link consumers that hang off its capability pointers and lists, and the order in which [`hda_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L489) and [`hda_init_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L607) bring the controller up.

```
    SOF Intel HDA controller bring-up (one PCI device, x86-64 ACPI)
    ──────────────────────────────────────────────────────────────

    struct sof_intel_hda_dev
    ┌────────────────────────────────────────────────────────────┐
    │  struct hda_bus hbus                                       │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │  struct hdac_bus core   (host HD-Audio controller)   │  │
    │  │    remap_addr   ppcap   mlcap   spbcap   gtscap      │  │
    │  │    codec_mask   stream_list   hlink_list             │  │
    │  └───┬───────────────┬──────────────┬─────────────┬─────┘  │
    └──────┼───────────────┼──────────────┼─────────────┼────────┘
           ▼               ▼              ▼             ▼
     ┌──────────┐  ┌──────────────┐ ┌───────────┐ ┌──────────────┐
     │ DSP (PP  │  │ HDA link #0  │ │ host DMA  │ │ multi-link:  │
     │ capabil- │  │ codecs +     │ │ streams   │ │ SoundWire +  │
     │ ity, DSP │  │ link #1      │ │ hdac_     │ │ DMIC links   │
     │ PCI func)│  │ iDISP HDMI   │ │ stream[N] │ │ hlink_list   │
     └──────────┘  └──────────────┘ └───────────┘ └──────────────┘
       ppcap          codec_mask      stream_list      mlcap

    bring-up order:
      hda_init ─▶ sof_hda_bus_init ─▶ hda_dsp_ctrl_get_caps
      hda_dsp_probe ─▶ hda_dsp_stream_init ─▶ hda_init_caps
      hda_init_caps ─▶ ctrl_init_chip ─▶ ml_init ─▶ sdw_probe ─▶ codec_probe
```
