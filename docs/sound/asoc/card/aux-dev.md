# ASoC auxiliary device (snd_soc_aux_dev)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ASoC auxiliary device is a component that belongs to a sound card but is never bound into a DAI link, so the machine driver lists it through the card's [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array rather than through [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and the ASoC core probes it for its DAPM widgets, kcontrols, and an optional machine init callback without ever opening a PCM stream on it. Each entry is a [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) that embeds one [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) descriptor naming the component to find plus an [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) function pointer, and the core matches that descriptor against a registered [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) by name in [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775), threads the matched components onto the card's [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and probes them in [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795). On x86-64 ACPI systems this mechanism attaches a smart amplifier or a jack-detection chip that is controlled over I2C, SoundWire, or another control bus but carries no PCM data of its own, and the SoundWire machine driver [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225) serves as the worked example, building its [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array dynamically from the SoundWire peripherals the platform firmware enumerates so each is probed for its widgets and kcontrols once its component is found.

```
    struct snd_soc_card
    ┌────────────────────────────────────────────────────────────┐
    │  dai_link[]      ─▶  CPU/codec DAI links (carry PCM)       │
    │  num_links                                                 │
    │                                                            │
    │  aux_dev[]  ─▶  struct snd_soc_aux_dev   (one per SDW aux) │
    │  num_aux_devs    ┌─────────────────────────────────────────┐      │
    │                  │ dlc  (snd_soc_dai_link_component)       │      │
    │                  │   .name = codec_info->auxs[j].codec_name│      │
    │                  │ init() ─▶ optional machine callback     │      │
    │                  └─────────────────┬───────────────────────┘      │
    │                                    │ soc_bind_aux_dev()    │
    │  aux_comp_list  ◀──────────────────┘  match by name        │
    └────────────────────────────────────┼───────────────────────┘
                                         │ no DAI link references it
                                         ▼
                              struct snd_soc_component
                              ┌──────────────────────────────────┐
                              │ name = SoundWire peripheral name │
                              │ card_aux_list  (on aux list)     │
                              │ init ◀─ copied from aux->init    │
                              │ DAPM widgets, kcontrols          │
                              └──────────────────────────────────┘
```

## SUMMARY

A machine driver declares the audio data path of a card as an array of [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entries in [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and it declares any component that is part of the same card yet sits outside that data path as an array of [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) entries in [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), with [`num_aux_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) giving the count. According to the comment on the field in [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), the array holds "optional auxiliary devices such as amplifiers or codecs with DAI link unused", so an amplifier whose enable and gain are programmed over I2C, or a jack-detection codec whose interrupt reports headset state, is registered here rather than as a back-end DAI link.

Each [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) embeds one [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) in its [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) field, used only for its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), and one [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback the machine driver supplies to add controls or set up jack detection once the component is probed. [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) processes the auxiliary devices in two stages around the DAI-link work. It calls [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) first, before any PCM runtime exists, to resolve each [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) to a registered component through [`soc_find_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L884) and link the matches onto [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), returning `-EPROBE_DEFER` when a named component has not registered yet. After the DAI-link components are probed by [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742), it calls [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795), which runs [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) on each bound auxiliary component in component-probe order.

The link between the auxiliary entry and the matched component is the component's [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) pointer. [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) calls [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52) to copy [`aux->init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) into [`component->init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), and [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) runs that callback through [`snd_soc_component_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58) after the component's own [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) has succeeded. Teardown reverses both stages from [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), where [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) removes each probed auxiliary component and [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764) clears the copied [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) pointer and unlinks it from [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972).

## SPECIFICATIONS

The [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) object is a Linux kernel software construct and has no standalone hardware specification. The auxiliary components it binds on an x86-64 ACPI system are themselves enumerated through ACPI or SoundWire, and the machine driver locates each one by the device name the bus assigns it, such as the SoundWire peripheral name a codec-info table records in its auxiliary array.

## LINUX KERNEL

### Auxiliary-device and card types (soc.h, soc-component.h)

- [`'\<struct snd_soc_aux_dev\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960): one auxiliary device entry; embeds the [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) descriptor and the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback
- [`'\<struct snd_soc_dai_link_component\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642): the matcher descriptor; the auxiliary device uses only its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) (device name)
- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): carries the [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array, the [`num_aux_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) count, and the [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) of bound components
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the matched component; its [`card_aux_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L218) node hangs on the card's [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and its [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) pointer receives the copied callback
- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the component's static driver, whose [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) and [`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L159) sequence the auxiliary probe

### Bind, probe, and remove path (soc-core.c)

- [`'\<soc_bind_aux_dev\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775): walk [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), match each [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) to a component, copy the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback, and add the component to [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972); returns `-EPROBE_DEFER` on a miss
- [`'\<soc_probe_aux_devices\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795): probe every bound auxiliary component in [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) by calling [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602)
- [`'\<soc_remove_aux_devices\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815): remove each auxiliary component in [`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L159) through [`soc_remove_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1585)
- [`'\<soc_unbind_aux_dev\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764): clear the copied [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and unlink each component from [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): the card instantiation path that calls [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) before the DAI-link runtimes and [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795) after the link components
- [`'\<soc_cleanup_card_resources\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114): the teardown path that calls [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) then [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764)

### Component matching and probe helpers

- [`'\<soc_find_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L884): return the first registered component matching a [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960)
- [`'\<snd_soc_is_matching_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856): the predicate that compares the [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) name (or node) against a candidate component
- [`'\<snd_soc_component_set_aux\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52): copy [`aux->init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) into [`component->init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), or clear it when passed NULL
- [`'\<snd_soc_component_init\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58): run [`component->init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) if present, the machine-specific init for the auxiliary component
- [`'\<soc_probe_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602): bring a component up (DAPM, driver [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), then [`snd_soc_component_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58)); shared by link and auxiliary components
- [`'\<soc_remove_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1585): tear a component down, calling [`snd_soc_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L313) when it was probed

### Iterators and the entry macro (soc.h, soc-component.h)

- [`'\<for_each_card_pre_auxs\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1104): iterate the [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array by index, used at bind time before the components are linked
- [`'\<for_each_card_auxs\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1114): iterate the bound components on [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), used at probe time
- [`'\<for_each_card_auxs_safe\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1116): the removal-safe variant used by [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) and [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764)
- [`'\<for_each_comp_order\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L23): iterate from `SND_SOC_COMP_ORDER_FIRST` to `SND_SOC_COMP_ORDER_LAST` so dependent components probe and remove in order
- [`'\<COMP_AUX\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L938): initialiser that fills a [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) from a single device name, the form a static auxiliary entry uses

### x86-64 ACPI SoundWire worked example (intel/boards, sdw_utils)

- [`'\<sof_card_dai_links_create\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225): the SoundWire machine driver card setup that declares [`sof_aux`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1237), counts the SoundWire aux endpoints, allocates the array, parses it, and assigns it to the card
- [`'\<asoc_sdw_count_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348): the generic SoundWire helper that sums [`aux_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L84) over every discovered peripheral into the caller's `num_aux`
- [`'\<asoc_sdw_parse_sdw_endpoints\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489): the generic SoundWire helper that sets each auxiliary [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) name from a peripheral's auxiliary device name
- [`'\<struct asoc_sdw_codec_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L73): the per-part codec-info table whose [`auxs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L83) array and [`aux_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L84) count drive the dynamic auxiliary build
- [`'\<struct asoc_sdw_aux_info\>':'include/sound/soc_sdw_utils.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L69): the entry holding the [`codec_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L70) copied into the auxiliary descriptor

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model that splits a card into reusable component drivers and a machine driver
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver guide where the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) fields including the auxiliary array are described
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): ASoC jack detection, the function an auxiliary jack-detection codec performs from its [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the component (codec) driver guide covering the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback run before the auxiliary init
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the dynamic audio power management an auxiliary component contributes widgets to without a DAI link

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The auxiliary-device interface is built around one type the machine driver populates and a fixed bind, probe, and remove sequence the ASoC core runs. A machine driver fills [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and [`num_aux_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) in its [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and registers the card with [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65), and the core does the rest.

| Lifecycle step | Function | Effect on card state |
|----------------|----------|----------------------|
| declare | machine driver fills [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) / [`num_aux_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) | array of `snd_soc_aux_dev` set |
| bind | [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) | match each entry, add component to `aux_comp_list` |
| copy init | [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52) | `component->init = aux->init` |
| probe | [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795) | probe each component, run init |
| run init | [`snd_soc_component_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58) | machine setup (jack, controls) |
| remove | [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) | remove each probed component |
| unbind | [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764) | clear init, unlink from `aux_comp_list` |

### snd_soc_aux_dev

[`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) is the entry a machine driver writes. The [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) field names the component to find and the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback runs once the component is probed, taking the matched [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) as its only argument.

### dlc (snd_soc_dai_link_component)

The embedded [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) is the same descriptor a DAI link uses to name a CPU or codec component, but an auxiliary device fills only [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) because there is no DAI to name. On x86-64 the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) is the bus-derived device name, such as the SoundWire peripheral name a codec-info auxiliary entry records.

### init

The [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) callback is where the machine driver performs setup that needs the component present, most commonly creating a jack with [`snd_soc_card_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L59) and wiring the auxiliary codec to report on it, or adding machine-level kcontrols. It is optional, and an entry that only needs the component probed for its own DAPM widgets leaves it NULL.

## DETAILS

### The card holds two parallel arrays

A [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) keeps the data-path links and the auxiliary devices in two separate arrays, and the auxiliary array sits beside the [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array in the structure with a comment that names its purpose:

```c
/* include/sound/soc.h:1046 */
	/*
	 * optional auxiliary devices such as amplifiers or codecs with DAI
	 * link unused
	 */
	struct snd_soc_aux_dev *aux_dev;
	int num_aux_devs;
	struct list_head aux_comp_list;
```

The [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) pointer and [`num_aux_devs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) count describe the static declaration the machine driver supplies, and [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is the runtime list the core fills with the components it matched. [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) initialises that list empty with [`INIT_LIST_HEAD(&card->aux_comp_list)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) before binding begins.

Each array element is a [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960), which is small. It carries the matcher descriptor and the callback and nothing else:

```c
/* include/sound/soc.h:960 */
struct snd_soc_aux_dev {
	/*
	 * specify multi-codec either by device name, or by
	 * DT/OF node, but not both.
	 */
	struct snd_soc_dai_link_component dlc;

	/* codec/machine specific init - e.g. add machine controls */
	int (*init)(struct snd_soc_component *component);
};
```

The [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) is a [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), the general ASoC descriptor for naming a component. An auxiliary device reads only its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), never the [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642), because no DAI is involved.

### snd_soc_bind_card processes aux devices in two stages

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) instantiates the whole card, and it brackets the DAI-link work with the two auxiliary stages. It binds the auxiliary devices first, before it adds any PCM runtime, then probes them after the link components but before the link DAIs:

```c
/* sound/soc/soc-core.c:2163 */
static int snd_soc_bind_card(struct snd_soc_card *card)
{
	...
	/* bind aux_devs too */
	ret = soc_bind_aux_dev(card);
	if (ret < 0)
		goto probe_end;

	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;
	...
	/* probe all components used by DAI links on this card */
	ret = soc_probe_link_components(card);
	if (ret < 0) {
		...
		goto probe_end;
	}

	/* probe auxiliary components */
	ret = soc_probe_aux_devices(card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: failed to probe aux component %d\n", ret);
		goto probe_end;
	}

	/* probe all DAI links on this card */
	ret = soc_probe_link_dais(card);
	...
}
```

Binding runs before the runtimes exist because [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) only needs the components already registered, and it returns `-EPROBE_DEFER` when one is missing so the whole card defers and retries later. The probe runs after [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742) so a DAI-link component shared with an auxiliary entry is brought up once, and before [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707) so an auxiliary init that creates a jack runs while the link DAIs are still being assembled. On any error the function jumps to `probe_end` and calls [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), which undoes both auxiliary stages.

```
    snd_soc_bind_card(): aux stages bracket the DAI-link work
    ──────────────────────────────────────────────────────────
    time ─────────────────────────────────────────────────────▶

    soc_bind_aux_dev()            stage 1: match each entry,
      (before any runtime)        add component to aux_comp_list
            │
            ▼
    snd_soc_add_pcm_runtimes()    DAI-link runtimes created
            │
            ▼
    soc_probe_link_components()   shared component brought up once
            │
            ▼
    soc_probe_aux_devices()       stage 2: probe bound aux comps,
      (after link components)     run each aux init (jack/controls)
            │
            ▼
    soc_probe_link_dais()         link DAIs assembled last
```

### soc_bind_aux_dev matches by name and copies the init callback

[`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) walks the [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array with [`for_each_card_pre_auxs()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1104), resolves each [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) to a registered component, records the callback on the component, and links the component onto [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972):

```c
/* sound/soc/soc-core.c:1775 */
static int soc_bind_aux_dev(struct snd_soc_card *card)
{
	struct snd_soc_component *component;
	struct snd_soc_aux_dev *aux;
	int i;

	for_each_card_pre_auxs(card, i, aux) {
		/* codecs, usually analog devices */
		component = soc_find_component(&aux->dlc);
		if (!component)
			return -EPROBE_DEFER;

		/* for snd_soc_component_init() */
		snd_soc_component_set_aux(component, aux);
		/* see for_each_card_auxs */
		list_add(&component->card_aux_list, &card->aux_comp_list);
	}
	return 0;
}
```

The comment "codecs, usually analog devices" describes what an auxiliary entry typically is, an analog part with controls but no PCM data path. [`soc_find_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L884) returns the first registered component that the [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) matches, walking every component under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48):

```c
/* sound/soc/soc-core.c:884 */
static struct snd_soc_component *soc_find_component(
	const struct snd_soc_dai_link_component *dlc)
{
	struct snd_soc_component *component;

	lockdep_assert_held(&client_mutex);
	...
	for_each_component(component)
		if (snd_soc_is_matching_component(dlc, component))
			return component;

	return NULL;
}
```

The match itself is by name. [`snd_soc_is_matching_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L856) compares the [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) against a candidate, and for an auxiliary device that carries no [`dai_args`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) the decisive test is the [`strcmp()`](https://elixir.bootlin.com/linux/v7.0/source/lib/string.c) on [`component->name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207):

```c
/* sound/soc/soc-core.c:856 */
static int snd_soc_is_matching_component(
	const struct snd_soc_dai_link_component *dlc,
	struct snd_soc_component *component)
{
	struct device_node *component_of_node;

	if (!dlc)
		return 0;

	if (dlc->dai_args) {
		struct snd_soc_dai *dai;

		for_each_component_dais(component, dai)
			if (snd_soc_is_matching_dai(dlc, dai))
				return 1;
		return 0;
	}

	component_of_node = soc_component_to_node(component);

	if (dlc->of_node && component_of_node != dlc->of_node)
		return 0;
	if (dlc->name && strcmp(component->name, dlc->name))
		return 0;

	return 1;
}
```

Once matched, [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52) records the auxiliary init on the component so [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) can find it later. The whole transfer from auxiliary entry to component is one assignment:

```c
/* sound/soc/soc-component.c:52 */
void snd_soc_component_set_aux(struct snd_soc_component *component,
			       struct snd_soc_aux_dev *aux)
{
	component->init = (aux) ? aux->init : NULL;
}
```

Passing NULL clears the pointer, which is what [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764) does at teardown so a later rebind of the same component does not run a stale callback.

### soc_probe_aux_devices probes each bound component in order

After binding, [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795) walks [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) once per component-probe order and probes the components whose [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) matches the current pass:

```c
/* sound/soc/soc-core.c:1795 */
static int soc_probe_aux_devices(struct snd_soc_card *card)
{
	struct snd_soc_component *component;
	int order;
	int ret;

	for_each_comp_order(order) {
		for_each_card_auxs(card, component) {
			if (component->driver->probe_order != order)
				continue;

			ret = soc_probe_component(card,	component);
			if (ret < 0)
				return ret;
		}
	}

	return 0;
}
```

The nesting of [`for_each_comp_order()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L23) outside [`for_each_card_auxs()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1114) lets an auxiliary component that another depends on declare an earlier [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) and so probe first. The probe itself is the same [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) the DAI-link components use, which runs the component DAPM setup, the driver [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and then the auxiliary init through [`snd_soc_component_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58). The comment in that path points back at [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52), tying the call to the copy done at bind time. [`snd_soc_component_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L58) runs the recorded callback only when one was set, so a link component that never went through [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52) has a NULL [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) and skips the step:

```c
/* sound/soc/soc-component.c:58 */
int snd_soc_component_init(struct snd_soc_component *component)
{
	int ret = 0;

	if (component->init)
		ret = component->init(component);

	return soc_component_ret(component, ret);
}
```

That init runs at the tail of each probe, which the outer loop repeats once per order value so a component picks its pass by the probe_order it declares:

```
    soc_probe_aux_devices(): order passes pick aux components
    ──────────────────────────────────────────────────────────
    for_each_comp_order(order)  ×  for_each_card_auxs(card, comp)

      order == FIRST  ┌──────────────────────────────────────┐
      ────────────▶   │ probe comps whose probe_order==FIRST │
                      └──────────────────────────────────────┘
      (mid orders)    ┌──────────────────────────────────────┐
      ────────────▶   │ same rule, one pass per order value  │
                      └──────────────────────────────────────┘
      order == LAST   ┌──────────────────────────────────────┐
      ────────────▶   │ probe comps whose probe_order==LAST  │
                      └──────────────────────────────────────┘

    each probe = soc_probe_component(): DAPM, driver probe,
                 then snd_soc_component_init() runs the aux init
    a dependency declares an earlier probe_order to probe first
```

### Teardown removes then unbinds

[`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114) reverses the bring-up. It removes the auxiliary components after the link DAIs and link components are gone, then unbinds them, calling [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) then [`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764). [`soc_remove_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1815) walks [`aux_comp_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) in reverse component order with the removal-safe iterator and removes each component that was probed:

```c
/* sound/soc/soc-core.c:1815 */
static void soc_remove_aux_devices(struct snd_soc_card *card)
{
	struct snd_soc_component *comp, *_comp;
	int order;

	for_each_comp_order(order) {
		for_each_card_auxs_safe(card, comp, _comp) {
			if (comp->driver->remove_order == order)
				soc_remove_component(comp, 1);
		}
	}
}
```

[`soc_unbind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1764) then clears the copied callback through [`snd_soc_component_set_aux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L52) with a NULL argument and unlinks each component from the list:

```c
/* sound/soc/soc-core.c:1764 */
static void soc_unbind_aux_dev(struct snd_soc_card *card)
{
	struct snd_soc_component *component, *_component;

	for_each_card_auxs_safe(card, component, _component) {
		/* for snd_soc_component_init() */
		snd_soc_component_set_aux(component, NULL);
		list_del(&component->card_aux_list);
	}
}
```

This unbind mirrors the bind step, and teardown walks the pair in reverse, removing each probed component before unbinding it from aux_comp_list:

```
    Teardown reverses bring-up (soc_cleanup_card_resources)
    ────────────────────────────────────────────────────────
    bring-up                       teardown (reverse)
      bind  add to aux_comp_list ◀── unbind  list_del, clear init
      probe run aux init         ◀── remove  soc_remove_component

    order inside soc_cleanup_card_resources():
      (link DAIs and link components removed first)
            │
            ▼
      soc_remove_aux_devices()   reverse comp order; remove each
                                 probed aux via soc_remove_component
            │
            ▼
      soc_unbind_aux_dev()       snd_soc_component_set_aux(NULL)
                                 clears init, list_del(card_aux_list)
```

### Worked example: SoundWire aux devices in the sof_sdw machine driver

The SoundWire machine driver does not know its peripherals at compile time, so it cannot write a static [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) the way a fixed board would. It instead builds the [`aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) array at runtime from the SoundWire peripherals the platform firmware enumerates. Each auxiliary device represents a SoundWire peripheral, for example a smart amplifier, that is attached to the card for its DAPM widgets and kcontrols but has no front-end DAI link of its own. The build happens in [`sof_card_dai_links_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1225), which counts how many auxiliary endpoints the discovered peripherals expose with [`asoc_sdw_count_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348):

```c
/* sound/soc/intel/boards/sof_sdw.c:1249 */
	ret = asoc_sdw_count_sdw_endpoints(card, &num_devs, &num_ends, &num_aux);
	if (ret < 0) {
		dev_err(dev, "failed to count devices/endpoints: %d\n", ret);
		return ret;
	}
```

That count comes from a driver-private codec-info table. [`asoc_sdw_count_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1348) walks every enumerated address and adds each part's [`aux_num`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L84) to the running total:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1348 */
int asoc_sdw_count_sdw_endpoints(struct snd_soc_card *card,
				 int *num_devs, int *num_ends, int *num_aux)
{
	...
	for (adr_link = mach_params->links; adr_link->num_adr; adr_link++) {
		*num_devs += adr_link->num_adr;

		for (i = 0; i < adr_link->num_adr; i++) {
			const struct snd_soc_acpi_adr_device *adr_dev = &adr_link->adr_d[i];
			struct asoc_sdw_codec_info *codec_info;

			*num_ends += adr_dev->num_endpoints;

			codec_info = asoc_sdw_find_codec_info_part(adr_dev->adr);
			if (!codec_info)
				return -EINVAL;

			*num_aux += codec_info->aux_num;
		}
	}
	...
}
```

With the count known, the driver allocates the array of that many [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) entries with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h), then parses the endpoints to fill it:

```c
/* sound/soc/intel/boards/sof_sdw.c:1273 */
	sof_aux = devm_kcalloc(dev, num_aux, sizeof(*sof_aux), GFP_KERNEL);
	if (!sof_aux) {
		ret = -ENOMEM;
		goto err_dai;
	}

	ret = asoc_sdw_parse_sdw_endpoints(card, sof_aux, sof_dais, sof_ends, &num_confs);
```

[`asoc_sdw_parse_sdw_endpoints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1489) receives the freshly allocated array and names each entry. For every auxiliary the part declares it copies the peripheral's auxiliary device name from [`auxs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L83) into the entry's [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) name and advances the pointer:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1530 */
			for (j = 0; j < codec_info->aux_num; j++) {
				soc_aux->dlc.name = codec_info->auxs[j].codec_name;
				soc_aux++;
			}
```

That [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) is the only field the descriptor needs, and it is the SoundWire device name the core will match against a registered [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207). The entries here leave [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) NULL because each auxiliary peripheral is wanted only for its own widgets and kcontrols, a purpose that needs no machine-level jack callback. Finally the driver publishes the array it built to the card so the ASoC core can pick it up during binding:

```c
/* sound/soc/intel/boards/sof_sdw.c:1349 */
	card->aux_dev = sof_aux;
	card->num_aux_devs = num_aux;
```

From this point the dynamically built array is indistinguishable from a static one. The ASoC core binds each entry to its named component in [`soc_bind_aux_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1775) and probes it in [`soc_probe_aux_devices()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1795), so the SoundWire peripheral contributes its widgets and kcontrols to the card without ever opening a PCM stream or joining a [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). Whether an auxiliary entry is written by hand or generated from firmware as here, the result is one [`struct snd_soc_aux_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) whose [`dlc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L960) names a component the core finds, binds, and probes for its controls and widgets alone.

```
    sof_sdw builds aux_dev[] from firmware enumeration
    ───────────────────────────────────────────────────────────

    struct asoc_sdw_codec_info  (per enumerated SoundWire part)
    ┌────────────────────────────────────────────┐
    │ aux_num            ─▶ counted into num_aux │
    │ auxs[j].codec_name ─▶ copied into dlc.name │
    └───────────────────────┬────────────────────┘
                            │ asoc_sdw_count_sdw_endpoints()
                            │ sums aux_num over every address
                            ▼
    num_aux  ─▶  devm_kcalloc(num_aux, sizeof aux)
                            │
                            ▼
    struct snd_soc_aux_dev sof_aux[]  (asoc_sdw_parse_sdw_endpoints)
    ┌────────────────────────────────────────────┐
    │ dlc.name = codec_info->auxs[j].codec_name  │
    │ init     = NULL                            │
    └───────────────────────┬────────────────────┘
                            │ publish: card->aux_dev = sof_aux
                            │          card->num_aux_devs = num_aux
                            ▼
                  soc_bind_aux_dev() matches dlc.name
                            ▼
                  struct snd_soc_component
```
