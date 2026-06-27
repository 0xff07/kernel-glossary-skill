# Control element I/O and notification

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A control element runs three callbacks. [`snd_kcontrol_info_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17) reports the element's type, channel count, and value range into a [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139); [`snd_kcontrol_get_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L18) reads the current value into a [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168); and [`snd_kcontrol_put_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L19) writes a new value and returns 1 when the stored value changed. The per-element [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L67) flags in [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) gate these callbacks, [`snd_ctl_elem_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) and [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) move the values under [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101), and a changed value fans out to subscribed control files through [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149).

```
   userspace ioctl                     kernel callback              metadata
   ───────────────                     ───────────────              ────────
   ELEM_INFO   ──▶ snd_ctl_elem_info ──▶ kctl->info(info)  fills type/count/range
   ELEM_READ   ──▶ snd_ctl_elem_read ──▶ kctl->get(value)  (needs ACCESS_READ)
   ELEM_WRITE  ──▶ snd_ctl_elem_write─▶ kctl->put(value)  (needs ACCESS_WRITE)
                                          │ returns 1 = changed
                                          ▼
                                       snd_ctl_notify_one(MASK_VALUE)
                                          │
   TLV_READ    ──▶ snd_ctl_tlv_ioctl ─▶ tlv.c() or read tlv.p[]   (dB scale)
                                          ▼
   poll()/read()◀── change_sleep ◀── queue struct snd_kctl_event on each
                                       subscribed struct snd_ctl_file
```

## SUMMARY

The behavior of one [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) is defined by the three callbacks declared as typedefs in [`include/sound/control.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17). The [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) callback fills a [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139), often through the enumerated-control helper [`snd_ctl_enum_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436). The [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callbacks read and write a [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168). [`snd_ctl_elem_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) checks the [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) bit and the presence of a [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callback before running it under a read hold of [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101). [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) checks [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096), the [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback, and the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66), and on a changed value it downgrades the rwsem and notifies before releasing.

The [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L77) union carries metadata too large for the value path, most often the dB scale of a volume control. [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) routes a TLV request to the [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback when [`SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1107) is set, otherwise reading the static [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) array. A change is announced with [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149), which queues a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) on each subscribed [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) and wakes its [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue, and [`snd_ctl_notify_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200) wraps it to offset the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127) and [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) of a multi-element control and drive the LED layers. The construction and registration of a control element are out of scope here and are documented with the [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260)/[`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) constructor pair. The ASoC layer supplies the three callbacks for its mixer controls, where [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) decode the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) in [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81) and read or write the component regmap rather than a raw chip pointer.

## SPECIFICATIONS

The control I/O surface is the ALSA control ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). Values and info travel in [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) and [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139), the `SNDRV_CTL_ELEM_ACCESS_*` bits encode access rights, and the `SNDRV_CTL_IOCTL_ELEM_*` numbers name the requests. The dB-scale metadata a control attaches through its TLV channel follows the ALSA TLV (Type-Length-Value) format, whose item types are defined in [`include/uapi/sound/tlv.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/tlv.h).

## LINUX KERNEL

### Callback typedefs and TLV ops (control.h)

- [`snd_kcontrol_info_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17): the info callback signature, filling a [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139)
- [`snd_kcontrol_get_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L18) / [`snd_kcontrol_put_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L19): the read and write callbacks over a [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168)
- [`snd_kcontrol_tlv_rw_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L20): the TLV callback, taking an op flag and a userspace TLV buffer
- [`SNDRV_CTL_TLV_OP_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L42) / [`SNDRV_CTL_TLV_OP_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L43) / [`SNDRV_CTL_TLV_OP_CMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L44): the op flags the TLV callback dispatches on

### Access flags (asound.h)

- [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) / [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) / [`SNDRV_CTL_ELEM_ACCESS_READWRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1097): readability and writability bits gating [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76)
- [`SNDRV_CTL_ELEM_ACCESS_VOLATILE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1098): the value may change without a notification, so userspace must re-read it
- [`SNDRV_CTL_ELEM_ACCESS_INACTIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1104): the element is present but does nothing for now, still readable for its info
- [`SNDRV_CTL_ELEM_ACCESS_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1105) / [`SNDRV_CTL_ELEM_ACCESS_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1106): the write-lock and lock-owner bits a [`SNDRV_CTL_IOCTL_ELEM_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1205) sets
- [`SNDRV_CTL_ELEM_ACCESS_TLV_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1100) / [`SNDRV_CTL_ELEM_ACCESS_TLV_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1101) / [`SNDRV_CTL_ELEM_ACCESS_TLV_COMMAND`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1103): the TLV permission bits
- [`SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1107): the kernel-only bit selecting the [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback over the [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) array

### Info, read, write, lock (control.c)

- [`'\<snd_ctl_enum_info\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436): the standard info helper for an enumerated control, setting type, channel count, item count, and the selected item name
- [`'\<snd_ctl_elem_read\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196): the read path behind [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203); checks the [`READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) bit then calls [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)
- [`'\<snd_ctl_elem_write\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267): the write path behind [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204); checks the [`WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) bit and the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66), calls [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), and notifies on a changed value
- [`'\<snd_ctl_elem_lock\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1345): claim a per-element write lock by setting [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66)

### TLV channel (control.c)

- [`'\<snd_ctl_tlv_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850): route a TLV request to the [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback or read the [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) array

### Notification and poll (control.c)

- [`'\<snd_ctl_notify\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149): queue a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) on each subscribed [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) and wake its readers, under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102)
- [`'\<snd_ctl_notify_one\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200): notify a single element of a multi-element control, offsetting [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127) and [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122), then drive the LED layers
- [`'\<snd_ctl_subscribe_events\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772): set the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag so this control file starts receiving events
- [`'\<snd_ctl_poll\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035): report `EPOLLIN` when the file's [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue is non-empty

### Event and file types (control.h)

- [`'\<struct snd_kctl_event\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89): the queued change record carrying the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L91) and accumulated event [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L92)
- [`'\<struct snd_ctl_file\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105): one open controlC%d handle; carries the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag, the [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue, and the [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue

### Driver worked example (cs35l41_hda.c)

- [`'\<cs35l41_fw_type_ctl_info\>':'sound/hda/codecs/side-codecs/cs35l41_hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/side-codecs/cs35l41_hda.c#L1323): an info callback calling [`snd_ctl_enum_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436) for an enumerated firmware-type control on a SoundWire/HDA bridge codec

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter, covering the info/get/put callbacks and the access and TLV flags
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated API reference pulling kernel-doc from [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c)

## OTHER SOURCES

- [ALSA project library documentation, Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [ALSA project library documentation, High Level Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__HControl.html)
- [alsa-utils (amixer, alsactl)](https://github.com/alsa-project/alsa-utils)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Three callbacks define an element's behavior, and the per-element access flags gate which of them userspace may invoke. A read goes through [`snd_ctl_elem_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) to [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75), a write through [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) to [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), and an info query to the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) callback. A TLV request takes a separate path through [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850).

| Callback | Typedef | Carrier | Returns |
|----------|---------|---------|---------|
| info | [`snd_kcontrol_info_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17) | [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) | 0 or error |
| get | [`snd_kcontrol_get_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L18) | [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) | 0 or error |
| put | [`snd_kcontrol_put_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L19) | [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) | 1 when changed, 0 unchanged, error |
| tlv | [`snd_kcontrol_tlv_rw_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L20) | userspace TLV buffer + op flag | bytes or error |

## DETAILS

### The info, get, and put contract

Three callbacks define an element's behavior, declared as typedefs in [`control.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17). [`snd_kcontrol_info_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L17) fills a [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) with the element's type, channel count, and value range; [`snd_kcontrol_get_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L18) reads the current value into a [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168); and [`snd_kcontrol_put_t`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L19) writes a new value and returns 1 when the stored value actually changed, which the core turns into a [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) notification:

```c
/* include/sound/control.h:17 */
typedef int (snd_kcontrol_info_t) (struct snd_kcontrol * kcontrol, struct snd_ctl_elem_info * uinfo);
typedef int (snd_kcontrol_get_t) (struct snd_kcontrol * kcontrol, struct snd_ctl_elem_value * ucontrol);
typedef int (snd_kcontrol_put_t) (struct snd_kcontrol * kcontrol, struct snd_ctl_elem_value * ucontrol);
typedef int (snd_kcontrol_tlv_rw_t)(struct snd_kcontrol *kcontrol,
				    int op_flag, /* SNDRV_CTL_TLV_OP_XXX */
				    unsigned int size,
				    unsigned int __user *tlv);
```

The per-element [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L67) flags in [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) gate these callbacks. [`snd_ctl_elem_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) refuses an element whose slot lacks [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) or has no [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callback, taking [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for read while it runs the callback. With [`CONFIG_SND_CTL_DEBUG`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig) it fills the returned value with a 0xdeadbeef pattern first and validates that the callback wrote only as many channels as its info reported:

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

[`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) is the symmetric write path. It checks [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096), the presence of a [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback, and the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66). An element locked by another control file rejects the write with `-EPERM`. On a changed value (a [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) return greater than zero) it downgrades the rwsem from write to read and notifies before releasing:

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

The same get and put sit with info in this table, each paired with the struct it carries, info writing the elem_info and get and put exchanging the elem_value with the hardware:

```
    info / get / put: carrier struct and what each touches
    ────────────────────────────────────────────────────────

    callback  carrier struct       fills or reads
    ┌──────┬────────────────────┬──────────────────────────┐
    │ info │ snd_ctl_elem_info  │ writes type, count,      │
    │      │                    │ value range              │
    │ get  │ snd_ctl_elem_value │ reads hw, writes         │
    │      │                    │ value.* into the buffer  │
    │ put  │ snd_ctl_elem_value │ reads the buffer, writes │
    │      │                    │ hw; returns 1 if changed │
    └──────┴────────────────────┴───────────┬──────────────┘
                                            ▼  put return > 0
              snd_ctl_notify_one(SNDRV_CTL_EVENT_MASK_VALUE)

    read gated by ACCESS_READ + a get; write gated by ACCESS_WRITE
    + a put + an unowned (or owning) vd->owner lock
```

### Access flags beyond read and write

The access bits beyond read and write describe the element's character. [`SNDRV_CTL_ELEM_ACCESS_VOLATILE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1098) marks a value that can change underneath userspace without a notification, so a client re-reads rather than trusting a cached copy. [`SNDRV_CTL_ELEM_ACCESS_INACTIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1104) marks an element that is present and queryable but does nothing for now. [`SNDRV_CTL_ELEM_ACCESS_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1105) and [`SNDRV_CTL_ELEM_ACCESS_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1106) report the write-lock state that [`snd_ctl_elem_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1345) sets by recording the claiming control file in [`vd->owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66):

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

An enumerated control fills its info through [`snd_ctl_enum_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436), the standard helper. It sets the type to [`SNDRV_CTL_ELEM_TYPE_ENUMERATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1079), records the channel and item counts, clamps the currently selected item, and copies that item's name into the info structure:

```c
/* sound/core/control.c:2436 */
int snd_ctl_enum_info(struct snd_ctl_elem_info *info, unsigned int channels,
		      unsigned int items, const char *const names[])
{
	info->type = SNDRV_CTL_ELEM_TYPE_ENUMERATED;
	info->count = channels;
	info->value.enumerated.items = items;
	if (!items)
		return 0;
	if (info->value.enumerated.item >= items)
		info->value.enumerated.item = items - 1;
	WARN(strlen(names[info->value.enumerated.item]) >= sizeof(info->value.enumerated.name),
	     "ALSA: too long item name '%s'\n",
	     names[info->value.enumerated.item]);
	strscpy(info->value.enumerated.name,
		names[info->value.enumerated.item],
		sizeof(info->value.enumerated.name));
	return 0;
}
```

The Cirrus [`cs35l41_fw_type_ctl_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/side-codecs/cs35l41_hda.c#L1323) callback is a one-line user of it, reporting a single-channel enumerated control over an array of firmware-type names:

```c
/* sound/hda/codecs/side-codecs/cs35l41_hda.c:1323 */
static int cs35l41_fw_type_ctl_info(struct snd_kcontrol *kcontrol, struct snd_ctl_elem_info *uinfo)
{
	return snd_ctl_enum_info(uinfo, 1, ARRAY_SIZE(cs35l41_hda_fw_ids), cs35l41_hda_fw_ids);
}
```

Each element's live access word collects bits from four roles, the read and write gates, the volatile and inactive character marks, the lock pair set in vd->owner, and the TLV permissions:

```
    Per-element vd->access flags, grouped by role
    ─────────────────────────────────────────────────

    ┌────────────┬────────────────────────────────────────┐
    │ gate       │ ACCESS_READ, ACCESS_WRITE,             │
    │ get/put    │ ACCESS_READWRITE                       │
    ├────────────┼────────────────────────────────────────┤
    │ character  │ ACCESS_VOLATILE  may change, no notify │
    │            │ ACCESS_INACTIVE  present, does nothing │
    ├────────────┼────────────────────────────────────────┤
    │ write lock │ ACCESS_LOCK, ACCESS_OWNER              │
    │            │ set in vd->owner by snd_ctl_elem_lock  │
    ├────────────┼────────────────────────────────────────┤
    │ TLV        │ ACCESS_TLV_READ, ACCESS_TLV_WRITE,     │
    │ channel    │ ACCESS_TLV_COMMAND                     │
    │            │ ACCESS_TLV_CALLBACK ▶ tlv.c, not tlv.p │
    └────────────┴────────────────────────────────────────┘
    every name is an SNDRV_CTL_ELEM_ACCESS_* bit OR-ed into access
```

### The TLV channel carries dB-scale metadata

The [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L77) union is a side channel for metadata too large for the value path, most often the dB scale that maps a volume control's raw steps to decibels. It is a union of a [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) const array (a static table the core reads directly) and a [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback (computed metadata), and the [`SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1107) flag selects which one is live. [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) implements the dispatch. It locates the element by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122), and when the callback bit is set it forwards the op (one of [`SNDRV_CTL_TLV_OP_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L42), [`SNDRV_CTL_TLV_OP_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L43), or [`SNDRV_CTL_TLV_OP_CMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L44)) to the handler, otherwise reading the static array for a read op:

```c
/* sound/core/control.c:1850 */
static int snd_ctl_tlv_ioctl(struct snd_ctl_file *file,
			     struct snd_ctl_tlv __user *buf,
                             int op_flag)
{
	struct snd_ctl_tlv header;
	unsigned int __user *container;
	unsigned int container_size;
	struct snd_kcontrol *kctl;
	struct snd_ctl_elem_id id;
	struct snd_kcontrol_volatile *vd;

	lockdep_assert_held(&file->card->controls_rwsem);
	...
	kctl = snd_ctl_find_numid(file->card, header.numid);
	if (kctl == NULL)
		return -ENOENT;

	/* Calculate index of the element in this set. */
	id = kctl->id;
	snd_ctl_build_ioff(&id, kctl, header.numid - id.numid);
	vd = &kctl->vd[snd_ctl_get_ioff(kctl, &id)];

	if (vd->access & SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK) {
		return call_tlv_handler(file, op_flag, kctl, &id, container,
					container_size);
	} else {
		if (op_flag == SNDRV_CTL_TLV_OP_READ) {
			return read_tlv_buf(kctl, &id, container,
					    container_size);
		}
	}

	/* Not supported. */
	return -ENXIO;
}
```

The callback bit and the op flag together select the answer, a set bit routing every op to the tlv.c handler and a clear bit reading the static tlv.p only for a read:

```
    snd_ctl_tlv_ioctl: which TLV source answers a request
    ────────────────────────────────────────────────────────

    locate kctl by header.numid, pick vd by the element offset

    TLV_CALLBACK   op_flag              resolution
    ┌───────┬────────────────────┬──────────────────────┐
    │ set   │ READ / WRITE / CMD │ call_tlv_handler ▶   │
    │       │                    │   tlv.c(op, buf)     │
    │ clear │ READ               │ read_tlv_buf ▶ tlv.p │
    │ clear │ WRITE / CMD        │ -ENXIO               │
    └───────┴────────────────────┴──────────────────────┘
    tlv.p is a static const dB-scale table read directly;
    tlv.c computes the metadata on demand
```

### The notify path queues an event and wakes the poll

A change is announced with [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149). According to its comment, "This can be called in the atomic context", which is why it works under the [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) spinlock rather than the sleeping rwsem. It walks [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), and for each subscribed [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) it either folds the new mask into an existing queued event with the same [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or appends a fresh [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89), then wakes the file's [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue:

```c
/* sound/core/control.c:149 */
void snd_ctl_notify(struct snd_card *card, unsigned int mask,
		    struct snd_ctl_elem_id *id)
{
	struct snd_ctl_file *ctl;
	struct snd_kctl_event *ev;

	if (snd_BUG_ON(!card || !id))
		return;
	if (card->shutdown)
		return;

	guard(read_lock_irqsave)(&card->controls_rwlock);
#if IS_ENABLED(CONFIG_SND_MIXER_OSS)
	card->mixer_oss_change_count++;
#endif
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
			} else {
				dev_err(card->dev, "No memory available to allocate event\n");
			}
_found:
			wake_up(&ctl->change_sleep);
		}
		snd_kill_fasync(ctl->fasync, SIGIO, POLL_IN);
	}
}
```

A multi-element control announces each sub-element through [`snd_ctl_notify_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200), which offsets the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127) and [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) before calling [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) and then runs any registered LED layer through [`lops->lnotify`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200):

```c
/* sound/core/control.c:200 */
void snd_ctl_notify_one(struct snd_card *card, unsigned int mask,
			struct snd_kcontrol *kctl, unsigned int ioff)
{
	struct snd_ctl_elem_id id = kctl->id;
	struct snd_ctl_layer_ops *lops;

	id.index += ioff;
	id.numid += ioff;
	snd_ctl_notify(card, mask, &id);
	guard(rwsem_read)(&snd_ctl_layer_rwsem);
	for (lops = snd_ctl_layer; lops; lops = lops->next)
		lops->lnotify(card, mask, kctl, ioff);
}
```

A client learns of the change by polling the control node. [`snd_ctl_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) returns readable when the file's [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue is non-empty, and reports nothing for a file that has not subscribed:

```c
/* sound/core/control.c:2035 */
static __poll_t snd_ctl_poll(struct file *file, poll_table * wait)
{
	__poll_t mask;
	struct snd_ctl_file *ctl;

	ctl = file->private_data;
	if (!ctl->subscribed)
		return 0;
	poll_wait(file, &ctl->change_sleep, wait);

	mask = 0;
	if (!list_empty(&ctl->events))
		mask |= EPOLLIN | EPOLLRDNORM;

	return mask;
}
```

Subscription is toggled by [`snd_ctl_subscribe_events()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772), which sets [`file->subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) so the file starts collecting events. A negative request reports the current state, and unsubscribing flushes any pending queue with [`snd_ctl_empty_read_queue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c):

```c
/* sound/core/control.c:1772 */
static int snd_ctl_subscribe_events(struct snd_ctl_file *file, int __user *ptr)
{
	int subscribe;
	if (get_user(subscribe, ptr))
		return -EFAULT;
	if (subscribe < 0) {
		subscribe = file->subscribed;
		if (put_user(subscribe, ptr))
			return -EFAULT;
		return 0;
	}
	if (subscribe) {
		file->subscribed = 1;
		return 0;
	} else if (file->subscribed) {
		snd_ctl_empty_read_queue(file);
		file->subscribed = 0;
	}
	return 0;
}
```

The queued [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) records hold the element [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L91) and an accumulated event [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L92), and the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) that owns the controlC%d handle carries the [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag, the [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue, and the [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) wait queue the notifier wakes:

```c
/* include/sound/control.h:89 */
struct snd_kctl_event {
	struct list_head list;	/* list of events */
	struct snd_ctl_elem_id id;
	unsigned int mask;
};
```

A subscribed reader collects these events with `read()` on the controlC%d node, decoding the mask into [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237), [`SNDRV_CTL_EVENT_MASK_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1238), [`SNDRV_CTL_EVENT_MASK_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1239), and [`SNDRV_CTL_EVENT_MASK_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1240) to learn which elements changed value, changed info, appeared, or went away.

```
    snd_ctl_notify fan-out and per-file event coalescing
    ───────────────────────────────────────────────────────

    snd_ctl_notify_one(mask, kctl, ioff)
      id = kctl->id;  id.index += ioff;  id.numid += ioff
      ─▶ snd_ctl_notify(card, mask, &id);  then run lops->lnotify
                  │
                  ▼  under controls_rwlock, walk card->ctl_files
                     and repeat the box below for each one:
    ┌───────────────────────────────────┐
    │ subscribed ctl_file (each one)    │
    │ scan its events for id.numid:     │
    │   found ▶ OR mask into ev->mask   │
    │   none  ▶ append a fresh          │
    │           snd_kctl_event to queue │
    │ wake_up(&change_sleep)            │
    └─────────────────┬─────────────────┘
                      ▼
    snd_ctl_poll reports EPOLLIN while events is non-empty;
    an unsubscribed ctl_file is skipped and gets no event
```

### The ASoC layer supplies the get and put handlers

For a control built from one of the `SOC_*` mixer macros, the [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) the core calls are ASoC functions rather than a per-codec handler. [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) casts [`kcontrol->private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81) back to the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the macro packed and forwards the register, mask, and range to the shared reader [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288):

```c
/* sound/soc/soc-ops.c:375 */
int snd_soc_get_volsw(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int mask = soc_mixer_mask(mc);

	return soc_get_volsw(kcontrol, ucontrol, mc, mask, mc->max - mc->min, false);
}
```

The shared [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) recovers the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) from [`snd_kcontrol_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14) and reads the value with [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671), so the value-movement contract here ends at the component regmap rather than a raw chip pointer. Its counterpart [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) decodes the same [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and writes the register through [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233), returning 1 on a changed value to drive the [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) notification just as the contract requires.
