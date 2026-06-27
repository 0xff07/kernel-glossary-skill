# ASoC kcontrol lifecycle

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ASoC mixer control begins life as a static [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template that a codec driver builds with a macro such as [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) or [`SOC_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110), each of which fills the template's [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) pointers with the generic handlers in [`soc-ops.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c) and packs the register address, bit shift, and value range into a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (or a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) for an enumerated control) reached through [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47). The template is const data that is held in the driver's `.controls` array and is shared by every card; nothing is instantiated until a component or the card probes. At probe, [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) walks that array and, for each template, calls [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) to copy the template into a runtime [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) via [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260), then hands that instance to [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546), which links it onto the underlying ALSA card's control list and assigns a numid. The control is freed when the card is freed by [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636). The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec on x86 SoundWire serves as the worked example, declaring its volume and switch controls in [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697) and registering them through its [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) component driver.

```
    SOC_SINGLE("Master Playback Volume", reg, shift, max, invert)
    ┌────────────────────────────────────────────────────────────┐
    │ struct snd_kcontrol_new   (const template, in .controls[]) │
    │   iface = SNDRV_CTL_ELEM_IFACE_MIXER                       │
    │   info  = snd_soc_info_volsw                               │
    │   get   = snd_soc_get_volsw   put = snd_soc_put_volsw      │
    │   private_value ─▶ struct soc_mixer_control { reg, shift,  │
    │                       min, max, invert }                   │
    └───────────────────────────┬────────────────────────────────┘
                                │ snd_soc_add_component_controls
                                │   ▶ snd_soc_cnew ▶ snd_ctl_new1
                                ▼
    ┌────────────────────────────────────────────────────────────┐
    │ struct snd_kcontrol       (runtime instance, kmalloc)      │
    │   id { iface, name, index, numid }                         │
    │   info / get / put  (copied from template)                 │
    │   private_value     (copied)   private_data = component    │
    └───────────────────────────┬────────────────────────────────┘
                                │ snd_ctl_add(card->snd_card, kcontrol)
                                ▼
    struct snd_card.controls  ◀── list_add_tail ──  one node per control
    (freed wholesale by snd_card_free at card teardown)
```

## SUMMARY

A control is described once as a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template and the control-definition macros are the standard way to write one. [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71), [`SOC_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L96), and [`SOC_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110) each expand to a brace-initialized template whose [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) is [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), whose [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) is [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332), whose [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) are [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396), and whose [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) is a pointer to a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) carrying the register, shift, min, and max. [`SOC_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229) and [`SOC_VALUE_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L221) do the same for an enumerated control, pointing [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) at a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273). [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) keeps [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) but lets the driver supply its own [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) for hardware the generic register access cannot reach.

The template array is named in the component driver's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) field and stays const, shared by every card that instantiates the codec. Instantiation happens at probe. [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) calls [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501), and card-wide controls go through [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521); both funnel into the static [`snd_soc_add_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2472), which loops over the array calling [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) per entry. [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) copies the template, applies the component name prefix, and calls [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) to allocate the runtime [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and copy the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) fields out of the template. [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) links the instance onto the ALSA card and assigns its numid. A static control is never freed individually; [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) releases the whole control list at card teardown. A topology-created control carries a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) inside its [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) so the topology layer can find and unload it when the firmware that created it is removed. The info/get/put handler bodies that the templates wire up are documented separately.

## SPECIFICATIONS

The [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) object is a Linux kernel software construct and has no standalone hardware specification. The control element protocol it presents to userspace (info, read, write, TLV) is the ALSA control API, and the dB-scale metadata a [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) control attaches is encoded in the ALSA TLV (Type-Length-Value) format from [`include/uapi/sound/tlv.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/tlv.h). On the x86 SoundWire path the register a control writes is an SDCA Control address built in the kernel by the [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) macro from a function, entity, control, and channel.

## LINUX KERNEL

### Control template and private types (control.h, soc.h)

- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the const template a driver writes; holds [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), the info/get/put pointers, and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)
- [`'\<struct snd_kcontrol\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70): the runtime instance allocated from the template; sits on the card control list via its [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) node and carries the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) with the assigned numid
- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231): the volume/switch private data reached through [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47); holds [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231)
- [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): the enumerated private data; holds [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`shift_r`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), and the optional [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) remap table
- [`'\<struct snd_soc_dobj\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61): the dynamic-object header embedded in a topology-created [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) or [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273); carries the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback, and a [`struct snd_soc_dobj_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) holding the back pointer to the created [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70)

### Control-definition macros (soc.h)

- [`'\<SOC_SINGLE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61): one-channel volume or switch in one register; expands to a template using the volsw handlers and a [`SOC_SINGLE_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L51) private value
- [`'\<SOC_SINGLE_TLV\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71): same as [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) plus a `tlv_array` for a dB scale and the [`SNDRV_CTL_ELEM_ACCESS_TLV_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1100) access bit
- [`'\<SOC_DOUBLE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L96): two channels packed into one register at `shift_left` and `shift_right`
- [`'\<SOC_DOUBLE_R\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110): two channels in two separate registers `reg_left` and `reg_right` at the same shift
- [`'\<SOC_ENUM\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229): an enumerated control over a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) declared with [`SOC_ENUM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L214) or [`SOC_ENUM_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L210)
- [`'\<SOC_VALUE_ENUM\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L221): an enumerated control whose item indices map to non-contiguous register values through the [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) table built by [`SOC_VALUE_ENUM_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L218)
- [`'\<SOC_SINGLE_EXT\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234): a single control with driver-supplied `xhandler_get` and `xhandler_put`, keeping [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) for the info callback
- [`'\<SOC_SINGLE_VALUE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L51): the helper that builds the compound-literal [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the single-channel macros place in [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)

### Registration and instantiation (soc-core.c, control.c)

- [`'\<snd_soc_add_component_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501): add a component's control array to the card under the component name prefix
- [`'\<snd_soc_add_card_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521): add a machine driver's card-wide control array with no prefix
- [`'\<snd_soc_add_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2472): the shared loop both helpers call, running [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) per template
- [`'\<snd_soc_cnew\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440): copy the template, build the prefixed long name, and allocate the runtime control through [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260)
- [`'\<snd_ctl_new1\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260): allocate the [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and copy [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) from the template
- [`'\<snd_ctl_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546): link the instance onto the card control list and assign its numid; frees the control automatically if the add fails
- [`'\<snd_ctl_free_one\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323): run the optional [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and free the instance, used on a control that was built but never added
- [`'\<snd_ctl_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618): unlink a single control from the card and release it, used when a topology unload removes one control
- [`'\<snd_card_free\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636): free the soundcard and with it every control on its list, the normal end of a static control's life

### Topology-created controls (soc-topology.c)

- [`'\<soc_tplg_dmixer_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905): build a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) from a firmware mixer block, tag the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) with [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35), and add it
- [`'\<soc_tplg_add_kcontrol\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335): create the runtime control for a topology mixer and store the back pointer in [`struct snd_soc_dobj_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49)

### rt722-sdca worked example (codecs/rt722-sdca.c, tas2783-sdw.c)

- [`'rt722_sdca_controls':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697): the [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) array of volume and switch controls the codec registers
- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) naming that array in its [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) field
- [`'tas2783_snd_controls':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L554): a TAS2783 amplifier control array using the single-channel range-EXT form

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA control element model, the info/get/put callbacks, and `snd_ctl_new1`/`snd_ctl_add`
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the naming convention (source, direction, function) the control [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) field follows
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide, where the `.controls` array is declared

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A control is instantiated through one of two registration helpers, distinguished by where the control belongs and what name prefix it gets. A component (a codec or platform) adds its own controls with [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501), which applies the component's name prefix so two instances of the same codec do not collide, and a machine driver adds card-global controls with [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521), which uses no prefix. Both reduce to a per-template call of [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) followed by [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546).

| Step | Function | Effect |
|------|----------|--------|
| define | `SOC_SINGLE` (macro) | const [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template in the driver's `.controls[]` |
| add (component) | [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) | loops the array, prefixes names with the component name |
| add (card) | [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521) | loops the array, no name prefix |
| build instance | [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) | copy template, build long name, call [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) |
| allocate | [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) | kmalloc the [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), copy info/get/put/private_value |
| attach | [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) | link onto `card->controls`, assign numid |
| free (static) | [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) | release the whole control list at card teardown |
| free (topology) | [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) via [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) `unload` | remove one control when its firmware is unloaded |

## DETAILS

### The template and its private value

A control template is plain const data. The [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) names the interface the control appears on, the three callbacks, an optional TLV pointer for a dB scale, and a single [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) word that the macros overload to carry a pointer to the per-control data:

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

For a volume or switch, [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) points at a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231). Its [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) name the register or registers, [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`rshift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the bit position per channel, [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the hardware value range, and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) whether a high register value is a low level:

```c
/* include/sound/soc.h:1231 */
struct soc_mixer_control {
	/* Minimum and maximum specified as written to the hardware */
	int min, max;
	/* Limited maximum value specified as presented through the control */
	int platform_max;
	int reg, rreg;
	unsigned int shift, rshift;
	u32 num_channels;
	unsigned int sign_bit;
	unsigned int invert:1;
	unsigned int autodisable:1;
	unsigned int sdca_q78:1;
#ifdef CONFIG_SND_SOC_TOPOLOGY
	struct snd_soc_dobj dobj;
#endif
};
```

For an enumerated control, [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) points at a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) instead. The [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) count and the [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) string array drive the info callback, [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) locate the field, and the optional [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) table maps each item index to a non-contiguous register value:

```c
/* include/sound/soc.h:1273 */
struct soc_enum {
	int reg;
	unsigned char shift_l;
	unsigned char shift_r;
	unsigned int items;
	unsigned int mask;
	const char * const *texts;
	const unsigned int *values;
	unsigned int autodisable:1;
#ifdef CONFIG_SND_SOC_TOPOLOGY
	struct snd_soc_dobj dobj;
#endif
};
```

The template's single private_value word casts to one of the two private structs the wired handlers expect, one carrying a volume or switch and the other an enumerated menu:

```
    private_value carries one of two private structs
    ──────────────────────────────────────────────────

    struct snd_kcontrol_new
    ┌────────────────────────────┐
    │ info / get / put           │
    │ private_value (one word)   │
    └──────────────┬─────────────┘
                   │ cast by the wired handlers
        ┌──────────┴───────────────────┐
        ▼                              ▼
    volume / switch                enumerated
    ┌──────────────────────┐   ┌──────────────────────┐
    │ struct               │   │ struct soc_enum      │
    │   soc_mixer_control  │   │   reg                │
    │   reg, rreg          │   │   shift_l, shift_r   │
    │   shift, rshift      │   │   items, mask        │
    │   min, max           │   │   texts[]            │
    │   platform_max       │   │   values[] (remap,   │
    │   sign_bit, invert   │   │     optional)        │
    └──────────────────────┘   └──────────────────────┘
     info=snd_soc_info_volsw    info=snd_soc_info_enum_double
```

### A control-definition macro expands to a template initializer

[`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) is a brace initializer for the template. It sets [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) to [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088), wires the three volsw handlers, and sets [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) to a [`SOC_SINGLE_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L51):

```c
/* include/sound/soc.h:61 */
#define SOC_SINGLE(xname, reg, shift, max, invert) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.info = snd_soc_info_volsw, .get = snd_soc_get_volsw,\
	.put = snd_soc_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(reg, shift, 0, max, invert, 0) }
```

[`SOC_SINGLE_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L51) is itself a thin wrapper that constructs the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) compound literal through [`SOC_DOUBLE_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L48) with both shifts equal, so a single control is a degenerate stereo control with one channel:

```c
/* include/sound/soc.h:42 */
#define SOC_DOUBLE_S_VALUE(xreg, shift_left, shift_right, xmin, xmax, xsign_bit, \
			   xinvert, xautodisable) \
	((unsigned long)&(struct soc_mixer_control) \
	{.reg = xreg, .rreg = xreg, .shift = shift_left, \
	.rshift = shift_right, .min = xmin, .max = xmax, \
	.sign_bit = xsign_bit, .invert = xinvert, .autodisable = xautodisable})
#define SOC_DOUBLE_VALUE(xreg, shift_left, shift_right, xmin, xmax, xinvert, xautodisable) \
	SOC_DOUBLE_S_VALUE(xreg, shift_left, shift_right, xmin, xmax, 0, xinvert, \
			   xautodisable)
#define SOC_SINGLE_VALUE(xreg, xshift, xmin, xmax, xinvert, xautodisable) \
	SOC_DOUBLE_VALUE(xreg, xshift, xshift, xmin, xmax, xinvert, xautodisable)
```

The variants change only which fields are set and which handlers are wired. [`SOC_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110) gives the two channels distinct registers with [`SOC_DOUBLE_R_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L58) so [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) differ, and [`SOC_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L71) adds a `tlv_array` and the [`SNDRV_CTL_ELEM_ACCESS_TLV_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1100) access bit so userspace can read the dB mapping, keeping the same three handlers as [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61):

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

[`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) keeps [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) for the info callback but substitutes the driver's own `xhandler_get` and `xhandler_put`, the path the rt722-sdca volume controls take because their register access is an SDCA command rather than a plain register write:

```c
/* include/sound/soc.h:234 */
#define SOC_SINGLE_EXT(xname, xreg, xshift, xmax, xinvert,\
	 xhandler_get, xhandler_put) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.info = snd_soc_info_volsw, \
	.get = xhandler_get, .put = xhandler_put, \
	.private_value = SOC_SINGLE_VALUE(xreg, xshift, 0, xmax, xinvert, 0) }
```

[`SOC_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229) takes a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) (commonly declared with [`SOC_ENUM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L214)) and points [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) at it, wiring the enum handlers instead:

```c
/* include/sound/soc.h:229 */
#define SOC_ENUM(xname, xenum) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname,\
	.info = snd_soc_info_enum_double, \
	.get = snd_soc_get_enum_double, .put = snd_soc_put_enum_double, \
	.private_value = (unsigned long)&xenum }
```

These macros line up in the table by what each fills, the handlers wired into info/get/put, the private struct under private_value, and the one differing extra, every row sharing iface MIXER:

```
    Which template slots each macro fills
    ───────────────────────────────────────

    macro            info / get / put         private_value   extra
    ┌──────────────┬───────────────────────┬───────────────┬─────────┐
    │ SOC_SINGLE   │ info_volsw            │ soc_mixer_    │ —       │
    │              │ get_volsw/put_volsw   │   control     │         │
    ├──────────────┼───────────────────────┼───────────────┼─────────┤
    │ SOC_SINGLE_  │ info_volsw            │ soc_mixer_    │ tlv.p,  │
    │   TLV        │ get_volsw/put_volsw   │   control     │ TLV_READ│
    ├──────────────┼───────────────────────┼───────────────┼─────────┤
    │ SOC_DOUBLE_R │ info_volsw            │ soc_mixer_    │ reg !=  │
    │              │ get_volsw/put_volsw   │   control     │ rreg    │
    ├──────────────┼───────────────────────┼───────────────┼─────────┤
    │ SOC_SINGLE_  │ info_volsw            │ soc_mixer_    │ driver  │
    │   EXT        │ driver get / put      │   control     │ get/put │
    ├──────────────┼───────────────────────┼───────────────┼─────────┤
    │ SOC_ENUM     │ info_enum_double      │ soc_enum      │ —       │
    │              │ get/put_enum_double   │ (&xenum)      │         │
    └──────────────┴───────────────────────┴───────────────┴─────────┘
     iface = SNDRV_CTL_ELEM_IFACE_MIXER for every row
```

### Instantiation copies the template into a runtime control

A component declares its template array in the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) field of its [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) hands that array to [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) during card binding. That helper resolves the component's ALSA card and passes the array, the component name prefix, and the component as the control private data into the shared [`snd_soc_add_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2472):

```c
/* sound/soc/soc-core.c:2501 */
int snd_soc_add_component_controls(struct snd_soc_component *component,
	const struct snd_kcontrol_new *controls, unsigned int num_controls)
{
	struct snd_card *card = component->card->snd_card;

	return snd_soc_add_controls(card, component->dev, controls,
			num_controls, component->name_prefix, component);
}
```

[`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521) is the machine-driver counterpart and differs only in passing a NULL prefix and the card itself as the private data. [`snd_soc_add_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2472) loops the array, and for each template builds the runtime control with [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and immediately adds it with [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546):

```c
/* sound/soc/soc-core.c:2472 */
static int snd_soc_add_controls(struct snd_card *card, struct device *dev,
	const struct snd_kcontrol_new *controls, int num_controls,
	const char *prefix, void *data)
{
	int i;

	for (i = 0; i < num_controls; i++) {
		const struct snd_kcontrol_new *control = &controls[i];
		int err = snd_ctl_add(card, snd_soc_cnew(control, data,
							 control->name, prefix));
		if (err < 0) {
			dev_err(dev, "ASoC: Failed to add %s: %d\n",
				control->name, err);
			return err;
		}
	}

	return 0;
}
```

[`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) copies the const template onto the stack, resets [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and when a prefix is present builds a prefixed long name with [`kasprintf()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sprintf.h) before calling [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) to produce the instance:

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

[`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) is where the runtime [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) is allocated. It defaults [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) to read-write and [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) to 1, copies the name into the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), and copies the [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) straight out of the template, setting [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to the component or card passed down:

```c
/* sound/core/control.c:260 */
struct snd_kcontrol *snd_ctl_new1(const struct snd_kcontrol_new *ncontrol,
				  void *private_data)
{
	struct snd_kcontrol *kctl;
	...
	/* The 'numid' member is decided when calling snd_ctl_add(). */
	kctl->id.iface = ncontrol->iface;
	kctl->id.device = ncontrol->device;
	kctl->id.subdevice = ncontrol->subdevice;
	if (ncontrol->name) {
		strscpy(kctl->id.name, ncontrol->name, sizeof(kctl->id.name));
		...
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

### Attaching to the ALSA card

[`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) links the finished instance onto the soundcard's control list and assigns the numid that lets userspace address it quickly. According to its kernel-doc, the function "frees automatically the control which cannot be added", so a failed add does not leak the instance [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) built:

```c
/* sound/core/control.c:546 */
int snd_ctl_add(struct snd_card *card, struct snd_kcontrol *kcontrol)
{
	return snd_ctl_add_replace(card, kcontrol, CTL_ADD_EXCLUSIVE);
}
```

After this point the control is on the underlying [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) control list and is reachable from userspace by name through alsa-lib amixer or any control client. A read calls the control's [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) op and a write its [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) op, both documented with the I/O handlers.

### Freeing: with the card, or one at a time

A statically registered control has no per-control free. [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) tears down the whole soundcard at the end of the device's life and releases every control on the list as part of that, so a codec never explicitly removes the controls it added at probe. According to its kernel-doc, [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) "releases the soundcard structure and the all assigned devices automatically", which includes the control interface. The single-control free path exists for the case where a control was built but never added. [`snd_ctl_free_one()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L323) runs the [`private_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) hook if one is set and frees the instance, and its kernel-doc warns "Don't call this after the control was added to the card", because an added control is owned by the card list and removed with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) instead:

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

The free path shown above is one exit from the states this figure walks, a template becoming a built instance, then an added control, then released wholesale at card teardown or singly on a topology unload:

```
    Lifecycle states of one control
    ──────────────────────────────────

    ┌────────────────────────────────────────────────┐
    │ TEMPLATE   const snd_kcontrol_new in .controls[]│
    │            shared, no instance, no numid        │
    └───────────────────────┬────────────────────────┘
                            ▼ snd_soc_cnew → snd_ctl_new1
    ┌────────────────────────────────────────────────┐
    │ BUILT      kmalloc snd_kcontrol, fields copied  │
    │            numid not yet assigned               │
    └───────────────────────┬────────────────────────┘
              ┌─────────────┴──────────────┐
   snd_ctl_add│ ok                  add fails / never added
              ▼                            ▼
    ┌──────────────────────┐    ┌──────────────────────────┐
    │ ADDED                │    │ snd_ctl_free_one          │
    │ on card->controls    │    │ (runs private_free, kfree)│
    │ numid assigned       │    └──────────────────────────┘
    └──────────┬───────────┘
       ┌───────┴────────────────────┐
       ▼ static                     ▼ topology
    snd_card_free                snd_ctl_remove
    (whole list at teardown)     (this one control, via dobj unload)
```

### Topology-created controls carry a dynamic-object header

A control created from a firmware topology file, rather than from a static C array, has to be removable on its own when the topology is unloaded. The topology layer threads a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) through the control's private data for exactly this. It records the object [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), an [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback, and a [`struct snd_soc_dobj_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) holding the back pointer to the created [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70):

```c
/* include/sound/soc-topology.h:61 */
struct snd_soc_dobj {
	enum snd_soc_dobj_type type;
	unsigned int index;	/* objects can belong in different groups */
	struct list_head list;
	int (*unload)(struct snd_soc_component *comp, struct snd_soc_dobj *dobj);
	union {
		struct snd_soc_dobj_control control;
		struct snd_soc_dobj_widget widget;
	};
	void *private; /* core does not touch this */
};
```

[`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) builds a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) on the stack from the firmware mixer block, tags the embedded [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) with [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35), records the component's `control_unload` op as the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback, then creates the control through [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335) and parks the dobj on the component's dobj list:

```c
/* sound/soc/soc-topology.c:905 */
static int soc_tplg_dmixer_create(struct soc_tplg *tplg, size_t size)
{
	struct snd_kcontrol_new kc = {0};
	struct soc_mixer_control *sm;
	int ret;
	...
	/* register dynamic object */
	sm = (struct soc_mixer_control *)kc.private_value;

	INIT_LIST_HEAD(&sm->dobj.list);
	sm->dobj.type = SND_SOC_DOBJ_MIXER;
	sm->dobj.index = tplg->index;
	if (tplg->ops)
		sm->dobj.unload = tplg->ops->control_unload;

	/* create control directly */
	ret = soc_tplg_add_kcontrol(tplg, &kc, &sm->dobj.control.kcontrol);
	if (ret < 0)
		return ret;

	list_add(&sm->dobj.list, &tplg->comp->dobj_list);

	return ret;
}
```

[`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335) is a thin shim onto the same [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) plus [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) pair used by the static path, and stores the resulting instance pointer in the dobj so the unload path can later remove that one control with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) without disturbing the rest of the card.

```
    Topology control: dobj links the private value to its kcontrol
    ────────────────────────────────────────────────────────────────

    struct soc_mixer_control       (the private_value data)
    ┌──────────────────────────────────────┐
    │ reg, shift, min, max ...             │
    │ struct snd_soc_dobj dobj  (embedded) │
    └──────────────────┬───────────────────┘
                       ▼  contains
    struct snd_soc_dobj
    ┌──────────────────────────────────────┐
    │ type   = SND_SOC_DOBJ_MIXER          │
    │ unload = tplg->ops->control_unload   │
    │ list             ──▶ comp->dobj_list │
    │ control.kcontrol (back pointer)      │
    └──────────────────┬───────────────────┘
                       ▼
    struct snd_kcontrol            (built by soc_tplg_add_kcontrol,
    ┌──────────────────────────────────────┐  the cnew + ctl_add pair)
    │ on card->controls list               │
    │ removed by snd_ctl_remove on unload  │
    └──────────────────────────────────────┘
```

### Worked example: rt722-sdca controls over x86 SoundWire

The Realtek RT722 is an SDCA codec reached over SoundWire on x86 ACPI platforms. It declares its mixer controls in the const array [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697), a mix of capture switches and dB-scaled volume controls. The volume controls use `SOC_DOUBLE_R_EXT_TLV` because an SDCA volume is two separate per-channel Control addresses (computed by the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) helper) and the register access is an SDCA command, so the codec supplies its own [`rt722_sdca_set_gain_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419) and [`rt722_sdca_set_gain_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L348) handlers in place of the generic volsw ones while still attaching a TLV array for the dB scale:

```c
/* sound/soc/codecs/rt722-sdca.c:697 */
static const struct snd_kcontrol_new rt722_sdca_controls[] = {
	/* Headphone playback settings */
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_R), 0, 0x57, 0,
		rt722_sdca_set_gain_get, rt722_sdca_set_gain_put, out_vol_tlv),
	/* Headset mic capture settings */
	SOC_DOUBLE_EXT("FU0F Capture Switch", SND_SOC_NOPM, 0, 1, 1, 0,
		rt722_sdca_fu0f_capture_get, rt722_sdca_fu0f_capture_put),
	...
};
```

The array is named in the codec's [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090), through the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) and [`num_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) fields, which is the array [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) feeds to [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) when the SoundWire card binds this codec:

```c
/* sound/soc/codecs/rt722-sdca.c:1090 */
static const struct snd_soc_component_driver soc_sdca_dev_rt722 = {
	.probe = rt722_sdca_probe,
	.controls = rt722_sdca_controls,
	.num_controls = ARRAY_SIZE(rt722_sdca_controls),
	.dapm_widgets = rt722_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt722_sdca_dapm_widgets),
	.dapm_routes = rt722_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt722_sdca_audio_map),
	.set_jack = rt722_sdca_set_jack_detect,
	.endianness = 1,
};
```

Because each control's name is prefixed with the codec's component name during [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440), a "FU05 Playback Volume" control on this codec appears to userspace under the prefixed long name, which keeps two SoundWire codecs of the same model on one card from colliding. The controls live until the SoundWire card is freed, at which point [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) releases them with the rest of the card's control list. The Texas Instruments [`tas2783_snd_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L554) array uses the single-channel range-EXT form for the same reason, registered the same way through its component driver's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) field, so the EXT variant changes only which handlers run while keeping the registration and teardown path identical.
