# ALSA character devices

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every node ALSA presents under /dev/snd shares the single character-device major [`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26) (116), and the minor number alone selects which card and sub-device an `open()` lands on. The ALSA core owns one global table [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48), an array of [`SNDRV_OS_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L9) (256) [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) pointers indexed by minor, and a sub-object joins it by calling [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249), which allocates a free minor through [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201), stores the per-node [`file_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L219) and private pointer in the table slot, and adds a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) in the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) whose [`devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L642) is [`MKDEV(major, minor)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kdev_t.h#L12). One file-operations struct [`snd_fops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170) is registered for the whole major by [`register_chrdev()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2589), so its [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) handler [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) reads the minor, looks up [`snd_minors[minor]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48), swaps the file's `f_op` for the registered node's operations with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2352), and calls that node's own `open`. The PCM, control, raw MIDI, hwdep, timer, sequencer, and compress layers each register their nodes through this one function.

```
    one major 116, minor selects card and device
    ─────────────────────────────────────────────
    SNDRV_MINOR(card, dev) = (card << 5) | dev   (static minors)

    bit:  31           5 4         0
         ┌──────────────┬───────────┐
         │     card     │   dev     │   8-bit minor, 0..255
         └──────────────┴───────────┘
          card = minor >> 5          dev = minor & 0x1f
          (SNDRV_MINOR_CARD)         (SNDRV_MINOR_DEVICE)

    dev within a card (SNDRV_MINOR_DEVICES = 32 slots):
      0        control       (controlC<card>)
      1        sequencer*     2..3     compress
      4..7     hwdep          8..15    raw midi
      16..23   pcm playback   24..31   pcm capture
      33       timer*         (*seq and timer are card-less globals)
```

## SUMMARY

ALSA registers exactly one character-device major, [`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26) (116), copied at boot into the runtime [`major`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L21) variable and the exported [`snd_major`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L22). [`alsa_sound_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L389) calls [`register_chrdev(major, "alsa", &snd_fops)`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L393), binding every minor under the major to one [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170). The dispatch from a minor to a sub-device is a table lookup. [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48) is a 256-entry array of [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) pointers, each entry recording the device [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), the owning card and device numbers, the node's [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), and the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) pointer passed to that node's `open`.

A sub-object surfaces a node by calling [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) from inside its [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback. The function allocates one [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), asks [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201) for the minor that encodes the requested type, card, and device index, sets [`device->devt = MKDEV(major, minor)`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L277), runs [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572), and installs the record at [`snd_minors[minor]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48). On a userspace `open()`, [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) takes [`iminor(inode)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1178), reads [`snd_minors[minor]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48), pins the node's [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) with [`fops_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2336), installs them with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2352), and forwards to the node's own [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L165). [`snd_lookup_minor_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99) returns the same record's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) by minor and type so a node's `open` can recover its object. Without [`CONFIG_SND_DYNAMIC_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig), the minor is a fixed function of the card and device, [`SNDRV_MINOR(card, dev)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L14); with it set, [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L178) scans for the first empty slot instead. The node names ([`controlC%d`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2367), [`pcmC%iD%i%c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645), [`hwC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L395), [`midiC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1850), [`comprC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/compress_offload.c#L1540), [`timer`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/timer.c#L2474), [`seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/seq/seq_clientmgr.c#L2662)) are set with [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3487) on the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) before it reaches [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249), and udev turns each into a /dev/snd entry through the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) [`devnode`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L30) callback.

## SPECIFICATIONS

The /dev/snd node interface has no external hardware specification. The device-node ABI is defined by the kernel itself, the minor-number layout in [`include/sound/minors.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h) and the static major 116 in [`Documentation/admin-guide/devices.txt`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/devices.txt#L1920), with the node names ([`controlC0`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2367), [`pcmC0D0p`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645)) becoming filesystem paths under /dev/snd by way of udev and the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) `devnode` rule. The per-node read/write/ioctl ABIs (the PCM ioctl set, the control ioctl set) are defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) and documented by their own subsystems.

## LINUX KERNEL

### Major number and runtime state (sound.c)

- [`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26): the standard sound major, 116, set in [`include/sound/core.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26)
- [`'\<major\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L21): file-static, initialized to [`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26), overridable by the `major` module parameter
- [`'\<snd_major\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L22): exported copy of the active major for other ALSA modules
- [`'\<snd_minors\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48): the [`SNDRV_OS_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L9)-sized array of [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) pointers, indexed by minor
- [`'\<snd_fops\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170): the single [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170) bound to the whole major; its only real method is [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143)
- [`'\<alsa_sound_init\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L389): the [`subsys_initcall`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/init.h#L301) that calls [`register_chrdev()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2589)

### The per-node record (include/sound/core.h)

- [`'\<struct snd_minor\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215): one table entry, holding the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) and [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) numbers, the node [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), the [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) sysfs device, and the [`card_ptr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215)

### Minor-number encoding (include/sound/minors.h)

- [`SNDRV_OS_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L9): 256, the size of [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48)
- [`SNDRV_MINOR_DEVICES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L11): 32, the per-card device-slot count (the 5-bit field)
- [`SNDRV_MINOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L14): `((card) << 5) | (dev)`, the static encoding of a minor
- [`SNDRV_MINOR_CARD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L12) / [`SNDRV_MINOR_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L13): the inverse, `minor >> 5` and `minor & 0x1f`
- [`SNDRV_MINOR_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L17) (0), [`SNDRV_MINOR_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L18) (1): the per-card control slot and the card-less global slot
- [`SNDRV_MINOR_SEQUENCER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L19) (1), [`SNDRV_MINOR_TIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L20) (33): the two card-less global minors
- [`SNDRV_MINOR_COMPRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L23) (2..3), [`SNDRV_MINOR_HWDEP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L24) (4..7), [`SNDRV_MINOR_RAWMIDI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L25) (8..15), [`SNDRV_MINOR_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L26) (16..23), [`SNDRV_MINOR_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L27) (24..31): the per-card device-index bases (non-dynamic build)
- [`SNDRV_DEVICE_TYPE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30), [`SNDRV_DEVICE_TYPE_HWDEP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L31), [`SNDRV_DEVICE_TYPE_RAWMIDI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L32), [`SNDRV_DEVICE_TYPE_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L33), [`SNDRV_DEVICE_TYPE_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L34), [`SNDRV_DEVICE_TYPE_SEQUENCER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L35), [`SNDRV_DEVICE_TYPE_TIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L36), [`SNDRV_DEVICE_TYPE_COMPRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L37): the device-type tags [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) receives; in the non-dynamic build each equals the matching device-index base

### Registration and dispatch (sound.c)

- [`'\<snd_register_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249): allocate a [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), pick a minor, set [`devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L642), [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572), install the record
- [`'\<snd_unregister_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L299): find the table slot whose [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) matches, clear it, [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3833)
- [`'\<snd_find_free_minor\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201): compute the minor from type/card/dev (non-dynamic) or scan for the first free slot (dynamic, [`'\<snd_find_free_minor\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L178))
- [`'\<snd_open\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143): the chrdev `open` that looks up the minor and swaps in the node's [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215)
- [`'\<snd_lookup_minor_data\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99): return the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) of the record at a minor when its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) matches, taking a card reference
- [`'\<autoload_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L119): on a miss, request the card or seq/timer module so the node can appear

### sound_class and the node device

- [`'\<sound_class\>':'sound/sound_core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37): the `"sound"` [`struct class`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/class.h#L50) every node device joins; its [`devnode`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L30) callback prefixes the name with `snd/`
- [`'\<sound_devnode\>':'sound/sound_core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L30): returns `snd/<dev_name>` for ALSA-major nodes, the udev path under /dev/snd
- [`'\<snd_device_alloc\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L127): allocate the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) in [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) that a node later hands to [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249)

### Per-subsystem registration callbacks

- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291): registers [`SNDRV_DEVICE_TYPE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) with [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266); name set [`controlC%d`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2367)
- [`'\<snd_pcm_dev_register\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044): registers one or both of [`SNDRV_DEVICE_TYPE_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L33)/[`SNDRV_DEVICE_TYPE_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L34) with [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206); name set [`pcmC%iD%i%c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645)
- [`'\<snd_hwdep_dev_register\>':'sound/core/hwdep.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L418): registers [`SNDRV_DEVICE_TYPE_HWDEP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L31) with [`snd_hwdep_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L326); name set [`hwC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L395)
- [`'\<snd_rawmidi_dev_register\>':'sound/core/rawmidi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1957): registers [`SNDRV_DEVICE_TYPE_RAWMIDI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L32) with [`snd_rawmidi_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1786); name set [`midiC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1850) (or [`umpC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1848))
- [`'\<snd_compress_dev_register\>':'sound/core/compress_offload.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/compress_offload.c#L1399): registers [`SNDRV_DEVICE_TYPE_COMPRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L37); name set [`comprC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/compress_offload.c#L1540)
- [`'\<alsa_timer_init\>':'sound/core/timer.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/timer.c#L2467): registers the one global [`SNDRV_DEVICE_TYPE_TIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L36) node named [`timer`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/timer.c#L2474)
- [`'\<snd_sequencer_device_init\>':'sound/core/seq/seq_clientmgr.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/seq/seq_clientmgr.c#L2655): registers the one global [`SNDRV_DEVICE_TYPE_SEQUENCER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L35) node named [`seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/seq/seq_clientmgr.c#L2662)

### /proc reporting (sound.c)

- [`'\<snd_minor_info_read\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L348): the `/proc/asound/devices` handler that walks [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48) and prints each minor with its card, device, and type name
- [`'\<snd_device_type_name\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L324): maps a [`SNDRV_DEVICE_TYPE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) value to a printable name for the proc dump

## KERNEL DOCUMENTATION

- [`Documentation/admin-guide/devices.txt`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/devices.txt#L1920): the static device-number registry, where line 1920 records `116 char Advanced Linux Sound Driver (ALSA)`
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the `/proc/asound/` tree, including the `devices` file that lists the native minor mappings
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the device-management chapters covering how a PCM, control, or hwdep object reaches [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249)
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated reference for the ALSA core, including the registration functions

## OTHER SOURCES

- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/), where alsa-lib maps logical names such as `hw:0,0` and `default` onto the /dev/snd nodes through its configuration files
- [systemd / udev sound device naming rules](https://github.com/systemd/systemd/blob/main/rules.d/78-sound-card.rules), the udev rules that act on the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) uevents and create the symlinks under /dev/snd/by-path
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

### The minor-number encoding (non-dynamic build)

The minor is an 8-bit number, and without [`CONFIG_SND_DYNAMIC_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig) it splits into a card number in the high bits and a device index within that card in the low 5 bits, computed by [`SNDRV_MINOR(card, dev)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L14). [`SNDRV_MINOR_DEVICES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L11) is 32, so each card owns one block of 32 consecutive minors and a minor decodes back with [`SNDRV_MINOR_CARD()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L12) and [`SNDRV_MINOR_DEVICE()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L13).

```
    minor = SNDRV_MINOR(card, dev) = (card << 5) | dev
    ──────────────────────────────────────────────────

    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
          │ card  │  dev    │   one byte, 0..255
          └─┴─┴─┴─┴─┴─┴─┴─┘
           │     │ │       │
           │     │ └───────┴── dev   = minor & 0x1f  (SNDRV_MINOR_DEVICE)
           └─────┴──────────── card  = minor >> 5    (SNDRV_MINOR_CARD)

    SNDRV_MINOR_DEVICES = 32   (one 32-minor block per card)
    SNDRV_OS_MINORS     = 256  (size of snd_minors[], 8 cards * 32)
```

The low 5-bit device index is partitioned by device type. The bases in [`include/sound/minors.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L17) reserve a fixed range to each subsystem, so within one card the control node is always at offset 0 and a PCM playback substream `dev` lands at offset `16 + dev`. The two card-less devices, the sequencer and the global timer, occupy [`SNDRV_MINOR_SEQUENCER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L19) (1) and [`SNDRV_MINOR_TIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L20) (33), where 33 is [`SNDRV_MINOR_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L18) plus one 32-minor block.

| Offset within card (dev) | Device type | Base macro |
|--------------------------|-------------|------------|
| 0 | control | [`SNDRV_MINOR_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L17) (0) |
| 2..3 | compress | [`SNDRV_MINOR_COMPRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L23) (2) |
| 4..7 | hwdep | [`SNDRV_MINOR_HWDEP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L24) (4) |
| 8..15 | raw midi | [`SNDRV_MINOR_RAWMIDI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L25) (8) |
| 16..23 | pcm playback | [`SNDRV_MINOR_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L26) (16) |
| 24..31 | pcm capture | [`SNDRV_MINOR_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L27) (24) |

The matching [`SNDRV_DEVICE_TYPE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) tags callers pass to [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) are, in this build, defined equal to those bases. According to the comment on the type block, the values are "same as first respective minor number to make minor allocation easier", which lets [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201) build the minor as `type + dev` for the multi-instance types.

### The device-type tags

The tag passed to [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) selects both the minor block and, in [`snd_minor_info_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L348), the printed name. Under [`CONFIG_SND_DYNAMIC_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig) the same names become a plain [`enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L41) (0..7) used only as a selector, since the minor is then the first free slot rather than a function of the type.

| Type tag | Static value (non-dynamic) | proc name |
|----------|----------------------------|-----------|
| [`SNDRV_DEVICE_TYPE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) | 0 | control |
| [`SNDRV_DEVICE_TYPE_SEQUENCER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L35) | 1 | sequencer |
| [`SNDRV_DEVICE_TYPE_COMPRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L37) | 2 | compress |
| [`SNDRV_DEVICE_TYPE_HWDEP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L31) | 4 | hardware dependent |
| [`SNDRV_DEVICE_TYPE_RAWMIDI`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L32) | 8 | raw midi |
| [`SNDRV_DEVICE_TYPE_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L33) | 16 | digital audio playback |
| [`SNDRV_DEVICE_TYPE_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L34) | 24 | digital audio capture |
| [`SNDRV_DEVICE_TYPE_TIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L36) | 33 | timer |

## DETAILS

### One major, a 256-entry minor table

The whole of ALSA's character-device space sits behind one major. [`major`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L21) starts as [`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26) and a module parameter may override it, and [`snd_major`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L22) exports the active value to other ALSA code:

```c
/* sound/core/sound.c:21 */
static int major = CONFIG_SND_MAJOR;
int snd_major;
EXPORT_SYMBOL(snd_major);
```

[`CONFIG_SND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L26) is the fixed standard major:

```c
/* include/sound/core.h:26 */
#define CONFIG_SND_MAJOR	116	/* standard configuration */
```

The routing table is a flat array indexed by minor. [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48) has [`SNDRV_OS_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L9) entries, and a NULL slot means no node is registered at that minor:

```c
/* sound/core/sound.c:48 */
static struct snd_minor *snd_minors[SNDRV_OS_MINORS];
static DEFINE_MUTEX(sound_mutex);
```

Each populated slot points at one [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215). The record carries the device type, the owning card and device numbers, the per-node [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) the node's `open` receives, the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) for sysfs, and a back pointer to the card:

```c
/* include/sound/core.h:215 */
struct snd_minor {
	int type;			/* SNDRV_DEVICE_TYPE_XXX */
	int card;			/* card number */
	int device;			/* device number */
	const struct file_operations *f_ops;	/* file operations */
	void *private_data;		/* private data for f_ops->open */
	struct device *dev;		/* device for sysfs */
	struct snd_card *card_ptr;	/* assigned card instance */
};
```

[`alsa_sound_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L389) binds the major to one [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170) at boot. [`register_chrdev(major, "alsa", &snd_fops)`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L393) claims all 256 minors of the major and routes every one to [`snd_fops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170):

```c
/* sound/core/sound.c:389 */
static int __init alsa_sound_init(void)
{
	snd_major = major;
	snd_ecards_limit = cards_limit;
	if (register_chrdev(major, "alsa", &snd_fops)) {
		pr_err("ALSA core: unable to register native major device number %d\n", major);
		return -EIO;
	}
	...
}
```

[`snd_fops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170) is deliberately thin. Its only substantive method is [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143), since the read, write, ioctl, and mmap methods belong to the per-node operations [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) installs once it knows the minor:

```c
/* sound/core/sound.c:170 */
static const struct file_operations snd_fops =
{
	.owner =	THIS_MODULE,
	.open =		snd_open,
	.llseek =	noop_llseek,
};
```

The open handler resolves the minor against that table, 256 slots split into a 32-minor block per card, each populated slot a record holding the node f_ops:

```
    snd_minors[]: one global 256-slot table, 32 slots per card
    ──────────────────────────────────────────────────────────

      minor:   0      32     64               224     255
             ┌──────┬──────┬──────┬─  ─  ─┬──────┐
             │card 0│card 1│card 2│  ...  │card 7│   SNDRV_OS_MINORS
             └──────┴──────┴──────┴─  ─  ─┴──────┘   = 256 (8 * 32)
              32 slots each  (SNDRV_MINOR_DEVICES = 32)

      one slot snd_minors[minor]:  NULL  = no node registered
                                   else ─▶ struct snd_minor
             ┌──────────────────────────────┐
             │ type   (SNDRV_DEVICE_TYPE_*) │
             │ card    device               │
             │ f_ops ─▶ node file_operations│
             │ private_data   card_ptr  dev │
             └──────────────────────────────┘
```

### snd_register_device installs the record

A sub-object surfaces its node by calling [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249), passing the device type, the card, the device index, the node's [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) for that node's `open`, and the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) whose name is already set. The function fills a fresh [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), asks [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201) for the minor, writes [`MKDEV(major, minor)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kdev_t.h#L12) into [`device->devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), adds the device to the driver model, and installs the record at [`snd_minors[minor]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48):

```c
/* sound/core/sound.c:249 */
int snd_register_device(int type, struct snd_card *card, int dev,
			const struct file_operations *f_ops,
			void *private_data, struct device *device)
{
	int minor;
	int err = 0;
	struct snd_minor *preg;

	if (snd_BUG_ON(!device))
		return -EINVAL;

	preg = kmalloc_obj(*preg);
	if (preg == NULL)
		return -ENOMEM;
	preg->type = type;
	preg->card = card ? card->number : -1;
	preg->device = dev;
	preg->f_ops = f_ops;
	preg->private_data = private_data;
	preg->card_ptr = card;
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

The card-less devices pass a NULL `card`, so [`preg->card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) becomes `-1`; the timer and sequencer take this path. [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) makes the node visible, because once the device with a [`devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L642) in the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) is added, the driver core emits a uevent and udev creates the matching /dev/snd node. [`snd_unregister_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L299) reverses it, scanning the table for the slot whose [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) matches, clearing it, and calling [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3833):

```c
/* sound/core/sound.c:299 */
int snd_unregister_device(struct device *dev)
{
	int minor;
	struct snd_minor *preg;

	guard(mutex)(&sound_mutex);
	for (minor = 0; minor < ARRAY_SIZE(snd_minors); ++minor) {
		preg = snd_minors[minor];
		if (preg && preg->dev == dev) {
			snd_minors[minor] = NULL;
			device_del(dev);
			kfree(preg);
			break;
		}
	}
	if (minor >= ARRAY_SIZE(snd_minors))
		return -ENOENT;
	return 0;
}
```

### snd_open dispatches through the minor table

A userspace `open("/dev/snd/pcmC0D0p")` reaches [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) because that node's major is 116 and [`snd_fops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L170) is the only handler the major has. [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) reads the minor with [`iminor()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1178), looks the record up, pins its [`f_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) with [`fops_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2336), installs them onto the open file with [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2352), and calls the node's own `open`:

```c
/* sound/core/sound.c:143 */
static int snd_open(struct inode *inode, struct file *file)
{
	unsigned int minor = iminor(inode);
	struct snd_minor *mptr = NULL;
	const struct file_operations *new_fops;
	int err = 0;

	if (minor >= ARRAY_SIZE(snd_minors))
		return -ENODEV;
	scoped_guard(mutex, &sound_mutex) {
		mptr = snd_minors[minor];
		if (mptr == NULL) {
			mptr = autoload_device(minor);
			if (!mptr)
				return -ENODEV;
		}
		new_fops = fops_get(mptr->f_ops);
	}
	if (!new_fops)
		return -ENODEV;
	replace_fops(file, new_fops);

	if (file->f_op->open)
		err = file->f_op->open(inode, file);
	return err;
}
```

After [`replace_fops()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2352) runs, `file->f_op` is the node's own [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1926), so the closing `file->f_op->open(inode, file)` enters, for a PCM playback node, the open routine in [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206), and every later `read`, `write`, or `ioctl` on the descriptor goes straight to the PCM methods without passing through [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) again. When the table slot is empty, [`autoload_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L119) decodes the minor with [`SNDRV_MINOR_DEVICE()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L13) and requests the card or seq/timer module, then re-reads the slot, so opening an `/dev/aloadC0` style node can trigger a module load.

A node's own `open` recovers its object from the same table through [`snd_lookup_minor_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99), which returns the record's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) only when the stored [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) matches, taking a reference on the card so the object stays put for the duration of the open:

```c
/* sound/core/sound.c:99 */
void *snd_lookup_minor_data(unsigned int minor, int type)
{
	struct snd_minor *mreg;
	void *private_data;

	if (minor >= ARRAY_SIZE(snd_minors))
		return NULL;
	guard(mutex)(&sound_mutex);
	mreg = snd_minors[minor];
	if (mreg && mreg->type == type) {
		private_data = mreg->private_data;
		if (private_data && mreg->card_ptr)
			get_device(&mreg->card_ptr->card_dev);
	} else
		private_data = NULL;
	return private_data;
}
```

That lookup runs inside the node open the core reaches by reading the minor, pulling the record, and installing its f_ops before calling through:

```
    snd_open(): minor → snd_minors[] record → node f_ops
    ─────────────────────────────────────────────────────

    ┌──────────────┐      ┌────────────────────┐
    │ inode        │      │ snd_minors[minor]  │
    │  iminor() ───┼──▶   │  struct snd_minor  │
    │  = minor     │      │   .f_ops ──────────┼───┐
    └──────────────┘      └────────────────────┘   │
                          (NULL slot ─▶              │
                           autoload_device)          ▼
                                              ┌────────────────┐
      file->f_op->open(inode, file)   ◀────── │ replace_fops:  │
      enters the node's own open      install │ file->f_op =   │
                                              │  node f_ops    │
                                              └────────────────┘
```

### Minor allocation encodes type, card, and device

[`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L201) turns the type, card, and device index into a minor. In the non-dynamic build the minor is a pure function of those three. The sequencer and timer take their fixed global minors, the control node takes [`SNDRV_MINOR(card->number, type)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L14) (offset 0 within the card), and every multi-instance type takes `SNDRV_MINOR(card->number, type + dev)`, where adding the device index to the type base walks across that subsystem's reserved sub-range:

```c
/* sound/core/sound.c:201 */
static int snd_find_free_minor(int type, struct snd_card *card, int dev)
{
	int minor;

	switch (type) {
	case SNDRV_DEVICE_TYPE_SEQUENCER:
	case SNDRV_DEVICE_TYPE_TIMER:
		minor = type;
		break;
	case SNDRV_DEVICE_TYPE_CONTROL:
		if (snd_BUG_ON(!card))
			return -EINVAL;
		minor = SNDRV_MINOR(card->number, type);
		break;
	case SNDRV_DEVICE_TYPE_HWDEP:
	case SNDRV_DEVICE_TYPE_RAWMIDI:
	case SNDRV_DEVICE_TYPE_PCM_PLAYBACK:
	case SNDRV_DEVICE_TYPE_PCM_CAPTURE:
	case SNDRV_DEVICE_TYPE_COMPRESS:
		if (snd_BUG_ON(!card))
			return -EINVAL;
		minor = SNDRV_MINOR(card->number, type + dev);
		break;
	default:
		return -EINVAL;
	}
	if (snd_BUG_ON(minor < 0 || minor >= SNDRV_OS_MINORS))
		return -EINVAL;
	if (snd_minors[minor])
		return -EBUSY;
	return minor;
}
```

The `type + dev` arithmetic works because the type tags equal the minor bases. The macros that define both halves follow; [`SNDRV_MINOR()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L14) shifts the card up by five bits and ORs in the device index, and the device-index bases carve the 32-slot block into per-subsystem ranges:

```c
/* include/sound/minors.h:9 */
#define SNDRV_OS_MINORS			256

#define SNDRV_MINOR_DEVICES		32
#define SNDRV_MINOR_CARD(minor)		((minor) >> 5)
#define SNDRV_MINOR_DEVICE(minor)	((minor) & 0x001f)
#define SNDRV_MINOR(card, dev)		(((card) << 5) | (dev))

/* these minors can still be used for autoloading devices (/dev/aload*) */
#define SNDRV_MINOR_CONTROL		0	/* 0 */
#define SNDRV_MINOR_GLOBAL		1	/* 1 */
#define SNDRV_MINOR_SEQUENCER		1	/* SNDRV_MINOR_GLOBAL + 0 * 32 */
#define SNDRV_MINOR_TIMER		33	/* SNDRV_MINOR_GLOBAL + 1 * 32 */
```

```c
/* include/sound/minors.h:23 */
#define SNDRV_MINOR_COMPRESS		2	/* 2 - 3 */
#define SNDRV_MINOR_HWDEP		4	/* 4 - 7 */
#define SNDRV_MINOR_RAWMIDI		8	/* 8 - 15 */
#define SNDRV_MINOR_PCM_PLAYBACK	16	/* 16 - 23 */
#define SNDRV_MINOR_PCM_CAPTURE		24	/* 24 - 31 */

/* same as first respective minor number to make minor allocation easier */
#define SNDRV_DEVICE_TYPE_CONTROL	SNDRV_MINOR_CONTROL
#define SNDRV_DEVICE_TYPE_HWDEP		SNDRV_MINOR_HWDEP
#define SNDRV_DEVICE_TYPE_RAWMIDI	SNDRV_MINOR_RAWMIDI
#define SNDRV_DEVICE_TYPE_PCM_PLAYBACK	SNDRV_MINOR_PCM_PLAYBACK
#define SNDRV_DEVICE_TYPE_PCM_CAPTURE	SNDRV_MINOR_PCM_CAPTURE
#define SNDRV_DEVICE_TYPE_SEQUENCER	SNDRV_MINOR_SEQUENCER
#define SNDRV_DEVICE_TYPE_TIMER		SNDRV_MINOR_TIMER
#define SNDRV_DEVICE_TYPE_COMPRESS	SNDRV_MINOR_COMPRESS
```

A card-0 PCM playback substream 0 therefore registers at minor `SNDRV_MINOR(0, 16 + 0)` = 16, a card-0 control at minor `SNDRV_MINOR(0, 0)` = 0, and a card-1 control at `SNDRV_MINOR(1, 0)` = 32. With [`CONFIG_SND_DYNAMIC_MINORS`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig) set, the [`SNDRV_DEVICE_TYPE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L41) names are instead a plain enum and the [`snd_find_free_minor()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L178) variant scans the table for the first empty slot (keeping only the sequencer and timer at their fixed minors), so the card-to-minor relationship is no longer fixed and only the type-to-name mapping survives.

### Each subsystem names its device and registers through snd_register_device

The node name is set on the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) with [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3487) before [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) is called, and that name, prefixed with `snd/` by the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37) [`devnode`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L30) callback, becomes the /dev/snd path. Each subsystem reaches [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) from inside the [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback the card's [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) layer runs during card registration.

The control object names its device [`controlC%d`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2367) in [`snd_ctl_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2350) and registers it from [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291):

```c
/* sound/core/control.c:2291 */
static int snd_ctl_dev_register(struct snd_device *device)
{
	struct snd_card *card = device->device_data;
	int err;

	err = snd_register_device(SNDRV_DEVICE_TYPE_CONTROL, card, -1,
				  &snd_ctl_f_ops, card, card->ctl_dev);
	if (err < 0)
		return err;
	call_snd_ctl_lops(card, lregister);
	return 0;
}
```

The PCM layer names each stream's device [`pcmC%iD%i%c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645) (the `%c` is `p` for playback or `c` for capture) when the stream is built, then [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044) registers one node per active direction, choosing [`SNDRV_DEVICE_TYPE_PCM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L33) or [`SNDRV_DEVICE_TYPE_PCM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L34) and passing the matching entry of [`snd_pcm_f_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L4206):

```c
/* sound/core/pcm.c:1044 */
static int snd_pcm_dev_register(struct snd_device *device)
{
	int cidx, err;
	struct snd_pcm_substream *substream;
	struct snd_pcm *pcm;
	...
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

The hwdep, raw MIDI, and compress objects follow the same shape from [`snd_hwdep_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L418), [`snd_rawmidi_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1957), and [`snd_compress_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/compress_offload.c#L1399), each naming its device [`hwC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/hwdep.c#L395), [`midiC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1850) (or [`umpC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/rawmidi.c#L1848) for a MIDI 2.0 UMP endpoint), and [`comprC%iD%i`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/compress_offload.c#L1540) before registering its type. The timer and sequencer are the two card-less nodes. Each is created once at module init rather than per card, so its device is a single file-static [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) named [`timer`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/timer.c#L2474) or [`seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/seq/seq_clientmgr.c#L2662) and registered with a NULL card:

```c
/* sound/core/timer.c:2467 */
static int __init alsa_timer_init(void)
{
	int err;

	err = snd_device_alloc(&timer_dev, NULL);
	if (err < 0)
		return err;
	dev_set_name(timer_dev, "timer");
	...
	err = snd_register_device(SNDRV_DEVICE_TYPE_TIMER, NULL, 0,
				  &snd_timer_f_ops, NULL, timer_dev);
	...
}
```

Every one of these devices was allocated by [`snd_device_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L127), which sets [`dev->class = &sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L138), so when [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) sets the [`devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L642) and runs [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572), the node lands in the `"sound"` class. [`sound_devnode()`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L30) is what places it under /dev/snd:

```c
/* sound/sound_core.c:30 */
static char *sound_devnode(const struct device *dev, umode_t *mode)
{
	if (MAJOR(dev->devt) == SOUND_MAJOR)
		return NULL;
	return kasprintf(GFP_KERNEL, "snd/%s", dev_name(dev));
}

const struct class sound_class = {
	.name = "sound",
	.devnode = sound_devnode,
};
EXPORT_SYMBOL(sound_class);
```

For an ALSA-major (116) device the [`MAJOR(dev->devt) == SOUND_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L32) test is false (SOUND_MAJOR 14 is the legacy OSS major), so the function returns `snd/<dev_name>`, and udev creates `/dev/snd/pcmC0D0p` from a device named [`pcmC0D0p`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L645).

```
    each subsystem's dev_register names a node and registers its type
    ────────────────────────────────────────────────────────────────

    dev_register callback        /dev/snd name   SNDRV_DEVICE_TYPE_*
    ──────────────────────────   ─────────────   ───────────────────
    snd_ctl_dev_register         controlC%d      CONTROL
    snd_pcm_dev_register         pcmC%iD%i p     PCM_PLAYBACK
    snd_pcm_dev_register         pcmC%iD%i c     PCM_CAPTURE
    snd_hwdep_dev_register       hwC%iD%i        HWDEP
    snd_rawmidi_dev_register     midiC%iD%i      RAWMIDI
    snd_compress_dev_register    comprC%iD%i     COMPRESS
    alsa_timer_init              timer           TIMER  (card-less)
    snd_sequencer_device_init    seq             SEQUENCER (card-less)
                  │
                  ▼  all call
       ┌─────────────────────────────────────────────┐
       │ snd_register_device(type, card, dev, f_ops, │
       │   private_data, device)                     │
       │   → snd_find_free_minor → snd_minors[minor] │
       └─────────────────────────────────────────────┘
```

### Userspace interaction

A directory listing of /dev/snd shows one entry per registered minor, all major 116, with the device type encoded in the node name. The control node `controlC0` is the entry a client opens first to enumerate a card, the PCM nodes `pcmC0D0p` and `pcmC0D0c` carry playback and capture streams, `hwC0D0` is the hardware-dependent node, `midiC0D0` carries raw MIDI, `comprC0D0` carries a compressed-audio stream, and the two card-less nodes `timer` and `seq` serve the whole system:

```
    $ ls -l /dev/snd
    crw-rw----  116, 16  pcmC0D0p     <- SNDRV_MINOR(0, 16)
    crw-rw----  116, 24  pcmC0D0c     <- SNDRV_MINOR(0, 24)
    crw-rw----  116,  4  hwC0D0       <- SNDRV_MINOR(0, 4)
    crw-rw----  116,  0  controlC0    <- SNDRV_MINOR(0, 0)
    crw-rw----  116, 33  timer        <- SNDRV_MINOR_TIMER
    crw-rw----  116,  1  seq          <- SNDRV_MINOR_SEQUENCER
```

An `open()` on any of these enters [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143), which reads the minor, finds the [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215) at [`snd_minors[minor]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48), and replaces the file's operations with that node's, so the subsequent ioctls a client issues on a PCM descriptor reach the PCM core. The PCM ioctl flow and the control ioctl flow each begin at the `open` that [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) dispatched.

The same table backs `/proc/asound/devices`. [`snd_minor_info_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L348) walks [`snd_minors[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L48) and, for each populated slot, prints the minor, the card and device numbers, and the type name from [`snd_device_type_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L324):

```c
/* sound/core/sound.c:348 */
static void snd_minor_info_read(struct snd_info_entry *entry, struct snd_info_buffer *buffer)
{
	int minor;
	struct snd_minor *mptr;

	guard(mutex)(&sound_mutex);
	for (minor = 0; minor < SNDRV_OS_MINORS; ++minor) {
		mptr = snd_minors[minor];
		if (!mptr)
			continue;
		if (mptr->card >= 0) {
			if (mptr->device >= 0)
				snd_iprintf(buffer, "%3i: [%2i-%2i]: %s\n",
					    minor, mptr->card, mptr->device,
					    snd_device_type_name(mptr->type));
			else
				snd_iprintf(buffer, "%3i: [%2i]   : %s\n",
					    minor, mptr->card,
					    snd_device_type_name(mptr->type));
		} else
			snd_iprintf(buffer, "%3i:        : %s\n", minor,
				    snd_device_type_name(mptr->type));
	}
}
```

A control node prints with `device` as `-1` (it registered with `dev` = `-1`), so it takes the `[%2i]` form rather than `[%2i-%2i]`, and the card-less timer and sequencer take the bare `%3i:        :` form. The result is the human-readable map of minor to device that `cat /proc/asound/devices` shows:

```
      0: [ 0]   : control
     16: [ 0- 0]: digital audio playback
     24: [ 0- 0]: digital audio capture
      4: [ 0- 0]: hardware dependent
     33:        : timer
      1:        : sequencer
```

The same node devices appear under /sys/class/sound/ because they joined the [`sound_class`](https://elixir.bootlin.com/linux/v7.0/source/sound/sound_core.c#L37), so `/sys/class/sound/pcmC0D0p/dev` reads `116:16`, the major and minor [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) wrote into [`devt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L642). alsa-lib reads neither the table nor /proc directly; it maps logical names such as `hw:0,0` and `default` onto these /dev/snd nodes through its configuration, and the `open()` it performs lands in [`snd_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L143) exactly as a raw `open()` would.
