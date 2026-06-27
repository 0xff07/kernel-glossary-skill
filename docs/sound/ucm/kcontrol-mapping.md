# UCM kcontrol mapping

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

UCM (Use Case Manager) is a userspace alsa-lib layer that names the verbs, devices, and modifiers of a sound card and applies a fixed set of control settings whenever one of those use cases is selected, and the only kernel surface it touches is the control (kcontrol) interface exposed by the card's control device, so a UCM `cset` line that names a control by the ASCII name in its [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) becomes a [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) ioctl that [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) routes to [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320), then [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267), which resolves the [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) through [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) to one [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and runs that control's [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback, an ASoC [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) toggle through [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725) or a [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) volume through [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396).

```
    UCM device config (userspace)              controlCx kcontrols (kernel)
    alsa-ucm-conf: sof-soundwire                created by ASoC + SOF topology

    SectionDevice."Headphones" {
      EnableSequence [
        cset "name='Headphone Switch' on"  ─▶  ┌─────────────────────────────┐
        cset "name='FU05 Playback           │  │ struct snd_kcontrol         │
               Volume' 87 87"               │  │  id.name "Headphone Switch" │
      ]                                      │  │  id.numid 12                │
    }                                        │  │  put = snd_soc_dapm_put_    │
                                             │  │        pin_switch           │
                                             │  └─────────────────────────────┘
       each cset line                        │  ┌─────────────────────────────┐
            │ alsa-lib snd_ctl_elem_write    │  │ struct snd_kcontrol         │
            ▼                                └▶ │  id.name "FU05 Playback     │
    SNDRV_CTL_IOCTL_ELEM_WRITE                  │            Volume"          │
            │ ioctl(/dev/snd/controlC0)         │  id.numid 7                 │
            ▼                                   │  count 2                    │
    snd_ctl_ioctl ─▶ snd_ctl_elem_write ─┐      │  put = rt711_sdca_set_gain_ │
                                         │      │        put                  │
              snd_ctl_find_id(card, &id) ┴─▶    └─────────────────────────────┘
              match by id.name, run kctl->put ─▶ hardware (DAPM sync, SoundWire)
```

## SUMMARY

UCM is the alsa-lib component that reads the per-card configuration tree shipped in the alsa-ucm-conf package and presents a card as a set of named use cases, a verb such as `HiFi`, devices such as `Headphones` or `Speaker`, and modifiers, each with an EnableSequence and a DisableSequence of control operations. The control operations are written with the `cset` keyword, whose argument is a control identifier and a value, for example `cset "name='Headphone Switch' on"`. UCM programs no registers and binds to no kernel module. Every EnableSequence step it runs is an ALSA control operation on the card's control character device, and the kernel side it drives is the control (kcontrol) interface in [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c). The control ioctl interface itself is documented separately; this page documents the `cset`/`cget`-to-kcontrol mapping and the control-naming conventions UCM relies on.

The control device is one character device per card, /dev/snd/controlCx, registered by [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) with the file operations in [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266), whose [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273) is [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899). That switch maps the element ioctls a UCM client uses. [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201) goes to [`snd_ctl_elem_list_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922), [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) to [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172), [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203) (a `cget`) to [`snd_ctl_elem_read_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244), and [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) (a `cset`) to [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320). The write path is the selection path. [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320) copies the [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) in from the client and calls [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267), which resolves the embedded [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) with [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840), checks the [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) bit, and runs the matched control's [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback.

The named controls those ioctls address are created during card bring-up. A driver describes one control with a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template and instantiates it with [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), and the SOF topology loader does the same through [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) for each control element in the topology binary. [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) links the resulting [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) onto the card and assigns its [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122). From that point the control is reachable by the ASCII name copied into its [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), which is exactly the string a UCM `cset` names. On an x86-64 ACPI SoundWire card driven by Sound Open Firmware, the names come from the codec drivers (a [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) such as a headphone pin switch added by the generic SoundWire machine, a [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282) volume in the rt711-sdca codec) and from the SOF topology, and the sof-soundwire UCM tree in alsa-ucm-conf names those exact strings in its EnableSequence `cset` lines.

## SPECIFICATIONS

The kcontrol interface is a Linux kernel software construct with no standalone hardware specification. The control ioctl numbers and the [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) and [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) layouts are the ALSA control ABI, defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) and versioned by [`SNDRV_CTL_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1061), reported to a client through [`SNDRV_CTL_IOCTL_PVERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1199). The name a `cset` carries is bounded by [`SNDRV_CTL_ELEM_ID_NAME_MAXLEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1119), 44 bytes including the terminator. UCM itself and the configuration syntax (SectionVerb, SectionDevice, EnableSequence, cset, cget, cdev) are defined by alsa-lib and the alsa-ucm-conf data set, both userspace projects outside the kernel tree.

## LINUX KERNEL

### Control identity and value types (uapi/sound/asound.h)

- [`'\<struct snd_ctl_elem_id\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121): the address of a control, either a numeric [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or the tuple of [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127); a UCM `cset` supplies the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) form
- [`'\<struct snd_ctl_elem_value\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168): the read/write payload, an embedded [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) plus a value union (`integer.value[]`, `enumerated.item[]`, `bytes.data[]`)
- [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204): write a control value; the ioctl a `cset` issues
- [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203): read a control value back; the ioctl a `cget` issues
- [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201): enumerate the card's controls and their ids
- [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202): query a control's type, range, and access from its id
- [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088): [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) value 2, the interface every ASoC mixer and DAPM control carries and the default a name-only `cset` matches against
- [`SNDRV_CTL_ELEM_ID_NAME_MAXLEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1119): 44, the byte limit on a control name and the bound a UCM name must respect

### Control device and ioctl dispatch (sound/core/control.c)

- [`'\<snd_ctl_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899): the control device [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273), a switch that routes each `SNDRV_CTL_IOCTL_*` command to its handler
- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291): registers the control character device with [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) under [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266)
- [`'\<snd_ctl_f_ops\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266): the [`struct file_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1926) wiring [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273) to [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899)
- [`'\<snd_ctl_elem_write_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320): copies the value in from the client, calls [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267), copies the result back
- [`'\<snd_ctl_elem_write\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267): finds the control by id, checks [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) and ownership, runs [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), notifies on change
- [`'\<snd_ctl_elem_read\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1196) / [`'\<snd_ctl_elem_read_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244): the `cget` path, checking [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) and running [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)
- [`'\<snd_ctl_elem_list_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922) / [`'\<snd_ctl_elem_info_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172): the list and info handlers a UCM client uses to discover controls and clamp values
- [`'\<snd_ctl_find_id\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840): resolve a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) to a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or by hashed name
- [`'\<snd_ctl_get_ioff\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L198) / [`'\<snd_ctl_build_ioff\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L207): convert between an id and the per-element offset inside a multi-element control
- [`'\<snd_ctl_notify_one\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200): post a [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) change event after a `cset` that changed the value

### Control object and creation (include/sound/control.h, sound/core/control.c)

- [`'\<struct snd_kcontrol\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70): the live control, carrying its [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), its [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72), and the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callbacks
- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the static template a driver or topology fills in before instantiation, holding [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L48), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L53), and the callbacks
- [`snd_kcontrol_chip`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14): the macro returning a control's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82), so a `put` callback recovers its component or card context
- [`'\<snd_ctl_new1\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260): allocate a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) from a template, copying [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51) into [`id.name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126)
- [`'\<snd_ctl_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546): add a control to the card and assign its [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122); defers to [`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509)
- [`'\<__snd_ctl_add_replace\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458): the locked core of insertion, links the control onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105), sets [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122), and adds the name-hash entries

### Topology and ASoC control creation (sound/soc)

- [`'\<snd_soc_cnew\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440): build a control from a template with an optional name prefix, then call [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260)
- [`'\<soc_tplg_kcontrol_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973): iterate the control elements in a topology header, dispatching mixer, enum, and bytes types
- [`'\<soc_tplg_control_dmixer_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637): fill a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) from a topology mixer record, copying the name from the binary into [`kc->name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51)
- [`'\<soc_tplg_kcontrol_bind_io\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459): attach the get/put/info handlers to a topology control by matching op ids
- [`'\<soc_tplg_add_dcontrol\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311): instantiate one topology control through [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and add it with [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546)
- [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369): the macro that builds a `"<name> Switch"` control with [`snd_soc_dapm_get_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3670) and [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725)
- [`'\<snd_soc_dapm_put_pin_switch\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725) / [`'\<snd_soc_dapm_get_pin_switch\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3670): the put and get callbacks a pin-switch `cset`/`cget` reaches, toggling or reading the named DAPM pin
- [`'\<__dapm_set_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932): set a named pin's connected state and report whether it changed, called from the pin-switch put
- [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) / [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282): the macros that build a single-channel and a two-channel volume control with a TLV dB range
- [`'\<snd_soc_put_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) / [`'\<snd_soc_get_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375): the generic put and get a [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) volume `cset`/`cget` reaches
- [`'\<rt711_sdca_set_gain_put\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L554): the codec put behind the `FU05 Playback Volume` `cset` on a SoundWire/SDCA jack codec, writing the SDCA gain over SoundWire

## KERNEL DOCUMENTATION

- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the naming convention for controls (source, direction, function), the convention UCM `cset` names follow
- [`Documentation/sound/designs/jack-controls.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/jack-controls.rst): the jack kcontrols a card exposes, which UCM consults to track headphone and microphone insertion
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter, covering [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), and the info/get/put callbacks the ioctl path drives
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM pin and widget model behind a pin switch
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): the front-end and back-end PCM model a SOF topology defines alongside its controls

## OTHER SOURCES

- [ALSA Use Case Manager (alsa-lib) documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__ucm.html)
- [alsa-ucm-conf repository](https://github.com/alsa-project/alsa-ucm-conf)
- [alsa-utils (alsaucm, amixer)](https://github.com/alsa-project/alsa-utils)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A UCM client opens /dev/snd/controlCx and issues control ioctls against the per-open [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105). Each is a command number defined in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) and handled by one case in [`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899). The `cset` keyword maps to the write ioctl, `cget` to the read ioctl, and the library's own discovery and validation map to the list and info ioctls.

The objects a `cset` and a `cget` carry are the control-id and control-value carriers below; they are created and owned by alsa-lib in the client address space, copied into kernel memory for the duration of one ioctl, and then released.

| UCM operation | ioctl | handler | carrier object |
|---------------|-------|---------|----------------|
| `cset` (write a value) | [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) | [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320) | [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) |
| `cget` (read current value) | [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203) | [`snd_ctl_elem_read_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244) | [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) |
| resolve a name, get range | [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) | [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172) | [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) |
| enumerate all controls | [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201) | [`snd_ctl_elem_list_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922) | [`struct snd_ctl_elem_list`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1130) |

The control objects the ioctls resolve to are kernel-owned and outlive any single client.

| object | created by | lifetime |
|--------|-----------|----------|
| [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) | filled by alsa-lib from a `cset`/`cget` identifier; stamped into a control at registration by [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) and [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) | the client copy lives for one ioctl; the copy embedded in a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) lives as long as the control is on the card |
| [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) | allocated by alsa-lib, duplicated into the kernel by [`memdup_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/string.h) in [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320) | one ioctl; freed by [`__free(kfree)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cleanup.h) when the handler returns |
| [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) from a template, or [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) from a topology record | from [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) until the card or component is removed |

## DETAILS

### cset and cget reach the element write and read ioctls

The control device is one character device per card, registered by [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) with the file operations in [`snd_ctl_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2266). UCM reaches it as /dev/snd/controlCx, and every `cset` and `cget` is an ioctl on this file:

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

[`snd_ctl_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1899) is the [`unlocked_ioctl`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2273). It recovers the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) and the card from the open file, then switches on the command. The element commands a UCM client uses each forward the userspace argument pointer to a dedicated handler. A `cset` is [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) and a `cget` is [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203):

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
	...
	case SNDRV_CTL_IOCTL_ELEM_LIST:
		return snd_ctl_elem_list_user(card, argp);
	case SNDRV_CTL_IOCTL_ELEM_INFO:
		return snd_ctl_elem_info_user(ctl, argp);
	case SNDRV_CTL_IOCTL_ELEM_READ:
		return snd_ctl_elem_read_user(card, argp);
	case SNDRV_CTL_IOCTL_ELEM_WRITE:
		return snd_ctl_elem_write_user(ctl, argp);
	...
	}
	...
}
```

A UCM session begins by enumerating the card. [`SNDRV_CTL_IOCTL_ELEM_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1201) returns the id of every control through [`snd_ctl_elem_list_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L922), and [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) resolves a name to its type, range, and access through [`snd_ctl_elem_info_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1172). Those let alsa-lib confirm that a control named in a `cset` exists and clamp a value to its range before writing. A `cget` reads the current value back through [`snd_ctl_elem_read_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1244), which is the read symmetric of the write path. The selection itself is the write path.

### snd_ctl_elem_write_user copies the value in and out

A `cset` arrives as [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) with a pointer to a userspace [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168). [`snd_ctl_elem_write_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1320) duplicates that structure into the kernel with [`memdup_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/string.h), waits for the card to be powered with [`snd_power_ref_and_wait()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c), calls [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267), and copies the (possibly adjusted) value back so the client sees what was actually applied:

```c
/* sound/core/control.c:1320 */
static int snd_ctl_elem_write_user(struct snd_ctl_file *file,
				   struct snd_ctl_elem_value __user *_control)
{
	struct snd_card *card;
	int result;
	struct snd_ctl_elem_value *control __free(kfree) =
		memdup_user(_control, sizeof(*control));

	if (IS_ERR(control))
		return PTR_ERR(control);

	card = file->card;
	result = snd_power_ref_and_wait(card);
	if (result < 0)
		return result;
	result = snd_ctl_elem_write(card, file, control);
	snd_power_unref(card);
	if (result < 0)
		return result;

	if (copy_to_user(_control, control, sizeof(*control)))
		return -EFAULT;
	return result;
}
```

The duplicated [`struct snd_ctl_elem_value`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1168) carries both the address and the data. Its first member is the [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) that names the control, and the value union holds the parsed `cset` argument:

```c
/* include/uapi/sound/asound.h:1168 */
struct snd_ctl_elem_value {
	struct snd_ctl_elem_id id;	/* W: element ID */
	unsigned int indirect: 1;	/* W: indirect access - obsoleted */
	union {
		union {
			long value[128];
			long *value_ptr;	/* obsoleted */
		} integer;
		union {
			long long value[64];
			long long *value_ptr;	/* obsoleted */
		} integer64;
		union {
			unsigned int item[128];
			unsigned int *item_ptr;	/* obsoleted */
		} enumerated;
		union {
			unsigned char data[512];
			unsigned char *data_ptr;	/* obsoleted */
		} bytes;
		struct snd_aes_iec958 iec958;
	} value;		/* RO */
	unsigned char reserved[128];
};
```

For `cset "name='Headphone Switch' on"` the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) is the string `Headphone Switch`, [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) is 0, and `value.integer.value[0]` is 1. For `cset "name='FU05 Playback Volume' 87 87"` the name is `FU05 Playback Volume` and `value.integer.value[0]` and `[1]` are both 87, one per channel.

```
    struct snd_ctl_elem_value: the cset/cget payload
    ───────────────────────────────────────────────────

    ┌────────────────────────────────────────────────┐
    │ struct snd_ctl_elem_id id   names the control  │
    ├────────────────────────────────────────────────┤
    │ union value  (exactly one arm carries data):   │
    │   integer.value[128]     long       volume     │
    │   integer64.value[64]    long long             │
    │   enumerated.item[128]   unsigned   enum item  │
    │   bytes.data[512]        unsigned char         │
    │   iec958                 struct                │
    └────────────────────────────────────────────────┘
```

### snd_ctl_elem_write resolves the id and runs the put callback

[`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) is where the `cset` binds to a kernel control. It takes [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write, calls [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) to map the id to a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), rejects the write with `-EPERM` if the control is not writable or holds no [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callback or is locked by another file, and finally invokes [`kctl->put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76):

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

	snd_ctl_build_ioff(&control->id, kctl, index_offset);
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

A control may hold several elements, so [`snd_ctl_get_ioff()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L198) computes the element offset from the id and [`snd_ctl_build_ioff()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L207) writes the resolved [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127) back into the id before the callback runs. When [`kctl->put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) returns a value greater than zero the control changed, and [`snd_ctl_notify_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L200) posts a [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) event so any other reader (a mixer GUI, a second UCM consumer) sees the new setting.

### snd_ctl_find_id matches the cset name to a control

[`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) is the name-to-object lookup. A `cset` supplies the name form, so [`id->numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) is 0 and the function uses the name hash under [`CONFIG_SND_CTL_FAST_LOOKUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig), falling back to a linear walk of [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) only when the hash records a collision:

```c
/* sound/core/control.c:840 */
struct snd_kcontrol *snd_ctl_find_id(struct snd_card *card,
				     const struct snd_ctl_elem_id *id)
{
	struct snd_kcontrol *kctl;

	if (snd_BUG_ON(!card || !id))
		return NULL;

	if (id->numid != 0)
		return snd_ctl_find_numid(card, id->numid);
#ifdef CONFIG_SND_CTL_FAST_LOOKUP
	kctl = xa_load(&card->ctl_hash, get_ctl_id_hash(id));
	if (kctl && elem_id_matches(kctl, id))
		return kctl;
	if (!card->ctl_hash_collision)
		return NULL; /* we can rely on only hash table */
#endif
	/* no matching in hash table - try all as the last resort */
	guard(read_lock_irqsave)(&card->controls_rwlock);
	list_for_each_entry(kctl, &card->controls, list)
		if (elem_id_matches(kctl, id))
			return kctl;

	return NULL;
}
```

The match compares the id tuple against each control's stored [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121). That id is set once when the control is created, so the string a UCM `cset` names is exactly the string a driver or topology put into [`id.name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126). The id structure carries the name, the interface, and the indices that disambiguate same-named controls on different devices:

```c
/* include/uapi/sound/asound.h:1121 */
struct snd_ctl_elem_id {
	unsigned int numid;		/* numeric identifier, zero = invalid */
	snd_ctl_elem_iface_t iface;	/* interface identifier */
	unsigned int device;		/* device/client number */
	unsigned int subdevice;		/* subdevice (substream) number */
	unsigned char name[SNDRV_CTL_ELEM_ID_NAME_MAXLEN];		/* ASCII name of item */
	unsigned int index;		/* index of item */
};
```

A `cset` that gives only `name=` matches on [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127), and alsa-lib defaults the interface to [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), value 2, which is the interface every ASoC mixer and DAPM control carries. The 44-byte [`SNDRV_CTL_ELEM_ID_NAME_MAXLEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1119) bound applies on both sides, so a UCM name that reaches the limit cannot match, and the topology loader rejects any control name that fills the field.

```
    snd_ctl_find_id: a cset id ─▶ one snd_kcontrol
    ────────────────────────────────────────────────

    struct snd_ctl_elem_id (from the cset)
    ┌────────────────────────────────────────┐
    │ numid    0 when the cset gives name=   │
    │ iface    IFACE_MIXER (value 2)         │
    │ device / subdevice / index             │
    │ name     "Headphone Switch"            │
    └────────────────────┬───────────────────┘
                         │
              numid != 0 │ numid == 0 (name form)
            ┌────────────┴────────────┐
            ▼                         ▼
    snd_ctl_find_numid        xa_load(ctl_hash, hash(id))
    (direct numid map)        match name+iface+dev+index
            │                         │ miss + collision
            │                         ▼
            │                 linear walk card->controls
            └────────────┬────────────┘
                         ▼
                  struct snd_kcontrol  (run kctl->put)
```

### The live control and the template it comes from

The object [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) returns is a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70). It holds the id a UCM `cset` matches, the element [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72), and the three callbacks the control interface drives:

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

A driver does not build this directly. It writes a static [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template that names the control and points at the callbacks, and the core copies the template into a live control at registration. [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) performs the copy. It transfers [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L48), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L49), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L50), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51), and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L52) from the template into the control's id, defaulting [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L53) to read/write and [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L54) to one:

```c
/* sound/core/control.c:260 */
struct snd_kcontrol *snd_ctl_new1(const struct snd_kcontrol_new *ncontrol,
				  void *private_data)
{
	struct snd_kcontrol *kctl;
	unsigned int count;
	unsigned int access;
	int err;
	...
	/* The 'numid' member is decided when calling snd_ctl_add(). */
	kctl->id.iface = ncontrol->iface;
	kctl->id.device = ncontrol->device;
	kctl->id.subdevice = ncontrol->subdevice;
	if (ncontrol->name) {
		strscpy(kctl->id.name, ncontrol->name, sizeof(kctl->id.name));
		if (strcmp(ncontrol->name, kctl->id.name) != 0)
			pr_warn("ALSA: Control name '%s' truncated to '%s'\n",
				ncontrol->name, kctl->id.name);
	}
	kctl->id.index = ncontrol->index;

	kctl->info = ncontrol->info;
	kctl->get = ncontrol->get;
	kctl->put = ncontrol->put;
	kctl->tlv.p = ncontrol->tlv.p;

	kctl->private_value = ncontrol->private_value;
	kctl->private_data = private_data;

	return kctl;
}
```

The comment "The 'numid' member is decided when calling snd_ctl_add()" marks the split between identity that comes from the template (the name) and identity that the card assigns (the [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122)). [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) is a thin wrapper over [`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509), and the locked core [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) links the control and stamps the numid:

```c
/* sound/core/control.c:458 */
	scoped_guard(write_lock_irq, &card->controls_rwlock) {
		list_add_tail(&kcontrol->list, &card->controls);
		card->controls_count += kcontrol->count;
		kcontrol->id.numid = card->last_numid + 1;
		card->last_numid += kcontrol->count;
	}

	add_hash_entries(card, kcontrol);
```

The control joins [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105), gets a [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122), and its name is entered into the hash that [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) later searches. After this point a UCM `cset` naming that string resolves to this control.

```
    template ─▶ live control: where each id field comes from
    ──────────────────────────────────────────────────────────

    struct snd_kcontrol_new            struct snd_kcontrol
    (static template)                  (live control on card)
    ┌─────────────────────┐            ┌─────────────────────────┐
    │ iface               │ snd_ctl_   │ id.iface                │
    │ device, subdevice   │ new1()     │ id.device, id.subdevice │
    │ name  ──────────────┼───────────▶│ id.name  (cset matches) │
    │ index               │  copies    │ id.index                │
    │ info / get / put    │            │ info / get / put        │
    └─────────────────────┘            │ id.numid ◀─ assigned    │
                                       └────────────┬────────────┘
                                                    │ snd_ctl_add()
                                                    ▼
                                   card->last_numid + 1 (card sets)
```

### The SOF topology creates the named controls

On an x86-64 ACPI SoundWire card the Sound Open Firmware loader parses a topology binary and creates its controls there. [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973) walks the control elements in a topology header and dispatches each by type, mixer controls (a volume) toward [`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637), enums toward the enum creator, and bytes toward the bytes creator:

```c
/* sound/soc/soc-topology.c:973 */
static int soc_tplg_kcontrol_elems_load(struct soc_tplg *tplg,
	struct snd_soc_tplg_hdr *hdr)
{
	int ret;
	int i;
	...
	for (i = 0; i < le32_to_cpu(hdr->count); i++) {
		struct snd_soc_tplg_ctl_hdr *control_hdr = (struct snd_soc_tplg_ctl_hdr *)tplg->pos;
		...
		switch (le32_to_cpu(control_hdr->type)) {
		case SND_SOC_TPLG_TYPE_MIXER:
			ret = soc_tplg_dmixer_create(tplg, le32_to_cpu(hdr->payload_size));
			break;
		case SND_SOC_TPLG_TYPE_ENUM:
			ret = soc_tplg_denum_create(tplg, le32_to_cpu(hdr->payload_size));
			break;
		case SND_SOC_TPLG_TYPE_BYTES:
			ret = soc_tplg_dbytes_create(tplg, le32_to_cpu(hdr->payload_size));
			break;
		default:
			ret = -EINVAL;
			break;
		}
		...
	}

	return 0;
}
```

The mixer path reaches [`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637), which copies the name straight out of the binary into the template and sets the interface to [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), rejecting up front any name that fills the 44-byte field:

```c
/* sound/soc/soc-topology.c:637 */
static int soc_tplg_control_dmixer_create(struct soc_tplg *tplg, struct snd_kcontrol_new *kc)
{
	struct snd_soc_tplg_mixer_control *mc;
	struct soc_mixer_control *sm;
	int err;

	mc = (struct snd_soc_tplg_mixer_control *)tplg->pos;

	/* validate kcontrol */
	if (strnlen(mc->hdr.name, SNDRV_CTL_ELEM_ID_NAME_MAXLEN) == SNDRV_CTL_ELEM_ID_NAME_MAXLEN)
		return -EINVAL;
	...
	kc->name = devm_kstrdup(tplg->dev, mc->hdr.name, GFP_KERNEL);
	if (!kc->name)
		return -ENOMEM;
	kc->private_value = (long)sm;
	kc->iface = SNDRV_CTL_ELEM_IFACE_MIXER;
	kc->access = le32_to_cpu(mc->hdr.access);
	...
	/* map io handlers */
	err = soc_tplg_kcontrol_bind_io(&mc->hdr, kc, tplg);
	...
}
```

The name in the topology binary becomes [`kc->name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51), and [`soc_tplg_kcontrol_bind_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459) attaches the get/put/info handlers by matching the op ids the topology declares against the vendor and standard handler tables. [`soc_tplg_add_dcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311) then turns the filled template into a live control:

```c
/* sound/soc/soc-topology.c:311 */
static int soc_tplg_add_dcontrol(struct snd_card *card, struct device *dev,
	const struct snd_kcontrol_new *control_new, const char *prefix,
	void *data, struct snd_kcontrol **kcontrol)
{
	int err;

	*kcontrol = snd_soc_cnew(control_new, data, control_new->name, prefix);
	if (*kcontrol == NULL) {
		dev_err(dev, "ASoC: Failed to create new kcontrol %s\n",
		control_new->name);
		return -ENOMEM;
	}

	err = snd_ctl_add(card, *kcontrol);
	if (err < 0) {
		dev_err(dev, "ASoC: Failed to add %s: %d\n",
			control_new->name, err);
		return err;
	}

	return 0;
}
```

[`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) is the ASoC wrapper that applies an optional name prefix and then calls [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), so a topology control follows the same template-to-control path as a native driver control and lands on [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) through [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546). The name string in the SOF topology file is therefore the contract the matching UCM `cset` relies on.

### A pin switch on a SoundWire card

The other source of names is the ASoC machine and codec drivers. A pin switch is built by the [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) macro, which names the control `"<name> Switch"`, sets [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) to [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), stores the bare pin name in [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62), and wires the DAPM pin callbacks:

```c
/* include/sound/soc-dapm.h:369 */
#define SOC_DAPM_PIN_SWITCH(xname) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname " Switch", \
	.info = snd_soc_dapm_info_pin_switch, \
	.get = snd_soc_dapm_get_pin_switch, \
	.put = snd_soc_dapm_put_pin_switch, \
	.private_value = (unsigned long)xname }
```

On an x86-64 ACPI SoundWire card the generic SoundWire machine driver in [`sound/soc/sdw_utils/soc_sdw_utils.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c) adds these per-jack and per-speaker switches. For an rt700/rt711-class jack codec it adds the [`'\<rt700_controls\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L68) set, which names `Headphones`, `AMIC`, and `Speaker`, producing controls `Headphones Switch`, `AMIC Switch`, and `Speaker Switch`:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:68 */
static const struct snd_kcontrol_new rt700_controls[] = {
	SOC_DAPM_PIN_SWITCH("Headphones"),
	SOC_DAPM_PIN_SWITCH("AMIC"),
	SOC_DAPM_PIN_SWITCH("Speaker"),
};
```

The boolean shape of the switch comes from [`snd_soc_dapm_info_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3638), which an [`SNDRV_CTL_IOCTL_ELEM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1202) on the control returns, so alsa-lib knows the value is a single [`SNDRV_CTL_ELEM_TYPE_BOOLEAN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1077) with a 0 to 1 range:

```c
/* sound/soc/soc-dapm.c:3638 */
int snd_soc_dapm_info_pin_switch(struct snd_kcontrol *kcontrol,
				 struct snd_ctl_elem_info *uinfo)
{
	uinfo->type = SNDRV_CTL_ELEM_TYPE_BOOLEAN;
	uinfo->count = 1;
	uinfo->value.integer.min = 0;
	uinfo->value.integer.max = 1;

	return 0;
}
```

When a sof-soundwire UCM device runs `cset "name='Headphones Switch' on"`, [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) calls that control's [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76), [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725), which recovers the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L23) with [`snd_kcontrol_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14), reads the pin name from [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62), and calls [`__dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3701):

```c
/* sound/soc/soc-dapm.c:3725 */
int snd_soc_dapm_put_pin_switch(struct snd_kcontrol *kcontrol,
				struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_card *card = snd_kcontrol_chip(kcontrol);
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	const char *pin = (const char *)kcontrol->private_value;

	return __dapm_put_pin_switch(dapm, pin, ucontrol);
}
```

[`__dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3701) reads the boolean from `ucontrol->value.integer.value[0]`, sets the pin's connected state with [`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932), and runs a DAPM power scan with [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005), so writing 1 to `Headphones Switch` powers up the headphone path:

```c
/* sound/soc/soc-dapm.c:3701 */
static int __dapm_put_pin_switch(struct snd_soc_dapm_context *dapm,
				 const char *pin,
				 struct snd_ctl_elem_value *ucontrol)
{
	int ret;

	snd_soc_dapm_mutex_lock(dapm);
	ret = __dapm_set_pin(dapm, pin, !!ucontrol->value.integer.value[0]);
	snd_soc_dapm_mutex_unlock(dapm);

	snd_soc_dapm_sync(dapm);

	return ret;
}
```

[`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932) finds the named widget, marks it dirty and invalidates its input and output paths if the connected state changed, and returns 1 on a change. That return propagates back through [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725) as the `put` result, so [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) emits a change event when a `cset` actually toggled the pin:

```c
/* sound/soc/soc-dapm.c:2932 */
static int __dapm_set_pin(struct snd_soc_dapm_context *dapm,
			  const char *pin, int status)
{
	struct snd_soc_dapm_widget *w = dapm_find_widget(dapm, pin, true);
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	int ret = 0;

	dapm_assert_locked(dapm);

	if (!w) {
		dev_err(dev, "ASoC: DAPM unknown pin %s\n", pin);
		return -EINVAL;
	}

	if (w->connected != status) {
		dapm_mark_dirty(w, "pin configuration");
		dapm_widget_invalidate_input_paths(w);
		dapm_widget_invalidate_output_paths(w);
		ret = 1;
	}

	w->connected = status;
	if (status == 0)
		w->force = 0;

	return ret;
}
```

The macro splits each bare name into the two strings the put path uses, the control name carrying an appended Switch and the private_value holding the plain pin the setter looks up:

```
    SOC_DAPM_PIN_SWITCH: pin name ─▶ control name ─▶ DAPM pin
    ───────────────────────────────────────────────────────────
    (rt700_controls; the macro appends " Switch" to each name)

    macro arg          control id.name        private_value (pin)
    ───────────────────────────────────────────────────────────────
    "Headphones"   ─▶  "Headphones Switch" ─▶  pin "Headphones"
    "AMIC"         ─▶  "AMIC Switch"       ─▶  pin "AMIC"
    "Speaker"      ─▶  "Speaker Switch"    ─▶  pin "Speaker"
    ───────────────────────────────────────────────────────────────
      cset name= matches id.name (iface = MIXER), runs put =
      snd_soc_dapm_put_pin_switch ─▶ __dapm_set_pin(pin) ─▶ sync
```

### A volume on a SoundWire/SDCA codec

The volume a UCM device sets is a codec control. The rt711-sdca codec, a SoundWire jack codec, declares its controls in [`rt711_sdca_snd_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L866), including the playback gain built with [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282):

```c
/* sound/soc/codecs/rt711-sdca.c:866 */
static const struct snd_kcontrol_new rt711_sdca_snd_controls[] = {
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_USER_FU05, RT711_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_USER_FU05, RT711_SDCA_CTL_FU_VOLUME, CH_R),
		0x57, 0x57, 0,
		rt711_sdca_set_gain_get, rt711_sdca_set_gain_put, out_vol_tlv),
	...
};
```

The control is named `FU05 Playback Volume`, and because [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282) is a left/right pair its info handler reports two values, so a UCM `cset "name='FU05 Playback Volume' 87 87"` fills `value.integer.value[0]` and `[1]` with 87. [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1267) runs the [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) the macro wired, [`rt711_sdca_set_gain_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L554), which clamps each channel to [`mc->max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h), converts the control value to the SDCA two's-complement gain encoding, and writes it over SoundWire, returning 1 when the stored value changed:

```c
/* sound/soc/codecs/rt711-sdca.c:554 */
static int rt711_sdca_set_gain_put(struct snd_kcontrol *kcontrol,
		struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	struct rt711_sdca_priv *rt711 = snd_soc_component_get_drvdata(component);
	unsigned int read_l, read_r, gain_l_val, gain_r_val;
	unsigned int i, adc_vol_flag = 0, changed = 0;
	unsigned int lvalue, rvalue;
	...
	/* L Channel */
	gain_l_val = ucontrol->value.integer.value[0];
	if (gain_l_val > mc->max)
		gain_l_val = mc->max;
	...
	if (lvalue != gain_l_val || rvalue != gain_r_val)
		changed = 1;
	else
		return 0;

	for (i = 0; i < 3; i++) { /* retry 3 times at most */
		/* Lch*/
		regmap_write(rt711->mbq_regmap, mc->reg, gain_l_val);

		/* Rch */
		regmap_write(rt711->mbq_regmap, mc->rreg, gain_r_val);
		...
	}

	return i == 3 ? -EIO : changed;
}
```

The [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) macro builds the single-channel variant of the same kind of volume control, also under [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), and wires the generic [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) rather than a codec-specific pair:

```c
/* include/sound/soc.h:71 */
#define SOC_SINGLE_TLV(xname, reg, shift, max, invert, tlv_array) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.access = SNDRV_CTL_ELEM_ACCESS_TLV_READ |\
		 SNDRV_CTL_ELEM_ACCESS_READWRITE,\
	.tlv.p = (tlv_array), \
	.info = snd_soc_info_volsw, .get = snd_soc_get_volsw,\
	.put = snd_soc_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(reg, shift, 0, max, invert, 0) }
```

[`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) recovers the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h) from [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62) and writes the clamped value through the component's register map, the generic counterpart to the codec-specific [`rt711_sdca_set_gain_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L554):

```c
/* sound/soc/soc-ops.c:396 */
int snd_soc_put_volsw(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int mask = soc_mixer_mask(mc);

	return soc_put_volsw(kcontrol, ucontrol, mc, mask, mc->max - mc->min);
}
```

The whole EnableSequence is a list of such `cset` lines. Selecting the `Headphones` device on a sof-soundwire card runs the pin switch on, then the volume, then any routing enums the SOF topology created, and each one is a single [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) resolved by name to one control that the codec driver, the generic machine driver, or the topology placed on the card. The UCM file holds only the strings and values; the controls and their behavior are entirely in the kernel and the topology binary.

```
    UCM use-case hierarchy ─▶ a cset sequence ─▶ kcontrols
    ────────────────────────────────────────────────────────
    (each EnableSequence cset = one SNDRV_CTL_IOCTL_ELEM_WRITE)

    SectionVerb "HiFi"
        ├── SectionDevice "Headphones"
        │     EnableSequence (in order):
        │       ├─ cset "Headphones Switch" on ─▶ put pin switch
        │       ├─ cset "FU05 Playback Volume" 87 87 ─▶ put gain
        │       └─ cset <routing enum> ─▶ put enum (SOF topology)
        ├── SectionDevice "Speaker"
        │     EnableSequence: cset "Speaker Switch" on ─▶ ...
        └── SectionModifier ...
                EnableSequence: more cset lines

    each cset ─▶ snd_ctl_find_id by name ─▶ one kctl->put ─▶ hardware
```
