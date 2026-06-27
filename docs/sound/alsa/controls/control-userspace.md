# Control userspace interface and ioctl dispatch

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The /dev/snd/controlC%d node is the single character device through which a userspace client enumerates and operates every control element on a card. An open of the node produces a per-open [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) that carries the card back pointer, the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag, a per-file [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue, and a [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue, and the file is linked onto [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106). Every request travels through [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899), a switch over the `SNDRV_CTL_IOCTL_*` numbers in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) that resolves the addressed [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and runs its [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback.

```
    controlC%d fd (one struct snd_ctl_file per open)
    ┌──────────────────────────────────────────────────────┐
    │ ioctl(fd, SNDRV_CTL_IOCTL_*, arg)                    │
    │        │                                             │
    │        ▼  snd_ctl_ioctl()                            │
    │   ┌─────────────────────────────────────────────┐    │
    │   │ PVERSION / CARD_INFO                        │    │
    │   │ ELEM_LIST / INFO / READ / WRITE             │    │
    │   │ ELEM_LOCK / UNLOCK                          │    │
    │   │ ELEM_ADD / REPLACE / REMOVE / TLV_* / SUBSCR│    │
    │   └───────┬─────────────────────────────────────┘    │
    │           │ resolve id (numid or tuple)              │
    │           ▼                                          │
    │   snd_ctl_find_id / snd_ctl_find_numid               │
    │           │                                          │
    │           ▼  run info / get / put under controls_rwsem│
    │       struct snd_kcontrol on card->controls          │
    └──────────────────────────────────────────────────────┘
       open  → snd_ctl_open  : alloc snd_ctl_file, link on ctl_files
       close → snd_ctl_release: unlink, drop owned locks, drain events
```

## SUMMARY

A client opens /dev/snd/controlC%d, and the sound core swaps the control [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266) into the file. [`snd_ctl_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45) allocates a [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105), initializes its [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) list, [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue, and [`read_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L110), stores it in [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), and links it onto [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102). [`snd_ctl_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109) unlinks it, clears any [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) write locks the file still holds, and drains its event queue.

The dispatcher [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) is a switch over the request number. [`SNDRV_CTL_IOCTL_PVERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1199) returns the protocol version, [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) returns card identity through [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867), [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201) enumerates ids through [`snd_ctl_elem_list_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922), [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) queries one element through [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172), and [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203) and [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) move values through [`snd_ctl_elem_read_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244) and [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320). [`SNDRV_CTL_IOCTL_ELEM_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1205) and [`SNDRV_CTL_IOCTL_ELEM_UNLOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1206) claim and release a per-element write lock. A request that matches no case falls through to a registered extra-ioctl list, [`snd_control_ioctls`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L36), that PCM and other managers extend. The user-defined element commands ([`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208) and its siblings), the TLV channel, and the event-delivery path (read, poll, subscribe) take the same dispatcher but are detailed with the user-defined element and event-delivery material.

## SPECIFICATIONS

The control element protocol exposed over /dev/snd/controlC%d is a Linux kernel software ABI with no standalone hardware specification. It is defined normatively by the uapi structures and ioctl numbers in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The version is [`SNDRV_CTL_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1061), which a client reads with [`SNDRV_CTL_IOCTL_PVERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1199). The element identity is a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), enumeration travels in [`struct snd_ctl_elem_list`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1130), and info and values in [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) and [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168). The `SNDRV_CTL_ELEM_ACCESS_*` bits encode access rights.

## LINUX KERNEL

### Per-open state and file operations (control.c, control.h)

- [`'\<struct snd_ctl_file\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105): one open controlC%d handle; holds the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L107) back pointer, the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag, the [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue, the [`read_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L110) spinlock, the [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue, and the [`fasync`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L112) handle
- [`'\<snd_ctl_f_ops\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266): the file operation struct wiring [`read`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2269), [`open`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2270), [`release`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2271), [`poll`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2272), [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273), and [`fasync`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2275)
- [`'\<snd_ctl_open\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45): allocate the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105), initialize its queues, and link it onto [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106)
- [`'\<snd_ctl_release\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109): unlink the file, release any [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) locks it held, and drain its events
- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291): the [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) register op publishing the controlC%d node

### The ioctl dispatcher (control.c)

- [`'\<snd_ctl_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899): the switch over `SNDRV_CTL_IOCTL_*` routing each request to its handler, then the [`snd_control_ioctls`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L36) extra list
- [`'\<snd_control_ioctls\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L36): the list of device-specific ioctl callbacks, extended by [`snd_ctl_register_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2077)
- [`'\<snd_ctl_register_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2077): add a [`snd_kctl_ioctl_func_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L127) to the extra-ioctl list

### Per-command handlers (control.c)

- [`'\<snd_ctl_card_info\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867): copy card identity into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063)
- [`'\<snd_ctl_elem_list\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L889) / [`'\<snd_ctl_elem_list_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922): walk [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) and copy a window of [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) entries out
- [`'\<snd_ctl_elem_info\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1159) / [`'\<snd_ctl_elem_info_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172): resolve the element and run its [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) callback, dropping kernel-only access bits before return
- [`'\<snd_ctl_elem_read\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) / [`'\<snd_ctl_elem_read_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244): check the [`READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) bit, run [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) under [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101)
- [`'\<snd_ctl_elem_write\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) / [`'\<snd_ctl_elem_write_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320): check the [`WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) bit and the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66), run [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), and notify on a changed value
- [`'\<snd_ctl_elem_lock\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1345) / [`'\<snd_ctl_elem_unlock\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1366): set and clear [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) for one element

### The uapi structures and constants (asound.h)

- [`'\<struct snd_ctl_elem_id\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121): the element address; the [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) plus the ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple
- [`'\<struct snd_ctl_elem_list\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1130): the enumeration window; [`offset`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1131), [`space`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1132), [`used`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1133), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1134), and the user [`pids`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1135) buffer
- [`'\<struct snd_ctl_elem_info\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139): the element description; [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1141), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1142), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1143), and the per-type [`value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1145) range
- [`'\<struct snd_ctl_elem_value\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168): the value carrier for read and write
- [`SNDRV_CTL_ELEM_ACCESS_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1105) / [`SNDRV_CTL_ELEM_ACCESS_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1106): the write-lock and lock-owner bits ELEM_LOCK reports

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter, covering the element id ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) and the info/get/put callbacks the ioctl path drives
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the source, direction, and function naming convention the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) field of the id tuple follows
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated API reference pulling kernel-doc from [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c)

## OTHER SOURCES

- [ALSA project library documentation, Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [ALSA project library documentation, High Level Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__HControl.html)
- [alsa-utils (amixer, alsactl)](https://github.com/alsa-project/alsa-utils)
- [ALSA project wiki, Listing and Setting Controls](https://www.alsa-project.org/wiki/AsListing_and_Setting_Controls)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A client drives the card by opening /dev/snd/controlC%d and issuing ioctls against the per-open [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105). Every request enters [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899), which resolves the addressed element by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or id and runs the matching handler.

| ioctl | handler | effect |
|-------|---------|--------|
| [`SNDRV_CTL_IOCTL_PVERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1199) | inline | return [`SNDRV_CTL_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1061) |
| [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) | [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) | fill [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063) |
| [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201) | [`snd_ctl_elem_list_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922) | copy a window of element ids |
| [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) | [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172) | run [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74), return type/range |
| [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203) | [`snd_ctl_elem_read_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244) | run [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75), return the value |
| [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) | [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320) | run [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), notify on change |
| [`SNDRV_CTL_IOCTL_ELEM_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1205) | [`snd_ctl_elem_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1345) | claim a per-element write lock |
| [`SNDRV_CTL_IOCTL_ELEM_UNLOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1206) | [`snd_ctl_elem_unlock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1366) | release a held write lock |
| [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208) | [`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) | create a user-defined control |
| [`SNDRV_CTL_IOCTL_ELEM_REPLACE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1209) | [`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) | replace a user-defined control |
| [`SNDRV_CTL_IOCTL_ELEM_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1210) | [`snd_ctl_elem_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1762) | drop a user-defined control |
| [`SNDRV_CTL_IOCTL_SUBSCRIBE_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1207) | [`snd_ctl_subscribe_events()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772) | arm or disarm change notification |
| [`SNDRV_CTL_IOCTL_TLV_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1211) | [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) | read TLV metadata under the rwsem |
| [`SNDRV_CTL_IOCTL_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1225) | inline | return `-ENOPROTOOPT` |
| [`SNDRV_CTL_IOCTL_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1226) | inline | return [`SNDRV_CTL_POWER_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1112) |

## DETAILS

### The controlC%d node and the per-open snd_ctl_file

Every card publishes one control node, /dev/snd/controlC%d, when [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) registers the [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) component with [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266). A client open of the node reaches [`snd_ctl_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45), which allocates one [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) per descriptor, initializes its [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) list, [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue, and [`read_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L110) spinlock, stores it in [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h), and links it onto [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102):

```c
/* sound/core/control.c:45 */
static int snd_ctl_open(struct inode *inode, struct file *file)
{
	struct snd_card *card;
	struct snd_ctl_file *ctl;
	int i, err;

	err = stream_open(inode, file);
	if (err < 0)
		return err;

	card = snd_lookup_minor_data(iminor(inode), SNDRV_DEVICE_TYPE_CONTROL);
	...
	ctl = kzalloc(sizeof(*ctl), GFP_KERNEL);
	if (ctl == NULL) {
		err = -ENOMEM;
		goto __error;
	}
	INIT_LIST_HEAD(&ctl->events);
	init_waitqueue_head(&ctl->change_sleep);
	spin_lock_init(&ctl->read_lock);
	ctl->card = card;
	for (i = 0; i < SND_CTL_SUBDEV_ITEMS; i++)
		ctl->preferred_subdevice[i] = -1;
	ctl->pid = get_pid(task_pid(current));
	file->private_data = ctl;
	scoped_guard(write_lock_irqsave, &card->controls_rwlock)
		list_add_tail(&ctl->list, &card->ctl_files);
	snd_card_unref(card);
	return 0;
	...
}
```

The per-open object carries the state every later ioctl and read needs. The [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) holds the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L107) back pointer, the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag that gates event delivery, the [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue guarded by [`read_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L110), the [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue that [`read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) and [`poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) block on, and the [`fasync`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L112) handle for SIGIO:

```c
/* include/sound/control.h:105 */
struct snd_ctl_file {
	struct list_head list;		/* list of all control files */
	struct snd_card *card;
	struct pid *pid;
	int preferred_subdevice[SND_CTL_SUBDEV_ITEMS];
	wait_queue_head_t change_sleep;
	spinlock_t read_lock;
	struct snd_fasync *fasync;
	int subscribed;			/* read interface is activated */
	struct list_head events;	/* waiting events for read */
};
```

[`snd_ctl_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109) reverses the open. It unlinks the file from [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), then takes [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write and walks every control to release the per-element write locks this file still owns, so a client that exits without unlocking does not strand an element, and finally drains the event queue:

```c
/* sound/core/control.c:109 */
static int snd_ctl_release(struct inode *inode, struct file *file)
{
	struct snd_card *card;
	struct snd_ctl_file *ctl;
	struct snd_kcontrol *control;
	unsigned int idx;

	ctl = file->private_data;
	file->private_data = NULL;
	card = ctl->card;

	scoped_guard(write_lock_irqsave, &card->controls_rwlock)
		list_del(&ctl->list);

	scoped_guard(rwsem_write, &card->controls_rwsem) {
		list_for_each_entry(control, &card->controls, list)
			for (idx = 0; idx < control->count; idx++)
				if (control->vd[idx].owner == ctl)
					control->vd[idx].owner = NULL;
	}

	snd_fasync_free(ctl->fasync);
	snd_ctl_empty_read_queue(ctl);
	put_pid(ctl->pid);
	kfree(ctl);
	module_put(card->module);
	snd_card_file_remove(card, file);
	return 0;
}
```

The file operation struct binds these to the node. [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266) wires [`read`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2269) to the event reader, [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273) to the dispatcher, [`poll`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2272) to the readiness check, and [`fasync`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2275) to the SIGIO registration:

```c
/* sound/core/control.c:2266 */
static const struct file_operations snd_ctl_f_ops =
{
	.owner =	THIS_MODULE,
	.read =		snd_ctl_read,
	.open =		snd_ctl_open,
	.release =	snd_ctl_release,
	.poll =		snd_ctl_poll,
	.unlocked_ioctl =	snd_ctl_ioctl,
	.compat_ioctl =	snd_ctl_ioctl_compat,
	.fasync =	snd_ctl_fasync,
};
```

The open path allocates one of these per descriptor for those operations to act on, holding the card back pointer, the subscribed gate, and the events queue behind change_sleep:

```
    struct snd_ctl_file: one per controlC%d open
    ───────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────┐
    │ struct snd_ctl_file                              │
    ├──────────────────────────────────────────────────┤
    │ list           node on card->ctl_files           │
    │ card           back pointer to struct snd_card   │
    │ pid            opening task pid                  │
    │ change_sleep   wait queue read/poll block on     │
    │ read_lock      spinlock guarding events          │
    │ fasync         SIGIO handle                      │
    │ subscribed     gate 0 = no events delivered      │
    │ events         queue of struct snd_kctl_event    │
    └──────────────────────────────────────────────────┘
    snd_ctl_open allocates and links; snd_ctl_release
    unlinks, clears owned vd->owner locks, drains events
```

### The ioctl dispatch

[`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) recovers the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) from [`file->private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h) and switches on the request number. The element commands forward to the per-command handlers, the version and power commands answer inline, and the three TLV commands wrap their handler in [`snd_power_ref_and_wait()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) and [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) because the TLV callback can reach hardware that must be powered up first:

```c
/* sound/core/control.c:1899 */
static long snd_ctl_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	struct snd_ctl_file *ctl;
	struct snd_card *card;
	struct snd_kctl_ioctl *p;
	void __user *argp = (void __user *)arg;
	int __user *ip = argp;
	int err;

	ctl = file->private_data;
	card = ctl->card;
	if (snd_BUG_ON(!card))
		return -ENXIO;
	switch (cmd) {
	case SNDRV_CTL_IOCTL_PVERSION:
		return put_user(SNDRV_CTL_VERSION, ip) ? -EFAULT : 0;
	case SNDRV_CTL_IOCTL_CARD_INFO:
		return snd_ctl_card_info(card, ctl, cmd, argp);
	case SNDRV_CTL_IOCTL_ELEM_LIST:
		return snd_ctl_elem_list_user(card, argp);
	case SNDRV_CTL_IOCTL_ELEM_INFO:
		return snd_ctl_elem_info_user(ctl, argp);
	case SNDRV_CTL_IOCTL_ELEM_READ:
		return snd_ctl_elem_read_user(card, argp);
	case SNDRV_CTL_IOCTL_ELEM_WRITE:
		return snd_ctl_elem_write_user(ctl, argp);
	case SNDRV_CTL_IOCTL_ELEM_LOCK:
		return snd_ctl_elem_lock(ctl, argp);
	case SNDRV_CTL_IOCTL_ELEM_UNLOCK:
		return snd_ctl_elem_unlock(ctl, argp);
	case SNDRV_CTL_IOCTL_ELEM_ADD:
		return snd_ctl_elem_add_user(ctl, argp, 0);
	case SNDRV_CTL_IOCTL_ELEM_REPLACE:
		return snd_ctl_elem_add_user(ctl, argp, 1);
	case SNDRV_CTL_IOCTL_ELEM_REMOVE:
		return snd_ctl_elem_remove(ctl, argp);
	case SNDRV_CTL_IOCTL_SUBSCRIBE_EVENTS:
		return snd_ctl_subscribe_events(ctl, ip);
	case SNDRV_CTL_IOCTL_TLV_READ:
		err = snd_power_ref_and_wait(card);
		if (err < 0)
			return err;
		scoped_guard(rwsem_read, &card->controls_rwsem)
			err = snd_ctl_tlv_ioctl(ctl, argp, SNDRV_CTL_TLV_OP_READ);
		snd_power_unref(card);
		return err;
	...
	case SNDRV_CTL_IOCTL_POWER:
		return -ENOPROTOOPT;
	case SNDRV_CTL_IOCTL_POWER_STATE:
		return put_user(SNDRV_CTL_POWER_D0, ip) ? -EFAULT : 0;
	}

	guard(rwsem_read)(&snd_ioctl_rwsem);
	list_for_each_entry(p, &snd_control_ioctls, list) {
		err = p->fioctl(card, ctl, cmd, arg);
		if (err != -ENOIOCTLCMD)
			return err;
	}
	dev_dbg(card->dev, "unknown ioctl = 0x%x\n", cmd);
	return -ENOTTY;
}
```

A request that matches no case label falls through to the registered extra-ioctl list [`snd_control_ioctls`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L36), walked under [`snd_ioctl_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L34). Each entry is a [`snd_kctl_ioctl_func_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L127) callback that a device manager added with [`snd_ctl_register_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2077), and the walk stops at the first callback that does not return `-ENOIOCTLCMD`. The ioctl numbers themselves are defined in the uapi header as a contiguous `'U'`-magic block:

```c
/* include/uapi/sound/asound.h:1199 */
#define SNDRV_CTL_IOCTL_PVERSION	_IOR('U', 0x00, int)
#define SNDRV_CTL_IOCTL_CARD_INFO	_IOR('U', 0x01, struct snd_ctl_card_info)
#define SNDRV_CTL_IOCTL_ELEM_LIST	_IOWR('U', 0x10, struct snd_ctl_elem_list)
#define SNDRV_CTL_IOCTL_ELEM_INFO	_IOWR('U', 0x11, struct snd_ctl_elem_info)
#define SNDRV_CTL_IOCTL_ELEM_READ	_IOWR('U', 0x12, struct snd_ctl_elem_value)
#define SNDRV_CTL_IOCTL_ELEM_WRITE	_IOWR('U', 0x13, struct snd_ctl_elem_value)
#define SNDRV_CTL_IOCTL_ELEM_LOCK	_IOW('U', 0x14, struct snd_ctl_elem_id)
#define SNDRV_CTL_IOCTL_ELEM_UNLOCK	_IOW('U', 0x15, struct snd_ctl_elem_id)
#define SNDRV_CTL_IOCTL_SUBSCRIBE_EVENTS _IOWR('U', 0x16, int)
#define SNDRV_CTL_IOCTL_ELEM_ADD	_IOWR('U', 0x17, struct snd_ctl_elem_info)
#define SNDRV_CTL_IOCTL_ELEM_REPLACE	_IOWR('U', 0x18, struct snd_ctl_elem_info)
#define SNDRV_CTL_IOCTL_ELEM_REMOVE	_IOWR('U', 0x19, struct snd_ctl_elem_id)
#define SNDRV_CTL_IOCTL_TLV_READ	_IOWR('U', 0x1a, struct snd_ctl_tlv)
#define SNDRV_CTL_IOCTL_TLV_WRITE	_IOWR('U', 0x1b, struct snd_ctl_tlv)
#define SNDRV_CTL_IOCTL_TLV_COMMAND	_IOWR('U', 0x1c, struct snd_ctl_tlv)
```

The first two commands answer without touching the control list. [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) is handled by [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867), which copies the card identity strings out of [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063) under [`snd_ioctl_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L34):

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

That handler is one row of the dispatcher's table, each request number from 0x00 routing to its handler before an unmatched one falls to the extra-ioctl walk:

```
    snd_ctl_ioctl: SNDRV_CTL_IOCTL_* number to handler
    ──────────────────────────────────────────────────────

     request _IO*('U', nr)       handler
    ┌─────────────────────────┬──────────────────────────┐
    │ PVERSION       0x00     │ inline SNDRV_CTL_VERSION │
    │ CARD_INFO      0x01     │ snd_ctl_card_info        │
    │ ELEM_LIST      0x10     │ snd_ctl_elem_list_user   │
    │ ELEM_INFO      0x11     │ snd_ctl_elem_info_user   │
    │ ELEM_READ      0x12     │ snd_ctl_elem_read_user   │
    │ ELEM_WRITE     0x13     │ snd_ctl_elem_write_user  │
    │ ELEM_LOCK      0x14     │ snd_ctl_elem_lock        │
    │ ELEM_UNLOCK    0x15     │ snd_ctl_elem_unlock      │
    │ SUBSCRIBE      0x16     │ snd_ctl_subscribe_events │
    │ ELEM_ADD       0x17     │ snd_ctl_elem_add_user, 0 │
    │ ELEM_REPLACE   0x18     │ snd_ctl_elem_add_user, 1 │
    │ ELEM_REMOVE    0x19     │ snd_ctl_elem_remove      │
    │ TLV_READ       0x1a     │ snd_ctl_tlv_ioctl, READ  │
    └─────────────────────────┴─────────────┬────────────┘
                                            ▼ no case match
    walk snd_control_ioctls; first reply not -ENOIOCTLCMD
    wins, otherwise -ENOTTY
```

### Enumerate, info, read, and write address the element by id

A client discovers the card's elements with [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201). The carrier [`struct snd_ctl_elem_list`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1130) is a window request, the [`offset`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1131) and [`space`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1132) name how many ids to skip and how many the [`pids`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1135) buffer can hold, and the kernel fills [`used`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1133) and the total [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1134) on return:

```c
/* include/uapi/sound/asound.h:1130 */
struct snd_ctl_elem_list {
	unsigned int offset;		/* W: first element ID to get */
	unsigned int space;		/* W: count of element IDs to get */
	unsigned int used;		/* R: count of element IDs set */
	unsigned int count;		/* R: count of all elements */
	struct snd_ctl_elem_id __user *pids; /* R: IDs */
	unsigned char reserved[50];
};
```

[`snd_ctl_elem_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L889) walks [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) under [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101), skips the first [`offset`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1131) sub-elements, and for each remaining one builds a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) with [`snd_ctl_build_ioff()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L207) and copies it out, stopping when the buffer is full:

```c
/* sound/core/control.c:889 */
static int snd_ctl_elem_list(struct snd_card *card,
			     struct snd_ctl_elem_list *list)
{
	struct snd_kcontrol *kctl;
	struct snd_ctl_elem_id id;
	unsigned int offset, space, jidx;

	offset = list->offset;
	space = list->space;

	guard(rwsem_read)(&card->controls_rwsem);
	list->count = card->controls_count;
	list->used = 0;
	if (!space)
		return 0;
	list_for_each_entry(kctl, &card->controls, list) {
		if (offset >= kctl->count) {
			offset -= kctl->count;
			continue;
		}
		for (jidx = offset; jidx < kctl->count; jidx++) {
			snd_ctl_build_ioff(&id, kctl, jidx);
			if (copy_to_user(list->pids + list->used, &id, sizeof(id)))
				return -EFAULT;
			list->used++;
			if (!--space)
				return 0;
		}
		offset = 0;
	}
	return 0;
}
```

Given an id, [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) returns the element's type and range. [`snd_ctl_elem_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1159) resolves the addressed [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) with [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) and runs its [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) callback, and the [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172) wrapper strips the kernel-only access bits before the result reaches userspace:

```c
/* sound/core/control.c:1159 */
static int snd_ctl_elem_info(struct snd_ctl_file *ctl,
			     struct snd_ctl_elem_info *info)
{
	struct snd_card *card = ctl->card;
	struct snd_kcontrol *kctl;

	guard(rwsem_read)(&card->controls_rwsem);
	kctl = snd_ctl_find_id(card, &info->id);
	if (!kctl)
		return -ENOENT;
	return __snd_ctl_elem_info(card, kctl, info, ctl);
}
```

The value moves through [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168), whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1169) field addresses the element the same way. [`snd_ctl_elem_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) takes [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for read, resolves the element, indexes its per-element volatile slot to test the [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) bit and the presence of a [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callback, then runs the callback:

```c
/* sound/core/control.c:1196 */
static int snd_ctl_elem_read(struct snd_card *card,
			     struct snd_ctl_elem_value *control)
{
	struct snd_kcontrol *kctl;
	struct snd_kcontrol_volatile *vd;
	unsigned int index_offset;
	struct snd_ctl_elem_info info;
	const u32 pattern = 0xdeadbeef;
	int ret;

	guard(rwsem_read)(&card->controls_rwsem);
	kctl = snd_ctl_find_id(card, &control->id);
	if (!kctl)
		return -ENOENT;

	index_offset = snd_ctl_get_ioff(kctl, &control->id);
	vd = &kctl->vd[index_offset];
	if (!(vd->access & SNDRV_CTL_ELEM_ACCESS_READ) || !kctl->get)
		return -EPERM;
	...
	ret = kctl->get(kctl, control);
	if (ret < 0)
		return ret;
	...
	return 0;
}
```

[`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) is the symmetric write. It takes the rwsem for write, checks the [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) bit, the presence of a [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback, and the lock owner, then runs [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76). When the callback reports the stored value changed (a return of 1), it downgrades the write hold to a read hold, announces the change with [`snd_ctl_notify_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200), and releases:

```c
/* sound/core/control.c:1267 */
static int snd_ctl_elem_write(struct snd_card *card, struct snd_ctl_file *file,
			      struct snd_ctl_elem_value *control)
{
	struct snd_kcontrol *kctl;
	struct snd_kcontrol_volatile *vd;
	unsigned int index_offset;
	int result = 0;

	down_write(&card->controls_rwsem);
	kctl = snd_ctl_find_id(card, &control->id);
	if (kctl == NULL) {
		up_write(&card->controls_rwsem);
		return -ENOENT;
	}

	index_offset = snd_ctl_get_ioff(kctl, &control->id);
	vd = &kctl->vd[index_offset];
	if (!(vd->access & SNDRV_CTL_ELEM_ACCESS_WRITE) || kctl->put == NULL ||
	    (file && vd->owner && vd->owner != file)) {
		up_write(&card->controls_rwsem);
		return -EPERM;
	}
	...
	if (!result)
		result = kctl->put(kctl, control);
	if (result < 0) {
		up_write(&card->controls_rwsem);
		return result;
	}

	if (result > 0) {
		downgrade_write(&card->controls_rwsem);
		snd_ctl_notify_one(card, SNDRV_CTL_EVENT_MASK_VALUE, kctl, index_offset);
		up_read(&card->controls_rwsem);
	} else {
		up_write(&card->controls_rwsem);
	}

	return 0;
}
```

The id that all four commands carry is the same [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), addressed either by the numeric [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) that [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815) resolves directly, or by the ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple that [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) matches.

```
    snd_ctl_elem_id key to a struct snd_kcontrol
    ─────────────────────────────────────────────────

    LIST / INFO / READ / WRITE all carry one elem_id

     addressing key              resolver
    ┌──────────────────────────┬─────────────────────────┐
    │ numid != 0               │ snd_ctl_find_numid      │
    │ numid == 0, by tuple:    │ snd_ctl_find_id         │
    │   iface, device,         │   matches the tuple     │
    │   subdevice, name, index │                         │
    └──────────────────────────┴────────────┬────────────┘
                                            ▼
    struct snd_kcontrol on card->controls; then
    snd_ctl_get_ioff picks vd[index_offset] slot
```

### Element locking through the owner fd

A client that needs exclusive write access claims a per-element lock with [`SNDRV_CTL_IOCTL_ELEM_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1205). [`snd_ctl_elem_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1345) resolves the element under [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) held for write, and records the claiming [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) in the per-element [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) slot, rejecting a second claim with `-EBUSY`:

```c
/* sound/core/control.c:1345 */
static int snd_ctl_elem_lock(struct snd_ctl_file *file,
			     struct snd_ctl_elem_id __user *_id)
{
	struct snd_card *card = file->card;
	struct snd_ctl_elem_id id;
	struct snd_kcontrol *kctl;
	struct snd_kcontrol_volatile *vd;

	if (copy_from_user(&id, _id, sizeof(id)))
		return -EFAULT;
	guard(rwsem_write)(&card->controls_rwsem);
	kctl = snd_ctl_find_id(card, &id);
	if (!kctl)
		return -ENOENT;
	vd = &kctl->vd[snd_ctl_get_ioff(kctl, &id)];
	if (vd->owner)
		return -EBUSY;
	vd->owner = file;
	return 0;
}
```

The recorded owner is what [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) consults. A write from any other file is refused with `-EPERM` while [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) is set to a different file, and a query of the element reports the lock through the [`SNDRV_CTL_ELEM_ACCESS_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1105) and [`SNDRV_CTL_ELEM_ACCESS_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1106) bits. [`SNDRV_CTL_IOCTL_ELEM_UNLOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1206) reaches [`snd_ctl_elem_unlock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1366), which clears [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) only when the calling file is the owner, returning `-EINVAL` for an unlocked element and `-EPERM` for one owned by another file:

```c
/* sound/core/control.c:1366 */
static int snd_ctl_elem_unlock(struct snd_ctl_file *file,
			       struct snd_ctl_elem_id __user *_id)
{
	...
	vd = &kctl->vd[snd_ctl_get_ioff(kctl, &id)];
	if (!vd->owner)
		return -EINVAL;
	if (vd->owner != file)
		return -EPERM;
	vd->owner = NULL;
	return 0;
}
```

Because [`snd_ctl_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109) clears every [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) equal to the closing file, a lock is dropped automatically when the holding fd is closed, so a crashed client cannot leave an element permanently locked.

```
    Per-element write lock recorded in vd->owner
    ─────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────┐
    │ vd->owner == NULL    element is unlocked         │
    ├──────────────────────────────────────────────────┤
    │ ELEM_LOCK   ▶ owner = file (else -EBUSY)         │
    │ ELEM_UNLOCK ▶ owner = NULL when file == owner    │
    │              -EINVAL unlocked, -EPERM other      │
    └──────────────────────────────────────────────────┘
                │                           │
         writer = owner         writer = other
                ▼                           ▼
    ┌────────────────────────┐  ┌────────────────────────┐
    │ ELEM_WRITE allowed     │  │ ELEM_WRITE refused     │
    │                        │  │ with -EPERM            │
    └────────────────────────┘  └────────────────────────┘
    snd_ctl_release clears every vd->owner == closing file
```

### A value change notifies subscribed control files

A value change announces itself to every subscribed control file. [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) takes [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) for read and walks [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), skipping any file whose [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag is clear. For each subscribed file it coalesces the new mask into an existing [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) with the same numid, or allocates a new one and appends it to the file's [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue, then wakes the [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue that a blocked [`read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) or [`poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) waits on.

According to the loop in [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149), an unsubscribed file is passed over, so an event is queued only on the files that asked for change reports with [`SNDRV_CTL_IOCTL_SUBSCRIBE_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1207):

```c
/* sound/core/control.c:164 */
	list_for_each_entry(ctl, &card->ctl_files, list) {
		if (!ctl->subscribed)
			continue;
		scoped_guard(spinlock, &ctl->read_lock) {
			list_for_each_entry(ev, &ctl->events, list) {
				if (ev->id.numid == id->numid) {
					ev->mask |= mask;
					goto _found;
				}
			}
			ev = kzalloc(sizeof(*ev), GFP_ATOMIC);
			if (ev) {
				ev->id = *id;
				ev->mask = mask;
				list_add_tail(&ev->list, &ctl->events);
			}
_found:
			wake_up(&ctl->change_sleep);
		}
		snd_kill_fasync(ctl->fasync, SIGIO, POLL_IN);
	}
```

Walking that loop across three open files lands an event on the two subscribed and passes over the unsubscribed one:

```
    snd_ctl_notify(card, mask, id)  (producer, atomic context)
       walks card->ctl_files, coalesces by numid, wakes change_sleep
         │             │              │
         ▼             ▼              ▼
    ctl_file[0]   ctl_file[1]    ctl_file[2]
    subscribed    not subscr.    subscribed
    events: +ev   (skipped)      events: +ev
```

### Control ioctl dispatch and event notification overview

The controlC%d descriptor carries one [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) per open, every request enters the [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) switch over the `SNDRV_CTL_IOCTL_*` numbers, and a value change reaches [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149), which fans an event out across [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) (coalescing by numid and waking [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109)) to only the subscribed files.

```
    controlC%d fd (one struct snd_ctl_file per open)
    ┌──────────────────────────────────────────────────────┐
    │ ioctl(fd, SNDRV_CTL_IOCTL_*, arg)                    │
    │        │                                             │
    │        ▼  snd_ctl_ioctl()                            │
    │   ┌─────────────────────────────────────────────┐    │
    │   │ ELEM_LIST / INFO / READ / WRITE / LOCK /    │    │
    │   │ ADD / REPLACE / REMOVE / TLV_* / SUBSCRIBE  │    │
    │   └─────────────────────────────────────────────┘    │
    │ events ◀── read()/poll() dequeues snd_kctl_event     │
    └────────────────────────────▲─────────────────────────┘
                                 │ queued on subscribed fds
    snd_ctl_notify(card, mask, id)  (producer, atomic context)
       walks card->ctl_files, coalesces by numid, wakes change_sleep
         │            │              │
         ▼            ▼              ▼
    ctl_file[0]   ctl_file[1]    ctl_file[2]
    subscribed    not subscr.    subscribed
    events: +ev   (skipped)      events: +ev
```
