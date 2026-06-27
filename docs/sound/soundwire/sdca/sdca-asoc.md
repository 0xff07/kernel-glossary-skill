# SDCA to ASoC auto-generation

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A parsed SDCA function is a graph of typed entities, and [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236) turns that [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) into the four ASoC arrays a codec needs ([`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)) by counting with [`sdca_asoc_count_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L73), allocating, then filling them through [`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697), [`sdca_asoc_populate_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986), and [`sdca_asoc_populate_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169), so a generic SDCA codec driver gets its DAPM graph, mixer controls, and DAI list without a hand-written topology.

```
    struct sdca_function_data (entities[], controls, clusters)
    ┌───────────────────────────────────────────────────────────┐
    │  IT/OT terminals   SU/MU selectors+mixers   PDE/CS supply │
    │  GE group entity   each entity[i].controls[j]             │
    └──────────────────────────────┬────────────────────────────┘
                                   │ sdca_asoc_populate_component
                                   │   count → devm_kcalloc → populate
              ┌──────────────┬─────┴──────┬───────────────┐
              ▼              ▼            ▼               ▼
    snd_soc_dapm_widget  snd_soc_dapm  snd_kcontrol_new  snd_soc_dai_driver
        [num_widgets]    _route[..]      [num_controls]    [num_dais]
        (1 per entity)   (sources,     (FU vol/switch,    (1 per dataport
                          clock, PDE)   GE/SU enum,        IT/OT terminal)
                                        pin switch)
              │              │            │               │
              └──────────────┴─────┬──────┴───────────────┘
                                   ▼
              struct snd_soc_component_driver  (+ *dai_drv, *num_dai_drv)
              .dapm_widgets .dapm_routes .controls  installed for probe
```

## SUMMARY

[`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236) is the single entry point a codec driver calls. It runs [`sdca_asoc_count_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L73) to size the four arrays, allocates each with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) against the device, then calls [`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697), [`sdca_asoc_populate_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986), and [`sdca_asoc_populate_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169), and finally writes the [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75), and [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) pointers into the caller's [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and returns the DAI array through the `dai_drv` and `num_dai_drv` out-parameters. The input is the [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) produced by the firmware parse, whose [`entities`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array of [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) drives every generated object.

The widget count is one per entity except the final terminating entity, and the route, control, and DAI counts accumulate per entity from the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) field. [`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697) makes a first pass that calls [`entity_early_parse_ge()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L154) on every [`SDCA_ENTITY_TYPE_GE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1066) group entity so the [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) it builds exists before a selector references it, then a second pass that switches on [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) and dispatches to a per-type builder: [`entity_parse_it()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L265) and [`entity_parse_ot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L297) for terminals, [`entity_parse_pde()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L385) for power, [`entity_parse_su()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L554) and [`entity_parse_mu()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L581) for selectors and mixers, [`entity_parse_cs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L662) for clocks, and [`entity_parse_simple()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L247) for the rest. Each builder sets the widget's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to one [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value, advances the widget pointer, and emits routes through [`add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L238) from the entity's [`sources`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) list.

[`sdca_asoc_populate_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986) walks the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array of each entity and calls [`populate_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L873) to build a volume or switch [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) backed by a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) whose register address is an SDCA Control address from [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), plus a pin switch for a non-dataport terminal through [`populate_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L952). [`sdca_asoc_populate_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169) emits one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) per dataport terminal, naming the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L417) stream for an [`SDCA_ENTITY_TYPE_IT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1057) and the [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L416) stream for an [`SDCA_ENTITY_TYPE_OT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1058), and computing the supported rates and formats from the terminal's clock and usage ranges in [`populate_rate_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1093). The in-tree caller is [`class_function_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L292), the generic SDCA class-function auxiliary driver; the Realtek rt722-sdca codec is the reference SDCA peripheral on Intel SoundWire, and the same `sdca_asoc_populate_*` family applies to it.

## SPECIFICATIONS

The mapping from SDCA entity types to ASoC objects follows the MIPI SDCA specification's entity model, in which a function is a directed graph of Input Terminals, Output Terminals, Selector Units, Mixer Units, Power Domain Entities, Clock Sources, and Group Entities, each carrying typed controls. The kernel encodes that model in [`enum sdca_entity_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055) and the per-control selector enums, and the population code switches on those values. A control is addressed on the wire by an SDCA Control address built from the function address, entity id, control selector, and channel number by the [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) macro, which is the register every generated [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) writes through. The MIPI SDCA specification is available only to MIPI members and is not linked here; the entity types, control selectors, and access layers are described from the kernel enums in [`include/sound/sdca_function.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h).

## LINUX KERNEL

### Public population API (sdca_asoc.c, sdca_asoc.h)

- [`'\<sdca_asoc_populate_component\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236): the one-call entry point; counts, allocates all four arrays internally, populates them, and writes them into a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) plus a returned [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array
- [`'\<sdca_asoc_count_component\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L73): fills `num_widgets`, `num_routes`, `num_controls`, and `num_dais` from the entity graph so the caller (or [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236)) can size the arrays
- [`'\<sdca_asoc_populate_dapm\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697): fills the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) and [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) arrays, one widget per entity, dispatching by [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185)
- [`'\<sdca_asoc_populate_controls\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986): fills the [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) array from the per-entity [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) and from non-dataport terminal pin switches
- [`'\<sdca_asoc_populate_dais\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169): fills the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array, one DAI per dataport terminal, attaching the caller's [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)

### Per-entity widget and route builders (sdca_asoc.c)

- [`'\<entity_parse_it\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L265): an Input Terminal becomes [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447) (dataport) or [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435) (analog), wiring a route from its AIF, clock, and sources
- [`'\<entity_parse_ot\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L297): an Output Terminal becomes [`snd_soc_dapm_aif_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L448) (dataport) or [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437) (analog)
- [`'\<entity_parse_pde\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L385): a Power Domain Entity becomes a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) with [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) set to a Requested PS Control and an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) of [`entity_pde_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L329), routed to every managed entity
- [`'\<entity_parse_su\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L554): a Selector Unit splits into [`entity_parse_su_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L438) (device-layer, a [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426) driven by a group kcontrol) or [`entity_parse_su_class()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L503) (class-layer, a [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426) with its own enum)
- [`'\<entity_parse_mu\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L581): a Mixer Unit becomes a [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428) with one boolean [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) per input source
- [`'\<entity_parse_cs\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L662): a Clock Source becomes a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) with [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) 1 and an [`entity_cs_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L647) settle delay
- [`'\<entity_parse_simple\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L247): the fallback that sets [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to a caller-passed [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) and adds source routes, used for [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430), [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449), and unhandled clock selectors
- [`'\<entity_early_parse_ge\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L154): builds the Group Entity's mode-select [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) ahead of the main pass and stores it in [`ge.kctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1111)
- [`'\<add_route\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L238): writes one [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) ([`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473)) and advances the route pointer

### Per-control kcontrol builders (sdca_asoc.c)

- [`'\<populate_control\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L873): builds a volume or switch [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) over a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), choosing volatile or plain volsw handlers and read-only or read-write [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)
- [`'\<populate_pin_switch\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L952): builds a DAPM pin switch [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) using [`snd_soc_dapm_info_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3638) for a non-dataport terminal
- [`'\<control_limit_kctl\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L781): converts a Q7.8 dB range into a TLV array and fills [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and the [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) flag on the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231)
- [`'\<exported_control\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L36): decides whether a control is user-visible from its [`layers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) bitmask, the gate both the count and the populate passes use
- [`'\<ge_put_enum_double\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L119): the put handler for the Group Entity enum, resuming the device and reading back the Detected Mode before applying

### DAI rate and format derivation (sdca_asoc.c)

- [`'\<populate_rate_format\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1093): fills [`formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) and [`rates`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of a [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) by intersecting the terminal's clock-source rates with its usage-control rates
- [`'\<rate_find_mask\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1021): maps a sample rate in Hz to its `SNDRV_PCM_RATE_*` bit
- [`'\<width_find_mask\>':'sound/soc/sdca/sdca_asoc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1071): maps a sample width in bits to its `SNDRV_PCM_FMTBIT_*` value

### Produced ASoC types (soc-dapm.h, control.h, soc.h, soc-dai.h)

- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): one DAPM graph node per entity; the builders set its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550), and [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553)
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): a sink/control/source edge; [`add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L238) fills the three string fields
- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): one ALSA control template per exported SDCA control, mixer kcontrol, or pin switch
- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231): the volume/switch private data behind [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47); [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) are SDCA Control addresses
- [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): the enumerated private data for a Group Entity or Selector Unit mux
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): one DAI per dataport terminal, carrying the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L417) or [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L416) [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) and the caller's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)
- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the destination; [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75), and [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) point at the generated arrays

### SDCA input types and selectors (sdca_function.h)

- [`'\<struct sdca_function_data\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419): the parsed function (the input); supplies the [`entities`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array, the [`clusters`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), and the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) carrying the function address. Parsing is owned by the SDCA data-model page
- [`'\<struct sdca_entity\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185): one entity; its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`label`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`sources`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), and the type union ([`iot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`pde`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`ge`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185)) drive every generated object
- [`'\<struct sdca_control\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810): one control; [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`mode`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), and [`layers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) become the kcontrol's register, range, and access
- [`'\<enum sdca_entity_type\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055): the discriminator the population switches read: [`SDCA_ENTITY_TYPE_IT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1057), [`SDCA_ENTITY_TYPE_OT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1058), [`SDCA_ENTITY_TYPE_MU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1059), [`SDCA_ENTITY_TYPE_SU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1060), [`SDCA_ENTITY_TYPE_CS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1063), [`SDCA_ENTITY_TYPE_PDE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1065), [`SDCA_ENTITY_TYPE_GE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1066)
- [`'\<enum sdca_access_layer\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L769): [`SDCA_ACCESS_LAYER_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L770), [`SDCA_ACCESS_LAYER_APPLICATION`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L771), [`SDCA_ACCESS_LAYER_CLASS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L772), and [`SDCA_ACCESS_LAYER_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L774), which select export and the SU device/class split
- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): builds the SDCA Control register address from function address, entity id, control selector, and channel number

### Generic SDCA codec driver (sdca_class_function.c)

- [`'\<class_function_probe\>':'sound/soc/sdca/sdca_class_function.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L292): the in-tree caller; parses one function, calls [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236), and registers the result with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'class_function_sdw_ops':'sound/soc/sdca/sdca_class_function.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L185): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) attached to every generated DAI, wiring [`sdca_asoc_free_constraints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1382) and the SoundWire stream callbacks
- [`'class_function_component_drv':'sound/soc/sdca/sdca_class_function.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L218): the template [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) copied per device and then filled by [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget types and route model that the generated [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) and [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) arrays conform to
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component driver and the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71), [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) fields the populate code writes
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI model the generated [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries describe
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream the [`class_function_sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L185) DAI ops join through the generated DAIs

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The four arrays are generated together and installed together, so a reader can trace each ASoC object back to the entity that produced it and forward to the component field that receives it. The widgets, routes, and controls are written into the caller's [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67); the DAI array is returned through out-parameters because [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) takes it separately. Every array is allocated with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) against the codec device, so all of it is freed when the device unbinds.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) array | [`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697) | device-managed, freed at unbind |
| [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) array | [`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697) via [`add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L238) | device-managed, freed at unbind |
| [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) array | [`sdca_asoc_populate_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986) | device-managed, freed at unbind |
| [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array | [`sdca_asoc_populate_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169) | device-managed, freed at unbind |
| Group Entity [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) | [`entity_early_parse_ge()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L154) | device-managed, referenced by SU muxes |
| [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) per control | [`populate_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L873) | device-managed, behind [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) |
| [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (filled) | caller, populated by [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236) | the codec device |

## DETAILS

### sdca_asoc_populate_component drives the whole generation

[`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236) is the function a codec driver calls with a parsed [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), an empty [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and a [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) to attach to each DAI. It counts the four object kinds, allocates each array with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) so they are released when the device unbinds, runs the three population passes, and then writes the widget, route, and control pointers into the component driver while returning the DAI array through `dai_drv` and `num_dai_drv`:

```c
/* sound/soc/sdca/sdca_asoc.c:1236 */
int sdca_asoc_populate_component(struct device *dev,
				 struct sdca_function_data *function,
				 struct snd_soc_component_driver *component_drv,
				 struct snd_soc_dai_driver **dai_drv, int *num_dai_drv,
				 const struct snd_soc_dai_ops *ops)
{
	struct snd_soc_dapm_widget *widgets;
	struct snd_soc_dapm_route *routes;
	struct snd_kcontrol_new *controls;
	struct snd_soc_dai_driver *dais;
	int num_widgets, num_routes, num_controls, num_dais;
	int ret;

	ret = sdca_asoc_count_component(dev, function, &num_widgets, &num_routes,
					&num_controls, &num_dais);
	if (ret)
		return ret;

	widgets = devm_kcalloc(dev, num_widgets, sizeof(*widgets), GFP_KERNEL);
	if (!widgets)
		return -ENOMEM;
	...
	ret = sdca_asoc_populate_dapm(dev, function, widgets, routes);
	if (ret)
		return ret;

	ret = sdca_asoc_populate_controls(dev, function, controls);
	if (ret)
		return ret;

	ret = sdca_asoc_populate_dais(dev, function, dais, ops);
	if (ret)
		return ret;

	component_drv->dapm_widgets = widgets;
	component_drv->num_dapm_widgets = num_widgets;
	component_drv->dapm_routes = routes;
	component_drv->num_dapm_routes = num_routes;
	component_drv->controls = controls;
	component_drv->num_controls = num_controls;

	*dai_drv = dais;
	*num_dai_drv = num_dais;

	return 0;
}
```

The split into [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73)/[`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75)/[`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) on the component versus the returned DAI array matches how [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) is called, which takes the component driver and the DAI array as separate arguments. The widgets, routes, and controls are then instantiated by the normal ASoC probe path, the same path a hand-written codec's static `.controls` and `.dapm_widgets` arrays follow.

### Counting sizes the arrays from the entity graph

[`sdca_asoc_count_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L73) sets the widget count to one per entity (excluding the final terminating entity at index `num_entities - 1`) and accumulates the route, control, and DAI counts by switching on each entity's [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185). A terminal contributes a route for its clock and a route for its dataport AIF, a control if it is not a dataport (the pin switch), and a DAI if it is a dataport; a Power Domain Entity contributes one route per managed entity; any entity with a [`group`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) and its source connections add further routes; and each control passing [`exported_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L36) adds a control:

```c
/* sound/soc/sdca/sdca_asoc.c:73 */
	*num_widgets = function->num_entities - 1;
	*num_routes = 0;
	*num_controls = 0;
	*num_dais = 0;

	for (i = 0; i < function->num_entities - 1; i++) {
		struct sdca_entity *entity = &function->entities[i];

		/* Add supply/DAI widget connections */
		switch (entity->type) {
		case SDCA_ENTITY_TYPE_IT:
		case SDCA_ENTITY_TYPE_OT:
			*num_routes += !!entity->iot.clock;
			*num_routes += !!entity->iot.is_dataport;
			*num_controls += !entity->iot.is_dataport;
			*num_dais += !!entity->iot.is_dataport;
			break;
		case SDCA_ENTITY_TYPE_PDE:
			*num_routes += entity->pde.num_managed;
			break;
		default:
			break;
		}

		if (entity->group)
			(*num_routes)++;

		/* Add primary entity connections from DisCo */
		*num_routes += entity->num_sources;

		for (j = 0; j < entity->num_controls; j++) {
			if (exported_control(entity, &entity->controls[j]))
				(*num_controls)++;
		}
	}
```

[`exported_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L36) is the gate used identically here and in the populate pass, so the counted and populated control numbers agree. It returns true for a Group Entity Detected Mode control unconditionally and otherwise tests whether the control's [`layers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) bitmask includes a user or application access layer:

```c
/* sound/soc/sdca/sdca_asoc.c:36 */
static bool exported_control(struct sdca_entity *entity, struct sdca_control *control)
{
	switch (SDCA_CTL_TYPE(entity->type, control->sel)) {
	case SDCA_CTL_TYPE_S(GE, DETECTED_MODE):
		return true;
	default:
		break;
	}

	return control->layers & (SDCA_ACCESS_LAYER_USER |
				  SDCA_ACCESS_LAYER_APPLICATION);
}
```

That gate decides the control column while the rest of the tally switches on entity type, a dataport terminal adding a DAI, a PDE adding a route per managed entity, and every entity adding one route per source:

```
    sdca_asoc_count_component: each entity type's array contributions
    ─────────────────────────────────────────────────────────────────
    (widgets = num_entities - 1; the rest accumulate per entity)

    entity->type        +wgt  +routes             +ctl  +dai
    ──────────────────  ────  ──────────────────  ────  ────
    IT / OT  dataport    1    clock? 1, AIF 1      0     1
    IT / OT  analog      1    clock? 1             1     0
    PDE                  1    num_managed          0     0
    other SU/MU/CS/..    1    0                    0     0
    ──────────────────  ────  ──────────────────  ────  ────
    every entity adds:        + num_sources
    entity->group set:        + 1 route
    each exported_control():                       + 1
```

### Two passes turn entities into widgets and routes

[`sdca_asoc_populate_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L697) runs two loops over the entities. The first loop handles only [`SDCA_ENTITY_TYPE_GE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1066), calling [`entity_early_parse_ge()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L154) so the group entity's mode-select kcontrol is built before a Selector Unit in the second loop refers to it. According to the comment, "Some entities need to add controls 'early' as they are referenced by other entities." The second loop sets the widget [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) to the entity [`label`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) and [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), then dispatches to a per-type builder, falling through to [`entity_parse_simple()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L247) with a default [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430) type:

```c
/* sound/soc/sdca/sdca_asoc.c:722 */
	for (i = 0; i < function->num_entities - 1; i++) {
		struct sdca_entity *entity = &function->entities[i];

		widget->name = entity->label;
		widget->reg = SND_SOC_NOPM;

		switch (entity->type) {
		case SDCA_ENTITY_TYPE_IT:
			ret = entity_parse_it(dev, function, entity, &widget, &route);
			break;
		case SDCA_ENTITY_TYPE_OT:
			ret = entity_parse_ot(dev, function, entity, &widget, &route);
			break;
		case SDCA_ENTITY_TYPE_PDE:
			ret = entity_parse_pde(dev, function, entity, &widget, &route);
			break;
		case SDCA_ENTITY_TYPE_SU:
			ret = entity_parse_su(dev, function, entity, &widget, &route);
			break;
		case SDCA_ENTITY_TYPE_MU:
			ret = entity_parse_mu(dev, function, entity, &widget, &route);
			break;
		case SDCA_ENTITY_TYPE_CS:
			ret = entity_parse_cs(dev, function, entity, &widget, &route);
			break;
		...
		default:
			ret = entity_parse_simple(dev, function, entity, &widget,
						  &route, snd_soc_dapm_pga);
			break;
		}
		if (ret)
			return ret;

		if (entity->group)
			add_route(&route, entity->label, NULL, entity->group->label);
	}
```

Each builder takes the widget and route pointers by address and advances them, so the next entity writes into the next array slot. [`add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L238) is the shared route writer, filling the [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) strings of one [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) and stepping the pointer:

```c
/* sound/soc/sdca/sdca_asoc.c:238 */
static void add_route(struct snd_soc_dapm_route **route, const char *sink,
		      const char *control, const char *source)
{
	(*route)->sink = sink;
	(*route)->control = control;
	(*route)->source = source;
	(*route)++;
}
```

The second pass sends each entity type to its builder, a terminal becoming an AIF or analog widget, a mixer unit a mixer and a selector a mux, and a power or clock domain a supply, with the group entity built first in pass one so a selector can point at it:

```
    entity->type dispatch: one DAPM widget id per SDCA entity
    ──────────────────────────────────────────────────────────
    (sdca_asoc_populate_dapm switches on type; routes from sources)

      SDCA entity type        builder            snd_soc_dapm_* widget
      ──────────────────────  ─────────────────  ─────────────────────
      IT  (dataport)          entity_parse_it    aif_in
      IT  (analog)            entity_parse_it    mic
      OT  (dataport)          entity_parse_ot    aif_out
      OT  (analog)            entity_parse_ot    spk
      MU                      entity_parse_mu    mixer
      SU                      entity_parse_su    mux  (uses GE kctl)
      PDE                     entity_parse_pde   supply  (PS event)
      CS                      entity_parse_cs    supply  (subseq 1)
      default                 entity_parse_simple pga
      ──────────────────────  ─────────────────  ─────────────────────
      GE is handled in pass 1 by entity_early_parse_ge, which builds
      the mux enum kctl first so a later SU can reference it
```

### A terminal becomes an AIF or an analog endpoint

[`entity_parse_it()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L265) gives an Input Terminal one of two widget types from its [`iot.is_dataport`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L960) flag. A dataport terminal becomes a [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447) and gets a route from a synthesized "Playback" AIF name into the terminal; a non-dataport terminal becomes a [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435). Either way the terminal's clock and each of its [`sources`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) become input routes:

```c
/* sound/soc/sdca/sdca_asoc.c:265 */
static int entity_parse_it(struct device *dev,
			   struct sdca_function_data *function,
			   struct sdca_entity *entity,
			   struct snd_soc_dapm_widget **widget,
			   struct snd_soc_dapm_route **route)
{
	int i;

	if (entity->iot.is_dataport) {
		const char *aif_name = devm_kasprintf(dev, GFP_KERNEL, "%s %s",
						      entity->label, "Playback");
		if (!aif_name)
			return -ENOMEM;

		(*widget)->id = snd_soc_dapm_aif_in;

		add_route(route, entity->label, NULL, aif_name);
	} else {
		(*widget)->id = snd_soc_dapm_mic;
	}

	if (entity->iot.clock)
		add_route(route, entity->label, NULL, entity->iot.clock->label);

	for (i = 0; i < entity->num_sources; i++)
		add_route(route, entity->label, NULL, entity->sources[i]->label);

	(*widget)++;

	return 0;
}
```

[`entity_parse_ot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L297) is the mirror image. A dataport Output Terminal becomes a [`snd_soc_dapm_aif_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L448) with a route from the terminal to a "Capture" AIF name, and a non-dataport terminal becomes a [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437). The AIF route direction is reversed because an output terminal sources the capture stream.

### A Power Domain Entity becomes a supply with a poll event

[`entity_parse_pde()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L385) builds a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) widget whose [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) is the Requested PS Control address (from [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335)), with [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) and [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533) set to the PS0 and PS3 power states and an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) of [`entity_pde_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L329). After validating that the Requested PS range covers both [`SDCA_PDE_PS0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L992) and [`SDCA_PDE_PS3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L995), it routes the supply to every entity in the PDE's [`pde.managed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) list:

```c
/* sound/soc/sdca/sdca_asoc.c:418 */
	(*widget)->id = snd_soc_dapm_supply;
	(*widget)->reg = SDW_SDCA_CTL(function->desc->adr, entity->id, control->sel, 0);
	(*widget)->mask = GENMASK(control->nbits - 1, 0);
	(*widget)->on_val = SDCA_PDE_PS0;
	(*widget)->off_val = SDCA_PDE_PS3;
	(*widget)->event_flags = SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_POST_PMD;
	(*widget)->event = entity_pde_event;
	(*widget)->priv = entity;
	(*widget)++;

	for (i = 0; i < entity->pde.num_managed; i++)
		add_route(route, entity->pde.managed[i]->label, NULL, entity->label);

	for (i = 0; i < entity->num_sources; i++)
		add_route(route, entity->label, NULL, entity->sources[i]->label);
```

[`entity_pde_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L329) runs on power up and power down because the widget sets [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) in [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549). It reads the Actual PS Control in a loop until it equals the target power state, applying the per-transition delay the function declares, so DAPM does not consider the supply settled until the hardware reports the new state. A Clock Source goes through [`entity_parse_cs()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L662), which builds a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) with [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) 1 so clocks power up after PDEs, and an [`entity_cs_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L647) that sleeps for the clock's settle delay.

```
    A PDE supply widget powers every entity on its managed list
    ─────────────────────────────────────────────────────────────

    ┌─────────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_supply  (one per PDE entity)                   │
    │   reg     = SDW_SDCA_CTL(adr, id, sel, 0)  Requested PS     │
    │   on_val  = SDCA_PDE_PS0     off_val = SDCA_PDE_PS3         │
    │   event   = entity_pde_event  (polls Actual PS until set)   │
    └───────────────────────────┬─────────────────────────────────┘
                                │ add_route per pde.managed[i]
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ managed[0]    │   │ managed[1]    │   │ managed[..]   │
    │ entity.label  │   │ entity.label  │   │ entity.label  │
    └───────────────┘   └───────────────┘   └───────────────┘
```

### A Mixer Unit becomes a DAPM mixer with per-source switches

[`entity_parse_mu()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L581) builds a [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428) widget with one [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) per input source, each a boolean volsw control over a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) with [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) of [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) (the mix is tracked entirely by DAPM in software) and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) set so the default is connected. The widget's [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) points at the per-source array, and one route per source carries the matching control name:

```c
/* sound/soc/sdca/sdca_asoc.c:636 */
	(*widget)->id = snd_soc_dapm_mixer;
	(*widget)->kcontrol_news = kctl;
	(*widget)->num_kcontrols = entity->num_sources;
	(*widget)++;

	for (i = 0; i < entity->num_sources; i++)
		add_route(route, entity->label, kctl[i].name, entity->sources[i]->label);
```

A Selector Unit is handled by [`entity_parse_su()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L554), which reads the Selector Control's access [`layers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810). When the control sits at the [`SDCA_ACCESS_LAYER_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L774) layer the selector is driven by a group entity and [`entity_parse_su_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L438) makes a [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426) using the group's [`ge.kctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1111); otherwise [`entity_parse_su_class()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L503) builds a [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426) with its own [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) whose first item is "No Signal" and whose remaining items are the source labels.

### Controls become volume, switch, or pin kcontrols

[`sdca_asoc_populate_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L986) walks every entity, adds a pin switch for a non-dataport terminal through [`populate_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L952), and calls [`populate_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L873) for each of the entity's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185):

```c
/* sound/soc/sdca/sdca_asoc.c:993 */
	for (i = 0; i < function->num_entities; i++) {
		struct sdca_entity *entity = &function->entities[i];

		switch (entity->type) {
		case SDCA_ENTITY_TYPE_IT:
		case SDCA_ENTITY_TYPE_OT:
			if (!entity->iot.is_dataport) {
				ret = populate_pin_switch(dev, entity, &kctl);
				if (ret)
					return ret;
			}
			break;
		default:
			break;
		}

		for (j = 0; j < entity->num_controls; j++) {
			ret = populate_control(dev, function, entity,
					       &entity->controls[j], &kctl);
			if (ret)
				return ret;
		}
	}
```

[`populate_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L873) is the control builder. It skips controls that [`exported_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L36) rejects, names the control "<entity> <control>" with a " Switch" suffix for a one-bit control, and walks the control's [`cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) channel bitmask to fill [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (first channel) and [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (second channel) with per-channel SDCA Control addresses, rejecting anything beyond stereo:

```c
/* sound/soc/sdca/sdca_asoc.c:901 */
	for_each_set_bit(cn, (unsigned long *)&control->cn_list,
			 BITS_PER_TYPE(control->cn_list)) {
		switch (index++) {
		case 0:
			mc->reg = SDW_SDCA_CTL(function->desc->adr, entity->id,
					       control->sel, cn);
			mc->rreg = mc->reg;
			break;
		case 1:
			mc->rreg = SDW_SDCA_CTL(function->desc->adr, entity->id,
						control->sel, cn);
			break;
		default:
			dev_err(dev, "%s: %s: only mono/stereo controls supported\n",
				entity->label, control->label);
			return -EINVAL;
		}
	}
```

It then sets the standard volsw handlers, swapping in [`volatile_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L831) and [`volatile_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L852) (which wrap the access in a runtime PM resume) when the control [`is_volatile`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), and sets [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) to read-only or read-write from [`readonly_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L49). A Q7.8 dB control gets a TLV through [`control_limit_kctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L781):

```c
/* sound/soc/sdca/sdca_asoc.c:926 */
	(*kctl)->name = control_name;
	(*kctl)->private_value = (unsigned long)mc;
	(*kctl)->iface = SNDRV_CTL_ELEM_IFACE_MIXER;
	(*kctl)->info = snd_soc_info_volsw;
	if (control->is_volatile) {
		(*kctl)->get = volatile_get_volsw;
		(*kctl)->put = volatile_put_volsw;
	} else {
		(*kctl)->get = snd_soc_get_volsw;
		(*kctl)->put = snd_soc_put_volsw;
	}

	if (readonly_control(control))
		(*kctl)->access = SNDRV_CTL_ELEM_ACCESS_READ;
	else
		(*kctl)->access = SNDRV_CTL_ELEM_ACCESS_READWRITE;

	ret = control_limit_kctl(dev, entity, control, *kctl);
	if (ret)
		return ret;

	(*kctl)++;
```

The resulting template is the same [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) a hand-written codec declares with `SOC_DOUBLE_R_EXT_TLV`; the only difference is that the register fields hold SDCA Control addresses and the handlers default to the generic [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332), [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375), and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) because regmap reaches the SDCA registers directly. [`populate_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L952) instead wires the DAPM pin handlers so an analog terminal can be enabled and disabled from userspace:

```c
/* sound/soc/sdca/sdca_asoc.c:952 */
static int populate_pin_switch(struct device *dev,
			       struct sdca_entity *entity,
			       struct snd_kcontrol_new **kctl)
{
	const char *control_name;

	control_name = devm_kasprintf(dev, GFP_KERNEL, "%s Switch", entity->label);
	if (!control_name)
		return -ENOMEM;

	(*kctl)->name = control_name;
	(*kctl)->private_value = (unsigned long)entity->label;
	(*kctl)->iface = SNDRV_CTL_ELEM_IFACE_MIXER;
	(*kctl)->info = snd_soc_dapm_info_pin_switch;
	(*kctl)->get = snd_soc_dapm_get_component_pin_switch;
	(*kctl)->put = snd_soc_dapm_put_component_pin_switch;
	(*kctl)++;

	return 0;
}
```

Past the pin switch, the volume and switch path walks the set channel bits of cn_list, the first filling reg and the second rreg of the mixer control, with more than two channels rejected and the kcontrol taking volsw handlers and a Switch suffix when it is one bit wide:

```
    cn_list channels become the reg / rreg of one stereo kcontrol
    ──────────────────────────────────────────────────────────────
    (populate_control: 1st set channel -> reg, 2nd -> rreg, >2 rejected)

    control->cn_list  (set bit = a Control Number / channel)
            │ for_each_set_bit, index 0,1
            ▼
    ┌──────────────────────────────────────────────────────┐
    │ struct soc_mixer_control                             │
    │   reg  = SDW_SDCA_CTL(desc->adr, id, sel, cn0)       │
    │   rreg = SDW_SDCA_CTL(desc->adr, id, sel, cn1)       │
    │   min / max / sdca_q78  (from control_limit_kctl)    │
    └───────────────────────────┬──────────────────────────┘
                                │ private_value
                                ▼
    ┌──────────────────────────────────────────────────────┐
    │ struct snd_kcontrol_new                              │
    │   name   "<entity> <control>"  (+ " Switch" if 1-bit)│
    │   info/get/put = volsw  (volatile_* if is_volatile)  │
    │   access = READ  or  READWRITE                       │
    └──────────────────────────────────────────────────────┘
```

### Each dataport terminal becomes a DAI driver

[`sdca_asoc_populate_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1169) emits one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) for each dataport terminal, choosing the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L417) stream for an Input Terminal and the [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L416) stream for an Output Terminal, naming the stream, setting [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) to 1 and [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) to [`SDCA_MAX_CHANNEL_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L39), filling the rates and formats, and recording the entity index in [`dais[j].id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) so the DAI ops can find the entity again:

```c
/* sound/soc/sdca/sdca_asoc.c:1176 */
	for (i = 0, j = 0; i < function->num_entities - 1; i++) {
		struct sdca_entity *entity = &function->entities[i];
		struct snd_soc_pcm_stream *stream;
		const char *stream_suffix;

		switch (entity->type) {
		case SDCA_ENTITY_TYPE_IT:
			stream = &dais[j].playback;
			stream_suffix = "Playback";
			break;
		case SDCA_ENTITY_TYPE_OT:
			stream = &dais[j].capture;
			stream_suffix = "Capture";
			break;
		default:
			continue;
		}

		/* Can't check earlier as only terminals have an iot member. */
		if (!entity->iot.is_dataport)
			continue;

		stream->stream_name = devm_kasprintf(dev, GFP_KERNEL, "%s %s",
						     entity->label, stream_suffix);
		if (!stream->stream_name)
			return -ENOMEM;
		/* Channels will be further limited by constraints */
		stream->channels_min = 1;
		stream->channels_max = SDCA_MAX_CHANNEL_COUNT;

		ret = populate_rate_format(dev, function, entity, stream);
		if (ret)
			return ret;

		dais[j].id = i;
		dais[j].name = entity->label;
		dais[j].ops = ops;
		j++;
	}
```

The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) attached to every DAI is the caller's, so the codec controls hw_params and stream start without the generation code knowing the transport. [`populate_rate_format()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1093) computes [`rates`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) and [`formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) by intersecting the clock source's available rates with the terminal's usage-control rates, mapping each surviving rate through [`rate_find_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1021) and its width through [`width_find_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1071):

```c
/* sound/soc/sdca/sdca_asoc.c:1137 */
	for (i = 0; i < range->rows; i++) {
		sample_rate = sdca_range(range, SDCA_USAGE_SAMPLE_RATE, i);
		sample_rate = rate_find_mask(sample_rate);

		if (sample_rate & clock_rates) {
			rates |= sample_rate;

			sample_width = sdca_range(range, SDCA_USAGE_SAMPLE_WIDTH, i);
			formats |= width_find_mask(sample_width);
		}
	}

	stream->formats = formats;
	stream->rates = rates;
```

### The generic SDCA class-function driver as the in-tree caller

[`class_function_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L292) is the one in-tree function that calls [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236). It is the probe for the generic SDCA class-function auxiliary driver, which binds to a single SDCA function on a SoundWire peripheral (the same kind of function the rt722-sdca codec exposes). The probe copies a template [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) per device, parses the function, then hands the parsed [`drv->function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) to the populate call along with [`class_function_sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L185) as the DAI ops:

```c
/* sound/soc/sdca/sdca_class_function.c:380 */
	if (desc->type == SDCA_FUNCTION_TYPE_UAJ)
		cmp_drv->set_jack = class_function_set_jack;

	ret = sdca_asoc_populate_component(dev, drv->function, cmp_drv,
					   &dais, &num_dais,
					   &class_function_sdw_ops);
	if (ret)
		return ret;
	...
	ret = devm_snd_soc_register_component(dev, cmp_drv, dais, num_dais);
	if (ret)
		return dev_err_probe(dev, ret, "failed to register component\n");
```

After the populate call, the component driver carries the generated widget, route, and control arrays, and `dais`/`num_dais` hold the generated DAI array. [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) then registers both, and the ASoC core instantiates the widgets, routes, controls, and DAIs through the same path a static codec uses. The DAI ops attach [`sdca_asoc_free_constraints()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1382) and the SoundWire stream callbacks, so the generated DAI participates in the normal SoundWire stream lifecycle:

```c
/* sound/soc/sdca/sdca_class_function.c:185 */
static const struct snd_soc_dai_ops class_function_sdw_ops = {
	.startup	= class_function_startup,
	.shutdown	= sdca_asoc_free_constraints,
	.set_stream	= class_function_sdw_set_stream,
	.hw_params	= class_function_sdw_add_peripheral,
	.hw_free	= class_function_sdw_remove_peripheral,
};
```

The template component driver is minimal, declaring only a probe, a remove, and the endianness flag, because everything else is filled by [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236):

```c
/* sound/soc/sdca/sdca_class_function.c:218 */
static const struct snd_soc_component_driver class_function_component_drv = {
	.probe			= class_function_component_probe,
	.remove			= class_function_component_remove,
	.endianness		= 1,
};
```

This is the mechanism that lets one generic driver serve any SDCA function. The entity graph parsed from firmware fully determines the DAPM topology, the controls, and the DAIs, so the driver supplies only the transport ops and the firmware parse, and [`sdca_asoc_populate_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_asoc.c#L1236) builds the rest of the ASoC component.
