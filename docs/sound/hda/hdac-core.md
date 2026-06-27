# HD-Audio core

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The HD-Audio core is the set of transport objects under [`sound/hda/core/`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core) that model an Intel High Definition Audio host controller independently of any one driver, and the three objects at its center are the controller bus [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291), a codec on that bus [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52), and a host DMA stream [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516). The bus owns the MMIO mapping, the CORB/RIRB command rings carried in two [`struct hdac_rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L269) records, the [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308) of codecs and the [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) of DMA engines, and the capability pointers ([`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303)) that the controller exposes through its linked capability list. Each [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) maps one stream descriptor register block (SDn) and the buffer descriptor list (BDL) that feeds it. On an x86-64 platform that boots Sound Open Firmware (SOF), the SOF Intel driver embeds one of these buses inside [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) and reuses [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31), [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609), and the stream functions to drive the same controller silicon the legacy [`sound/hda/common/`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common) driver drives, except that SOF uses the controller to host the DSP and the SoundWire, DMIC, and SSP links rather than only HD-Audio codecs.

```
    HD-Audio core object hierarchy
    ──────────────────────────────

    struct hdac_bus                          (the controller)
    ┌────────────────────────────────────────────────────────────┐
    │  remap_addr (MMIO)   ops ─▶ hdac_bus_ops                   │
    │  ppcap  spbcap  mlcap   (capability pointers)              │
    │  corb : hdac_rb   rirb : hdac_rb        (command rings)    │
    │  codec_list ─┐                                             │
    │  stream_list ┼───────────┐                                 │
    └──────────────┼───────────┼─────────────────────────────────┘
                   │           │
        ┌──────────┴───┐       └──────────┬──────────┬──────────┐
        ▼              ▼                  ▼          ▼          ▼
   struct hdac_device  ...          struct hdac_stream  ...  (SDn rings)
   ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐
   │ addr (caddr) │ │ addr (caddr) │ │ sd_addr    │ │ sd_addr    │
   │ vendor_id    │ │ vendor_id    │ │ bdl (BDL)  │ │ bdl (BDL)  │
   │ subsystem_id │ │ subsystem_id │ │ direction  │ │ direction  │
   │ widgets ─▶   │ │ widgets ─▶   │ │ lpib/dpib  │ │ lpib/dpib  │
   └──────────────┘ └──────────────┘ └────────────┘ └────────────┘
     codecs on the link             host DMA stream rings (SDIn/SDOn)
```

## SUMMARY

The HD-Audio core factors an Intel HD-Audio controller into one bus object and two object families hung off it. [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) holds the controller's MMIO base in [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298), a [`const struct hdac_bus_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L243) function pointer struct in [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293) for sending a verb and reading its response, a [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) bitmap of detected codec addresses, the [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308) and [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) heads, the [`corb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L326) and [`rirb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L327) command rings, and the [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), and [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) capability pointers. Each codec on the link is a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) recording its link address in [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L56), its [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) and [`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64), its widget tree in [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L89), and the bound [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222). Each host DMA engine is a [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) mapping one stream descriptor register block through [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), carrying the buffer descriptor list in [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518), its [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), and the position values [`lpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L534) and [`dpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L533).

The core supplies the functions that bring those objects to life. [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) zeroes a bus and initializes its lists and locks, [`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406) walks the controller's linked capability list and fills the [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301)/[`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302)/[`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointers, and [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609) resets the controller, programs the CORB/RIRB through [`snd_hdac_bus_init_cmd_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L43), and enables interrupts. On the stream side, [`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) computes the SDn register offset and links the stream onto the bus, [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361) hands an unused stream to a PCM substream, [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) programs the stream tag, cyclic buffer length, format, and BDL base into the SDn registers, and [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) sets the run bit. The SOF Intel driver wraps a bus in [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) (through an intermediate [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38)), reaches it with [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562), and brings the controller up in [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) and [`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895).

The same core objects back the legacy controller driver too. [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018) wraps [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609), [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) calls [`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406), [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L43) calls [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361), [`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152) calls [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257), and [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) calls [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41).

## SPECIFICATIONS

The objects model the controller and link defined by the Intel High Definition Audio specification. [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) sets [`sdo_limit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L382) to 8 and its comment cites the rule for the STRIPE control value as per Rev 1.0a, and [`snd_hdac_bus_reset_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L523) cites the codec PLL settle delay of Rev 0.9 section 5.5.1.

- Intel High Definition Audio Specification, section 3.3: controller register set (GCAP, GCTL, INTCTL, INTSTS, CORB/RIRB, stream descriptors)
- Intel High Definition Audio Specification, section 3.3.36: stream descriptor (SDn) register block
- Intel High Definition Audio Specification, section 4.4.1: command output ring buffer (CORB) and response input ring buffer (RIRB)
- Intel High Definition Audio Specification, section 5.5.1: codec PLL settle timing referenced by [`snd_hdac_bus_reset_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L523)

## LINUX KERNEL

### Core objects (include/sound/hdaudio.h)

- [`'\<struct hdac_bus\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291): the controller; owns the MMIO mapping, the verb [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293), the [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) bitmap, the [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308) and [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) heads, the [`corb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L326)/[`rirb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L327) rings, and the capability pointers
- [`'\<struct hdac_device\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52): a codec on the bus; carries [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L56), [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63), [`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64), the [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L89) tree, and the node id range [`start_nid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L82)/[`end_nid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L82)
- [`'\<struct hdac_stream\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516): a host DMA stream / SDn descriptor; carries the [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518) buffer descriptor list, [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), and the positions [`lpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L534)/[`dpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L533)
- [`'\<struct hdac_rb\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L269): one CORB or RIRB ring, with its DMA [`buf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L270)/[`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L271) and the per-codec pending-request counts
- [`'\<struct hdac_bus_ops\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L243): the verb function pointer struct with [`command`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L245), [`get_response`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L247), and [`link_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L250)
- [`'\<struct hdac_driver\>':'include/sound/hdaudio.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222): the codec driver bound to a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52), with its [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L225) and [`match`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L226)

### Bus bring-up (sound/hda/core/bus.c, controller.c)

- [`'\<snd_hdac_bus_init\>':'sound/hda/core/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31): zero a bus, set [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293) (default if NULL), initialize [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337), [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308), [`hlink_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L378), the locks, and [`sdo_limit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L382)
- [`'\<snd_hdac_bus_exit\>':'sound/hda/core/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L71): cancel the unsolicited-event work and tear the bus back down, the inverse of [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31)
- [`'\<snd_hdac_bus_parse_capabilities\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406): walk the controller's linked capability list from [`AZX_REG_LLCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L33), setting [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303), [`gtscap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L304), [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), and [`drsmcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L305)
- [`'\<snd_hdac_bus_init_chip\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609): reset the link, clear interrupts, set up the command I/O, enable interrupts, program the position buffer, and set [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340)
- [`'\<snd_hdac_bus_init_cmd_io\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L43): program [`AZX_REG_CORBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L41) and [`AZX_REG_RIRBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L53), size both rings to 256 entries, enable their DMA, and accept unsolicited responses through [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27)
- [`'\<snd_hdac_bus_reset_link\>':'sound/hda/core/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L523): toggle [`AZX_GCTL_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L25), wait for the codec PLL, and read [`AZX_REG_STATESTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L29) into [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320)
- [`'\<snd_hdac_ext_bus_init\>':'sound/hda/core/ext/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29): call [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31), then attach the [`ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L294) used by ASoC HDA codec drivers and set [`cmd_dma_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L379)

### Codec bring-up (sound/hda/core/device.c)

- [`'\<snd_hdac_device_init\>':'sound/hda/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41): initialize the embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) of a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52), add it to the bus, and read [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63)/[`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64)/[`revision_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L65) and the AFG/MFG nodes over the verb path

### Stream bring-up (sound/hda/core/stream.c)

- [`'\<snd_hdac_stream_init\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94): set [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527) to `remap_addr + 0x20 * idx + 0x80`, set [`sd_int_sta_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L536), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547), [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), and add the stream to [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337)
- [`'\<snd_hdac_stream_assign\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361): find an unused stream matching the substream direction, mark it [`opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L550), and record [`assigned_key`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L548) and [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L539)
- [`'\<snd_hdac_stream_setup\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257): program the [`AZX_REG_SD_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L81) stream tag, [`AZX_REG_SD_CBL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L85), [`AZX_REG_SD_FORMAT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L89), [`AZX_REG_SD_LVI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L86), and the [`AZX_REG_SD_BDLPL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L91) BDL base
- [`'\<snd_hdac_stream_start\>':'sound/hda/core/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130): record [`start_wallclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L559) from [`AZX_REG_WALLCLK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L38), enable the stream's interrupt in [`AZX_REG_INTCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L36), and set [`SD_CTL_DMA_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L164) with [`SD_INT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L175)

### MMIO accessor macros (include/sound/hdaudio.h)

- [`snd_hdac_chip_writel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L482) / [`snd_hdac_chip_readl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L488): read or write a global controller register by its `AZX_REG_*` short name relative to [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298)
- [`snd_hdac_chip_updatel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L496): read-modify-write a global register, used for [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27) and the per-stream [`AZX_REG_INTCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L36) enable bit
- [`snd_hdac_stream_writel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L615) / [`snd_hdac_stream_readl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L621): read or write a stream descriptor register relative to a stream's [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527)

### Legacy controller-driver callers (sound/hda/common, sound/hda/controllers)

- [`'\<azx_init_chip\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018): the legacy controller bring-up wrapper over [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609)
- [`'\<azx_first_init\>':'sound/hda/controllers/intel.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852): the Intel controller probe that calls [`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406) after mapping the BAR
- [`'\<azx_assign_device\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L43): wraps [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361) and converts the result to the legacy [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57)
- [`'\<azx_pcm_prepare\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152): the legacy `.prepare` PCM op that calls [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257)
- [`'\<snd_hda_codec_device_init\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885): allocate a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) and call [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) on its embedded [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52)

### SOF Intel controller wrapper (sound/soc/sof/intel)

- [`'\<struct sof_intel_hda_dev\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496): the SOF host-controller frontend; embeds [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) as [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512) and tracks [`stream_max`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L524), the SoundWire context [`sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L539), and the [`nhlt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L548) table
- [`'\<struct hda_bus\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38): the legacy HDA codec bus that embeds [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member
- [`'\<sof_to_bus\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562): return the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) inside a SOF device as `&hda->hbus.core`
- [`bus_to_sof_hda`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588): the inverse [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) recovering the [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496) from an [`hbus.core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39)
- [`'\<sof_hda_bus_init\>':'sound/soc/sof/intel/hda-bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69): initialize the embedded bus, calling [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29) when HDA-link support is configured
- [`'\<hda_dsp_ctrl_init_chip\>':'sound/soc/sof/intel/hda-ctrl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186): SOF's own controller bring-up that resets the link, clears stream status, enables CIE/GIE interrupts, and sets [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340)
- [`'\<hda_dsp_stream_init\>':'sound/soc/sof/intel/hda-stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895): read the stream counts from [`AZX_REG_GCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L14), allocate the position buffer and the CORB/RIRB buffer, and build one [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) per SDn

## KERNEL DOCUMENTATION

- [`Documentation/sound/hd-audio/notes.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/notes.rst): the HD-Audio driver design, the controller and codec split, and the CORB/RIRB command protocol
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the MultiLink capability the [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointer addresses, which carries the SoundWire, DMIC, and SSP sublinks
- [`Documentation/sound/hd-audio/models.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/models.rst): the codec model quirks keyed off the [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) and [`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64) of a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52)
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, which connects the host DMA stream to a back-end link the SOF DSP feeds

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Intel High Definition Audio Specification (Revision 1.0a)](https://www.intel.com/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The bus and stream functions reach the controller only through the `AZX_REG_*` short names defined in [`include/sound/hda_register.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h), each an offset that the [`snd_hdac_chip_readl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L488) and [`snd_hdac_stream_readl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L621) accessor macros add to a base. The global registers ([`AZX_REG_GCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L14), [`AZX_REG_GCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L24), [`AZX_REG_INTCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L36), [`AZX_REG_INTSTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L37)) sit at the start of the MMIO window addressed through [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298); the command-ring registers ([`AZX_REG_CORBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L41), [`AZX_REG_RIRBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L53)) point the controller at the [`corb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L326) and [`rirb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L327) DMA buffers; and the per-stream registers ([`AZX_REG_SD_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L81), [`AZX_REG_SD_STS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L83)) are offsets from a stream's [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527).

The two register sets are distinct address spaces reached through two different bases. A global register at offset `reg` lands at `remap_addr + reg`, the same for every stream, and a stream descriptor register at offset `reg` lands at `sd_addr + reg`, where each stream's [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527) is `remap_addr + 0x20 * index + 0x80`. The figure below plots the global registers the core touches on the left and one stream descriptor block on the right, with the offsets drawn to scale.

```
    Global registers (base = remap_addr)
    ────────────────────────────────────
     off
    ┌──────┬─────────────────────────────────────────────────────────┐
    │ 0x00 │ GCAP   capabilities: ISS (15:8), OSS (15:12), 64-ok     │
    │ 0x08 │ GCTL   CRST (0), FCNTRL (1), UNSOL (8)                   │
    │ 0x0e │ STATESTS  state-change status (read into codec_mask)    │
    │ 0x14 │ LLCH   linked-capability list head (first cap offset)   │
    │ 0x20 │ INTCTL per-stream SIE bits, CIE (30), GIE (31)          │
    │ 0x24 │ INTSTS per-stream + controller interrupt status         │
    │ 0x30 │ WALLCLK  24 MHz wall-clock counter (read at start)      │
    │ 0x40 │ CORBLBASE / CORBUBASE   CORB DMA base (low / high)      │
    │ 0x50 │ RIRBLBASE / RIRBUBASE   RIRB DMA base (low / high)      │
    │ 0x70 │ DPLBASE / DPUBASE   position buffer base (low / high)   │
    └──────┴─────────────────────────────────────────────────────────┘

    Stream descriptor block (base = sd_addr)
    ────────────────────────────────────────
     off
    ┌──────┬─────────────────────────────────────────────────────────┐
    │+0x00 │ SD_CTL    RUN, SRST, IOCE/FEIE/DEIE, STRM (23:20)       │
    │+0x03 │ SD_STS    BCIS, FIFOE, DESE (per-stream int status)     │
    │+0x04 │ SD_LPIB   link position in current buffer               │
    │+0x08 │ SD_CBL    cyclic buffer length (bufsize, bytes)         │
    │+0x0c │ SD_LVI    last valid index of the BDL (frags - 1)       │
    │+0x12 │ SD_FORMAT stream format value (format_val)              │
    │+0x18 │ SD_BDLPL / SD_BDLPU   BDL base (low / high)             │
    └──────┴─────────────────────────────────────────────────────────┘
```

The stream run bit and the interrupt-enable bits of SD_CTL are written by the core start path, and the stream-tag nibble at bits 23 to 20 is written by the setup path. The figure below plots the low byte of SD_CTL to scale, where RUN is bit 1 and the interrupt-enable triplet IOCE/FEIE/DEIE sits in bits 2 to 4; the wide STRM field above the byte is named in the legend.

```
    AZX_REG_SD_CTL (stream descriptor control, low byte)
    ────────────────────────────────────────────────────

    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│·│·│D│F│I│R│S│
          └─┴─┴─┴─┴─┴─┴─┴─┘
                   │ │ │ │ │
            DEIE ──┘ │ │ │ │
            FEIE ────┘ │ │ │
            IOCE ──────┘ │ │
            RUN ─────────┘ │
            SRST ──────────┘

    S    = SRST (0x01, bit 0)              stream reset (not on the start path)
    R    = SD_CTL_DMA_START (0x02, bit 1)  stream run, set by snd_hdac_stream_start
    I    = SD_INT_COMPLETE (0x04, bit 2)   buffer-complete interrupt enable
    F    = SD_INT_FIFO_ERR (bit 3)         FIFO-error interrupt enable
    D    = SD_INT_DESC_ERR (bit 4)         descriptor-error interrupt enable
    SD_INT_MASK gathers I, F, and D; bits 5:7 of the byte are reserved
    STRM = SD_CTL_STREAM_TAG_MASK (0xf << 20), in the high byte, set by setup
    TP   = SD_CTL_TRAFFIC_PRIO (1 << 18), set when bus->snoop is off
```

The bit constants used by the core appear in the same header. [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27) enables acceptance of unsolicited responses, [`AZX_GCTL_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L25) is the controller reset bit, [`SD_CTL_DMA_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L164) (0x02) is the stream run bit, [`SD_CTL_STREAM_TAG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L168) ((0xf << 20)) selects the stream tag field, and [`SD_INT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L175) gathers the three per-stream interrupt enables.

## DETAILS

### The bus object and its capability pointers

A [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) is the in-memory image of one controller. It holds the MMIO mapping in [`remap_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L298), the verb function pointer struct in [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293), the five capability pointers the controller exposes, the [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) bitmap of detected codec addresses, the two command rings, and the two list heads that anchor the codecs and the streams:

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

	/* link caddr -> codec */
	struct hdac_device *caddr_tbl[HDA_MAX_CODEC_ADDRESS + 1];
	...
	/* bit flags of detected codecs */
	unsigned long codec_mask;
	...
	/* CORB/RIRB */
	struct hdac_rb corb;
	struct hdac_rb rirb;
	...
	/* hdac_stream linked list */
	struct list_head stream_list;

	/* operation state */
	bool chip_init:1;		/* h/w initialized */
	...
};
```

The [`caddr_tbl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L312) array indexes the codecs by their link address so a response carrying a codec address resolves to a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) in one step, while [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308) walks all of them. The [`ppcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L301), [`spbcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L302), and [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointers stay NULL until [`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406) discovers them.

The verb [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L293) is a small function pointer struct. It carries the three operations a controller backend implements so the core can issue a command and collect its response without knowing whether the transport is CORB/RIRB DMA or PIO:

```c
/* include/sound/hdaudio.h:243 */
struct hdac_bus_ops {
	/* send a single command */
	int (*command)(struct hdac_bus *bus, unsigned int cmd);
	/* get a response from the last command */
	int (*get_response)(struct hdac_bus *bus, unsigned int addr,
			    unsigned int *res);
	/* notify of codec link power-up/down */
	void (*link_power)(struct hdac_device *hdev, bool enable);
};
```

[`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31) is the constructor. It clears the whole structure, installs the supplied ops or the file-local default set, initializes the three list heads and the locks, sets [`irq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L299) to -1, and sets [`sdo_limit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L382) to 8:

```c
/* sound/hda/core/bus.c:31 */
int snd_hdac_bus_init(struct hdac_bus *bus, struct device *dev,
		      const struct hdac_bus_ops *ops)
{
	memset(bus, 0, sizeof(*bus));
	bus->dev = dev;
	if (ops)
		bus->ops = ops;
	else
		bus->ops = &default_ops;
	bus->dma_type = SNDRV_DMA_TYPE_DEV;
	INIT_LIST_HEAD(&bus->stream_list);
	INIT_LIST_HEAD(&bus->codec_list);
	INIT_WORK(&bus->unsol_work, snd_hdac_bus_process_unsol_events);
	spin_lock_init(&bus->reg_lock);
	mutex_init(&bus->cmd_mutex);
	mutex_init(&bus->lock);
	INIT_LIST_HEAD(&bus->hlink_list);
	init_waitqueue_head(&bus->rirb_wq);
	bus->irq = -1;
	bus->addr_offset = 0;
	...
	bus->sdo_limit = 8;

	return 0;
}
```

According to the comment on [`sdo_limit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L382) in this function, the default value of 8 is "as per the HD audio specification (Rev 1.0a)" and is used to derive the STRIPE control value from the channel count, sample width, and number of serial data out signals.

[`snd_hdac_bus_parse_capabilities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L406) reads the capability list header at [`AZX_REG_LLCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L33) and follows the next-pointer chain, dispatching on the capability id of each node to store its base in the matching pointer field:

```c
/* sound/hda/core/controller.c:406 */
int snd_hdac_bus_parse_capabilities(struct hdac_bus *bus)
{
	unsigned int cur_cap;
	unsigned int offset;
	unsigned int counter = 0;

	offset = snd_hdac_chip_readw(bus, LLCH);

	/* Lets walk the linked capabilities list */
	do {
		cur_cap = _snd_hdac_chip_readl(bus, offset);
		...
		switch ((cur_cap & AZX_CAP_HDR_ID_MASK) >> AZX_CAP_HDR_ID_OFF) {
		case AZX_ML_CAP_ID:
			dev_dbg(bus->dev, "Found ML capability\n");
			bus->mlcap = bus->remap_addr + offset;
			break;
		...
		case AZX_PP_CAP_ID:
			/* PP capability found, the Audio DSP is present */
			dev_dbg(bus->dev, "Found PP capability offset=%x\n", offset);
			bus->ppcap = bus->remap_addr + offset;
			break;

		case AZX_SPB_CAP_ID:
			/* SPIB capability found, handler function */
			dev_dbg(bus->dev, "Found SPB capability\n");
			bus->spbcap = bus->remap_addr + offset;
			break;
		...
		}
		...
		/* read the offset of next capability */
		offset = cur_cap & AZX_CAP_HDR_NXT_PTR_MASK;

	} while (offset);

	return 0;
}
```

According to the comment on the [`AZX_PP_CAP_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L222) case, when the Processing Pipe capability is found "the Audio DSP is present", so the same controller can also host the DSP. The [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) pointer set in the [`AZX_ML_CAP_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L259) case addresses the MultiLink block through which the SoundWire, DMIC, and SSP sublinks are reached. The legacy Intel controller calls this from [`azx_first_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L1852) once the BAR is mapped, the same way SOF calls its own [`hda_dsp_ctrl_get_caps()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L58).

```
    Linked capability list walk (snd_hdac_bus_parse_capabilities)
    ─────────────────────────────────────────────────────────────
                AZX_REG_LLCH ─▶ first capability offset
                                      │
                                      ▼
    ┌──────────────┐ ───────▶ ┌──────────────┐ ───────▶ ┌──────────────┐
    │ cap node     │          │ cap node     │          │ cap node     │
    │ id │ next ptr│          │ id │ next ptr│          │ id │ next=0  │
    └──┬───────────┘          └──┬───────────┘          └──┬───────────┘
       │                         │                         │
       ▼                         ▼                         ▼
    bus->mlcap                bus->ppcap                bus->spbcap

    id   = (cur_cap & AZX_CAP_HDR_ID_MASK) >> AZX_CAP_HDR_ID_OFF
    next = cur_cap & AZX_CAP_HDR_NXT_PTR_MASK   (loop until next == 0)
    AZX_ML_CAP_ID ─▶ mlcap   AZX_PP_CAP_ID ─▶ ppcap   AZX_SPB_CAP_ID ─▶ spbcap
    each pointer = remap_addr + offset
```

### Controller bring-up programs the command rings

[`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609) is the one call that takes a quiescent controller to a running one. It returns early if [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340) is already set, then resets the link, clears and re-enables interrupts, programs the command I/O, optionally programs the position buffer base, and finally sets [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340):

```c
/* sound/hda/core/controller.c:609 */
bool snd_hdac_bus_init_chip(struct hdac_bus *bus, bool full_reset)
{
	if (bus->chip_init)
		return false;

	/* reset controller */
	snd_hdac_bus_reset_link(bus, full_reset);

	/* clear interrupts */
	azx_int_clear(bus);

	/* initialize the codec command I/O */
	snd_hdac_bus_init_cmd_io(bus);

	/* enable interrupts after CORB/RIRB buffers are initialized above */
	azx_int_enable(bus);

	/* program the position buffer */
	if (bus->use_posbuf && bus->posbuf.addr) {
		snd_hdac_chip_writel(bus, DPLBASE, (u32)(bus->posbuf.addr + bus->addr_offset));
		snd_hdac_chip_writel(bus, DPUBASE, upper_32_bits(bus->posbuf.addr + bus->addr_offset));
	}

	bus->chip_init = true;

	return true;
}
```

The legacy controller driver calls this through [`azx_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1018), which adds one chipset workaround when the boolean return reports the chip was actually initialized:

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

The command-ring setup is the substance of that sequence. [`snd_hdac_bus_init_cmd_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L43) splits the single DMA buffer in [`rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L332) into a CORB half and a RIRB half, writes each ring's physical base into the [`AZX_REG_CORBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L41) and [`AZX_REG_RIRBLBASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L53) registers, sizes each to 256 entries, enables the ring DMA, and sets [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27) so the controller delivers unsolicited responses:

```c
/* sound/hda/core/controller.c:43 */
void snd_hdac_bus_init_cmd_io(struct hdac_bus *bus)
{
	WARN_ON_ONCE(!bus->rb.area);

	guard(spinlock_irq)(&bus->reg_lock);
	/* CORB set up */
	bus->corb.addr = bus->rb.addr;
	bus->corb.buf = (__le32 *)bus->rb.area;
	snd_hdac_chip_writel(bus, CORBLBASE, (u32)(bus->corb.addr + bus->addr_offset));
	snd_hdac_chip_writel(bus, CORBUBASE, upper_32_bits(bus->corb.addr + bus->addr_offset));
	...
	/* RIRB set up */
	bus->rirb.addr = bus->rb.addr + 2048;
	bus->rirb.buf = (__le32 *)(bus->rb.area + 2048);
	bus->rirb.wp = bus->rirb.rp = 0;
	memset(bus->rirb.cmds, 0, sizeof(bus->rirb.cmds));
	snd_hdac_chip_writel(bus, RIRBLBASE, (u32)(bus->rirb.addr + bus->addr_offset));
	snd_hdac_chip_writel(bus, RIRBUBASE, upper_32_bits(bus->rirb.addr + bus->addr_offset));
	...
	/* Accept unsolicited responses */
	snd_hdac_chip_updatel(bus, GCTL, AZX_GCTL_UNSOL, AZX_GCTL_UNSOL);
}
```

The single DMA buffer in [`rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L332) is split at the 2048-byte midpoint, the CORB taking the low half and the RIRB the high half, and each half is described by one [`struct hdac_rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L269). A 4-byte-per-entry CORB carries commands out and an 8-byte-per-entry RIRB carries responses back, with the per-codec pending-request counts in [`cmds`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L273):

```c
/* include/sound/hdaudio.h:269 */
struct hdac_rb {
	__le32 *buf;		/* virtual address of CORB/RIRB buffer */
	dma_addr_t addr;	/* physical address of CORB/RIRB buffer */
	unsigned short rp, wp;	/* RIRB read/write pointers */
	int cmds[HDA_MAX_CODECS];	/* number of pending requests */
	u32 res[HDA_MAX_CODECS];	/* last read value */
};
```

The link reset that precedes the ring setup is [`snd_hdac_bus_reset_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L523). It clears [`AZX_REG_STATESTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L29), drives [`AZX_GCTL_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L25) low and back high with the spec-mandated delays, then reads [`AZX_REG_STATESTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L29) into [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) to learn which codec addresses responded:

```c
/* sound/hda/core/controller.c:523 */
int snd_hdac_bus_reset_link(struct hdac_bus *bus, bool full_reset)
{
	if (!full_reset)
		goto skip_reset;

	/* clear STATESTS if not in reset */
	if (snd_hdac_chip_readb(bus, GCTL) & AZX_GCTL_RESET)
		snd_hdac_chip_writew(bus, STATESTS, STATESTS_INT_MASK);

	/* reset controller */
	snd_hdac_bus_enter_link_reset(bus);

	/* delay for >= 100us for codec PLL to settle per spec
	 * Rev 0.9 section 5.5.1
	 */
	usleep_range(500, 1000);

	/* Bring controller out of reset */
	snd_hdac_bus_exit_link_reset(bus);
	...
 skip_reset:
	/* check to see if controller is ready */
	if (!snd_hdac_chip_readb(bus, GCTL)) {
		dev_dbg(bus->dev, "controller not ready!\n");
		return -EBUSY;
	}

	/* detect codecs */
	if (!bus->codec_mask) {
		bus->codec_mask = snd_hdac_chip_readw(bus, STATESTS);
		dev_dbg(bus->dev, "codec_mask = 0x%lx\n", bus->codec_mask);
	}

	return 0;
}
```

According to the comment in this function, the post-reset delay covers the codec PLL settle time described in "Rev 0.9 section 5.5.1", so the [`AZX_REG_STATESTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L29) read that follows reports a stable codec bitmap.

```
    One rb DMA buffer split into the CORB and RIRB rings
    ────────────────────────────────────────────────────

    bus->rb.area                  +2048                          +4096
    ┌──────────────────────────────┬───────────────────────────────┐
    │ CORB  (commands out)         │ RIRB  (responses in)          │
    │ 256 entries x 4 bytes        │ 256 entries x 8 bytes         │
    └──────────────────────────────┴───────────────────────────────┘
    corb.addr = rb.addr            rirb.addr = rb.addr + 2048
    base ─▶ CORBLBASE/CORBUBASE    base ─▶ RIRBLBASE/RIRBUBASE

    RIRB ring entries (struct hdac_rb)
    ┌────┬────┬────┬────┬────┬────┬────┬────┐
    │ e0 │ e1 │ e2 │ e3 │ e4 │ .. │    │    │
    └────┴────┴────┴────┴────┴────┴────┴────┘
                ▲         ▲
               rp        wp
    rp = read pointer   wp = write pointer (advanced on a response)
```

### A codec on the bus

Each bit set in [`codec_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L320) corresponds to a codec address, and a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) represents the codec at that address. It records the [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L56) on the link, the function group node ids, the [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) and [`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64) that drive model matching, the widget node id range, and the parsed widget tree:

```c
/* include/sound/hdaudio.h:52 */
struct hdac_device {
	struct device dev;
	int type;
	struct hdac_bus *bus;
	unsigned int addr;		/* codec address */
	struct list_head list;		/* list point for bus codec_list */

	hda_nid_t afg;			/* AFG node id */
	hda_nid_t mfg;			/* MFG node id */

	/* ids */
	unsigned int vendor_id;
	unsigned int subsystem_id;
	unsigned int revision_id;
	...
	/* widgets */
	unsigned int num_nodes;
	hda_nid_t start_nid, end_nid;
	...
	/* sysfs */
	struct mutex widget_lock;
	struct hdac_widget_tree *widgets;
	...
};
```

[`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) populates one of these. It initializes the embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), parents it to the bus device, adds the codec to the bus, and reads the [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63), [`subsystem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L64), and [`revision_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L65) over the verb path before discovering the function group nodes:

```c
/* sound/hda/core/device.c:41 */
int snd_hdac_device_init(struct hdac_device *codec, struct hdac_bus *bus,
			 const char *name, unsigned int addr)
{
	struct device *dev;
	hda_nid_t fg;
	int err;

	dev = &codec->dev;
	device_initialize(dev);
	dev->parent = bus->dev;
	dev->bus = &snd_hda_bus_type;
	dev->release = default_release;
	dev->groups = hdac_dev_attr_groups;
	dev_set_name(dev, "%s", name);
	device_enable_async_suspend(dev);

	codec->bus = bus;
	codec->addr = addr;
	codec->type = HDA_DEV_CORE;
	mutex_init(&codec->widget_lock);
	mutex_init(&codec->regmap_lock);
	pm_runtime_set_active(&codec->dev);
	pm_runtime_get_noresume(&codec->dev);
	atomic_set(&codec->in_pm, 0);

	err = snd_hdac_bus_add_device(bus, codec);
	if (err < 0)
		goto error;

	/* fill parameters */
	codec->vendor_id = snd_hdac_read_parm(codec, AC_NODE_ROOT,
					      AC_PAR_VENDOR_ID);
	...
}
```

The legacy codec layer reaches this through [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885), which allocates a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) wrapping the [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) and then calls the core initializer on the embedded object once the address is range-checked.

A codec is bound to a [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222), the driver-model object whose [`match`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L226) callback compares the codec ids against an [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L225) and whose [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L230)/[`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L231) hooks are run by the extended bus layer:

```c
/* include/sound/hdaudio.h:222 */
struct hdac_driver {
	struct device_driver driver;
	int type;
	const struct hda_device_id *id_table;
	int (*match)(struct hdac_device *dev, const struct hdac_driver *drv);
	void (*unsol_event)(struct hdac_device *dev, unsigned int event);

	/* fields used by ext bus APIs */
	int (*probe)(struct hdac_device *dev);
	int (*remove)(struct hdac_device *dev);
	void (*shutdown)(struct hdac_device *dev);
};
```

Before that driver can act on a codec, the bus resolves which one a response came from by its address, codec_mask marking the addresses that answered and caddr_tbl indexing the codec at each one while codec_list threads them all for a full walk:

```
    Codec address resolves a response to a codec in one step
    ────────────────────────────────────────────────────────

    codec_mask   (bit n set = a codec answered at address n)
    ┌───┬───┬───┬───┬───┬───┬───┬───┐
    │ b7│ b6│ b5│ b4│ b3│ b2│ b1│ b0│
    └───┴───┴───┴───┴───┴───┴───┴───┘

    caddr_tbl[addr] indexes the codecs by link address
       caddr_tbl[0]                   ─▶ hdac_device  addr=0
       caddr_tbl[1]                   ─▶ hdac_device  addr=1
       caddr_tbl[HDA_MAX_CODEC_ADDRESS] ─▶ ...

    each hdac_device : addr  vendor_id  subsystem_id  widgets
    codec_list threads every hdac_device for a full walk
```

### A host DMA stream and its descriptor registers

A [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) is one host DMA engine. It maps a single stream descriptor register block through [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), owns the buffer descriptor list in [`bdl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L518) and a slot in the position buffer through [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L519), records its [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520) and assigned [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), and tracks playback position in [`lpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L534) and [`dpib`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L533):

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
	u32 dpib;		/* DMA position in buffer */
	u32 lpib;		/* Linear position in buffer */

	u32 sd_int_sta_mask;	/* stream int status mask */
	...
	unsigned char stream_tag;	/* assigned stream */
	unsigned char index;		/* stream index */
	int assigned_key;		/* last device# key assigned to */

	bool opened:1;
	bool running:1;
	...
	struct list_head list;
	...
};
```

[`snd_hdac_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L94) computes where the descriptor block sits. The SDn blocks are spaced 0x20 apart starting at offset 0x80, so stream index `idx` maps to `remap_addr + 0x20 * idx + 0x80`, and the per-stream interrupt bit is `1 << idx`. The function also wires up the SPIB and DMA-resume sub-addresses when those capabilities are present, then links the stream onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337):

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

	if (bus->spbcap) {
		azx_dev->spib_addr = bus->spbcap + AZX_SPB_BASE +
					AZX_SPB_INTERVAL * idx +
					AZX_SPB_SPIB;
		...
	}
	...
}
```

When a PCM substream opens, [`snd_hdac_stream_assign()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L361) hands it a stream. It builds a unique key from the substream number, direction, and PCM device, then walks [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) for an unopened stream of the matching direction, preferring one whose [`assigned_key`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L548) already equals this key so the same engine is reused across opens:

```c
/* sound/hda/core/stream.c:361 */
struct hdac_stream *snd_hdac_stream_assign(struct hdac_bus *bus,
					   struct snd_pcm_substream *substream)
{
	struct hdac_stream *azx_dev;
	struct hdac_stream *res = NULL;

	/* make a non-zero unique key for the substream */
	int key = (substream->number << 2) | (substream->stream + 1);

	if (substream->pcm)
		key |= (substream->pcm->device << 16);

	guard(spinlock_irq)(&bus->reg_lock);
	list_for_each_entry(azx_dev, &bus->stream_list, list) {
		if (azx_dev->direction != substream->stream)
			continue;
		if (azx_dev->opened)
			continue;
		if (azx_dev->assigned_key == key) {
			res = azx_dev;
			break;
		}
		if (!res || bus->reverse_assign)
			res = azx_dev;
	}
	if (res) {
		res->opened = 1;
		res->running = 0;
		res->assigned_key = key;
		res->substream = substream;
	}
	return res;
}
```

The legacy controller reaches this through [`azx_assign_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L43), which converts the returned core stream to the driver-private [`struct azx_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L57):

```c
/* sound/hda/common/controller.c:43 */
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

[`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) programs the assigned stream's descriptor registers. It clears the run bit, writes the stream tag into the [`AZX_REG_SD_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L81) field selected by [`SD_CTL_STREAM_TAG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L168), sets the cyclic buffer length in [`AZX_REG_SD_CBL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L85), the format in [`AZX_REG_SD_FORMAT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L89), the last valid BDL index in [`AZX_REG_SD_LVI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L86), and the BDL base into [`AZX_REG_SD_BDLPL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L91):

```c
/* sound/hda/core/stream.c:257 */
int snd_hdac_stream_setup(struct hdac_stream *azx_dev, bool code_loading)
{
	struct hdac_bus *bus = azx_dev->bus;
	...
	/* make sure the run bit is zero for SD */
	snd_hdac_stream_clear(azx_dev);
	/* program the stream_tag */
	val = snd_hdac_stream_readl(azx_dev, SD_CTL);
	val = (val & ~SD_CTL_STREAM_TAG_MASK) |
		(azx_dev->stream_tag << SD_CTL_STREAM_TAG_SHIFT);
	if (!bus->snoop)
		val |= SD_CTL_TRAFFIC_PRIO;
	snd_hdac_stream_writel(azx_dev, SD_CTL, val);

	/* program the length of samples in cyclic buffer */
	snd_hdac_stream_writel(azx_dev, SD_CBL, azx_dev->bufsize);

	/* program the stream format */
	snd_hdac_stream_writew(azx_dev, SD_FORMAT, azx_dev->format_val);

	/* program the stream LVI (last valid index) of the BDL */
	snd_hdac_stream_writew(azx_dev, SD_LVI, azx_dev->frags - 1);

	/* program the BDL address */
	/* lower BDL address */
	snd_hdac_stream_writel(azx_dev, SD_BDLPL, (u32)(azx_dev->bdl.addr + bus->addr_offset));
	/* upper BDL address */
	snd_hdac_stream_writel(azx_dev, SD_BDLPU,
			       upper_32_bits(azx_dev->bdl.addr + bus->addr_offset));
	...
}
```

The legacy `.prepare` PCM op [`azx_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L152) computes the format value and then calls this function, so the SDn programming above runs once per PCM prepare for a legacy HD-Audio stream.

[`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) commits the start. It snapshots [`AZX_REG_WALLCLK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L38) into [`start_wallclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L559), enables this stream's interrupt by setting bit [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547) in [`AZX_REG_INTCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L36), then sets [`SD_CTL_DMA_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L164) together with [`SD_INT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L175) in [`AZX_REG_SD_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L81) and marks the stream [`running`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L551):

```c
/* sound/hda/core/stream.c:130 */
void snd_hdac_stream_start(struct hdac_stream *azx_dev)
{
	struct hdac_bus *bus = azx_dev->bus;
	int stripe_ctl;

	trace_snd_hdac_stream_start(bus, azx_dev);

	azx_dev->start_wallclk = snd_hdac_chip_readl(bus, WALLCLK);

	/* enable SIE */
	snd_hdac_chip_updatel(bus, INTCTL,
			      1 << azx_dev->index,
			      1 << azx_dev->index);
	...
	/* set DMA start and interrupt mask */
	if (bus->access_sdnctl_in_dword)
		snd_hdac_stream_updatel(azx_dev, SD_CTL,
				0, SD_CTL_DMA_START | SD_INT_MASK);
	else
		snd_hdac_stream_updateb(azx_dev, SD_CTL,
				0, SD_CTL_DMA_START | SD_INT_MASK);
	azx_dev->running = true;
}
```

The per-stream interrupt enable in [`AZX_REG_INTCTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L36) uses [`snd_hdac_chip_updatel()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L496) to set just bit [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L547), the same bit set in [`sd_int_sta_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L536) at init, so a later [`AZX_REG_INTSTS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L37) read identifies which stream raised the interrupt. The run bit and the interrupt mask are written together in one [`AZX_REG_SD_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L81) update, as a dword on controllers that require [`access_sdnctl_in_dword`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L353) and as a byte otherwise.

```
    Stream descriptor blocks at remap_addr + 0x20*idx + 0x80
    ────────────────────────────────────────────────────────
     idx     sd_addr      sd_int_sta_mask = 1 << idx
    ┌──────┬────────────┬───────────────────────────────┐
    │  0   │   0x80     │ 0x01   SDI0 (capture)         │
    │  1   │   0xa0     │ 0x02   SDI1                   │
    │  2   │   0xc0     │ 0x04   SDI2                   │
    │ ...  │   ...      │ ...                           │
    │  7   │   0x160    │ 0x80   SDO3 (playback)        │
    └──────┴────────────┴───────────────────────────────┘
    stride 0x20 between blocks; one struct hdac_stream per idx
```

### SOF wraps the same bus to host the DSP

The SOF Intel driver does not define its own controller object. It embeds the HD-Audio core bus inside its host-controller frontend [`struct sof_intel_hda_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L496), through one level of nesting. The SOF device contains a [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) named [`hbus`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L512), and that in turn contains the [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) member:

```c
/* sound/soc/sof/intel/hda.h:496 */
struct sof_intel_hda_dev {
	bool imrboot_supported;
	...
	struct hda_bus hbus;

	/* hw config */
	const struct sof_intel_dsp_desc *desc;
	...
	/* the maximum number of streams (playback + capture) supported */
	u32 stream_max;
	...
	/* sdw context allocated by SoundWire driver */
	struct sdw_intel_ctx *sdw;
	...
	/* Intel NHLT information */
	struct nhlt_acpi_table *nhlt;
	...
};
```

```c
/* include/sound/hda_codec.h:38 */
struct hda_bus {
	struct hdac_bus core;

	struct snd_card *card;

	struct pci_dev *pci;
	...
};
```

Every SOF function that touches the controller reaches the bus through the inline [`sof_to_bus()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L562), which returns the address of the nested [`hbus.core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39), and recovers the enclosing SOF device with the [`bus_to_sof_hda`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L588) [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) macro:

```c
/* sound/soc/sof/intel/hda.h:562 */
static inline struct hdac_bus *sof_to_bus(struct snd_sof_dev *s)
{
	struct sof_intel_hda_dev *hda = s->pdata->hw_pdata;

	return &hda->hbus.core;
}
```

```c
/* sound/soc/sof/intel/hda.h:588 */
#define bus_to_sof_hda(bus) \
	container_of(bus, struct sof_intel_hda_dev, hbus.core)
```

[`sof_hda_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-bus.c#L69) initializes that embedded bus. When HDA-link support is configured it calls the extended-bus constructor [`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29), which is a thin shell over [`snd_hdac_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/bus.c#L31); the minimal path still memsets the bus and initializes [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) and [`reg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L364) directly:

```c
/* sound/soc/sof/intel/hda-bus.c:69 */
void sof_hda_bus_init(struct snd_sof_dev *sdev, struct device *dev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);

#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_LINK)
#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_AUDIO_CODEC)
	const struct sof_intel_dsp_desc *chip = get_chip_info(sdev->pdata);

	snd_hdac_ext_bus_init(bus, dev, &bus_core_ops, sof_hda_ext_ops);
	...
#else
	snd_hdac_ext_bus_init(bus, dev, NULL, NULL);
#endif
#else
	memset(bus, 0, sizeof(*bus));
	bus->dev = dev;

	INIT_LIST_HEAD(&bus->stream_list);

	bus->irq = -1;
	...
	spin_lock_init(&bus->reg_lock);
#endif /* CONFIG_SND_SOC_SOF_HDA_LINK */
}
```

[`snd_hdac_ext_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/bus.c#L29) shows that the extended bus is the same object plus the ASoC codec [`ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L294) and a flag:

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

The bus those calls set up sits two structs inside the SOF device, hbus holding the shared core, with one accessor returning hbus.core going down and a container_of recovering the front-end going back up:

```
    SOF nests the core bus two levels deep
    ──────────────────────────────────────

    struct sof_intel_hda_dev
    ┌──────────────────────────────────────────────────────┐
    │  struct hda_bus hbus                                 │
    │  ┌────────────────────────────────────────────────┐  │
    │  │  struct hdac_bus core  (shared core bus)       │  │
    │  └────────────────────────────────────────────────┘  │
    │  desc   stream_max   sdw   nhlt                      │
    └──────────────────────────────────────────────────────┘
       ▲                                  │
       │ bus_to_sof_hda(bus)              ▼ sof_to_bus = &hda->hbus.core
       └──────────────────────────────────┘
    container_of(bus, struct sof_intel_hda_dev, hbus.core)
```

### SOF controller bring-up reuses the same registers

SOF brings the controller up in [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186) rather than calling [`snd_hdac_bus_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L609), because the DSP boot needs finer control over clock gating and the reset ordering, but it programs the identical registers on the same [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291). It resets the link, walks [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) clearing each stream's status, enables the control and global interrupt enables, programs the position buffer base, and sets [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340):

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
	...
	/* Accept unsolicited responses */
	snd_hdac_chip_updatel(bus, GCTL, AZX_GCTL_UNSOL, AZX_GCTL_UNSOL);

	if (detect_codec)
		hda_codec_detect_mask(sdev);

	/* clear stream status */
	list_for_each_entry(stream, &bus->stream_list, list) {
		sd_offset = SOF_STREAM_SD_OFFSET(stream);
		snd_sof_dsp_write(sdev, HDA_DSP_HDA_BAR,
				  sd_offset + SOF_HDA_ADSP_REG_SD_STS,
				  SOF_HDA_CL_DMA_SD_INT_MASK);
	}
	...
	bus->chip_init = true;
	...
}
```

The same [`snd_hdac_chip_updatel()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L496) accessor and the same [`AZX_GCTL_UNSOL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L27) constant appear here as in [`snd_hdac_bus_init_cmd_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/controller.c#L43), confirming both paths drive one controller through one register definition.

[`hda_dsp_stream_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L895) builds the stream objects. It reads the input and output stream counts from the [`AZX_REG_GCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L14) capability register, allocates the shared position buffer and the CORB/RIRB buffer into [`posbuf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L333) and [`rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L332), then for each stream fills a [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) embedded in a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47), sets its [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527), [`direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L520), and [`stream_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L546), allocates its BDL, and links it onto [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337):

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
	/* create capture and playback streams */
	for (i = 0; i < num_total; i++) {
		...
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
		...
		list_add_tail(&hstream->list, &bus->stream_list);
	}

	/* store total stream count (playback + capture) from GCAP */
	sof_hda->stream_max = num_total;
	...
}
```

The bit-shift decode of [`gcap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-stream.c#L904) reads the same input-stream and output-stream count fields the spec defines for [`AZX_REG_GCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_register.h#L14), and the resulting streams are the same kind of [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) the legacy path links, except that SOF embeds each in a [`struct hdac_ext_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L47) to carry the Processing Pipe sub-addresses. The legacy [`sound/hda/common/`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common) driver instead uses these host streams only to move PCM data to and from HD-Audio codecs, whereas SOF uses some of them to load and converse with the DSP and routes the audio data through the SoundWire, DMIC, and SSP links reached via the [`mlcap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L303) MultiLink block rather than through HD-Audio codecs alone.

### SOF stream descriptor programming

For an HD-Audio-link stream, SOF programs the descriptor through the extended wrapper [`snd_hdac_ext_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/stream.c#L234), reached from [`hda_setup_hext_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L168), and that wrapper reaches the embedded [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) through the [`hdac_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L70) accessor, so the same stream-tag and format fields are written that [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257) writes for the legacy path:

```c
/* sound/hda/core/ext/stream.c:234 */
int snd_hdac_ext_stream_setup(struct hdac_ext_stream *hext_stream, int fmt)
{
	struct hdac_stream *hstream = &hext_stream->hstream;
	unsigned int val;

	/* make sure the run bit is zero for SD */
	snd_hdac_ext_stream_clear(hext_stream);
	/* program the stream_tag */
	val = readl(hext_stream->pplc_addr + AZX_REG_PPLCCTL);
	val = (val & ~AZX_PPLCCTL_STRM_MASK) |
		(hstream->stream_tag << AZX_PPLCCTL_STRM_SHIFT);
	writel(val, hext_stream->pplc_addr + AZX_REG_PPLCCTL);

	/* program the stream format */
	writew(fmt, hext_stream->pplc_addr + AZX_REG_PPLCFMT);

	return 0;
}
```

The [`hdac_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio_ext.h#L70) accessor is the bridge between the extended object and the core object SOF and the legacy driver share:

```c
/* include/sound/hdaudio_ext.h:47 */
struct hdac_ext_stream {
	struct hdac_stream hstream;
	...
};

#define hdac_stream(s)		(&(s)->hstream)
```

### Global and per-stream register blocks side by side

The global controller registers (GCAP, GCTL, INTCTL, CORBLBASE, RIRBLBASE) are reached from the bus MMIO base while a stream descriptor block (SD_CTL, SD_STS, SD_LPIB, SD_CBL, SD_LVI, SD_FORMAT, SD_BDLPL) is reached from a stream's `sd_addr`, with the run bit set by [`snd_hdac_stream_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L130) and the stream tag programmed by [`snd_hdac_stream_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/stream.c#L257).

```
    Global registers (from remap_addr)        Per-stream block (from sd_addr)
    ──────────────────────────────────        ───────────────────────────────
    0x00  GCAP    capabilities (ISS/OSS)       +0x00  SD_CTL   run, stream tag
    0x08  GCTL    reset, unsol enable          +0x03  SD_STS   status / IRQ
    0x20  INTCTL  per-stream + global IRQ en   +0x04  SD_LPIB  link position
    0x24  INTSTS  per-stream + global IRQ sts  +0x08  SD_CBL   cyclic buf len
    0x40  CORBLBASE  command ring base         +0x0c  SD_LVI   last valid index
    0x50  RIRBLBASE  response ring base        +0x12  SD_FORMAT stream format
    0x70  DPLBASE    position buffer base      +0x18  SD_BDLPL BDL base (low)

    SD_CTL.run  = SD_CTL_DMA_START (0x02)        snd_hdac_stream_start()
    SD_CTL.strm = SD_CTL_STREAM_TAG_MASK (0xf<<20)  snd_hdac_stream_setup()
    INTCTL bit n enables stream index n          (1 << azx_dev->index)
```

### Controller bus with its codec and stream object families

A [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) owns the MMIO mapping, the [`struct hdac_rb`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L269) command rings, and the capability pointers, anchoring a [`codec_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L308) of [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) codecs and a [`stream_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L337) of [`struct hdac_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L516) DMA engines that each map one SDn descriptor block through [`sd_addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L527).

```
    HD-Audio core object hierarchy
    ──────────────────────────────

    struct hdac_bus                          (the controller)
    ┌───────────────────────────────────────────────────────────┐
    │  remap_addr (MMIO)   ops ─▶ hdac_bus_ops                  │
    │  ppcap  spbcap  mlcap   (capability pointers)             │
    │  corb : hdac_rb   rirb : hdac_rb        (command rings)   │
    │  codec_list ─┐                                            │
    │  stream_list ├───────────┐                                │
    └──────────────┼───────────┼────────────────────────────────┘
                   │           │
        ┌──────────┴───┐       └──────────┬──────────┬──────────┐
        ▼              ▼                  ▼          ▼          ▼
   struct hdac_device  ...          struct hdac_stream  ...  (SDn rings)
   ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐
   │ addr (caddr) │ │ addr (caddr) │ │ sd_addr    │ │ sd_addr    │
   │ vendor_id    │ │ vendor_id    │ │ bdl (BDL)  │ │ bdl (BDL)  │
   │ subsystem_id │ │ subsystem_id │ │ direction  │ │ direction  │
   │ widgets ─▶   │ │ widgets ─▶   │ │ lpib/dpib  │ │ lpib/dpib  │
   └──────────────┘ └──────────────┘ └────────────┘ └────────────┘
     codecs on the link             host DMA stream rings (SDIn/SDOn)
```
