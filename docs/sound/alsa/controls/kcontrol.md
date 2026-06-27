# Control element construction (snd_kcontrol)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A driver describes one ALSA control element as a const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template, and [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) allocates a heap [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) from it. The template carries the interface, name, access bits, the info/get/put callbacks, an optional TLV channel, and one [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62) word. The runtime instance copies those fields and appends a [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) flexible array of per-element [`struct snd_kcontrol_volatile`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L65) entries, one for each of the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) identical elements, each holding the lock owner and the live access flags. The numeric id stays zero until [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) links the instance onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) under [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) and stamps [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) from [`card->last_numid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L100).

```
    const struct snd_kcontrol_new      (template, in a driver array)
    ┌───────────────────────────────────────────────────────────┐
    │ iface, name, index, access                                │
    │ info / get / put     tlv.p / tlv.c                        │
    │ private_value                                             │
    └───────────────────────────┬───────────────────────────────┘
                                │ snd_ctl_new1(template, private_data)
                                ▼  kzalloc_flex(.., vd, count)
    struct snd_kcontrol                (runtime instance, heap)
    ┌───────────────────────────────────────────────────────────┐
    │ list ─┐   id { numid, iface, device, subdevice, name, .. }│
    │ count │   info / get / put   tlv   private_value/_data    │
    │ vd[] __counted_by(count):                                 │
    │   ┌────────────────┬────────────────┬────────────────┐    │
    │   │ vd[0]          │ vd[1]          │ ... vd[count-1]│    │
    │   │ owner, access  │ owner, access  │                │    │
    │   └────────────────┴────────────────┴────────────────┘    │
    └───────┼───────────────────────────────────────────────────┘
            │ snd_ctl_add(card, kctl): numid = last_numid + 1
            ▼
    card->controls  ◀── list_add_tail ──  one node per control element
    (under controls_rwsem; lookup under controls_rwlock; numid addresses it)
```

## SUMMARY

A control element is one [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) registered directly on a [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) and reached through the single controlC%d device, so it carries no [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) of its own. A driver writes the const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template, and [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) turns it into a runtime instance. It defaults the access field to [`SNDRV_CTL_ELEM_ACCESS_READWRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1097) when the template leaves it zero, defaults the element [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to one, then copies the id fields, the three callbacks, the [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) pointer, and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81). The allocation underneath is [`snd_ctl_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228), which sizes the [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) flexible array to the element count and seeds every entry's access flags. The instance has no numeric id at this point, as the comment in [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) records that "The 'numid' member is decided when calling snd_ctl_add()".

[`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) forwards to [`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509) with [`CTL_ADD_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454), which takes [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write and runs [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) to link the instance onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) and assign [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) from [`card->last_numid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L100). [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618), [`snd_ctl_remove_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L637), and [`snd_ctl_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L566) unlink or swap an element, and [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323) runs the optional [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83) and frees an instance that was built but never added. Lookup runs through [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815), [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840), and the by-name wrapper [`snd_ctl_find_id_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L159), each reading under [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102). The info/get/put contract these elements run, the TLV channel, and the change-notification path are out of scope here and are documented alongside the value-movement code. The ASoC layer drives this same constructor from its `SOC_*` template macros, which expand to a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) that [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) clones through [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) and [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) registers with [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546).

## SPECIFICATIONS

The [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) object is a Linux kernel software construct and has no standalone hardware specification. The control element protocol it presents to userspace is the ALSA control ABI, defined by the uapi structures and ioctls in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The element identity is a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), the `SNDRV_CTL_ELEM_ACCESS_*` bits encode access rights, and the `SNDRV_CTL_ELEM_IFACE_*` values place an element on the mixer, on a PCM, or globally on the card.

## LINUX KERNEL

### Control element types (control.h, asound.h)

- [`'\<struct snd_kcontrol\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70): the runtime control element; holds the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) node, the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) callbacks, the [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L77) union, [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81)/[`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82)/[`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83), and the [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) flexible array
- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the const template a driver writes; holds [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L48), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L53), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L54), the info/get/put pointers, the [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L58) union, and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62)
- [`'\<struct snd_kcontrol_volatile\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L65): one [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) element; holds the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) control file and the per-element [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L67) flags
- [`'\<struct snd_ctl_elem_id\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121): the element identity; the [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) plus the ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple
- [`snd_kcontrol_chip`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14): the macro returning [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82) so a callback recovers its chip context
- [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) / [`SNDRV_CTL_ELEM_IFACE_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1089) / [`SNDRV_CTL_ELEM_IFACE_CARD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1086): the [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) values placing an element on the mixer, on a PCM, or globally

### Construction and allocation (control.c)

- [`'\<snd_ctl_new1\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260): build a runtime instance from a template, defaulting access and count, copying id/callbacks/tlv/private fields
- [`'\<snd_ctl_new\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228): the internal allocator [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) calls; sizes the [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) array to [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and seeds each element's access
- [`'\<snd_ctl_free_one\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323): run the optional [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83) and free an instance that was built but not added

### Add, remove, replace (control.c)

- [`'\<snd_ctl_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546): add an instance with [`CTL_ADD_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454), assigning the numid; frees the control if the add fails
- [`'\<snd_ctl_replace\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L566): replace an existing element, optionally adding it when absent
- [`'\<snd_ctl_add_replace\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509): take [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write and call [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458), freeing on error
- [`'\<__snd_ctl_add_replace\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458): link onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105), set [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) from [`card->last_numid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L100), and notify ADD per element
- [`'\<snd_ctl_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618): unlink one element and release it, taking the rwsem internally
- [`'\<snd_ctl_remove_id\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L637): find by [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) then remove
- [`'\<__snd_ctl_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L574): the locked remover, removing hash entries, unlinking under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102), and notifying REMOVE per element

### Lookup (control.c)

- [`'\<snd_ctl_find_numid\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815): find by numeric id, through the xarray when [`CONFIG_SND_CTL_FAST_LOOKUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig) is set
- [`'\<snd_ctl_find_id\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840): find by full id, dispatching to [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815) when [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) is set, otherwise matching the tuple
- [`'\<snd_ctl_find_id_mixer\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L159): the by-name wrapper that fills a [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) id and calls [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840)

### ALSA-core worked example (pcm_lib.c)

- [`'\<snd_pcm_add_chmap_ctls\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2583): build a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) on the stack, call [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), set [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83), and add the channel-map control

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter, covering the [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) definition and the [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260)/[`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) constructor pattern
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the naming convention (source, direction, function) the control [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51) field follows
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated API reference pulling kernel-doc from [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c)

## OTHER SOURCES

- [ALSA project library documentation, Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [ALSA project library documentation, High Level Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__HControl.html)
- [alsa-utils (amixer, alsactl)](https://github.com/alsa-project/alsa-utils)
- [`4e9652003bc3`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=4e9652003bc39032c3ab79e607aa3d1913c7cf57) ("ALSA: control: Annotate snd_kcontrol with __counted_by()") added the [`__counted_by(count)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) annotation on the [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) flexible array
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A control element is defined, built, attached, found, and torn down through a small helper set in [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c). A driver fills a const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), turns it into a runtime instance with [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), and hands that instance to [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546), which assigns the numeric id and links it onto the card. Lookups address an element by numid, by full id, or by name.

| Step | Function | Effect |
|------|----------|--------|
| define | const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) | a template carrying iface, name, access, info/get/put, [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62) |
| build | [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) | allocate the instance, default access/count, copy the template fields |
| allocate | [`snd_ctl_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228) | [`kzalloc_flex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) the struct plus its [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) elements |
| attach | [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) | link onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105), assign [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) |
| replace | [`snd_ctl_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L566) | swap an element, optionally adding it when absent |
| find (numid) | [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815) | resolve a numeric id to its [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) |
| find (id) | [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) | resolve a full [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) |
| find (name) | [`snd_ctl_find_id_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L159) | resolve a mixer control by name string |
| remove | [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) / [`snd_ctl_remove_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L637) | unlink one element and release it |
| free (unadded) | [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323) | run [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83) and free an instance never added |

## DETAILS

### The template and the runtime instance

A control begins as a const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), plain data that several cards can share. It names the interface the element appears on, the name and index, the access bits, the element [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L54), the three callbacks, an optional TLV channel, and a single [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62) word that a stateless handler reads to recover its per-control parameters:

```c
/* include/sound/control.h:47 */
struct snd_kcontrol_new {
	snd_ctl_elem_iface_t iface;	/* interface identifier */
	unsigned int device;		/* device/client number */
	unsigned int subdevice;		/* subdevice (substream) number */
	const char *name;		/* ASCII name of item */
	unsigned int index;		/* index of item */
	unsigned int access;		/* access rights */
	unsigned int count;		/* count of same elements */
	snd_kcontrol_info_t *info;
	snd_kcontrol_get_t *get;
	snd_kcontrol_put_t *put;
	union {
		snd_kcontrol_tlv_rw_t *c;
		const unsigned int *p;
	} tlv;
	unsigned long private_value;
};
```

The runtime [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) is the per-instance object. It mirrors the template's callbacks, tlv, and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81), replaces the template's plain [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L48)/[`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L51) fields with a full [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) whose [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) fills at add time, adds a [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L71) node and a [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82) chip pointer, and ends with a [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) flexible array:

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

One control element can represent several identical hardware controls. Their number is [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), and each gets its own per-element volatile slot in [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84). Each [`struct snd_kcontrol_volatile`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L65) holds the lock [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L66) (the control file that claimed a write lock) and the live [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L67) flags for that element:

```c
/* include/sound/control.h:65 */
struct snd_kcontrol_volatile {
	struct snd_ctl_file *owner;	/* locked */
	unsigned int access;	/* access rights */
};
```

The [`vd[] __counted_by(count)`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) annotation ties the array length to the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) field so the compiler's bounds-checking instrumentation knows how many entries the trailing array holds. The identity itself is the uapi [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), whose [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) is the fast handle and whose ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple is the stable address userspace uses:

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

The id whose layout this shows is one entry in the provenance table below, which marks each runtime field as copied from the template, resolved from a default, or created fresh like the numid and the chip pointer:

```
    snd_kcontrol_new field → snd_kcontrol field provenance
    ─────────────────────────────────────────────────────────

    template field          runtime field        origin
    ┌──────────────────────┬────────────────────┬────────────┐
    │ iface, device,       │ id.iface, .device, │ copied     │
    │ subdevice, name,     │ .subdevice, .name, │            │
    │ index                │ .index             │            │
    │ info / get / put     │ info / get / put   │ copied     │
    │ tlv.p                │ tlv.p              │ copied     │
    │ private_value        │ private_value      │ copied     │
    │ access (or default)  │ vd[*].access       │ resolved   │
    │ count (or 1)         │ count              │ resolved   │
    └──────────────────────┴────────────────────┴────────────┘
    created at runtime, no template source:
    ┌──────────────────────────────────────────────────────────┐
    │ list          card->controls node, linked by snd_ctl_add │
    │ id.numid      stamped at add time, zero until then       │
    │ private_data  the chip pointer passed to snd_ctl_new1    │
    │ private_free  optional, set by the caller after build    │
    │ vd[count]     snd_kcontrol_volatile { owner, access }    │
    └──────────────────────────────────────────────────────────┘
```

### snd_ctl_new1 builds the instance from the template

[`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) is the constructor. It reads the template's [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L54), substituting one when the field is zero, and the [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L53), substituting [`SNDRV_CTL_ELEM_ACCESS_READWRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1097) when the field is zero and then masking off any bits outside the permitted set. It calls [`snd_ctl_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228) to allocate, copies the id fields ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)), the callbacks, the [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) pointer, and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81), and stores the caller's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82). The comment marks where the numid is decided:

```c
/* sound/core/control.c:260 */
struct snd_kcontrol *snd_ctl_new1(const struct snd_kcontrol_new *ncontrol,
				  void *private_data)
{
	struct snd_kcontrol *kctl;
	unsigned int count;
	unsigned int access;
	int err;

	if (snd_BUG_ON(!ncontrol || !ncontrol->info))
		return NULL;

	count = ncontrol->count;
	if (count == 0)
		count = 1;

	access = ncontrol->access;
	if (access == 0)
		access = SNDRV_CTL_ELEM_ACCESS_READWRITE;
	access &= (SNDRV_CTL_ELEM_ACCESS_READWRITE |
		   SNDRV_CTL_ELEM_ACCESS_VOLATILE |
		   SNDRV_CTL_ELEM_ACCESS_INACTIVE |
		   SNDRV_CTL_ELEM_ACCESS_TLV_READWRITE |
		   SNDRV_CTL_ELEM_ACCESS_TLV_COMMAND |
		   SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK |
		   SNDRV_CTL_ELEM_ACCESS_LED_MASK |
		   SNDRV_CTL_ELEM_ACCESS_SKIP_CHECK);

	err = snd_ctl_new(&kctl, count, access, NULL);
	if (err < 0)
		return NULL;

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

The allocation is [`snd_ctl_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228), which uses [`kzalloc_flex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) to allocate the struct together with [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) trailing [`vd[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L84) elements, records the count, and seeds every element with the resolved access flags and the lock owner. The owner is NULL here and is set only when a [`file`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228) is given for a user-defined control:

```c
/* sound/core/control.c:228 */
static int snd_ctl_new(struct snd_kcontrol **kctl, unsigned int count,
		       unsigned int access, struct snd_ctl_file *file)
{
	unsigned int idx;

	if (count == 0 || count > MAX_CONTROL_COUNT)
		return -EINVAL;

	*kctl = kzalloc_flex(**kctl, vd, count);
	if (!*kctl)
		return -ENOMEM;

	(*kctl)->count = count;
	for (idx = 0; idx < count; idx++) {
		(*kctl)->vd[idx].access = access;
		(*kctl)->vd[idx].owner = file;
	}

	return 0;
}
```

An instance built but not added is released with [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323), which runs the optional [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83) before [`kfree`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h). The comment on the function reads "Don't call this after the control was added to the card", because a control already on the list is freed through the remove path instead:

```c
/* sound/core/control.c:323 */
void snd_ctl_free_one(struct snd_kcontrol *kcontrol)
{
	if (kcontrol) {
		if (kcontrol->private_free)
			kcontrol->private_free(kcontrol);
		kfree(kcontrol);
	}
}
```

Before any memory is taken, the constructor fixes count and access, a zero count becoming 1 and a zero access becoming READWRITE then masked down to the permitted bits that seed every vd[*].access:

```
    snd_ctl_new1: resolving access and count before allocation
    ────────────────────────────────────────────────────────────

    count  = ncontrol->count;   if 0 ▶ 1
    access = ncontrol->access;  if 0 ▶ SNDRV_CTL_ELEM_ACCESS_READWRITE
                                then  access &= permitted-bit set ▼
    ┌──────────────────────────────────────────────────────────┐
    │ SNDRV_CTL_ELEM_ACCESS_READWRITE                          │
    │ SNDRV_CTL_ELEM_ACCESS_VOLATILE                           │
    │ SNDRV_CTL_ELEM_ACCESS_INACTIVE                           │
    │ SNDRV_CTL_ELEM_ACCESS_TLV_READWRITE                      │
    │ SNDRV_CTL_ELEM_ACCESS_TLV_COMMAND                        │
    │ SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK                       │
    │ SNDRV_CTL_ELEM_ACCESS_LED_MASK                           │
    │ SNDRV_CTL_ELEM_ACCESS_SKIP_CHECK                         │
    └──────────────────────────────────────────────────────────┘
    any bit outside this set is dropped; snd_ctl_new(count, access)
    then seeds every vd[*].access with the result
```

### The numid is decided at add time

The element has no [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) until [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) puts it on the card. [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) is a thin forwarder that selects the exclusive mode, so an add fails when a matching id is already present:

```c
/* sound/core/control.c:546 */
int snd_ctl_add(struct snd_card *card, struct snd_kcontrol *kcontrol)
{
	return snd_ctl_add_replace(card, kcontrol, CTL_ADD_EXCLUSIVE);
}
```

[`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509) takes [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write and delegates to [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458). On any failure it frees the rejected control through [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323), so a caller never frees a control it handed to [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546):

```c
/* sound/core/control.c:509 */
static int snd_ctl_add_replace(struct snd_card *card,
			       struct snd_kcontrol *kcontrol,
			       enum snd_ctl_add_mode mode)
{
	int err = -EINVAL;

	if (! kcontrol)
		return err;
	if (snd_BUG_ON(!card || !kcontrol->info))
		goto error;

	scoped_guard(rwsem_write, &card->controls_rwsem)
		err = __snd_ctl_add_replace(card, kcontrol, mode);

	if (err < 0)
		goto error;
	return 0;

 error:
	snd_ctl_free_one(kcontrol);
	return err;
}
```

[`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) runs with the rwsem held for write. It looks for an existing element with [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840), rejecting a duplicate under [`CTL_ADD_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454) or removing the old one otherwise, then takes [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) to link the instance onto [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) and stamp [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) from [`card->last_numid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L100), advancing the counter by the element [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) so each sub-element gets a distinct id:

```c
/* sound/core/control.c:458 */
static int __snd_ctl_add_replace(struct snd_card *card,
				 struct snd_kcontrol *kcontrol,
				 enum snd_ctl_add_mode mode)
{
	struct snd_ctl_elem_id id;
	unsigned int idx;
	struct snd_kcontrol *old;
	int err;

	lockdep_assert_held_write(&card->controls_rwsem);

	id = kcontrol->id;
	if (id.index > UINT_MAX - kcontrol->count)
		return -EINVAL;

	old = snd_ctl_find_id(card, &id);
	if (!old) {
		if (mode == CTL_REPLACE)
			return -EINVAL;
	} else {
		if (mode == CTL_ADD_EXCLUSIVE) {
			dev_err(card->dev,
				"control %i:%i:%i:%s:%i is already present\n",
				id.iface, id.device, id.subdevice, id.name,
				id.index);
			return -EBUSY;
		}

		err = snd_ctl_remove_locked(card, old);
		if (err < 0)
			return err;
	}

	if (snd_ctl_find_hole(card, kcontrol->count) < 0)
		return -ENOMEM;

	scoped_guard(write_lock_irq, &card->controls_rwlock) {
		list_add_tail(&kcontrol->list, &card->controls);
		card->controls_count += kcontrol->count;
		kcontrol->id.numid = card->last_numid + 1;
		card->last_numid += kcontrol->count;
	}

	add_hash_entries(card, kcontrol);

	for (idx = 0; idx < kcontrol->count; idx++)
		snd_ctl_notify_one(card, SNDRV_CTL_EVENT_MASK_ADD, kcontrol, idx);

	return 0;
}
```

The id is the element's address. The numeric [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) is the fast handle assigned here, and the ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple is the human-readable address that survives across reboots and across topology changes. A mixer volume sits on [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088); a channel-map or per-stream control sits on [`SNDRV_CTL_ELEM_IFACE_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1089) and names the [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124) and [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125) it belongs to.

```
    numid assignment under controls_rwlock at add time
    ─────────────────────────────────────────────────────

    before:  card->last_numid = N

    list_add_tail(&kcontrol->list, &card->controls)
    kcontrol->id.numid = N + 1
    card->last_numid  += kcontrol->count     (count sub-elements)

    one control element with count = 3 reserves a numid run:
    ┌──────────────┬──────────────┬──────────────┐
    │ sub-element 0│ sub-element 1│ sub-element 2│
    │ numid = N+1  │ numid = N+2  │ numid = N+3  │
    └──────────────┴──────────────┴──────────────┘

    after:   card->last_numid = N + 3   (next control starts at N+4)

    the (iface, device, subdevice, name, index) tuple is the stable
    address; numid is the fast handle stamped only here
```

### Remove, replace, and the two locks

A registered element is removed with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618), which takes the rwsem for write and delegates to [`__snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L574). That function unlinks the element under [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102), notifies REMOVE for each sub-element, and frees the instance through [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323):

```c
/* sound/core/control.c:574 */
static int __snd_ctl_remove(struct snd_card *card,
			    struct snd_kcontrol *kcontrol,
			    bool remove_hash)
{
	unsigned int idx;

	lockdep_assert_held_write(&card->controls_rwsem);

	if (snd_BUG_ON(!card || !kcontrol))
		return -EINVAL;

	if (remove_hash)
		remove_hash_entries(card, kcontrol);

	scoped_guard(write_lock_irq, &card->controls_rwlock) {
		list_del(&kcontrol->list);
		card->controls_count -= kcontrol->count;
	}

	for (idx = 0; idx < kcontrol->count; idx++)
		snd_ctl_notify_one(card, SNDRV_CTL_EVENT_MASK_REMOVE, kcontrol, idx);
	snd_ctl_free_one(kcontrol);
	return 0;
}
```

[`snd_ctl_remove_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L637) does the same after resolving the element by id, and [`snd_ctl_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L566) routes through [`snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L509) with [`CTL_REPLACE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454) or [`CTL_ADD_ON_REPLACE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L454). The two locks divide the work by context. [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) is the sleeping lock guarding the list and the element values for add, remove, info, read, and write. [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) is the spinlock guarding the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) list traversal and the [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) walk on the notification path, which can run in atomic context. A driver recovers its chip context inside a callback through [`snd_kcontrol_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14), which returns [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82):

```c
/* include/sound/control.h:14 */
#define snd_kcontrol_chip(kcontrol) ((kcontrol)->private_data)
```

The two locks split by the context each runs in, the sleeping rwsem held across add, remove, and the value callbacks and the atomic-safe spinlock taken for the list walk and the notify fan-out:

```
    Two card locks divide the control work by context
    ────────────────────────────────────────────────────

    ┌─────────────────────────────┐  ┌─────────────────────────────┐
    │ card->controls_rwsem        │  │ card->controls_rwlock       │
    │ sleeping rwsem              │  │ spinlock, atomic-safe       │
    ├─────────────────────────────┤  ├─────────────────────────────┤
    │ guards the list and element │  │ guards the controls list    │
    │ values for:                 │  │ traversal and the ctl_files │
    │   add / remove              │  │ walk on:                    │
    │   info / read / write       │  │   the notify path           │
    └──────────────┬──────────────┘  └──────────────┬──────────────┘
                   ▼ held for write                 ▼ taken inside
    ┌─────────────────────────────┐  ┌─────────────────────────────┐
    │ __snd_ctl_add_replace       │  │ list_add_tail / list_del,   │
    │ __snd_ctl_remove            │  │ numid stamp, list walk in   │
    │ (link / unlink the element) │  │ snd_ctl_find_id fallback    │
    └─────────────────────────────┘  └─────────────────────────────┘
```

### Lookup by numid, full id, or name

A request addresses an element either by its numeric [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or by the ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1124), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1125), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple. [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) prefers the numid when it is non-zero, then tries the hash table under [`CONFIG_SND_CTL_FAST_LOOKUP`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/Kconfig), and falls back to a list walk under [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102):

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

In-kernel code that looks a control up by name uses [`snd_ctl_find_id_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L159), a wrapper that fills a [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) id from a name string and calls [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840):

```c
/* include/sound/control.h:159 */
static inline struct snd_kcontrol *
snd_ctl_find_id_mixer(struct snd_card *card, const char *name)
{
	struct snd_ctl_elem_id id = {};

	id.iface = SNDRV_CTL_ELEM_IFACE_MIXER;
	strscpy(id.name, name, sizeof(id.name));
	return snd_ctl_find_id(card, &id);
}
```

That wrapper feeds a filled-in id to the resolver, which takes the numid straight to the numeric lookup when it is set and otherwise tries the hash table before falling back to a list walk under controls_rwlock:

```
    snd_ctl_find_id: which resolution path a lookup key takes
    ───────────────────────────────────────────────────────────

    lookup key                   resolution
    ┌──────────────────────────┬─────────────────────────────────┐
    │ id.numid != 0            │ snd_ctl_find_numid(numid)       │
    │ numid == 0, hash hit     │ xa_load(ctl_hash) + id match    │
    │ numid == 0, no collision │ NULL, hash is authoritative     │
    │ numid == 0, fallback     │ walk list under controls_rwlock │
    └──────────────────────────┴─────────────────────────────────┘
    hash path active only under CONFIG_SND_CTL_FAST_LOOKUP

    by-name entry point:
    ┌──────────────────────────────────────────────────────────┐
    │ snd_ctl_find_id_mixer(card, name)                        │
    │   id.iface = SNDRV_CTL_ELEM_IFACE_MIXER                  │
    │   id.name  = name        ─▶  snd_ctl_find_id(card, &id)  │
    └──────────────────────────────────────────────────────────┘
```

### ALSA-core worked example: a PCM channel-map control

The clearest in-core example of building a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) without the SOC macros is [`snd_pcm_add_chmap_ctls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L2583), which gives a PCM stream a channel-map control. It builds a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) on the stack on the [`SNDRV_CTL_ELEM_IFACE_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1089) interface, marks it [`SNDRV_CTL_ELEM_ACCESS_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1095) plus [`SNDRV_CTL_ELEM_ACCESS_VOLATILE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1098) (the map varies with the open stream) plus a TLV read channel, and sets [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L54) to the substream count so one element covers every subdevice:

```c
/* sound/core/pcm_lib.c:2583 */
int snd_pcm_add_chmap_ctls(struct snd_pcm *pcm, int stream,
			   const struct snd_pcm_chmap_elem *chmap,
			   int max_channels,
			   unsigned long private_value,
			   struct snd_pcm_chmap **info_ret)
{
	struct snd_pcm_chmap *info;
	struct snd_kcontrol_new knew = {
		.iface = SNDRV_CTL_ELEM_IFACE_PCM,
		.access = SNDRV_CTL_ELEM_ACCESS_READ |
			SNDRV_CTL_ELEM_ACCESS_VOLATILE |
			SNDRV_CTL_ELEM_ACCESS_TLV_READ |
			SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK,
		.info = pcm_chmap_ctl_info,
		.get = pcm_chmap_ctl_get,
		.tlv.c = pcm_chmap_ctl_tlv,
	};
	int err;
	...
	knew.device = pcm->device;
	knew.count = pcm->streams[stream].substream_count;
	knew.private_value = private_value;
	info->kctl = snd_ctl_new1(&knew, info);
	if (!info->kctl) {
		kfree(info);
		return -ENOMEM;
	}
	info->kctl->private_free = pcm_chmap_ctl_private_free;
	err = snd_ctl_add(pcm->card, info->kctl);
	if (err < 0)
		return err;
	pcm->streams[stream].chmap_kctl = info->kctl;
	if (info_ret)
		*info_ret = info;
	return 0;
}
```

The sequence is the canonical one. [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) allocates the instance from the stack template with [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) as the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82); the caller attaches a [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L83) so the [`struct snd_pcm_chmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1463) wrapper is released when the control is; and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) links it onto [`pcm->card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L535) and assigns the numid. A driver that codecs build through the `SOC_*` macros produces the same [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) templates and reaches this same constructor.

### The ASoC layer builds these templates from SOC_* macros

A codec or machine driver in [`sound/soc/`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc) rarely writes a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) by hand. The `SOC_SINGLE`, `SOC_DOUBLE`, and `SOC_SINGLE_TLV` family of macros expand to one such template whose [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L76) are stock ASoC handlers and whose [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L62) packs a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) describing the register, shift, and range:

```c
/* include/sound/soc.h:61 */
#define SOC_SINGLE(xname, reg, shift, max, invert) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.info = snd_soc_info_volsw, .get = snd_soc_get_volsw,\
	.put = snd_soc_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(reg, shift, 0, max, invert, 0) }
```

These templates reach the core constructor through [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440), which copies the template, clears its [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L52), prepends the component name prefix to the control name, and hands the result to [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260):

```c
/* sound/soc/soc-core.c:2440 */
struct snd_kcontrol *snd_soc_cnew(const struct snd_kcontrol_new *_template,
				  void *data, const char *long_name,
				  const char *prefix)
{
	struct snd_kcontrol_new template;
	struct snd_kcontrol *kcontrol;
	char *name = NULL;

	memcpy(&template, _template, sizeof(template));
	template.index = 0;

	if (!long_name)
		long_name = template.name;

	if (prefix) {
		name = kasprintf(GFP_KERNEL, "%s %s", prefix, long_name);
		if (!name)
			return NULL;

		template.name = name;
	} else {
		template.name = long_name;
	}

	kcontrol = snd_ctl_new1(&template, data);

	kfree(name);

	return kcontrol;
}
```

The bulk-registration helper [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) walks an array of these templates and runs each through [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) followed by [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546), so the live element ASoC presents on the card is the same [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) any ALSA driver registers, only with its [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L81) carrying a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and its [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82) set to the owning [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207).
