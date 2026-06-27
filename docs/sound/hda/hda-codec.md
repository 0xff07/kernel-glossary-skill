# HD-Audio codec driver model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The legacy HD-Audio codec model wraps the transport-level [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) in a richer [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) that a vendor driver binds to through a [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) on the [`snd_hda_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/hda_bus_type.c#L79) bus, and the binding glue ([`hda_codec_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87)) runs the driver's [`struct hda_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L108) callbacks to probe the part, build its [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) streams, and build its mixer controls. A [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) embeds the core device as its first member [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), points at the [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38) it belongs to, carries the matched [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186) entry that selected the driver, holds the [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190) of PCM objects the driver builds, and stashes the driver's private parser state in [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195). On an Intel x86-64 machine driven by the legacy azx/HDA controller path, a Realtek ALC part such as the ALC269 family is bound by [`alc269_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8772), whose [`alc269_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489) allocates a [`struct alc_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L77) and runs the generic auto-parser [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019) over the BIOS pin configuration.

```
    legacy HD-Audio codec object  (above hdac_device)
    ─────────────────────────────────────────────────

    struct hda_codec
    ┌──────────────────────────────────────────────────────────────┐
    │  core : struct hdac_device   (embedded base, verb transport) │
    │  bus  ─▶ struct hda_bus ─▶ struct hdac_bus core              │
    │  preset ─▶ struct hda_device_id  (vendor_id ⇒ driver)       │
    │  spec  ─▶ void *  (struct alc_spec for Realtek)             │
    │  pcm_list_head ─┐                                            │
    └─────────────────┼────────────────────────────────────────────┘
                      │ build_pcms op fills pcm_list_head
        ┌─────────────┴───────────┬──────────────────┐
        ▼                         ▼                  ▼
   struct hda_pcm            struct hda_pcm     struct hda_pcm
   ┌──────────────┐          ┌───────────────┐  ┌──────────────┐
   │ name "Analog"│          │ name "Digital"│  │ "Alt Analog" │
   │ stream[0] PB │          │ stream[0] PB  │  │ stream[0] PB │
   │ stream[1] CAP│          │ stream[1] CAP │  │ stream[1] CAP│
   │ pcm_type     │          │ pcm_type SPDIF│  │ pcm_type     │
   └──────────────┘          └───────────────┘  └──────────────┘

    bound driver
    struct hda_codec_driver alc269_driver
    ┌──────────────────────────────────────────────────────────────┐
    │  core : struct hdac_driver   (match ⇒ hda_codec_match)       │
    │  id   ─▶ struct hda_device_id snd_hda_id_alc269[]           │
    │  ops  ─▶ struct hda_codec_ops alc269_codec_ops              │
    │           .probe .build_pcms .build_controls .init ...       │
    └──────────────────────────────────────────────────────────────┘
```

## SUMMARY

The codec object is one [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) per detected codec address, layered on the transport [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) it embeds in its first field [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179). It records the owning [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L180), the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L181), the codec [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L182), the matched [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186) that bound a driver, the [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190) of [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) objects, the widget-capability cache [`wcaps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L203), and the driver-private [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195) pointer. A vendor driver is a [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) that embeds a [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L90), carries an [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table of [`struct hda_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L263) entries, and an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92) pointer to a [`struct hda_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L108) function pointer struct whose [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109), [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112), [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111), and [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L113) entries the bind glue drives.

The codec is constructed in two stages. [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) allocates a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) and calls [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) on its embedded [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), then [`snd_hda_codec_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L967) reads the widget caps and pin defaults and registers the codec as an ALSA device; [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947) runs both. Driver binding is started by [`snd_hda_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L315), which registers the codec on [`snd_hda_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/hda_bus_type.c#L79) and triggers a module load and match. The match callback [`hda_codec_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21) walks the driver's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table, stores the first matching entry in [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186), and the driver core then calls [`hda_codec_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87), which runs the codec's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op followed by [`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300) and [`snd_hda_codec_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3060). The driver registry is set up by [`__hda_codec_driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L182), which a vendor module invokes through the [`module_hda_codec_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103) macro.

The PCM objects are built by the driver's [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op. [`snd_hda_codec_parse_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3258) calls that op (each call to [`snd_hda_codec_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L700) appends a [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) to [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190)), then [`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300) assigns each a device number and calls [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692) so the controller creates the ALSA [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L613). The generic auto-parser supplies a complete [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) and [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) implementation through [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734) and [`snd_hda_gen_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5222), built from the pin map that [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) reads and [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019) turns into DAC/ADC paths. The Realtek ALC269 driver reaches this through [`alc269_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489), which calls [`alc_alloc_spec()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1029) and [`alc269_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L50), then sets [`alc269_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8704) to use [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734) for the PCM op.

## SPECIFICATIONS

The codec layer models the codec node and its function group defined by the Intel High Definition Audio specification, reached over the verb path of the embedded [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52). The pin-configuration default that [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) reads with [`snd_hda_codec_get_pincfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L393) is the configuration default register the specification defines, whose sequence, association, default-device, and location subfields the parser decodes to assign line-out, speaker, headphone, mic, and digital pins.

- Intel High Definition Audio Specification, section 7.3.3.31: configuration default (the pin default-config register decoded by [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172))
- Intel High Definition Audio Specification, section 7.3.4.5: audio widget capabilities (the per-widget caps cached in [`wcaps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L203) and read by [`snd_hda_codec_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L967))
- Intel High Definition Audio Specification, section 7.3.3: codec verbs and parameters (the converter setup, stream tag, and format the [`struct hda_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L124) prepare path programs)

## LINUX KERNEL

### Codec object and PCM types (include/sound/hda_codec.h)

- [`'\<struct hda_codec\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178): one codec; embeds [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) as [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), and carries [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L180), [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186), [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190), [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195), and [`wcaps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L203)
- [`'\<struct hda_bus\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38): the codec bus; embeds [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) as [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39), and adds the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L41), the [`pci`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L43) device, and the [`prepare_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L46)
- [`'\<struct hda_codec_ops\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L108): the codec driver's function pointer struct ([`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L110), [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111), [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112), [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L113), [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L114), [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L117), [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L118))
- [`'\<struct hda_codec_driver\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89): the bound driver; embeds [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222) as [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L90), carries the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92) pointer
- [`'\<struct hda_pcm\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164): one PCM the codec exports; carries a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L165), two [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L166) entries, a [`pcm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L167), the assigned [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L168) number, and the bound [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L169)
- [`'\<struct hda_pcm_stream\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L140): one direction of a PCM; carries [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L141), the channel and rate/format limits, the converter [`nid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L144), and the per-stream [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L150)
- [`'\<struct hda_pcm_ops\>':'include/sound/hda_codec.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L124): the per-stream codec-side callbacks ([`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L125), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L129), [`cleanup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L132)) that program the converter at hw_params time
- [`'\<struct hda_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L263): one match entry (a [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L264), optional [`rev_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L265), a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L267), and [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L268))

### Codec construction (sound/hda/common/codec.c)

- [`'\<snd_hda_codec_device_init\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885): allocate a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178), call [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) on its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), set the [`HDA_DEV_LEGACY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L104) type, and init the mutexes and snd_array members
- [`'\<snd_hda_codec_device_new\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L967): read the widget caps and pin defaults, power up to D0, create the proc and hwdep nodes, and register the codec as an [`SNDRV_DEV_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h) snd device
- [`'\<snd_hda_codec_new\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947): the combined constructor; runs [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) then [`snd_hda_codec_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L967)
- [`'\<snd_hda_codec_pcm_new\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L700): allocate a [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164), name it, and append it to [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190)
- [`'\<snd_hda_codec_parse_pcms\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3258): call the driver's [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op once, then fill the default rate/format/channel values for each populated stream
- [`'\<snd_hda_codec_build_pcms\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300): assign a device number to each [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) and call [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692)
- [`'\<snd_hda_codec_build_controls\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3060): call the driver's [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) op and run the codec init
- [`'\<snd_hda_codec_register\>':'sound/hda/common/codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L811): start the codec's runtime PM and add it to the bus once probing is done

### Driver binding (sound/hda/common/bind.c)

- [`'\<snd_hda_codec_configure\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L315): register the codec device on [`snd_hda_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/hda_bus_type.c#L79), try a module-specific bind, then fall back to the generic codec, and set [`configured`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L231)
- [`'\<hda_codec_match\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21): the [`match`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L226) callback; walk the driver's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table comparing [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63), and store the hit in [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186)
- [`'\<hda_codec_driver_probe\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87): the driver-core [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h); set the codec name, init regmap, run the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op, then [`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300) and [`snd_hda_codec_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3060)
- [`'\<hda_codec_driver_remove\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L152): the driver-core [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h); disconnect the PCMs, drain the [`pcm_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L191), run the codec [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L110) op, and clear [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186)
- [`'\<hda_codec_unsol_event\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L42): the [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h) hook; forward an unsolicited response to the driver's [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L114) op
- [`'\<__hda_codec_driver_register\>':'sound/hda/common/bind.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L182): fill in the embedded [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222) probe/remove/match callbacks and call [`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c)
- [`snd_hda_codec_set_name`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L64): copy the preset name into the [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179) chip name and update the card mixer name
- [`module_hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103): module init/exit wrapper that calls [`hda_codec_driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L100) and [`hda_codec_driver_unregister()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L102)

### Generic auto-parser (sound/hda/common/auto_parser.c, sound/hda/codecs/generic.c)

- [`'\<snd_hda_parse_pin_defcfg\>':'sound/hda/common/auto_parser.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172): walk every pin widget, read its [`snd_hda_codec_get_pincfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L393) default, and fill a [`struct auto_pin_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63) with line-out, speaker, headphone, mic, and digital pins
- [`'\<struct auto_pin_cfg\>':'sound/hda/common/hda_auto_parser.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63): the parsed pin map; carries [`line_outs`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L64) and [`line_out_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L66), the speaker and HP arrays, the [`inputs`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L73) array, and the digital pins
- [`'\<snd_hda_gen_parse_auto_config\>':'sound/hda/codecs/generic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019): turn a [`struct auto_pin_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63) into DAC/ADC paths, build the mixer controls, and set up the [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90)
- [`'\<snd_hda_gen_build_pcms\>':'sound/hda/codecs/generic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734): the generic [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op; create the Analog, Digital, and Alt Analog [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) objects from the parsed converter nids
- [`'\<snd_hda_gen_build_controls\>':'sound/hda/codecs/generic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5222): the generic [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) op; register the controls the parser built
- [`'\<snd_hda_gen_init\>':'sound/hda/codecs/generic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L6023): the generic codec init; program the parsed pins and paths into the hardware

### PCM attachment (sound/hda/common/controller.c)

- [`'\<snd_hda_attach_pcm_stream\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692): create the ALSA [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L613) for a [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164), wrap it in a [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L40), set [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L611), and pre-allocate the buffer
- [`'\<azx_codec_configure\>':'sound/hda/common/controller.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243): the legacy controller's per-codec configure loop; call [`snd_hda_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L315) on each codec on the bus

### Realtek ALC worked example (sound/hda/codecs/realtek)

- [`'alc269_driver':'sound/hda/codecs/realtek/alc269.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8772): the [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) for the ALC269 and compatible parts; registered through [`module_hda_codec_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103)
- [`'alc269_codec_ops':'sound/hda/codecs/realtek/alc269.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8704): the [`struct hda_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L108) wiring [`alc269_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489), [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734), and [`alc_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L766)
- [`'snd_hda_id_alc269':'sound/hda/codecs/realtek/alc269.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8720): the [`struct hda_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L263) table mapping `0x10ec0269` and siblings to the driver
- [`'\<alc269_probe\>':'sound/hda/codecs/realtek/alc269.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489): the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op; allocate the spec, select the codec variant by [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63), apply fixups, and run [`alc269_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L50)
- [`'\<alc_alloc_spec\>':'sound/hda/codecs/realtek/realtek.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1029): allocate a [`struct alc_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L77), store it in [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195), and init the embedded [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90)
- [`'\<alc269_parse_auto_config\>':'sound/hda/codecs/realtek/alc269.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L50): pick the ignore/SSID nid lists by variant and call [`alc_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1004)
- [`'\<alc_parse_auto_config\>':'sound/hda/codecs/realtek/realtek.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1004): run [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) then [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019)
- [`'\<struct alc_spec\>':'sound/hda/codecs/realtek/realtek.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L77): the Realtek private state; [`gen`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L78) (a [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90)) is its first member, followed by GPIO, mute-LED, and codec-variant fields
- [`'\<alc_build_controls\>':'sound/hda/codecs/realtek/realtek.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L766): the Realtek [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) op; call [`snd_hda_gen_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5222) then apply the build-stage fixups
- [`'\<alc_init\>':'sound/hda/codecs/realtek/realtek.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L779): the Realtek [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L113) op; run the variant init hook and [`snd_hda_gen_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L6023)

## KERNEL DOCUMENTATION

- [`Documentation/sound/hd-audio/notes.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/notes.rst): the HD-Audio driver design, the controller/codec split, and the codec driver binding model
- [`Documentation/sound/hd-audio/models.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/models.rst): the `model=` option that sets [`modelname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L187) and steers the auto-parser, listed per codec family
- [`Documentation/sound/hd-audio/controls.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/controls.rst): the codec-specific mixer controls the [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) op exports
- [`Documentation/sound/hd-audio/realtek-pc-beep.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/realtek-pc-beep.rst): the Realtek PC-beep widget the ALC driver wires through [`beep_nid`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h)
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA PCM and control APIs the [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) objects feed into

## OTHER SOURCES

- [ALSA project HD-Audio wiki](https://www.alsa-project.org/wiki/Matrix:Module-hda-intel)
- [Intel High Definition Audio Specification (Revision 1.0a)](https://www.intel.com/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The codec layer creates four objects whose lifetimes nest inside the controller. The codec object and its driver binding live for as long as the controller card is bound; the PCM objects live across a configure cycle and are torn down at unbind; the parser config is a transient stack object that exists only during the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op.

| object | created by | lifetime |
|--------|-----------|----------|
| [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) | [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) (via [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947)) | from controller probe until the card and its codecs are freed |
| [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) binding | [`hda_codec_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87) after [`hda_codec_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21) sets [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186) | from the driver bind until [`hda_codec_driver_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L152) |
| [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) | [`snd_hda_codec_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L700) inside the [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op | held in [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190) under [`pcm_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L191) until unbind drains the refcount |
| [`struct auto_pin_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63) | [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) (into [`autocfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h)) | populated during [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109); copied into the [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90) |

### struct hda_codec

The codec object is allocated by [`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) and lives until the card is freed. Its first member is the transport [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), so a [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) pointer can be recovered to a [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) with [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) through the [`hdac_to_hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L294) macro, and the device pointer of the embedded core recovers the codec through [`dev_to_hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L291).

### struct hda_codec_driver binding

A vendor module declares one static [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) with its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92) and registers it with [`module_hda_codec_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103). The bind is created when [`hda_codec_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21) finds the codec's [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) in the table and the driver core calls [`hda_codec_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87); it is torn down by [`hda_codec_driver_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L152) at unbind.

### struct hda_pcm

Each [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) is created inside the driver's [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op by [`snd_hda_codec_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L700) and added to [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190). It is reference-counted by the codec's [`pcm_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L191), and [`hda_codec_driver_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L152) waits on [`remove_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L192) until the count drains before freeing the codec.

### struct auto_pin_cfg

The parser config is a transient object filled by [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) during the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op. The Realtek path declares it as the [`autocfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h) member of the codec's [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90), so the parsed pin map outlives the parse call as part of the generic spec.

## DETAILS

### struct hda_codec layers the codec object over hdac_device

A [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178) is the legacy view of one codec. Its first field is the transport [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), the same [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52) the HD-Audio core uses for verbs and the widget tree, and the rest of the struct holds the higher-level state a codec driver needs. That state covers the [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L180) and [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L181) it belongs to, the matched [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186), the [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190), the driver-private [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195), and the widget-capability cache [`wcaps`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L203):

```c
/* include/sound/hda_codec.h:178 */
/* codec information */
struct hda_codec {
	struct hdac_device core;
	struct hda_bus *bus;
	struct snd_card *card;
	unsigned int addr;	/* codec addr*/
	u32 probe_id; /* overridden id for probing */

	/* detected preset */
	const struct hda_device_id *preset;
	const char *modelname;	/* model name for preset */

	/* PCM to create, set by hda_codec_ops.build_pcms callback */
	struct list_head pcm_list_head;
	refcount_t pcm_ref;
	wait_queue_head_t remove_sleep;

	/* codec specific info */
	void *spec;
	...
	/* widget capabilities cache */
	u32 *wcaps;
	...
	/* misc flags */
	unsigned int configured:1; /* codec was configured */
	unsigned int in_freeing:1; /* being released */
	...
};
```

Because [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179) is the first member, the three [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) helpers near the struct convert between the views the driver core and the codec layer use. The bind glue uses [`dev_to_hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L291) to recover a codec from the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) the driver core hands it, and [`hdac_to_hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L294) to recover it from a transport [`struct hdac_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L52):

```c
/* include/sound/hda_codec.h:291 */
#define dev_to_hda_codec(_dev)	container_of(_dev, struct hda_codec, core.dev)
#define hda_codec_dev(_dev)	(&(_dev)->core.dev)

#define hdac_to_hda_codec(_hdac) container_of(_hdac, struct hda_codec, core)
```

The codec object sits inside one [`struct hda_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L38), which itself wraps the transport [`struct hdac_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L291) as its first member [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L39) and adds the ALSA [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L41), the [`pci`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L43) device a Realtek probe inspects for subsystem-id quirks, and the [`prepare_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L46) that serializes PCM prepare:

```c
/* include/sound/hda_codec.h:38 */
struct hda_bus {
	struct hdac_bus core;

	struct snd_card *card;

	struct pci_dev *pci;
	const char *modelname;

	struct mutex prepare_mutex;
	...
};
```

### snd_hda_codec_device_init allocates the codec over its core

[`snd_hda_codec_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L885) is the allocating constructor. It allocates the [`struct hda_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L178), formats the device name from the card and codec address, runs [`snd_hdac_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c#L41) on the embedded [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L179), sets the device type to [`HDA_DEV_LEGACY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L104), and initializes the per-codec mutexes, snd_array tables, and the [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190):

```c
/* sound/hda/common/codec.c:885 */
struct hda_codec *
snd_hda_codec_device_init(struct hda_bus *bus, unsigned int codec_addr,
			  const char *fmt, ...)
{
	va_list vargs;
	char name[DEV_NAME_LEN];
	struct hda_codec *codec;
	int err;
	...
	codec = kzalloc_obj(*codec);
	if (!codec)
		return ERR_PTR(-ENOMEM);
	...
	err = snd_hdac_device_init(&codec->core, &bus->core, name, codec_addr);
	if (err < 0) {
		kfree(codec);
		return ERR_PTR(err);
	}

	codec->bus = bus;
	codec->depop_delay = -1;
	codec->fixup_id = HDA_FIXUP_ID_NOT_SET;
	codec->core.dev.release = snd_hda_codec_dev_release;
	codec->core.type = HDA_DEV_LEGACY;
	...
	INIT_LIST_HEAD(&codec->conn_list);
	INIT_LIST_HEAD(&codec->pcm_list_head);
	INIT_DELAYED_WORK(&codec->jackpoll_work, hda_jackpoll_work);
	refcount_set(&codec->pcm_ref, 1);
	init_waitqueue_head(&codec->remove_sleep);

	return codec;
}
```

The legacy controller path takes the second step through [`snd_hda_codec_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L967), which reads the widget caps with `read_widget_caps()` and the pin defaults with `read_pin_defaults()`, powers the codec to D0, creates its proc and hwdep files, and registers it as an [`SNDRV_DEV_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h) snd device so it is freed with the card. [`snd_hda_codec_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L947) is the wrapper that runs both, which is the entry the controller's codec-creation loop uses:

```c
/* sound/hda/common/codec.c:947 */
int snd_hda_codec_new(struct hda_bus *bus, struct snd_card *card,
		      unsigned int codec_addr, struct hda_codec **codecp)
{
	struct hda_codec *codec;
	int ret;

	codec = snd_hda_codec_device_init(bus, codec_addr, "hdaudioC%dD%d",
					  card->number, codec_addr);
	if (IS_ERR(codec))
		return PTR_ERR(codec);
	*codecp = codec;

	ret = snd_hda_codec_device_new(bus, card, codec_addr, *codecp, true);
	if (ret)
		put_device(hda_codec_dev(*codecp));

	return ret;
}
```

### snd_hda_codec_configure binds a driver to the codec

After the controller has created the codecs, it configures each one. [`azx_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L1243) walks the bus codec list with the [`list_for_each_codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L296) macro and calls [`snd_hda_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L315) on each:

```c
/* sound/hda/common/controller.c:1243 */
int azx_codec_configure(struct azx *chip)
{
	struct hda_codec *codec, *next;
	int success = 0;

	list_for_each_codec(codec, &chip->bus) {
		if (!snd_hda_codec_configure(codec))
			success++;
	}
	...
}
```

[`snd_hda_codec_configure()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L315) registers the codec's device on [`snd_hda_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/hda_bus_type.c#L79) through [`snd_hdac_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/device.c), then tries to bind a vendor module with `codec_bind_module()` and falls back to the generic codec with `codec_bind_generic()`. Binding succeeds when a driver's [`match`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L226) callback sets [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186):

```c
/* sound/hda/common/bind.c:315 */
int snd_hda_codec_configure(struct hda_codec *codec)
{
	int err;

	if (codec->configured)
		return 0;

	if (is_generic_config(codec))
		codec->probe_id = HDA_CODEC_ID_GENERIC;
	else
		codec->probe_id = 0;

	if (!device_is_registered(&codec->core.dev)) {
		err = snd_hdac_device_register(&codec->core);
		if (err < 0)
			return err;
	}

	if (!codec->preset)
		codec_bind_module(codec);
	if (!codec->preset) {
		err = codec_bind_generic(codec);
		if (err < 0) {
			codec_dbg(codec, "Unable to bind the codec\n");
			return err;
		}
	}

	codec->configured = 1;
	return 0;
}
```

The match itself is [`hda_codec_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21). It recovers the codec and the driver from their embedded cores, then walks the driver's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table comparing the codec's [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) (or the override [`probe_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L183) used to force the generic driver) and the [`revision_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L65), and records the matching [`struct hda_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L263) in [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186):

```c
/* sound/hda/common/bind.c:21 */
static int hda_codec_match(struct hdac_device *dev, const struct hdac_driver *drv)
{
	struct hda_codec *codec = container_of(dev, struct hda_codec, core);
	const struct hda_codec_driver *driver =
		container_of(drv, struct hda_codec_driver, core);
	const struct hda_device_id *list;
	/* check probe_id instead of vendor_id if set */
	u32 id = codec->probe_id ? codec->probe_id : codec->core.vendor_id;
	u32 rev_id = codec->core.revision_id;

	for (list = driver->id; list->vendor_id; list++) {
		if (list->vendor_id == id &&
		    (!list->rev_id || list->rev_id == rev_id)) {
			codec->preset = list;
			return 1;
		}
	}
	return 0;
}
```

### hda_codec_driver_probe runs the codec ops

Once the device and driver match, the driver core calls [`hda_codec_driver_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L87). It recovers the codec and driver, sets the codec name from the [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186), initializes the codec's verb-cache regmap, then runs the driver's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op followed by [`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300) and [`snd_hda_codec_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3060). The error tail calls the driver's [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L110) op and clears [`preset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L186) so a later bind can retry:

```c
/* sound/hda/common/bind.c:87 */
static int hda_codec_driver_probe(struct device *dev)
{
	struct hda_codec *codec = dev_to_hda_codec(dev);
	struct module *owner = dev->driver->owner;
	struct hda_codec_driver *driver = hda_codec_to_driver(codec);
	int err;
	...
	if (WARN_ON(!codec->preset))
		return -EINVAL;

	err = snd_hda_codec_set_name(codec, codec->preset->name);
	if (err < 0)
		goto error;
	err = snd_hdac_regmap_init(&codec->core);
	if (err < 0)
		goto error;
	...
	if (WARN_ON(!(driver->ops && driver->ops->probe))) {
		err = -EINVAL;
		goto error_module_put;
	}

	err = driver->ops->probe(codec, codec->preset);
	if (err < 0)
		goto error_module_put;
	err = snd_hda_codec_build_pcms(codec);
	if (err < 0)
		goto error_module;
	err = snd_hda_codec_build_controls(codec);
	if (err < 0)
		goto error_module;
	...
	codec->core.lazy_cache = true;
	return 0;

 error_module:
	if (driver->ops->remove)
		driver->ops->remove(codec);
 error_module_put:
	module_put(owner);

 error:
	snd_hda_codec_cleanup_for_unbind(codec);
	codec->preset = NULL;
	return err;
}
```

The callbacks the glue invokes are the [`struct hda_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L108) function pointer struct. The leading entries are the lifecycle hooks ([`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L110)), the build entries the probe path runs ([`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111), [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112)), the per-init hook [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L113), and the runtime hooks for unsolicited events and power management:

```c
/* include/sound/hda_codec.h:108 */
/* ops for hda codec driver */
struct hda_codec_ops {
	int (*probe)(struct hda_codec *codec, const struct hda_device_id *id);
	void (*remove)(struct hda_codec *codec);
	int (*build_controls)(struct hda_codec *codec);
	int (*build_pcms)(struct hda_codec *codec);
	int (*init)(struct hda_codec *codec);
	void (*unsol_event)(struct hda_codec *codec, unsigned int res);
	void (*set_power_state)(struct hda_codec *codec, hda_nid_t fg,
				unsigned int power_state);
	int (*suspend)(struct hda_codec *codec);
	int (*resume)(struct hda_codec *codec);
	int (*check_power_status)(struct hda_codec *codec, hda_nid_t nid);
	void (*stream_pm)(struct hda_codec *codec, hda_nid_t nid, bool on);
};
```

The [`struct hda_codec_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L89) that carries those ops embeds a transport [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222) as its [`core`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L90), and adds the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92) pointer:

```c
/* include/sound/hda_codec.h:89 */
struct hda_codec_driver {
	struct hdac_driver core;
	const struct hda_device_id *id;
	const struct hda_codec_ops *ops;
};
```

The ops pointer out of that driver lands on this vtable, the figure flagging which entries the bind path runs and in what order, the probe op first and then the two build steps:

```
    struct hda_codec_driver and its hda_codec_ops vtable
    ──────────────────────────────────────────────────────

    struct hda_codec_driver
    ┌──────────────────────────────────┐
    │ core : struct hdac_driver        │
    │ id   ─▶ struct hda_device_id []  │
    │ ops  ─┐                          │
    └──────┼───────────────────────────┘
           │ ops
           ▼
    struct hda_codec_ops
    ┌──────────────────────────────────────────────────┐
    │ probe            ─┐  driver-core bind path       │
    │ build_pcms        │  runs, in order:             │
    │ build_controls    │    probe ─▶ build_pcms       │
    │ init              │           ─▶ build_controls  │
    │ remove           ─┘                              │
    │ unsol_event          jack / unsolicited response │
    │ set_power_state      per-widget power            │
    │ suspend  resume      codec PM                    │
    │ check_power_status   stream_pm                   │
    └──────────────────────────────────────────────────┘
```

### __hda_codec_driver_register wires the driver onto snd_hda_bus_type

A vendor module never calls the driver core directly. The [`module_hda_codec_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103) macro expands to a module init/exit pair that calls [`hda_codec_driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L100), which forwards to [`__hda_codec_driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L182). That function fills in the embedded [`struct hdac_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L222) so its [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h) and [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h) point at the bind glue, its bus is [`snd_hda_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/hda_bus_type.c#L79), and its [`match`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L226) and [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h) are the HDA codec versions, then calls [`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c):

```c
/* sound/hda/common/bind.c:182 */
int __hda_codec_driver_register(struct hda_codec_driver *drv, const char *name,
			       struct module *owner)
{
	drv->core.driver.name = name;
	drv->core.driver.owner = owner;
	drv->core.driver.bus = &snd_hda_bus_type;
	drv->core.driver.probe = hda_codec_driver_probe;
	drv->core.driver.remove = hda_codec_driver_remove;
	drv->core.driver.shutdown = hda_codec_driver_shutdown;
	drv->core.driver.pm = pm_ptr(&hda_codec_driver_pm);
	drv->core.type = HDA_DEV_LEGACY;
	drv->core.match = hda_codec_match;
	drv->core.unsol_event = hda_codec_unsol_event;
	return driver_register(&drv->core.driver);
}
```

The unsolicited-event path the registration installs is [`hda_codec_unsol_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L42). When the controller delivers an unsolicited response (a jack insertion, say), the HD-Audio core dispatches it here, and the glue forwards it to the driver's [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L114) op unless the card or bus is shutting down or in system suspend:

```c
/* sound/hda/common/bind.c:42 */
static void hda_codec_unsol_event(struct hdac_device *dev, unsigned int ev)
{
	struct hda_codec *codec = container_of(dev, struct hda_codec, core);
	struct hda_codec_driver *driver = hda_codec_to_driver(codec);

	/* ignore unsol events during shutdown */
	if (codec->card->shutdown || codec->bus->shutdown)
		return;

	/* ignore unsol events during system suspend/resume */
	if (codec->core.dev.power.power_state.event != PM_EVENT_ON)
		return;

	if (driver->ops->unsol_event)
		driver->ops->unsol_event(codec, ev);
}
```

### The build_pcms op populates pcm_list_head

[`snd_hda_codec_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3300) runs in two stages. It first calls [`snd_hda_codec_parse_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3258) to invoke the driver op and fill the default stream parameters, then walks [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190), assigns each populated [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) a free device number with `get_empty_pcm_device()`, and calls [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692) to create the ALSA PCM:

```c
/* sound/hda/common/codec.c:3300 */
int snd_hda_codec_build_pcms(struct hda_codec *codec)
{
	struct hda_bus *bus = codec->bus;
	struct hda_pcm *cpcm;
	int dev, err;

	err = snd_hda_codec_parse_pcms(codec);
	if (err < 0)
		return err;

	/* attach a new PCM streams */
	list_for_each_entry(cpcm, &codec->pcm_list_head, list) {
		if (cpcm->pcm)
			continue; /* already attached */
		if (!cpcm->stream[0].substreams && !cpcm->stream[1].substreams)
			continue; /* no substreams assigned */

		dev = get_empty_pcm_device(bus, cpcm->pcm_type);
		if (dev < 0) {
			cpcm->device = SNDRV_PCM_INVALID_DEVICE;
			continue; /* no fatal error */
		}
		cpcm->device = dev;
		err =  snd_hda_attach_pcm_stream(bus, codec, cpcm);
		...
	}

	return 0;
}
```

[`snd_hda_codec_parse_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L3258) is where the driver's [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op runs. It calls the op once (guarded so a re-configure does not rebuild), then walks each populated [`struct hda_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L140) and fills its default rate/format/channel values with `set_pcm_default_values()`:

```c
/* sound/hda/common/codec.c:3258 */
int snd_hda_codec_parse_pcms(struct hda_codec *codec)
{
	struct hda_codec_driver *driver = hda_codec_to_driver(codec);
	struct hda_pcm *cpcm;
	int err;

	if (!list_empty(&codec->pcm_list_head))
		return 0; /* already parsed */

	if (!driver->ops->build_pcms)
		return 0;

	err = driver->ops->build_pcms(codec);
	if (err < 0) {
		codec_err(codec, "cannot build PCMs for #%d (error %d)\n",
			  codec->core.addr, err);
		return err;
	}

	list_for_each_entry(cpcm, &codec->pcm_list_head, list) {
		int stream;

		for_each_pcm_streams(stream) {
			struct hda_pcm_stream *info = &cpcm->stream[stream];

			if (!info->substreams)
				continue;
			err = set_pcm_default_values(codec, info);
			...
		}
	}

	return 0;
}
```

Each [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) carries a [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L165), a two-element [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L166) array (one [`struct hda_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L140) per direction), a [`pcm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L167), the assigned [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L168) number, and a back pointer to the owning [`codec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L172) and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L173) link into [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190):

```c
/* include/sound/hda_codec.h:164 */
struct hda_pcm {
	char *name;
	struct hda_pcm_stream stream[2];
	unsigned int pcm_type;	/* HDA_PCM_TYPE_XXX */
	int device;		/* device number to assign */
	struct snd_pcm *pcm;	/* assigned PCM instance */
	bool own_chmap;		/* codec driver provides own channel maps */
	/* private: */
	struct hda_codec *codec;
	struct list_head list;
	unsigned int disconnected:1;
};
```

One [`struct hda_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L140) describes one direction. It carries its [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L141) count (zero means the direction is unused), the channel and rate/format limits the parser fills, the converter [`nid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L144) the prepare path sets up, and the per-stream [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L150) (a [`struct hda_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L124)) whose [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L129) callback programs the converter with the stream tag and format at hw_params time:

```c
/* include/sound/hda_codec.h:140 */
/* PCM information for each substream */
struct hda_pcm_stream {
	unsigned int substreams;	/* number of substreams, 0 = not exist*/
	unsigned int channels_min;	/* min. number of channels */
	unsigned int channels_max;	/* max. number of channels */
	hda_nid_t nid;	/* default NID to query rates/formats/bps, or set up */
	u32 rates;	/* supported rates */
	u64 formats;	/* supported formats (SNDRV_PCM_FMTBIT_) */
	u32 subformats;	/* for S32_LE format, SNDRV_PCM_SUBFMTBIT_* */
	unsigned int maxbps;	/* supported max. bit per sample */
	const struct snd_pcm_chmap_elem *chmap; /* chmap to override */
	struct hda_pcm_ops ops;
};
```

A [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) is created by [`snd_hda_codec_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/codec.c#L700), which a driver's [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op calls once per PCM. It allocates the object, names it with the variadic format, appends it to [`pcm_list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L190), and takes a reference on the codec's [`pcm_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L191):

```c
/* sound/hda/common/codec.c:700 */
struct hda_pcm *snd_hda_codec_pcm_new(struct hda_codec *codec,
				      const char *fmt, ...)
{
	struct hda_pcm *pcm;
	va_list args;

	pcm = kzalloc_obj(*pcm);
	if (!pcm)
		return NULL;

	pcm->codec = codec;
	va_start(args, fmt);
	pcm->name = kvasprintf(GFP_KERNEL, fmt, args);
	va_end(args);
	if (!pcm->name) {
		kfree(pcm);
		return NULL;
	}

	list_add_tail(&pcm->list, &codec->pcm_list_head);
	refcount_inc(&codec->pcm_ref);
	return pcm;
}
```

The attach side, [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692), is where the codec-layer [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) becomes a real ALSA device. It calls [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c) with the substream counts from the two stream entries, wraps the result in a controller-side [`struct azx_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_controller.h#L40), installs [`azx_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L611) for the directions that have substreams, and pre-allocates the DMA buffer:

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
	apcm->chip = chip;
	apcm->pcm = pcm;
	apcm->codec = codec;
	apcm->info = cpcm;
	...
	cpcm->pcm = pcm;
	for (s = 0; s < 2; s++) {
		if (cpcm->stream[s].substreams)
			snd_pcm_set_ops(pcm, s, &azx_pcm_ops);
	}
	...
	return 0;
}
```

The fields that attach reads (the name and the two stream entries) sit in the object this way, each stream expanding into its own per-direction record:

```
    struct hda_pcm memory layout (one PCM, on pcm_list_head)
    ───────────────────────────────────────────────────────

    struct hda_pcm
    ┌──────────────────────────────────────────┐
    │ char *name                               │
    │ unsigned int pcm_type   HDA_PCM_TYPE_    │
    │ int device              assigned number  │
    │ struct snd_pcm *pcm     ALSA instance    │
    │ struct hda_codec *codec  (back ptr)      │
    │ struct list_head list                    │
    │ struct hda_pcm_stream stream[2]          │
    └────────────────────────┬─────────────────┘
                             │ per direction (playback, capture)
                             ▼
    struct hda_pcm_stream
    ┌────────────────────────────────────────────┐
    │ substreams         0 = direction unused    │
    │ channels_min / channels_max                │
    │ hda_nid_t nid      converter widget        │
    │ rates / formats / subformats / maxbps      │
    │ struct hda_pcm_ops ops ─▶ open / prepare / │
    │                          cleanup           │
    └────────────────────────────────────────────┘
```

### The generic auto-parser builds the codec from BIOS pin config

A codec driver that does not hand-roll its widgets uses the generic parser. The parse has two halves. [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) reads the hardware pin configuration into a [`struct auto_pin_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63), and [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019) turns that map into DAC/ADC paths and mixer controls. The first half walks every pin widget with the [`for_each_hda_codec_node`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_local.h) iterator, reads each pin's default with [`snd_hda_codec_get_pincfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L393), and switches on the decoded default-device to file the pin under line-out, speaker, headphone, mic, or digital:

```c
/* sound/hda/common/auto_parser.c:172 */
int snd_hda_parse_pin_defcfg(struct hda_codec *codec,
			     struct auto_pin_cfg *cfg,
			     const hda_nid_t *ignore_nids,
			     unsigned int cond_flags)
{
	...
	for_each_hda_codec_node(nid, codec) {
		unsigned int wid_caps = get_wcaps(codec, nid);
		unsigned int wid_type = get_wcaps_type(wid_caps);
		unsigned int def_conf;
		short assoc, loc, conn, dev;

		/* read all default configuration for pin complex */
		if (wid_type != AC_WID_PIN)
			continue;
		...
		def_conf = snd_hda_codec_get_pincfg(codec, nid);
		conn = get_defcfg_connect(def_conf);
		if (conn == AC_JACK_PORT_NONE)
			continue;
		loc = get_defcfg_location(def_conf);
		dev = get_defcfg_device(def_conf);
		...
		switch (dev) {
		case AC_JACK_LINE_OUT:
			...
			line_out[cfg->line_outs].pin = nid;
			line_out[cfg->line_outs].seq = seq;
			cfg->line_outs++;
			break;
		case AC_JACK_SPEAKER:
			...
			speaker_out[cfg->speaker_outs].pin = nid;
			cfg->speaker_outs++;
			break;
		case AC_JACK_HP_OUT:
			...
			hp_out[cfg->hp_outs].pin = nid;
			cfg->hp_outs++;
			break;
		case AC_JACK_MIC_IN:
			add_auto_cfg_input_pin(codec, cfg, nid, AUTO_PIN_MIC);
			break;
		...
		}
	}
	...
}
```

The result is a [`struct auto_pin_cfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L63) whose arrays name the pins of each role. The output pins are sorted by sequence into [`line_out_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L66), [`speaker_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L68), and [`hp_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L71); the inputs go into the [`inputs`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L73) array; and the digital pins go into [`dig_out_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L75) and [`dig_in_pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/hda_auto_parser.h#L76):

```c
/* sound/hda/common/hda_auto_parser.h:63 */
struct auto_pin_cfg {
	int line_outs;
	/* sorted in the order of Front/Surr/CLFE/Side */
	hda_nid_t line_out_pins[AUTO_CFG_MAX_OUTS];
	int speaker_outs;
	hda_nid_t speaker_pins[AUTO_CFG_MAX_OUTS];
	int hp_outs;
	int line_out_type;	/* AUTO_PIN_XXX_OUT */
	hda_nid_t hp_pins[AUTO_CFG_MAX_OUTS];
	int num_inputs;
	struct auto_pin_cfg_item inputs[AUTO_CFG_MAX_INS];
	int dig_outs;
	hda_nid_t dig_out_pins[2];
	hda_nid_t dig_in_pin;
	hda_nid_t mono_out_pin;
	int dig_out_type[2]; /* HDA_PCM_TYPE_XXX */
	int dig_in_type; /* HDA_PCM_TYPE_XXX */
};
```

The second half, [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019), copies the config into the codec's [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90), fills the DAC nid list, parses the output paths, and creates the multi-out, headphone, speaker, capture, and mic-boost controls. The output-path and control-creation steps run in sequence, each returning a negative error that aborts the parse:

```c
/* sound/hda/codecs/generic.c:5019 */
int snd_hda_gen_parse_auto_config(struct hda_codec *codec,
				  struct auto_pin_cfg *cfg)
{
	struct hda_gen_spec *spec = codec->spec;
	int err;
	...
	if (cfg != &spec->autocfg) {
		spec->autocfg = *cfg;
		cfg = &spec->autocfg;
	}
	...
	fill_all_dac_nids(codec);
	...
	err = parse_output_paths(codec);
	if (err < 0)
		return err;
	err = create_multi_channel_mode(codec);
	if (err < 0)
		return err;
	err = create_multi_out_ctls(codec, cfg);
	if (err < 0)
		return err;
	err = create_hp_out_ctls(codec);
	if (err < 0)
		return err;
	err = create_speaker_out_ctls(codec);
	if (err < 0)
		return err;
	...
	err = create_input_ctls(codec);
	if (err < 0)
		return err;
	...
	err = create_capture_mixers(codec);
	if (err < 0)
		return err;

	err = parse_mic_boost(codec);
	if (err < 0)
		return err;
	...
	return 1;
}
```

The generic [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) op, [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734), then turns the parsed converter nids into [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) objects. It creates an Analog PCM at index 0 (playback off the first DAC, capture off the first ADC), a Digital PCM at index 1 when the codec has an SPDIF or HDMI converter, and an Alt Analog PCM at index 2 for extra ADCs:

```c
/* sound/hda/codecs/generic.c:5734 */
int snd_hda_gen_build_pcms(struct hda_codec *codec)
{
	struct hda_gen_spec *spec = codec->spec;
	struct hda_pcm *info;
	bool have_multi_adcs;

	if (spec->no_analog)
		goto skip_analog;

	fill_pcm_stream_name(spec->stream_name_analog,
			     sizeof(spec->stream_name_analog),
			     " Analog", codec->core.chip_name);
	info = snd_hda_codec_pcm_new(codec, "%s", spec->stream_name_analog);
	if (!info)
		return -ENOMEM;
	spec->pcm_rec[0] = info;

	if (spec->multiout.num_dacs > 0) {
		setup_pcm_stream(&info->stream[SNDRV_PCM_STREAM_PLAYBACK],
				 &pcm_analog_playback,
				 spec->stream_analog_playback,
				 spec->multiout.dac_nids[0]);
		...
	}
	if (spec->num_adc_nids) {
		setup_pcm_stream(&info->stream[SNDRV_PCM_STREAM_CAPTURE],
				 ...
				 spec->adc_nids[0]);
	}

 skip_analog:
	/* SPDIF for stream index #1 */
	if (spec->multiout.dig_out_nid || spec->dig_in_nid) {
		...
		info = snd_hda_codec_pcm_new(codec, "%s",
					     spec->stream_name_digital);
		if (!info)
			return -ENOMEM;
		...
		spec->pcm_rec[1] = info;
		if (spec->dig_out_type)
			info->pcm_type = spec->dig_out_type;
		else
			info->pcm_type = HDA_PCM_TYPE_SPDIF;
		...
	}
	...
	return 0;
}
```

Those PCMs trace back to the pin map the parser filled first, the figure showing each pin's decoded default-device routed into its matching output or input array:

```
    snd_hda_parse_pin_defcfg: pin default-device ─▶ auto_pin_cfg
    ────────────────────────────────────────────────────────────
    (per pin widget: skip non-AC_WID_PIN and AC_JACK_PORT_NONE)

    get_defcfg_device(def_conf)      filed into struct auto_pin_cfg
    ┌──────────────────────┬───────────────────────────────────────┐
    │ AC_JACK_LINE_OUT     │ line_out_pins[], line_outs++          │
    │ AC_JACK_SPEAKER      │ speaker_pins[], speaker_outs++        │
    │ AC_JACK_HP_OUT       │ hp_pins[],      hp_outs++             │
    │ AC_JACK_MIC_IN       │ inputs[] (AUTO_PIN_MIC), num_inputs++ │
    │ (digital)            │ dig_out_pins[] / dig_in_pin           │
    └──────────────────────┴───────────────────────────────────────┘

    each pin read with snd_hda_codec_get_pincfg(); the filled cfg
    then feeds snd_hda_gen_parse_auto_config() to build DAC/ADC paths
```

### A Realtek ALC driver hooks the generic parser in

The Realtek ALC269 family is bound by the static [`alc269_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8772), declared with its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table and its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92), and registered through [`module_hda_codec_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L103):

```c
/* sound/hda/codecs/realtek/alc269.c:8772 */
static struct hda_codec_driver alc269_driver = {
	.id = snd_hda_id_alc269,
	.ops = &alc269_codec_ops,
};

module_hda_codec_driver(alc269_driver);
```

The [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L91) table is an array of [`struct hda_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L263) entries built by the [`HDA_CODEC_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L86) macro, one per supported vendor id, terminated by a zero entry. [`hda_codec_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/bind.c#L21) compares the codec's [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) against the [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L264) field of each:

```c
/* sound/hda/codecs/realtek/alc269.c:8720 */
static const struct hda_device_id snd_hda_id_alc269[] = {
	HDA_CODEC_ID(0x10ec0215, "ALC215"),
	...
	HDA_CODEC_ID(0x10ec0256, "ALC256"),
	HDA_CODEC_ID(0x10ec0257, "ALC257"),
	HDA_CODEC_ID(0x10ec0269, "ALC269"),
	...
	{} /* terminator */
};
MODULE_DEVICE_TABLE(hdaudio, snd_hda_id_alc269);
```

The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L92) the driver supplies, [`alc269_codec_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8704), points its [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) at the Realtek-specific [`alc269_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489), but reuses the generic implementations for the PCM and power ops: [`build_pcms`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L112) is [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734) directly, and [`unsol_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L114) is the shared jack handler [`snd_hda_jack_unsol_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/jack.c#L713):

```c
/* sound/hda/codecs/realtek/alc269.c:8704 */
static const struct hda_codec_ops alc269_codec_ops = {
	.probe = alc269_probe,
	.remove = alc269_remove,
	.build_controls = alc_build_controls,
	.build_pcms = snd_hda_gen_build_pcms,
	.init = alc_init,
	.unsol_event = snd_hda_jack_unsol_event,
	.suspend = alc269_suspend,
	.resume = alc269_resume,
	.check_power_status = snd_hda_gen_check_power_status,
	.stream_pm = snd_hda_gen_stream_pm,
};
```

[`alc269_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L8489) is the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L109) op the bind glue runs. It allocates the spec with [`alc_alloc_spec()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1029), selects a codec variant from the [`vendor_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L63) and the COEF register, applies the pin and vendor fixups, and finally runs the auto-parse through [`alc269_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L50):

```c
/* sound/hda/codecs/realtek/alc269.c:8489 */
static int alc269_probe(struct hda_codec *codec, const struct hda_device_id *id)
{
	struct alc_spec *spec;
	int err;

	err = alc_alloc_spec(codec, 0x0b);
	if (err < 0)
		return err;

	spec = codec->spec;
	spec->gen.shared_mic_vref_pin = 0x18;
	codec->power_save_node = 0;
	spec->en_3kpull_low = true;
	...
	switch (codec->core.vendor_id) {
	case 0x10ec0269:
		spec->codec_variant = ALC269_TYPE_ALC269VA;
		...
		break;
	...
	}
	...
	/* automatic parse from the BIOS config */
	err = alc269_parse_auto_config(codec);
	if (err < 0)
		goto error;
	...
	return 0;

 error:
	alc269_remove(codec);
	return err;
}
```

[`alc_alloc_spec()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1029) allocates a [`struct alc_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L77), stores it in the codec's [`spec`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L195), initializes the embedded [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90) with [`snd_hda_gen_spec_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L37), and records the mixer nid the parser uses as the analog mixing widget:

```c
/* sound/hda/codecs/realtek/realtek.c:1029 */
int alc_alloc_spec(struct hda_codec *codec, hda_nid_t mixer_nid)
{
	struct alc_spec *spec = kzalloc_obj(*spec);
	int err;

	if (!spec)
		return -ENOMEM;
	codec->spec = spec;
	snd_hda_gen_spec_init(&spec->gen);
	spec->gen.mixer_nid = mixer_nid;
	spec->gen.own_eapd_ctl = 1;
	codec->single_adc_amp = 1;
	/* FIXME: do we need this for all Realtek codec models? */
	codec->spdif_status_reset = 1;
	codec->forced_resume = 1;
	mutex_init(&spec->coef_mutex);

	err = alc_codec_rename_from_preset(codec);
	if (err < 0) {
		kfree(spec);
		return err;
	}
	return 0;
}
```

The [`struct alc_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L77) keeps the generic [`gen`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.h#L78) as its first member so the generic parser and the Realtek code share the same spec, and the comment states the constraint:

```c
/* sound/hda/codecs/realtek/realtek.h:77 */
struct alc_spec {
	struct hda_gen_spec gen; /* must be at head */

	/* codec parameterization */
	struct alc_customize_define cdefine;
	unsigned int parse_flags; /* flag for snd_hda_parse_pin_defcfg() */

	/* GPIO bits */
	unsigned int gpio_mask;
	unsigned int gpio_dir;
	unsigned int gpio_data;
	...
	int init_amp;
	int codec_variant;	/* flag for other variants */
	...
};
```

The Realtek auto-parse runs in two layers. [`alc269_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/alc269.c#L50) picks the ignore-nid and SSID-nid lists by codec variant and forwards to the shared [`alc_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1004):

```c
/* sound/hda/codecs/realtek/alc269.c:50 */
static int alc269_parse_auto_config(struct hda_codec *codec)
{
	static const hda_nid_t alc269_ignore[] = { 0x1d, 0 };
	static const hda_nid_t alc269_ssids[] = { 0, 0x1b, 0x14, 0x21 };
	static const hda_nid_t alc269va_ssids[] = { 0x15, 0x1b, 0x14, 0 };
	struct alc_spec *spec = codec->spec;
	const hda_nid_t *ssids;

	switch (spec->codec_variant) {
	...
	case ALC269_TYPE_ALC269VB:
	...
		ssids = alc269_ssids;
		break;
	default:
		ssids = alc269_ssids;
		break;
	}

	return alc_parse_auto_config(codec, alc269_ignore, ssids);
}
```

[`alc_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L1004) is the join point with the generic parser. It runs [`snd_hda_parse_pin_defcfg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/auto_parser.c#L172) into the spec's [`autocfg`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h), checks the subsystem id for board-specific quirks, then runs [`snd_hda_gen_parse_auto_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5019) to build the paths and controls:

```c
/* sound/hda/codecs/realtek/realtek.c:1004 */
int alc_parse_auto_config(struct hda_codec *codec,
			  const hda_nid_t *ignore_nids,
			  const hda_nid_t *ssid_nids)
{
	struct alc_spec *spec = codec->spec;
	struct auto_pin_cfg *cfg = &spec->gen.autocfg;
	int err;

	err = snd_hda_parse_pin_defcfg(codec, cfg, ignore_nids,
				       spec->parse_flags);
	if (err < 0)
		return err;

	if (ssid_nids)
		alc_ssid_check(codec, ssid_nids);

	err = snd_hda_gen_parse_auto_config(codec, cfg);
	if (err < 0)
		return err;

	return 1;
}
```

After the probe op returns, the bind glue calls the [`build_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L111) op. The Realtek [`alc_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L766) defers to [`snd_hda_gen_build_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5222) for the controls the parser created, then applies the build-stage fixups:

```c
/* sound/hda/codecs/realtek/realtek.c:766 */
int alc_build_controls(struct hda_codec *codec)
{
	int err;

	err = snd_hda_gen_build_controls(codec);
	if (err < 0)
		return err;

	snd_hda_apply_fixup(codec, HDA_FIXUP_ACT_BUILD);
	return 0;
}
```

The [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L113) op, [`alc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/realtek/realtek.c#L779), runs the variant init hook the probe selected and then [`snd_hda_gen_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L6023), which programs the parsed pins and paths into the hardware, so the same parsed [`struct hda_gen_spec`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.h#L90) drives the PCM build, the control build, and the hardware init:

```c
/* sound/hda/codecs/realtek/realtek.c:779 */
int alc_init(struct hda_codec *codec)
{
	struct alc_spec *spec = codec->spec;

	/* hibernation resume needs the full chip initialization */
	if (is_s4_resume(codec))
		alc_pre_init(codec);

	if (spec->init_hook)
		spec->init_hook(codec);

	spec->gen.skip_verbs = 1; /* applied in below */
	snd_hda_gen_init(codec);
	alc_fix_pll(codec);
	alc_auto_init_amp(codec, spec->init_amp);
	snd_hda_apply_verbs(codec); /* apply verbs here after own init */

	snd_hda_apply_fixup(codec, HDA_FIXUP_ACT_INIT);

	return 0;
}
```

All of these steps reach the codec spec through both views, the figure placing the generic state at offset 0 so the Realtek struct and the generic struct land on the same bytes:

```
    codec->spec aliases struct alc_spec and its head hda_gen_spec
    ─────────────────────────────────────────────────────────────

    struct hda_codec
    ┌─────────────────────────┐
    │ void *spec ─┐           │
    └────────────┼────────────┘
                 │ one address, two views (gen at offset 0)
        ┌────────┴────────┐
        ▼                 ▼
    struct alc_spec       struct hda_gen_spec  (= &spec->gen)
    ┌────────────────────────────────────────────────────┐
    │ struct hda_gen_spec gen     (must be at head)      │
    │   autocfg, dac/adc nids, mixer state               │
    │ struct alc_customize_define cdefine                │
    │ unsigned int parse_flags                           │
    │ gpio_mask / gpio_dir / gpio_data                   │
    │ int init_amp / codec_variant                       │
    └────────────────────────────────────────────────────┘

    Realtek code uses alc_spec; the generic parser uses the
    same bytes as hda_gen_spec, so one parse fills both views
```
