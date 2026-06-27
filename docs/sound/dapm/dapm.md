# DAPM overview

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

DAPM (Dynamic Audio Power Management) models an audio device as a directed graph and keeps powered only the blocks that sit on an active stream path. The graph is built from three record types and one per-domain context. A node is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), one power-controllable point carrying an [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) from [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) (for example [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L429), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427), [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), or [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424)) and the register coordinates ([`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529), [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L530), [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531), [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532)) that switch it. An instantiated edge is a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), the declarative edge a driver writes is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and each widget belongs to a [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) that tracks the bias level of one component or the card. The card roots the whole graph in lists on [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and DAPM rewalks it whenever a stream starts or stops or a kcontrol changes. The Realtek RT722 SDCA codec on SoundWire is the worked example, declaring its pins, feature units, and power-domain supplies as the [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) array and the wiring as the [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) route array.

```
    snd_soc_dapm_widget nodes joined by snd_soc_dapm_path edges
    ──────────────────────────────────────────────────────────

       ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
       │  MIC2        │     │  LINE1       │     │  LINE2       │
       │ (input, EP)  │     │ (input, EP)  │     │ (input, EP)  │
       └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
              │                    │                    │
              ▼                    ▼                    ▼
            ┌────────────────────────────────────────────────┐
            │              ADC 22 Mux  (mux)                 │
            └───────────────────────┬────────────────────────┘
                                    ▼
                          ┌───────────────────┐
                          │  FU 36  (adc)     │
                          └─────────┬─────────┘
                                    ▼
                          ┌───────────────────┐
                          │  DP2TX  (aif_out) │
                          │  endpoint (EP)    │
                          └───────────────────┘

    each ─▶ is one snd_soc_dapm_path; connect=1 makes the edge live
```

## SUMMARY

DAPM holds an in-memory directed graph of the audio hardware so a power-controllable block draws current only while a stream routes audio through it. The graph has three record types. A node is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), naming one power-controllable point and holding the register field that switches it. An edge is a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), linking a source widget to a sink widget and carrying a [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit for whether the edge currently passes signal. A declarative edge is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), the static `{sink, control, source}` triple a driver writes and which [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) resolves into a path. Every widget belongs to a [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44), a power domain whose [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) advances through [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415), from [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) through [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419).

The card owns the graph. The [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070), [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), and [`dapm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1072) lists on [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) thread every widget, path, and context, the [`dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073) list queues widgets whose power needs rechecking, and [`dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) serializes every mutation and power run. A component receives its context from [`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189) at [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) and is bound to the card by [`snd_soc_dapm_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4877). At bring-up the core instantiates each component's widget templates with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932), wires the card routes with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272), and finalizes the new widgets with [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322). The power algorithm [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) walks every complete path from a source endpoint to a sink endpoint and powers exactly the widgets that lie on one. The full widget taxonomy, the routing detail, and the power walk are each their own page.

## SPECIFICATIONS

The DAPM graph is a Linux kernel software construct and has no standalone hardware specification. On the worked-example hardware each widget corresponds to an SDCA entity (a feature unit or a power-domain entity) reached over SoundWire; this page describes only the kernel graph.

## LINUX KERNEL

### Graph record types (include/sound/soc-dapm.h)

- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): one graph node; carries the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) type, the [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533)/[`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535)/[`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) bits, the register coordinates, the [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists, the [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555), and the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L521) back pointer
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): one instantiated edge; the [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) pair (aliased [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496)/[`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497)) and the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): the declarative `{`[`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476)`}` triple a driver writes, with an optional [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) predicate
- [`'\<enum snd_soc_bias_level\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415): the four power levels [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416), [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417), [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418), [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419)
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget type tag set; the full taxonomy is a separate page
- [`'\<enum snd_soc_dapm_direction\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600): [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), the two indices into the widget [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) array and the path [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) array

### The DAPM context (sound/soc/soc-dapm.c)

- [`'\<struct snd_soc_dapm_context\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44): one power domain; holds [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) and [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53), the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L49) and [`card`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L50) back pointers, the [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L54) node, and the [`wcache_sink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L56)/[`wcache_source`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L57) lookup caches
- [`'\<snd_soc_dapm_alloc\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189): allocate one context with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) tied to the device
- [`'\<snd_soc_dapm_init\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4877): set the [`card`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L50)/[`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L49) back pointers, seed [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416), and link onto [`card->dapm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1072)
- [`'\<snd_soc_dapm_to_dev\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L194): resolve a context to its [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565)

### Card-owned graph lists (include/sound/soc.h)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): roots the graph in [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070), [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), [`dapm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1072), and [`dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073), guarded by [`dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998); the card's own context is [`card->dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1079) and its declarative input is [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1063)/[`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1065)

### Graph construction at card bring-up (sound/soc/soc-dapm.c, sound/soc/soc-core.c)

- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932): instantiate an array of widget templates into live widgets, each via [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757)
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): resolve an array of routes into paths, each via [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100)
- [`'\<snd_soc_dapm_add_route\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100): look up the source and sink widgets by name and call [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604)
- [`'\<dapm_add_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604): allocate one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), set its [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) pair, and add it to [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) and both widgets' [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists
- [`'\<snd_soc_dapm_new_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322): finalize every not-yet-finished widget, read its initial power state, mark it dirty, and run [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once
- [`'\<snd_soc_component_initialize\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850): allocate the component's [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) context from [`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189)
- [`'\<dapm_mark_dirty\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220): queue a widget on [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073) so the next power run rechecks it
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): the power algorithm that scans the dirty widgets, computes target power and per-context bias, and runs the up and down sequences

### Widget template macros (include/sound/soc-dapm.h)

- [`'\<SND_SOC_DAPM_INPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) / [`'\<SND_SOC_DAPM_OUTPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64): declare an input or output pin endpoint widget
- [`'\<SND_SOC_DAPM_PGA\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) / [`'\<SND_SOC_DAPM_MIXER\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106) / [`'\<SND_SOC_DAPM_MUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129): declare a gain stage, a mixer, or a selector widget with a register field
- [`'\<SND_SOC_DAPM_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308): declare a power or clock supply widget with an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback
- [`'\<SND_SOC_DAPM_AIF_IN\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) / [`'\<SND_SOC_DAPM_AIF_OUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265): declare the audio-interface endpoint widget that ties the graph to a DAI stream
- [`'\<SND_SOC_NOPM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26): the [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) sentinel (-1) for a widget with no direct register control

### rt722-sdca worked example (sound/soc/codecs/rt722-sdca.c)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the codec's widget array (pins, feature units, muxes, supplies, AIF endpoints)
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the codec's route array joining those widgets
- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that carries [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1094) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1096) to the core

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM concept, the widget types, and the route declaration syntax
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component, card, and DAPM model at a glance
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): codec driver guide covering the widget and route arrays a codec registers
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the pop and click suppression that the bias-level sequencing addresses
- [`Documentation/sound/soc/codec-to-codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec-to-codec.rst): codec-to-codec links, where DAPM routes connect two codecs without a CPU DAI

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The graph is built and queried through a small set of entry points, each taking or reaching a [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) and running under [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998). A driver supplies declarative input (a widget-template array and a route array), and the core turns it into live nodes and edges.

| Entry point | Input | Effect on the graph |
|-------------|-------|---------------------|
| [`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189) | a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) | allocate one context |
| [`snd_soc_dapm_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4877) | context, card, component | bind context, add to `dapm_list` |
| [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) | template array | add nodes to `widgets` |
| [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) | route array | add edges to `paths` |
| [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) | card | finalize nodes, run power once |
| [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) | card, event | recompute and apply power |

A widget template is one entry of a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) array built with the `SND_SOC_DAPM_*` macros, and a route is one [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) `{`[`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476)`}` triple naming two widgets and the optional kcontrol that gates the edge. A [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) of NULL is a static edge that is always connected, and a non-NULL [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) names a mixer or mux kcontrol whose setting decides whether the edge passes signal.

## DETAILS

### The widget is the graph node

A [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) represents one power-controllable point. Its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) selects a type from [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), the register fields [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) through [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) tell DAPM how to switch it, the status bits [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533), [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534), and [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) record its state, the two [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists hold its incoming and outgoing paths, and the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L521) pointer names the owning context:

```c
/* include/sound/soc-dapm.h:516 */
struct snd_soc_dapm_widget {
	enum snd_soc_dapm_type id;
	const char *name;			/* widget name */
	const char *sname;			/* stream name */
	struct list_head list;
	struct snd_soc_dapm_context *dapm;

	void *priv;				/* widget specific data */
	struct regulator *regulator;		/* attached regulator */
	struct pinctrl *pinctrl;		/* attached pinctrl */

	/* dapm control */
	int reg;				/* negative reg = no direct dapm */
	unsigned char shift;			/* bits to shift */
	unsigned int mask;			/* non-shifted mask */
	unsigned int on_val;			/* on state value */
	unsigned int off_val;			/* off state value */
	unsigned char power:1;			/* block power status */
	unsigned char active:1;			/* active stream on DAC, ADC's */
	unsigned char connected:1;		/* connected codec pin */
	unsigned char new:1;			/* cnew complete */
	unsigned char force:1;			/* force state */
	unsigned char ignore_suspend:1;		/* kept enabled over suspend */
	unsigned char new_power:1;		/* power from this run */
	unsigned char power_checked:1;		/* power checked this run */
	unsigned char is_supply:1;		/* Widget is a supply type widget */
	unsigned char is_ep:2;			/* Widget is a endpoint type widget */
	unsigned char no_wname_in_kcontrol_name:1; /* No widget name prefix in kcontrol name */
	int subseq;				/* sort within widget type */

	int (*power_check)(struct snd_soc_dapm_widget *w);

	/* external events */
	unsigned short event_flags;		/* flags to specify event types */
	int (*event)(struct snd_soc_dapm_widget*, struct snd_kcontrol *, int);

	/* kcontrols that relate to this widget */
	int num_kcontrols;
	const struct snd_kcontrol_new *kcontrol_news;
	struct snd_kcontrol **kcontrols;
	struct snd_soc_dobj dobj;

	/* widget input and output edges */
	struct list_head edges[2];

	/* used during DAPM updates */
	struct list_head work_list;
	struct list_head power_list;
	struct list_head dirty;
	int endpoints[2];

	struct clk *clk;

	int channel;
};
```

The [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) array has two elements indexed by [`enum snd_soc_dapm_direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600), so [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) at [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) lists the paths arriving and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602) lists those leaving. The two-bit [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) field marks endpoint widgets, the ones a power walk can start or finish at, and the [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback with [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) lets a widget run driver code at power-up or power-down. The [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) field is signed, and a negative value written as [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) means the widget has no register of its own and DAPM powers it by graph position, which is how every widget in the SoundWire worked example is declared.

```
    snd_soc_dapm_widget: register coordinates plus a status bitfield
    ────────────────────────────────────────────────────────────────

      register field that switches the block (reg < 0 = SND_SOC_NOPM)
      ┌──────┬───────┬──────┬────────┬─────────┐
      │ reg  │ shift │ mask │ on_val │ off_val │
      └──────┴───────┴──────┴────────┴─────────┘

      status bits (1 bit each, is_ep is 2 bits)
        power         block is powered on now
        active        a stream runs on this DAC / ADC
        connected     codec pin is wired up
        new           cnew finished (finalized)
        force         power forced on
        new_power     power decided this run
        power_checked already evaluated this run
        is_supply     widget is a supply type
        is_ep:2       endpoint: SOURCE start / SINK end of a walk

      id ──▶ enum snd_soc_dapm_type      dapm ──▶ owning context
      edges[IN] arriving paths           edges[OUT] leaving paths
```

### The path is the instantiated edge

A [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) connects exactly two widgets. A union gives the same two pointers two names, so [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497) read naturally in code while [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) is indexed by direction during the walk, and the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit says whether the edge currently passes signal:

```c
/* include/sound/soc-dapm.h:486 */
struct snd_soc_dapm_path {
	const char *name;

	/*
	 * source (input) and sink (output) widgets
	 * The union is for convience, since it is a lot nicer to type
	 * p->source, rather than p->node[SND_SOC_DAPM_DIR_IN]
	 */
	union {
		struct {
			struct snd_soc_dapm_widget *source;
			struct snd_soc_dapm_widget *sink;
		};
		struct snd_soc_dapm_widget *node[2];
	};

	/* status */
	u32 connect:1;		/* source and sink widgets are connected */
	u32 walking:1;		/* path is in the process of being walked */
	u32 is_supply:1;	/* At least one of the connected widgets is a supply */

	int (*connected)(struct snd_soc_dapm_widget *source,
			 struct snd_soc_dapm_widget *sink);

	struct list_head list_node[2];
	struct list_head list_kcontrol;
	struct list_head list;
};
```

Each path appears on three kinds of list. The [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L513) node threads it onto [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), and the two [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510) entries thread it onto the [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) list of each widget, so the same path is reachable globally and from either end. For a static edge the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set once at creation, and for a mixer or mux edge it follows the kcontrol that gates the signal.

```
    snd_soc_dapm_path: a union names the two ends; three list heads
    ──────────────────────────────────────────────────────────────

      union { source ; sink }  aliases  node[2]
      ┌───────────────────────┬───────────────────────┐
      │ source = node[DIR_IN] │ sink = node[DIR_OUT]  │
      └───────────────────────┴───────────────────────┘

      status bits        connect:1   walking:1   is_supply:1

      link heads (same path on three lists at once)
      ┌──────────────┬───────────────┬───────────────┐
      │ list         │ list_node[2]  │ list_kcontrol │
      │ card->paths  │ each widget's │ owning mixer/ │
      │ (every edge) │ edges[dir]    │ mux kcontrol  │
      └──────────────┴───────────────┴───────────────┘
```

### The route is the declarative form

A driver does not build paths directly; it writes a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) triple naming a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) widget, an optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) kcontrol, and a [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) widget, and the core resolves the names into widget pointers and creates the path:

```c
/* include/sound/soc-dapm.h:473 */
struct snd_soc_dapm_route {
	const char *sink;
	const char *control;
	const char *source;

	/* Note: currently only supported for links where source is a supply */
	int (*connected)(struct snd_soc_dapm_widget *source,
			 struct snd_soc_dapm_widget *sink);

	struct snd_soc_dobj dobj;
};
```

[`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) takes the locked mutex once and calls [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) for each entry:

```c
/* sound/soc/soc-dapm.c:3272 */
int snd_soc_dapm_add_routes(struct snd_soc_dapm_context *dapm,
			    const struct snd_soc_dapm_route *route, int num)
{
	int i, ret = 0;

	snd_soc_dapm_mutex_lock(dapm);
	for (i = 0; i < num; i++) {
		int r = snd_soc_dapm_add_route(dapm, route);
		if (r < 0)
			ret = r;
		route++;
	}
	snd_soc_dapm_mutex_unlock(dapm);

	return ret;
}
```

[`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) resolves the [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) names to widgets, consulting the [`wcache_source`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L57) and [`wcache_sink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L56) caches before scanning [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070), then hands the two widgets and the [`route->control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) to [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604):

```c
/* sound/soc/soc-dapm.c:3100 */
	wsource	= dapm_wcache_lookup(dapm->wcache_source, source);
	wsink	= dapm_wcache_lookup(dapm->wcache_sink,   sink);

	if (wsink && wsource)
		goto skip_search;
	...
skip_search:
	/* update cache */
	dapm->wcache_sink	= wsink;
	dapm->wcache_source	= wsource;

	ret = dapm_add_path(dapm, wsource, wsink, route->control,
		route->connected);
```

### dapm_add_path allocates the edge and links both ends

[`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) allocates one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), stores the two widgets in its [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) pair indexed by [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), and sets [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) to 1 when the route has no [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475):

```c
/* sound/soc/soc-dapm.c:641 */
	path = kzalloc_obj(struct snd_soc_dapm_path);
	if (!path)
		return -ENOMEM;

	path->node[SND_SOC_DAPM_DIR_IN] = wsource;
	path->node[SND_SOC_DAPM_DIR_OUT] = wsink;

	path->connected = connected;
	INIT_LIST_HEAD(&path->list);
	INIT_LIST_HEAD(&path->list_kcontrol);

	if (wsource->is_supply || wsink->is_supply)
		path->is_supply = 1;

	/* connect static paths */
	if (control == NULL) {
		path->connect = 1;
	} else {
```

After the kcontrol handling, the path is threaded onto the card list and onto each widget's edge list, and both widgets are marked dirty so the next power run reconsiders them:

```c
/* sound/soc/soc-dapm.c:687 */
	list_add(&path->list, &dapm->card->paths);

	dapm_for_each_direction(dir)
		list_add(&path->list_node[dir], &path->node[dir]->edges[dir]);

	dapm_for_each_direction(dir) {
		dapm_update_widget_flags(path->node[dir]);
		dapm_mark_dirty(path->node[dir], "Route added");
	}
```

The loop over [`enum snd_soc_dapm_direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600) adds the path to the sink's incoming edges and the source's outgoing edges through the symmetric [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510) entries, so a later traversal can follow edges out of a source or into a sink with the same indexing.

### The context is one power domain

A [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) groups the widgets that share a bias state. Its [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) is the current power level and [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) is the level a running computation wants to reach, both from [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415); the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L49) and [`card`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L50) back pointers name what the context belongs to, and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L54) node sits on the card's context list:

```c
/* sound/soc/soc-dapm.c:44 */
struct snd_soc_dapm_context {
	enum snd_soc_bias_level bias_level;

	bool idle_bias;				/* Use BIAS_OFF instead of STANDBY when false */

	struct snd_soc_component *component;	/* parent component */
	struct snd_soc_card *card;		/* parent card */

	/* used during DAPM updates */
	enum snd_soc_bias_level target_bias_level;
	struct list_head list;

	struct snd_soc_dapm_widget *wcache_sink;
	struct snd_soc_dapm_widget *wcache_source;

#ifdef CONFIG_DEBUG_FS
	struct dentry *debugfs_dapm;
#endif
};
```

The bias levels run from off to full power:

```c
/* include/sound/soc-dapm.h:415 */
enum snd_soc_bias_level {
	SND_SOC_BIAS_OFF = 0,
	SND_SOC_BIAS_STANDBY = 1,
	SND_SOC_BIAS_PREPARE = 2,
	SND_SOC_BIAS_ON = 3,
};
```

The card holds one context of its own in [`card->dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1079), and every component holds its own in the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) field of [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207). All of them link on [`card->dapm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1072), so a power run iterates every domain.

```
    enum snd_soc_bias_level: one context climbs and descends the ladder
    ──────────────────────────────────────────────────────────────────

      value   level                  bias_level ──▶ target_bias_level

        3   ┌──────────────┐  ON        full power, signal flowing
            │ SND_SOC_BIAS │
        2   │   _PREPARE   │  PREPARE   transitional, around ON
        1   │              │  STANDBY   supplies up, idle floor
        0   └──────────────┘  OFF       powered down (init seed)

      up:    OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON
      down:  ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF
```

### A component gets its context at initialization

A component's context comes into existence in [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850), which calls [`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189) and stores the result in [`component->dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207):

```c
/* sound/soc/soc-core.c:2850 */
int snd_soc_component_initialize(struct snd_soc_component *component,
				 const struct snd_soc_component_driver *driver,
				 struct device *dev)
{
	component->dapm = snd_soc_dapm_alloc(dev);
	if (!component->dapm)
		return -ENOMEM;
```

[`snd_soc_dapm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L189) is a thin device-managed allocation, so the context is freed with the component device:

```c
/* sound/soc/soc-dapm.c:189 */
struct snd_soc_dapm_context *snd_soc_dapm_alloc(struct device *dev)
{
	return devm_kzalloc(dev, sizeof(struct snd_soc_dapm_context), GFP_KERNEL);
}
```

[`snd_soc_dapm_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4877) later binds the context to a card, filling the [`card`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L50) and [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L49) back pointers, seeding [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416), and linking onto [`card->dapm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1072):

```c
/* sound/soc/soc-dapm.c:4877 */
void snd_soc_dapm_init(struct snd_soc_dapm_context *dapm,
		       struct snd_soc_card *card,
		       struct snd_soc_component *component)
{
	dapm->card		= card;
	dapm->component		= component;
	dapm->bias_level	= SND_SOC_BIAS_OFF;

	if (component)
		dapm->idle_bias		= component->driver->idle_bias_on;

	INIT_LIST_HEAD(&dapm->list);
	/* see for_each_card_dapms */
	list_add(&dapm->list, &card->dapm_list);
}
```

### Widgets and routes are added at card bring-up

Once the context is bound, the per-component probe path calls [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) with the driver's [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) array right after [`snd_soc_dapm_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4877):

```c
/* sound/soc/soc-core.c:1632 */
	snd_soc_dapm_init(dapm, card, component);

	ret = snd_soc_dapm_new_controls(dapm,
					component->driver->dapm_widgets,
					component->driver->num_dapm_widgets);
```

[`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) turns each template into a live widget with [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757), adding nodes to [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070):

```c
/* sound/soc/soc-dapm.c:3932 */
int snd_soc_dapm_new_controls(struct snd_soc_dapm_context *dapm,
	const struct snd_soc_dapm_widget *widget,
	unsigned int num)
{
	int i;
	int ret = 0;

	snd_soc_dapm_mutex_lock_root(dapm);
	for (i = 0; i < num; i++) {
		struct snd_soc_dapm_widget *w = snd_soc_dapm_new_control_unlocked(dapm, widget);
		if (IS_ERR(w)) {
			ret = PTR_ERR(w);
			break;
		}
		widget++;
	}
	snd_soc_dapm_mutex_unlock(dapm);
	return ret;
}
```

The card-level wiring is added later in the card probe through [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) on [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1065), after the component widgets and routes are in place. The card probe then finalizes the graph with [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322), which completes any widget whose [`new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L536) bit is clear, reads each widget's initial power state from its register, marks it dirty, and runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once so the graph reaches a consistent state before the card registers:

```c
/* sound/soc/soc-dapm.c:3322 */
int snd_soc_dapm_new_widgets(struct snd_soc_card *card)
{
	struct snd_soc_dapm_widget *w;
	unsigned int val;

	snd_soc_dapm_mutex_lock_root(card);

	for_each_card_widgets(card, w)
	{
		if (w->new)
			continue;
		...
		/* Read the initial power state from the device */
		if (w->reg >= 0) {
			val = dapm_read(w->dapm, w->reg);
			val = val >> w->shift;
			val &= w->mask;
			if (val == w->on_val)
				w->power = 1;
		}

		w->new = 1;

		dapm_mark_dirty(w, "new widget");
		dapm_debugfs_add_widget(w);
	}

	dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, NULL);
	snd_soc_dapm_mutex_unlock(card);
	return 0;
}
```

The three bring-up calls run in this order, one adding the widget nodes, the next adding the path edges, and this last one reading initial power and running the power pass once:

```
    Card bring-up adds nodes, then edges, then finalizes and powers
    ──────────────────────────────────────────────────────────────

      snd_soc_dapm_new_controls    template array ──▶ live widgets
        │                          added to card->widgets (nodes)
        ▼
      snd_soc_dapm_add_routes      route array ──▶ paths
        │                          added to card->paths (edges)
        ▼
      snd_soc_dapm_new_widgets     read initial power, mark dirty,
                                   run dapm_power_widgets() once

      nodes exist before edges link them; the single power run lands
      the graph consistent before the card registers.
```

### Powering only the active part of the graph

[`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) turns the graph into register writes. According to its leading comment it powers a widget only when it sits on a complete path from a valid source endpoint to a valid sink endpoint:

```c
/* sound/soc/soc-dapm.c:2252 */
/*
 * Scan each dapm widget for complete audio path.
 * A complete path is a route that has valid endpoints i.e.:-
 *
 *  o DAC to output pin.
 *  o Input pin to ADC.
 *  o Input pin to Output pin (bypass, sidetone)
 *  o DAC to ADC (loopback).
 */
static int dapm_power_widgets(struct snd_soc_card *card, int event,
			      struct snd_soc_dapm_update *update)
```

It first floors every context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53), then checks the dirty widgets and sorts them into an up list and a down list:

```c
/* sound/soc/soc-dapm.c:2278 */
	for_each_card_dapms(card, d) {
		if (snd_soc_dapm_get_idle_bias(d))
			d->target_bias_level = SND_SOC_BIAS_STANDBY;
		else
			d->target_bias_level = SND_SOC_BIAS_OFF;
	}

	dapm_reset(card);
	...
	list_for_each_entry(w, &card->dapm_dirty, dirty) {
		dapm_power_one_widget(w, &up_list, &down_list);
	}
```

How a widget's power is decided, how a context's bias is raised to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) for an active path or only to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) for a supply, and how the up and down sequences run are the subject of a separate page. This page establishes only that the data model the walk reads is the widget, path, and context graph above.

### rt722-sdca builds its graph from widgets and routes

The Realtek RT722 declares its DAPM graph as two static arrays the component driver passes to the core. The widget array [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) declares the endpoint pins with [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) and [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60), the power-domain entities as [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) widgets with event callbacks, the feature units as DAC and ADC widgets, the input selectors with [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129), and the SoundWire data-port endpoints with [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) and [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265), each one declared with [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) because power is driven by the supply events:

```c
/* sound/soc/codecs/rt722-sdca.c:996 */
static const struct snd_soc_dapm_widget rt722_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("MIC2"),
	SND_SOC_DAPM_INPUT("LINE1"),
	SND_SOC_DAPM_INPUT("LINE2"),
	SND_SOC_DAPM_INPUT("DMIC1_2"),
	SND_SOC_DAPM_INPUT("DMIC3_4"),

	SND_SOC_DAPM_SUPPLY("PDE 23", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde23_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	...
	SND_SOC_DAPM_MUX("ADC 22 Mux", SND_SOC_NOPM, 0, 0,
		&rt722_sdca_adc22_mux),
	...
	SND_SOC_DAPM_AIF_IN("DP1RX", "DP1 Headphone Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP2TX", "DP2 Headset Capture", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_IN("DP3RX", "DP3 Speaker Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP6TX", "DP6 DMic Capture", 0, SND_SOC_NOPM, 0, 0),
};
```

The route array [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) is the declarative wiring, where each triple names a sink, an optional control, and a source:

```c
/* sound/soc/codecs/rt722-sdca.c:1043 */
static const struct snd_soc_dapm_route rt722_sdca_audio_map[] = {
	{"FU 42", NULL, "DP1RX"},
	{"FU 21", NULL, "DP3RX"},

	{"ADC 22 Mux", "MIC2", "MIC2"},
	{"ADC 22 Mux", "LINE1", "LINE1"},
	{"ADC 22 Mux", "LINE2", "LINE2"},
	...
	{"DP2TX", NULL, "FU 36"},
	{"DP6TX", NULL, "FU 113"},

	{"HP", NULL, "PDE 47"},
	{"HP", NULL, "FU 42"},
	{"SPK", NULL, "PDE 23"},
	{"SPK", NULL, "FU 21"},
};
```

The triple `{"ADC 22 Mux", "MIC2", "MIC2"}` is an edge into the `ADC 22 Mux` sink from the `MIC2` source gated by the mux control's `MIC2` selection, so [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) leaves the path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit under the kcontrol, whereas `{"DP2TX", NULL, "FU 36"}` has a NULL control and creates a permanently connected edge from the `FU 36` feature unit to the `DP2TX` SoundWire output port. A supply triple such as `{"HP", NULL, "PDE 47"}` connects a power-domain supply widget to the endpoint it powers, so a walk reaching `HP` also brings up the `PDE 47` domain. The component driver carries both arrays to the core through [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090):

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
	...
};
```

When this codec binds, the core calls [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) on the widget array to create the nodes on [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070), then [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) on the route array to create the edges on [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), and the result is the directed graph [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) walks to power only the headset or speaker path the running stream uses.

```
    rt722-sdca playback + speaker paths; PDE supplies hang off sideways
    ──────────────────────────────────────────────────────────────────

      ┌────────┐      ┌────────┐      ┌────────┐
      │ DP1RX  │ ───▶ │ FU 42  │ ───▶ │   HP   │ ◀── PDE 47 (supply)
      │ aif_in │      │  dac   │      │ output │
      └────────┘      └────────┘      └────────┘

      ┌────────┐      ┌────────┐      ┌────────┐
      │ DP3RX  │ ───▶ │ FU 21  │ ───▶ │  SPK   │ ◀── PDE 23 (supply)
      │ aif_in │      │  dac   │      │ output │
      └────────┘      └────────┘      └────────┘

      static routes {"HP",NULL,"FU 42"} and {"SPK",NULL,"FU 21"} pass
      signal; {"HP",NULL,"PDE 47"} ties the supply to the output pin.
```
