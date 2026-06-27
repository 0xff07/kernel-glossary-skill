# ALSA object model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ALSA models one sound card as a [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) that owns a list of [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) components, each stamped with an [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) tag and pointing back at its card. Exactly one component is the control device ([`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50)); the rest wrap functional objects a driver creates, among them a PCM device ([`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43)), a raw MIDI device, and a timer. A PCM device is a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) carrying two [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) stream descriptors (playback at index 0, capture at index 1), each stream owns a singly linked chain of [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) (one per subdevice), and opening a substream allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) that holds the negotiated hardware parameters and the ring-buffer state. A mixer control is a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) registered on the card itself and reached through that single control device rather than through a device of its own. ASoC layers on this model without replacing it, since [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) to create the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) it stores in [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and an ASoC PCM is an ordinary [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) built by [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767).

```
    snd_card  (one per sound card)
    ┌───────────────────────────────────────────┐
    │ devices ──▶ list of snd_device            │
    │ controls ─▶ list of snd_kcontrol          │
    │ card_dev   (cardX, /sys/class/sound)      │
    └───────────────────┬───────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    snd_device      snd_device        snd_device
    SNDRV_DEV_      SNDRV_DEV_PCM     SNDRV_DEV_
    CONTROL                          RAWMIDI ...
        │               │
        ▼               ▼
    controlC0       snd_pcm
    node            ┌──────────────────────────┐
                    │ streams[0] playback      │
                    │ streams[1] capture       │
                    └──────┬─────────────┬─────┘
                           ▼             ▼
                    snd_pcm_str     snd_pcm_str
                    (playback)      (capture)
                       │ substream     │
                       ▼               ▼
                    snd_pcm_substream  ...  (one per subdevice)
                       │ next ──▶ substream ──▶ substream
                       ▼
                    snd_pcm_runtime  (allocated on open)
```

## SUMMARY

The card is the root. A driver brings it into existence with [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), which allocates the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) together with an optional private region, attaches the card to a parent [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), and initializes the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) that surfaces as cardX in sysfs. A functional object joins the card as a component through [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29), which allocates a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), records its [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38), and links it into the card's [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list in type order, so the control device, which the enum lists last, registers after everything it depends on. That control device is produced by [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) and is the lone [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) component on every card.

A PCM device starts at [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), which forwards to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697). That allocates a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), populates its two [`streams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) entries with one [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) call per direction, and then registers the whole PCM as an [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) component with [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29). Each [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) call fills the per-direction [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) and threads one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice through the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer. The [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) comes later, at the moment a client opens a substream, when [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) allocates it and stores it in [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464).

A mixer control follows a separate path. [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) places a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) on the card's own [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list, where it is reached through the single control device and is never wrapped in a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67). The whole card becomes visible with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870), which adds [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) to sysfs and then calls [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189) to walk the [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list and publish a character-device node for each registrable component. ASoC reaches the same machinery through [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), which calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), builds the per-link PCMs as [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) objects, and closes with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870).

## SPECIFICATIONS

The ALSA object model is a Linux kernel software construct and has no standalone hardware specification. The userspace boundary it exposes, the control protocol over /dev/snd/controlC%d and the PCM protocol over /dev/snd/pcmC%iD%i%c, is defined by the uapi structures and ioctls in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The stream formats a PCM carries (the `SNDRV_PCM_FORMAT_*` sets and the rate sets) follow the codec and bus standards of the hardware behind the card.

## LINUX KERNEL

### Core object types (include/sound/core.h)

- [`'\<struct snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80): the root object for one sound card; owns the [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list, the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list, the [`ctl_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) control device, and the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) cardX sysfs object
- [`'\<struct snd_device\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67): one component attached to a card; carries the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) tag, the opaque [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer to the real object, and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) function pointer struct that registers and frees it
- [`'\<enum snd_device_type\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38): the component type, which doubles as the registration order; [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) for a PCM device and [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) (last in the enum) for the control device
- [`'\<struct snd_device_ops\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61): the per-component [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61)/[`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61)/[`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) hooks the lifecycle runs

### PCM object types (include/sound/pcm.h)

- [`'\<struct snd_pcm\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534): one PCM device; holds the [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) index and the two-element [`streams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) array
- [`'\<struct snd_pcm_str\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513): one direction's stream descriptor; holds [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), the head [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) pointer, and the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) naming the pcmC%iD%i%c node
- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): one subdevice instance; back-points to its [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) and [`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), chains onward through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), and owns the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) once opened
- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the per-open state; holds the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the negotiated HW params ([`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)), and the [`dma_area`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) ring buffer

### Control object type (include/sound/control.h)

- [`'\<struct snd_kcontrol\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70): one mixer control; identified by [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), driven by [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) callbacks, registered on the card instead of inside a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67)

### Card and component lifecycle (sound/core)

- [`'\<snd_card_new\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171): allocate and initialize a [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) with the requested index, id, and private size
- [`'\<snd_card_register\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870): add [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) to sysfs and register every component through [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189)
- [`'\<snd_device_new\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29): allocate a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) and splice it into [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) sorted by [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38)
- [`'\<snd_device_register_all\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189): walk the [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list and run each component's register op
- [`'\<snd_register_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249): assign a minor and create the /dev/snd character-device node for a component
- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291): the [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) register op that publishes the controlC%d node

### PCM lifecycle (sound/core/pcm.c)

- [`'\<snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767): public entry that creates a non-internal PCM, forwarding to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697)
- [`'\<_snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697): allocate the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), build both streams, and attach it as an [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) component
- [`'\<snd_pcm_new_stream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627): fill one [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), name its [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), and link the per-subdevice [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) chain
- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): pick a free substream on open and allocate its [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362)
- [`'\<snd_pcm_dev_register\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044): the [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) register op that creates a pcmC%iD%i%c node per populated direction

### Control registration and the userspace ioctl (sound/core/control.c)

- [`'\<snd_ctl_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546): add a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to the card's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list and assign its numid
- [`'\<snd_ctl_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899): the controlC%d ioctl dispatcher; its [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) case calls [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867)
- [`'\<snd_ctl_card_info\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867): copy card identity fields into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063) for userspace

### ASoC entry on top of the model (sound/soc/soc-core.c)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the ASoC card; holds the [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) pointer to the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) it creates
- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): build an ASoC card by calling [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), creating the per-link PCMs, and registering with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the card/device/PCM/control construction walkthrough, including [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) usage
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated API reference pulling kernel-doc from [`sound/core/pcm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c) and [`include/sound/pcm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h)
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the naming convention for the [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) identity exposed on the control device
- [`Documentation/sound/designs/channel-mapping-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/channel-mapping-api.rst): the channel-map controls attached per [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) through [`chmap_kctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513)
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver that populates a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) before [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) builds the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80)

## OTHER SOURCES

- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [ALSA project wiki](https://www.alsa-project.org/wiki/Main_Page)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

User space reaches the card through three surfaces, the character-device nodes under /dev/snd, the text files under /proc/asound, and the sysfs attributes under /sys/class/sound. A different mechanism derives each surface from the in-kernel object graph, and the table maps the kernel object to the node and to the call that creates it.

| kernel object | userspace surface | created by |
|---------------|-------------------|------------|
| control device ([`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50)) | /dev/snd/controlC%d | [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) |
| [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) direction | /dev/snd/pcmC%iD%i%c | [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044) |
| [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | `SNDRV_CTL_IOCTL_ELEM_*` on controlC%d | [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) |
| [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) identity | [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) | [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) |
| [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) | /sys/class/sound/cardX | [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) |

### controlC%d carries the whole card

Each card has exactly one control node, /dev/snd/controlC%d, named from [`card->number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) when [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) runs [`dev_set_name(card->ctl_dev, "controlC%d", ...)`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2367). Opening this node lets a client enumerate and operate every [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) on the card and query the card itself, all through [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899).

### pcmC%iD%i%c is per direction

Each playback or capture direction of a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) gets its own node, /dev/snd/pcmC%iD%i%c, with a trailing `p` for playback or `c` for capture. [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) sets the name from [`card->number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`pcm->device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), and the direction, and [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044) publishes the node.

### /proc/asound and /sys/class/sound/cardX

The text view under /proc/asound is rooted at the [`asound`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/info.c#L431) proc directory, where each card gets a numbered subtree plus an id symlink, so /proc/asound/card0 and /proc/asound/pcmCxDyp expose human-readable state. The sysfs view comes from the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), initialized with class [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) and name cardX, so /sys/class/sound/cardX exposes the [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L808) and [`number`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L817) attributes once [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) adds it.

## DETAILS

### The card is the root and owns two separate lists

The [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) is the anchor every other object points back to, and its two collections stay distinct. The [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list holds [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) components (the PCM, raw MIDI, timer, and the control device), while the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list holds [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) objects directly. The embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) is the sysfs cardX object, and [`ctl_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) is the device behind the controlC%d node:

```c
/* include/sound/core.h:80 */
struct snd_card {
	int number;			/* number of soundcard (index to
								snd_cards) */

	char id[16];			/* id string of this card */
	char driver[16];		/* driver name */
	char shortname[32];		/* short name of this soundcard */
	char longname[80];		/* name of this soundcard */
	...
	struct list_head devices;	/* devices */

	struct device *ctl_dev;		/* control device */
	...
	struct list_head controls;	/* all controls for this card */
	struct list_head ctl_files;	/* active control files */
	...
	struct device *dev;		/* device assigned to this card */
	struct device card_dev;		/* cardX object for sysfs */
	const struct attribute_group *dev_groups[4]; /* assigned sysfs attr */
	bool registered;		/* card_dev is registered? */
	...
};
```

[`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) allocates the structure with the requested [`extra_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) for driver-private data appended after it, then hands the rest of the setup to [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276):

```c
/* sound/core/init.c:171 */
int snd_card_new(struct device *parent, int idx, const char *xid,
		    struct module *module, int extra_size,
		    struct snd_card **card_ret)
{
	struct snd_card *card;
	int err;

	if (snd_BUG_ON(!card_ret))
		return -EINVAL;
	*card_ret = NULL;

	if (extra_size < 0)
		extra_size = 0;
	card = kzalloc(sizeof(*card) + extra_size, GFP_KERNEL);
	if (!card)
		return -ENOMEM;

	err = snd_card_init(card, parent, idx, xid, module, extra_size);
	if (err < 0)
		return err; /* card is freed by error handler */

	*card_ret = card;
	return 0;
}
```

The structure that allocates here keeps its components apart in two lists, the devices list holding the snd_device wrappers (the PCM, raw MIDI, timer, and control) and the controls list holding the kcontrol mixer entries directly:

```
    snd_card owns two separate collections
    ──────────────────────────────────────

    ┌─────────────────────────────────────────────┐
    │ struct snd_card                             │
    │   devices    (list_head)                    │
    │   controls   (list_head)                    │
    │   ctl_dev   ─▶ controlC%d device            │
    │   card_dev  ─▶ cardX sysfs object           │
    └───────┬────────────────────────┬────────────┘
            │ devices                │ controls
            ▼                        ▼
    ┌───────────────────┐    ┌────────────────────┐
    │ snd_device list   │    │ snd_kcontrol list  │
    │  PCM, RAWMIDI,    │    │  mixer controls    │
    │  timer, CONTROL   │    │  (added directly)  │
    └───────────────────┘    └────────────────────┘
```

### A component is a snd_device with a type tag

A functional object joins the card as a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), a thin wrapper holding the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), an opaque [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer to the real object, and an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) function pointer struct that knows how to register, disconnect, and free it:

```c
/* include/sound/core.h:67 */
struct snd_device {
	struct list_head list;		/* list of registered devices */
	struct snd_card *card;		/* card which holds this device */
	enum snd_device_state state;	/* state of the device */
	enum snd_device_type type;	/* device type */
	void *device_data;		/* device structure */
	const struct snd_device_ops *ops;	/* operations */
};
```

The [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) value names both the kind of the component and the order it registers in. According to the comment on the enum, "this also defines the calling order", and [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) carries the comment "NOTE: this must be the last one", so the control device registers after the PCM and the other lower-numbered components:

```c
/* include/sound/core.h:38 */
enum snd_device_type {
	SNDRV_DEV_LOWLEVEL,
	SNDRV_DEV_INFO,
	SNDRV_DEV_BUS,
	SNDRV_DEV_CODEC,
	SNDRV_DEV_PCM,
	SNDRV_DEV_COMPRESS,
	SNDRV_DEV_RAWMIDI,
	SNDRV_DEV_TIMER,
	SNDRV_DEV_SEQUENCER,
	SNDRV_DEV_HWDEP,
	SNDRV_DEV_JACK,
	SNDRV_DEV_CONTROL,	/* NOTE: this must be the last one */
};
```

[`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29) applies that order at insertion. It walks [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) backward and inserts the new component after the first entry whose type is less than or equal to the new one, keeping the list sorted so that [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189) later registers in type order:

```c
/* sound/core/device.c:29 */
int snd_device_new(struct snd_card *card, enum snd_device_type type,
		   void *device_data, const struct snd_device_ops *ops)
{
	struct snd_device *dev;
	struct list_head *p;

	if (snd_BUG_ON(!card || !device_data || !ops))
		return -ENXIO;
	dev = kzalloc_obj(*dev);
	if (!dev)
		return -ENOMEM;
	INIT_LIST_HEAD(&dev->list);
	dev->card = card;
	dev->type = type;
	dev->state = SNDRV_DEV_BUILD;
	dev->device_data = device_data;
	dev->ops = ops;

	/* insert the entry in an incrementally sorted list */
	list_for_each_prev(p, &card->devices) {
		struct snd_device *pdev = list_entry(p, struct snd_device, list);
		if ((unsigned int)pdev->type <= (unsigned int)type)
			break;
	}

	list_add(&dev->list, p);
	return 0;
}
```

The sorted insert above lays the components out in type order, the low-numbered hardware level at the head and the control device at the tail where its comment requires it:

```
    enum snd_device_type value = position in card->devices
    ──────────────────────────────────────────────────────
    snd_device_new inserts sorted; register walks low ─▶ high

    head (low type)                              tail (high type)
       SNDRV_DEV_LOWLEVEL = 0   ─▶ registers first  (hardware)
       SNDRV_DEV_INFO     = 1
       ...
       SNDRV_DEV_PCM      = 4   ─▶ the pcmC%iD%i%c nodes
       ...
       SNDRV_DEV_CONTROL  = 11  ─▶ registers last   (controlC%d)
                                   "must be the last one"
```

### A PCM device holds two streams

A [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) is the object a PCM component points at through [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67). It carries a [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) index and a fixed two-element [`streams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) array, index 0 for playback and index 1 for capture:

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
	...
};
```

Each [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) describes one direction. It records the subdevice count in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), points at the head of the substream chain through [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), and owns the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) that names the character node:

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

The [`chmap_kctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) field shows a stream can own a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) for channel mapping, yet that control still lands on the card's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) list and surfaces through the one control device rather than the PCM node.

### snd_pcm_new builds both streams

[`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) is a one-line forwarder to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) with `internal` false:

```c
/* sound/core/pcm.c:767 */
int snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, struct snd_pcm **rpcm)
{
	return _snd_pcm_new(card, id, device, playback_count, capture_count,
			false, rpcm);
}
```

[`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) allocates the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), calls [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) once per direction with the requested substream count, then registers the PCM as an [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) component whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) wire up [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044):

```c
/* sound/core/pcm.c:697 */
static int _snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, bool internal,
		struct snd_pcm **rpcm)
{
	struct snd_pcm *pcm;
	int err;
	static const struct snd_device_ops ops = {
		.dev_free = snd_pcm_dev_free,
		.dev_register =	snd_pcm_dev_register,
		.dev_disconnect = snd_pcm_dev_disconnect,
	};
	...
	pcm->card = card;
	pcm->device = device;
	pcm->internal = internal;
	...
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

### A stream holds a chain of substreams

[`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) fills one [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513), names its [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) with the pcmC%iD%i%c pattern, and allocates one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice, threading them through the [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) pointer with the head kept in [`pstr->substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513):

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
	...
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
		prev = substream;
	}
	return 0;
}
```

The [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) back-points to its parent [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) and [`pstr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), chains to its sibling through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), and reserves the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) slot that stays null until the subdevice is opened:

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
	/* -- runtime information -- */
	struct snd_pcm_runtime *runtime;
	...
	/* -- next substream -- */
	struct snd_pcm_substream *next;
	...
	int ref_count;
	atomic_t mmap_count;
	unsigned int f_flags;
	...
};
```

### The runtime is created on open

The [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) is the one object in the hierarchy that is per-open rather than per-device. It holds the stream [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), the negotiated hardware parameters, the software parameters, and the DMA ring buffer pointer:

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
	snd_pcm_subformat_t subformat;	/* subformat */
	unsigned int rate;		/* rate in Hz */
	unsigned int channels;		/* channels */
	snd_pcm_uframes_t period_size;	/* period size */
	unsigned int periods;		/* periods */
	snd_pcm_uframes_t buffer_size;	/* buffer size */
	...
	/* -- DMA -- */
	unsigned char *dma_area;	/* DMA area */
	dma_addr_t dma_addr;		/* physical bus address (not accessible from main CPU) */
	size_t dma_bytes;		/* size of DMA area */
	...
};
```

[`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) runs when a client opens a pcmC%iD%i%c node. It selects a free substream from the chain, allocates the runtime, seeds the initial [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) to [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307), and stores it in [`substream->runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464):

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
	...
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

The runtime that attach allocates here carries the per-open transfer state, the stream state at the top, the negotiated format, rate, and channels below it, and the DMA ring buffer at the bottom:

```
    struct snd_pcm_runtime  (allocated per open by attach)
    ─────────────────────────────────────────────────────

    substream->runtime ─▶ ┌──────────────────────────────┐
                          │ -- Status --                 │
                          │   state (SNDRV_PCM_STATE_*)  │
                          ├──────────────────────────────┤
                          │ -- HW params --              │
                          │   format  rate  channels     │
                          │   buffer_size                │
                          ├──────────────────────────────┤
                          │ -- DMA --                    │
                          │   dma_area (ring buffer)     │
                          │   dma_addr  dma_bytes        │
                          └──────────────────────────────┘
       null until open; freed on close (per-open scope)
```

### A control is added to the card through snd_ctl_add

A [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) is reached through the one control device yet is itself no [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67). It carries a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) identity and the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) callbacks the ioctl path drives:

```c
/* include/sound/control.h:70 */
struct snd_kcontrol {
	struct list_head list;		/* list of controls */
	struct snd_ctl_elem_id id;
	unsigned int count;		/* count of same elements */
	snd_kcontrol_info_t *info;
	snd_kcontrol_get_t *get;
	snd_kcontrol_put_t *put;
	union {
		snd_kcontrol_tlv_rw_t *c;
		const unsigned int *p;
	} tlv;
	unsigned long private_value;
	void *private_data;
	void (*private_free)(struct snd_kcontrol *kcontrol);
	struct snd_kcontrol_volatile vd[] __counted_by(count);	/* volatile data */
};
```

[`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) places the control on the card. It forwards to [`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509) in [`CTL_ADD_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454) mode, which links the control into [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) and assigns the numid used for fast lookup:

```c
/* sound/core/control.c:546 */
int snd_ctl_add(struct snd_card *card, struct snd_kcontrol *kcontrol)
{
	return snd_ctl_add_replace(card, kcontrol, CTL_ADD_EXCLUSIVE);
}
```

### Registration walks the device list and creates nodes

[`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) is where the in-memory object graph becomes visible to user space. It adds the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) to sysfs (creating /sys/class/sound/cardX), marks the card [`registered`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), and calls [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189) to register every component:

```c
/* sound/core/init.c:870 */
int snd_card_register(struct snd_card *card)
{
	int err;

	if (snd_BUG_ON(!card))
		return -EINVAL;

	if (!card->registered) {
		err = device_add(&card->card_dev);
		if (err < 0)
			return err;
		card->registered = true;
	} else {
		...
	}
	...
	err = snd_device_register_all(card);
	if (err < 0)
		return err;
	...
}
```

The PCM register op [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044) loops over the two directions of the [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), skips a direction with no substreams, and calls [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) once per populated direction with the per-direction [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) to create the pcmC%iD%i%c node:

```c
/* sound/core/pcm.c:1044 */
static int snd_pcm_dev_register(struct snd_device *device)
{
	int cidx, err;
	struct snd_pcm_substream *substream;
	struct snd_pcm *pcm;
	...
	pcm = device->device_data;

	guard(mutex)(&register_mutex);
	err = snd_pcm_add(pcm);
	if (err)
		return err;
	for (cidx = 0; cidx < 2; cidx++) {
		int devtype = -1;
		if (pcm->streams[cidx].substream == NULL)
			continue;
		switch (cidx) {
		case SNDRV_PCM_STREAM_PLAYBACK:
			devtype = SNDRV_DEVICE_TYPE_PCM_PLAYBACK;
			break;
		case SNDRV_PCM_STREAM_CAPTURE:
			devtype = SNDRV_DEVICE_TYPE_PCM_CAPTURE;
			break;
		}
		/* register pcm */
		err = snd_register_device(devtype, pcm->card, pcm->device,
					  &snd_pcm_f_ops[cidx], pcm,
					  pcm->streams[cidx].dev);
		...
	}
	...
}
```

[`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) claims a free minor, sets the devt on the passed [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), and adds it so udev creates the /dev/snd node:

```c
/* sound/core/sound.c:249 */
int snd_register_device(int type, struct snd_card *card, int dev,
			const struct file_operations *f_ops,
			void *private_data, struct device *device)
{
	int minor;
	int err = 0;
	struct snd_minor *preg;
	...
	guard(mutex)(&sound_mutex);
	minor = snd_find_free_minor(type, card, dev);
	if (minor < 0) {
		err = minor;
		goto error;
	}

	preg->dev = device;
	device->devt = MKDEV(major, minor);
	err = device_add(device);
	if (err < 0)
		goto error;

	snd_minors[minor] = preg;
 error:
	if (err < 0)
		kfree(preg);
	return err;
}
```

### Userspace reads card identity through SNDRV_CTL_IOCTL_CARD_INFO

A client that has opened controlC%d learns about the card by issuing [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200), defined in the uapi header as a read ioctl returning a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063):

```c
/* include/uapi/sound/asound.h:1200 */
#define SNDRV_CTL_IOCTL_CARD_INFO	_IOR('U', 0x01, struct snd_ctl_card_info)
```

The dispatcher [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) routes that command to [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867):

```c
/* sound/core/control.c:1915 */
	case SNDRV_CTL_IOCTL_CARD_INFO:
		return snd_ctl_card_info(card, ctl, cmd, argp);
```

[`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) copies the identity fields straight out of the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), the [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`shortname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), [`mixername`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), and [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), into the uapi structure and returns it to user space:

```c
/* sound/core/control.c:867 */
static int snd_ctl_card_info(struct snd_card *card, struct snd_ctl_file * ctl,
			     unsigned int cmd, void __user *arg)
{
	struct snd_ctl_card_info *info __free(kfree) =
		kzalloc(sizeof(*info), GFP_KERNEL);

	if (! info)
		return -ENOMEM;
	scoped_guard(rwsem_read, &snd_ioctl_rwsem) {
		info->card = card->number;
		strscpy(info->id, card->id, sizeof(info->id));
		strscpy(info->driver, card->driver, sizeof(info->driver));
		strscpy(info->name, card->shortname, sizeof(info->name));
		strscpy(info->longname, card->longname, sizeof(info->longname));
		strscpy(info->mixername, card->mixername, sizeof(info->mixername));
		strscpy(info->components, card->components, sizeof(info->components));
	}
	if (copy_to_user(arg, info, sizeof(struct snd_ctl_card_info)))
		return -EFAULT;
	return 0;
}
```

The [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063) mirrors the in-kernel name fields, which keeps the kernel object and the userspace view in step:

```c
/* include/uapi/sound/asound.h:1063 */
struct snd_ctl_card_info {
	int card;			/* card number */
	int pad;			/* reserved for future (was type) */
	unsigned char id[16];		/* ID of card (user selectable) */
	unsigned char driver[16];	/* Driver name */
	unsigned char name[32];		/* Short name of soundcard */
	unsigned char longname[80];	/* name + info text about soundcard */
	unsigned char reserved_[16];	/* reserved for future (was ID of mixer) */
	unsigned char mixername[80];	/* visual mixer identification */
	unsigned char components[128];	/* card components / fine identification, delimited with one space (AC97 etc..) */
};
```

### ASoC creates a snd_card and ordinary PCMs

[`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is the ASoC card description, and it keeps a [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) pointer to the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) that backs it:

```c
/* include/sound/soc.h:972 */
struct snd_soc_card {
	const char *name;
	const char *long_name;
	const char *driver_name;
	const char *components;
	...
	struct device *dev;
	struct snd_card *snd_card;
	struct module *owner;
	...
};
```

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) is where ASoC enters the ALSA object model. It calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) to allocate the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) into [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and later, after the per-link PCMs and controls are built, calls [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) on that same object, so the resulting card, its PCM devices, and its controls are the same kinds of objects this page describes:

```c
/* sound/soc/soc-core.c:2163 */
static int snd_soc_bind_card(struct snd_soc_card *card)
{
	...
	/* card bind complete so register a sound card */
	ret = snd_card_new(card->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
			card->owner, 0, &card->snd_card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: can't create sound card for card %s: %d\n",
			card->name, ret);
		goto probe_end;
	}
	...
	ret = snd_card_register(card->snd_card);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: failed to register soundcard %d\n",
				ret);
		goto probe_end;
	}

	card->instantiated = 1;
	...
}
```

The ASoC core builds each DAI link's PCM as a plain [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534) through [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) from its PCM-construction path, and adds card and DAI controls as [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) objects on [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), so the /dev/snd/pcmC%iD%i%c and controlC%d nodes a userspace client opens on an ASoC card come from exactly the registration paths shown here.
