# DAPM widget routing

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAPM route is a declarative record that names a connection between two audio widgets, and the kernel keeps the declaration and the instantiated connection in two separate types. A driver or topology file supplies an array of [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) entries, each a triple of three strings ([`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476)) plus an optional [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback, and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) resolves the two names to live [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) objects and asks [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) to allocate one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486). The path is the instantiated edge. It stores the two endpoint pointers in its [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) union, links itself onto the card's [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) list and onto each widget's [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) list, and carries the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit that says whether signal currently flows. When the route names a [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) ties the path to a mixer or mux kcontrol so the path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) state tracks that control, and when the route supplies a [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback the supply check in [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) calls it to gate a supply path dynamically. The Realtek rt722-sdca codec is the worked example, declaring its full audio map as the [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) array.

```
    A route declares {sink, control, source}; the core builds a path edge.

    route table (declarative)
    ┌──────────┬─────────┬──────────┐
    │  sink    │ control │  source  │
    ├──────────┼─────────┼──────────┤
    │ "FU 42"  │  NULL   │ "DP1RX"  │   static path, connect = 1
    │ "ADC 22  │ "MIC2"  │ "MIC2"   │   gated path, connect set
    │  Mux"    │         │          │   by the mux kcontrol
    └──────────┴─────────┴──────────┘
                   │  snd_soc_dapm_add_routes  ─▶  dapm_add_path
                   ▼
    instantiated edges (snd_soc_dapm_path)
    ┌────────┐         ┌────────┐         ┌────────┐
    │ DP1RX  │ ──────▶ │ FU 42  │ ──────▶ │   HP   │
    │ aif_in │ path A  │  dac   │ path B  │ output │
    └────────┘         └────────┘         └────────┘
        every path sits on both widgets' edges[] arrays
        (sink side = IN, source side = OUT); card->paths lists them all
```

## SUMMARY

A route describes a connection in words; a path is the object that connection becomes. A component driver lists routes in [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and a count in [`num_dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), each entry a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) naming the [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) (the receiving widget), the [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) (the sending widget), and an optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string that selects a mixer or mux leg. At card bring-up the core calls [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272), which holds the DAPM mutex and loops over the array calling [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) for each entry.

[`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) prefixes the names when the context has a component prefix, then resolves each string to a widget, first through the per-context [`wcache_sink`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L56) and [`wcache_source`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L57) caches via [`dapm_wcache_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1014) and otherwise by walking [`for_each_card_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1126) and comparing [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518). With both widgets in hand it calls [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604), which allocates a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), stores the source in [`node[SND_SOC_DAPM_DIR_IN]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and the sink in [`node[SND_SOC_DAPM_DIR_OUT]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), sets the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit (statically when there is no control, or from the mixer or mux kcontrol when there is), links the path onto [`dapm->card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), and for each direction adds the path's [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510) onto the corresponding widget's [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559).

After linking, [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) recomputes each endpoint's input and output category with [`dapm_update_widget_flags()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L507) and marks both widgets dirty with [`dapm_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220), and if the card is already running it invalidates the cached endpoint counts with [`dapm_path_invalidate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L314). The reverse [`snd_soc_dapm_del_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3298) removes paths through [`snd_soc_dapm_del_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3197), which finds the matching path on [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) and frees it with [`dapm_free_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2835). Topology adds routes the same way: [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026) builds a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) from each firmware graph element and calls [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272).

## SPECIFICATIONS

The [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) and [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) are Linux kernel software constructs of the ASoC power graph and have no standalone hardware specification. On the worked-example hardware the widget names the routes connect (FU, PDE, the data ports) come from an SDCA function topology.

## LINUX KERNEL

### Route and path types (soc-dapm.h)

- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): the declarative record, three name strings ([`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476)) plus the optional [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback and a [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L483) for topology bookkeeping
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): the instantiated edge, the [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499)/[`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496)/[`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497) union, the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503)/[`walking`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L504)/[`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) status bits, the [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback, and the [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510)/[`list_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L511)/[`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L513) link heads
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): a graph node; its [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) hold the input-side and output-side path lists, [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518) is what a route matches, and [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) decides whether a control attaches a mixer or a mux
- [`'\<enum snd_soc_dapm_direction\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600): [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), used to index both [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) and [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559)
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget kinds; [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_demux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427), and [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) change how a control or supply route is wired

### Adding and removing routes (soc-dapm.c)

- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): the public entry; takes the DAPM mutex and adds every route, returning the last error so teardown can free the partial graph
- [`'\<snd_soc_dapm_add_route\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100): resolve one route's [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) strings (with prefix handling and the cache) and hand them to [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604)
- [`'\<dapm_add_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604): allocate the [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), set the endpoint pointers and [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit, attach a control kcontrol when present, and link onto [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) and both widgets' [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559)
- [`'\<dapm_check_dynamic_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L558): reject a [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) on a route whose endpoints are neither a demux source nor a mux/mixer/switch sink
- [`'\<dapm_connect_mux\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L446): match the route's [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string against a mux/demux enum text and set [`path->connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) for the selected item
- [`'\<dapm_connect_mixer\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L482): find the named mixer or switch kcontrol on the sink widget and call [`dapm_set_mixer_path_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L398) to seed [`path->connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503)
- [`'\<dapm_set_mixer_path_status\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L398): read the mixer control's register to set the initial [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) state of one path
- [`'\<snd_soc_dapm_del_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3298) / [`'\<snd_soc_dapm_del_route\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3197): the removal entry that scans [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) for a matching path and frees it

### Widget lookup, path bookkeeping, and the walk

- [`'\<dapm_find_widget\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2894): resolve a pin name to a widget within a context, with optional fall back to another context
- [`'\<dapm_wcache_lookup\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1014): the bounded (depth 2) cache scan that short-circuits the full search for consecutive routes touching the same widgets
- [`'\<dapm_free_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2835): unlink a path from both widgets' edge lists, its kcontrol, and [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), then free it
- [`'\<dapm_update_widget_flags\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L507): recompute a widget's endpoint category from its edges after a path change
- [`'\<dapm_path_invalidate\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L314): reset the cached endpoint counts of the widgets a path touches
- [`'\<dapm_mark_dirty\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220): queue a widget on [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073)
- [`'\<dapm_is_connected_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487): the recursive edge walk; follows only edges whose [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set and skips [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) edges
- [`'\<dapm_supply_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749): the supply power check that calls a path's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback

### Iterators, macros, and card lists

- [`'\<for_each_card_widgets\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1126): iterate every widget on [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070)
- [`'\<snd_soc_dapm_widget_for_each_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717): iterate one direction of a widget's [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) via the path's [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510)
- [`'\<snd_soc_dapm_widget_for_each_sink_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L741) / [`'\<snd_soc_dapm_widget_for_each_source_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L750): the direction specializations
- [`'\<snd_soc_dapm_mutex_lock\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505): take the card's DAPM mutex
- [`'\<SND_SOC_NOPM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26): the sentinel register value (-1) marking a virtual mux

### rt722-sdca worked example and topology (codecs/rt722-sdca.c, soc-topology.c)

- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the array of routes that declares the codec's full graph
- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the component driver that registers [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so the core adds them at probe
- [`'\<soc_tplg_dapm_graph_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026): build a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) from each firmware graph element and add it with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): defines a widget as a part of the hardware that can be enabled and a route as an interconnection that exists when sound can flow
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide, where a driver lists its widgets and routes
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where front-end and back-end routes are stitched into one graph across a DAI link
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): jack detection, a common trigger for forcing pin widgets that route arrays terminate at

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A route is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) and a path is a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486); the table pairs each route field with what it becomes once [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) has run.

| Route field | Type | Becomes in the path |
|-------------|------|---------------------|
| `sink` | `const char *` | resolved to `node[SND_SOC_DAPM_DIR_OUT]` (the path's [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497)) |
| `source` | `const char *` | resolved to `node[SND_SOC_DAPM_DIR_IN]` (the path's [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496)) |
| `control` | `const char *` | NULL: static path, [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) = 1; non-NULL: ties [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) to a mixer/mux kcontrol |
| `connected` | `int (*)(...)` | copied to the path's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507); consulted only for supply paths |
| `dobj` | `struct snd_soc_dobj` | topology bookkeeping only; not copied to the path |

The path status bits the route does not set are filled by [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604).

| Path status bit | Width | Meaning |
|-----------------|-------|---------|
| `connect` | 1 | source and sink are connected; the walk follows the edge only when set |
| `walking` | 1 | the path is on the current recursion stack (cycle guard) |
| `is_supply` | 1 | at least one endpoint is a supply widget; the signal walk skips it |

## DETAILS

### Route versus path

A route is a constant description and a path is a mutable object. The route is three name strings and an optional callback, read exactly once when the route is added:

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

The path is the edge the route turns into. It stores resolved widget pointers in a union so the source and sink can be read either by name ([`p->source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496), [`p->sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497)) or by direction index ([`p->node[dir]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499)):

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

The names [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497) alias `node[0]` and `node[1]`, which are [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602):

```c
/* include/sound/soc-dapm.h:600 */
enum snd_soc_dapm_direction {
	SND_SOC_DAPM_DIR_IN,
	SND_SOC_DAPM_DIR_OUT,
};
```

The endpoint widgets each keep two edge lists indexed by the same enum, where [`edges[SND_SOC_DAPM_DIR_IN]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) holds the paths arriving and [`edges[SND_SOC_DAPM_DIR_OUT]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) the paths leaving. The two specialized iterators name the relationship from the path's point of view; both wrap [`snd_soc_dapm_widget_for_each_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717):

```c
/* include/sound/soc-dapm.h:741 */
#define snd_soc_dapm_widget_for_each_sink_path(w, p) \
	snd_soc_dapm_widget_for_each_path(w, SND_SOC_DAPM_DIR_IN, p)

#define snd_soc_dapm_widget_for_each_source_path(w, p) \
	snd_soc_dapm_widget_for_each_path(w, SND_SOC_DAPM_DIR_OUT, p)
```

The build helper turns one route record into one path, resolving the two name strings into the node[] pair by direction and copying the connected callback across:

```
    A route record resolves to one path; the union aliases node[]
    ──────────────────────────────────────────────────────────────

    struct snd_soc_dapm_route       struct snd_soc_dapm_path
    ┌────────────────────┐          ┌─────────────────────────┐
    │ source   (name)    │ ───────▶ │ node[IN]   = source     │
    │ sink     (name)    │ ───────▶ │ node[OUT]  = sink        │
    │ control  (name)    │          │ connect : 1             │
    │ connected (cb)     │ ───────▶ │ connected (cb)          │
    └────────────────────┘          └─────────────────────────┘
        dapm_add_path resolves both names, fills node[] by direction
        node[IN] = SND_SOC_DAPM_DIR_IN, node[OUT] = SND_SOC_DAPM_DIR_OUT
```

### Routes are added at card bring-up

[`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) takes the card's DAPM mutex and adds each entry in order, keeping the last error so the caller can tear the card down on failure:

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

According to the kernel-doc, "The sink is the widget receiving the audio signal, whilst the source is the sender of the audio signal", and "On error all resources can be freed with a call to snd_soc_card_free()". The rt722-sdca codec registers its array and count on the component driver, so the core calls this for the codec's routes during card instantiation. Topology adds routes through the same call: [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026) fills a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) from each firmware graph element, records its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L483) for later unload, and adds it one at a time:

```c
/* sound/soc/soc-topology.c:1076 */
	/* add route dobj to dobj_list */
	route->dobj.type = SND_SOC_DOBJ_GRAPH;
	if (tplg->ops)
		route->dobj.unload = tplg->ops->dapm_route_unload;
	route->dobj.index = tplg->index;
	list_add(&route->dobj.list, &tplg->comp->dobj_list);

	ret = soc_tplg_add_route(tplg, route);
	...
	ret = snd_soc_dapm_add_routes(dapm, route, 1);
	if (ret)
		break;
```

### A route names widgets by string and resolves them

[`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) first applies the context's component prefix to the [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) names, because a widget on a prefixed component carries the prefix in its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518), then resolves each name to a widget. The fast path is the per-context one-entry cache; on a miss it walks every widget with [`for_each_card_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1126), favouring a widget from the current DAPM context:

```c
/* sound/soc/soc-dapm.c:3100 */
	wsource	= dapm_wcache_lookup(dapm->wcache_source, source);
	wsink	= dapm_wcache_lookup(dapm->wcache_sink,   sink);

	if (wsink && wsource)
		goto skip_search;

	/*
	 * find src and dest widgets over all widgets but favor a widget from
	 * current DAPM context
	 */
	for_each_card_widgets(dapm->card, w) {
		if (!wsink && !(strcmp(w->name, sink))) {
			wtsink = w;
			if (w->dapm == dapm) {
				wsink = w;
				if (wsource)
					break;
			}
			...
		}
		...
	}
```

[`dapm_wcache_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1014) scans only two list entries from the last hit, which covers an array that touches the same widget on consecutive rows:

```c
/* sound/soc/soc-dapm.c:1014 */
static struct snd_soc_dapm_widget *
dapm_wcache_lookup(struct snd_soc_dapm_widget *w, const char *name)
{
	if (w) {
		struct list_head *wlist = &w->dapm->card->widgets;
		const int depth = 2;
		int i = 0;

		list_for_each_entry_from(w, wlist, list) {
			if (!strcmp(name, w->name))
				return w;

			if (++i == depth)
				break;
		}
	}

	return NULL;
}
```

When both widgets are found it updates the cache and calls [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604), passing the route's [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) and [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) through; a missing widget fails the route with an error line naming the unresolved side.

The same string-to-widget resolution is exposed on its own for the pin API as [`dapm_find_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2894), which prefixes the pin name the same way a route name is prefixed and walks [`for_each_card_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1126), preferring a widget in the caller's own context and only falling back to a widget in another context when asked:

```c
/* sound/soc/soc-dapm.c:2894 */
static struct snd_soc_dapm_widget *dapm_find_widget(
			struct snd_soc_dapm_context *dapm, const char *pin,
			bool search_other_contexts)
{
	struct snd_soc_dapm_widget *w;
	struct snd_soc_dapm_widget *fallback = NULL;
	char prefixed_pin[80];
	const char *pin_name;
	const char *prefix = dapm_prefix(dapm);

	if (prefix) {
		snprintf(prefixed_pin, sizeof(prefixed_pin), "%s %s",
			 prefix, pin);
		pin_name = prefixed_pin;
	} else {
		pin_name = pin;
	}

	for_each_card_widgets(dapm->card, w) {
		if (!strcmp(w->name, pin_name)) {
			if (w->dapm == dapm)
				return w;
			else
				fallback = w;
		}
	}

	if (search_other_contexts)
		return fallback;

	return NULL;
}
```

[`dapm_find_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2894) is the route-resolution loop boiled down to one name, returning the matched [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) so the pin enable and disable paths can name an endpoint the same way a route's [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) do.

### dapm_add_path instantiates the edge

[`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) takes the two resolved widgets, the route's [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string, and its [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback, and starts by rejecting the route shapes it cannot represent. It refuses a non-supply into a supply, a [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback on a non-supply source, or a control on a supply source:

```c
/* sound/soc/soc-dapm.c:604 */
static int dapm_add_path(
	struct snd_soc_dapm_context *dapm,
	struct snd_soc_dapm_widget *wsource, struct snd_soc_dapm_widget *wsink,
	const char *control,
	int (*connected)(struct snd_soc_dapm_widget *source,
			 struct snd_soc_dapm_widget *sink))
{
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	enum snd_soc_dapm_direction dir;
	struct snd_soc_dapm_path *path;
	int ret;

	if (wsink->is_supply && !wsource->is_supply) {
		dev_err(dev,
			"Connecting non-supply widget to supply widget is not supported (%s -> %s)\n",
			wsource->name, wsink->name);
		return -EINVAL;
	}

	if (connected && !wsource->is_supply) {
		dev_err(dev,
			"connected() callback only supported for supply widgets (%s -> %s)\n",
			wsource->name, wsink->name);
		return -EINVAL;
	}

	if (wsource->is_supply && control) {
		dev_err(dev,
			"Conditional paths are not supported for supply widgets (%s -> [%s] -> %s)\n",
			wsource->name, control, wsink->name);
		return -EINVAL;
	}
```

This is where the route's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback restriction is enforced, because the callback is copied to [`path->connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) only for a supply source, matching the kernel-doc note on the route field that the callback is currently supported only when the source is a supply. After the guards, [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) calls [`dapm_check_dynamic_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L558) to validate a control against the endpoint kinds, then allocates the path and stores the resolved endpoints by direction:

```c
/* sound/soc/soc-dapm.c:604 */
	ret = dapm_check_dynamic_path(dapm, wsource, wsink, control);
	if (ret)
		return ret;

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
```

The route's source becomes [`node[SND_SOC_DAPM_DIR_IN]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and its sink becomes [`node[SND_SOC_DAPM_DIR_OUT]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), and [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) is set if either widget is a supply.

### The widget kind decides how a control is wired

Every widget carries an [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) drawn from [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), and that kind is what [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) switches on to decide whether a [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) names a mux leg, a mixer leg, or nothing at all:

```c
/* include/sound/soc-dapm.h:423 */
enum snd_soc_dapm_type {
	snd_soc_dapm_input = 0,		/* input pin */
	snd_soc_dapm_output,		/* output pin */
	snd_soc_dapm_mux,		/* selects 1 analog signal from many inputs */
	snd_soc_dapm_demux,		/* connects the input to one of multiple outputs */
	snd_soc_dapm_mixer,		/* mixes several analog signals together */
	snd_soc_dapm_mixer_named_ctl,	/* mixer with named controls */
	snd_soc_dapm_pga,		/* programmable gain/attenuation (volume) */
	snd_soc_dapm_out_drv,		/* output driver */
	snd_soc_dapm_adc,		/* analog to digital converter */
	snd_soc_dapm_dac,		/* digital to analog converter */
	snd_soc_dapm_micbias,		/* microphone bias (power) - DEPRECATED: use snd_soc_dapm_supply */
	snd_soc_dapm_mic,		/* microphone */
	snd_soc_dapm_hp,		/* headphones */
	snd_soc_dapm_spk,		/* speaker */
	snd_soc_dapm_line,		/* line input/output */
	snd_soc_dapm_switch,		/* analog switch */
	snd_soc_dapm_vmid,		/* codec bias/vmid - to minimise pops */
	snd_soc_dapm_pre,		/* machine specific pre widget - exec first */
	snd_soc_dapm_post,		/* machine specific post widget - exec last */
	snd_soc_dapm_supply,		/* power/clock supply */
	snd_soc_dapm_pinctrl,		/* pinctrl */
	snd_soc_dapm_regulator_supply,	/* external regulator */
	snd_soc_dapm_clock_supply,	/* external clock */
	snd_soc_dapm_aif_in,		/* audio interface input */
	snd_soc_dapm_aif_out,		/* audio interface output */
	snd_soc_dapm_siggen,		/* signal generator */
	snd_soc_dapm_sink,
	snd_soc_dapm_dai_in,		/* link to DAI structure */
	snd_soc_dapm_dai_out,
	snd_soc_dapm_dai_link,		/* link between two DAI structures */
	snd_soc_dapm_kcontrol,		/* Auto-disabled kcontrol */
	snd_soc_dapm_buffer,		/* DSP/CODEC internal buffer */
	snd_soc_dapm_scheduler,		/* DSP/CODEC internal scheduler */
	snd_soc_dapm_effect,		/* DSP/CODEC effect component */
	snd_soc_dapm_src,		/* DSP/CODEC SRC component */
	snd_soc_dapm_asrc,		/* DSP/CODEC ASRC component */
	snd_soc_dapm_encoder,		/* FW/SW audio encoder component */
	snd_soc_dapm_decoder,		/* FW/SW audio decoder component */

	/* Don't edit below this line */
	SND_SOC_DAPM_TYPE_COUNT
};
```

Only a handful of these kinds make a control meaningful: [`snd_soc_dapm_demux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427) on the source side and [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426), [`snd_soc_dapm_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L439), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), and [`snd_soc_dapm_mixer_named_ctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L429) on the sink side; [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) and its variants ([`snd_soc_dapm_regulator_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L445), [`snd_soc_dapm_clock_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L446)) are the kinds whose paths get [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) set and are skipped by the signal walk.

```
    Which widget id makes a control meaningful (dapm_check_dynamic_path)
    ───────────────────────────────────────────────────────────────────

    ┌──────────────────────────────┬────────┬──────────────┐
    │ widget id                    │ side   │ control?     │
    ├──────────────────────────────┼────────┼──────────────┤
    │ snd_soc_dapm_demux           │ source │ mux leg      │
    │ snd_soc_dapm_mux             │ sink   │ mux leg      │
    │ snd_soc_dapm_switch          │ sink   │ mixer leg    │
    │ snd_soc_dapm_mixer           │ sink   │ mixer leg    │
    │ snd_soc_dapm_mixer_named_ctl │ sink   │ mixer leg    │
    │ snd_soc_dapm_supply          │ either │ none, is_sup │
    └──────────────────────────────┴────────┴──────────────┘
```

### A control name ties the path to a mixer or mux kcontrol

When the route names no control the path is static, with [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) set to 1; when it names a control, [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) dispatches on the endpoint widget kind:

```c
/* sound/soc/soc-dapm.c:604 */
	/* connect static paths */
	if (control == NULL) {
		path->connect = 1;
	} else {
		switch (wsource->id) {
		case snd_soc_dapm_demux:
			ret = dapm_connect_mux(dapm, path, control, wsource);
			...
		}

		switch (wsink->id) {
		case snd_soc_dapm_mux:
			ret = dapm_connect_mux(dapm, path, control, wsink);
			...
		case snd_soc_dapm_switch:
		case snd_soc_dapm_mixer:
		case snd_soc_dapm_mixer_named_ctl:
			ret = dapm_connect_mixer(dapm, path, control);
			...
		}
	}
```

A control whose sink is a [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426) (or whose source is a [`snd_soc_dapm_demux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427)) goes through [`dapm_connect_mux()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L446), which matches the control string against the mux's enumeration texts and sets [`path->connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) when that leg is the selected item; a virtual mux marked [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) defaults to the first item:

```c
/* sound/soc/soc-dapm.c:446 */
static int dapm_connect_mux(struct snd_soc_dapm_context *dapm,
			    struct snd_soc_dapm_path *path, const char *control_name,
			    struct snd_soc_dapm_widget *w)
{
	const struct snd_kcontrol_new *kcontrol = &w->kcontrol_news[0];
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;
	unsigned int item;
	int i;

	if (e->reg != SND_SOC_NOPM) {
		unsigned int val;

		val = dapm_read(dapm, e->reg);
		val = (val >> e->shift_l) & e->mask;
		item = snd_soc_enum_val_to_item(e, val);
	} else {
		/* since a virtual mux has no backing registers to
		 * decide which path to connect, it will try to match
		 * with the first enumeration.  ...
		 */
		item = 0;
	}

	i = match_string(e->texts, e->items, control_name);
	if (i < 0)
		return -ENODEV;

	path->name = e->texts[i];
	path->connect = (i == item);
	return 0;
}
```

A control whose sink is a [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_mixer_named_ctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L429), or [`snd_soc_dapm_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L439) goes through [`dapm_connect_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L482), which finds the named kcontrol on the sink widget and seeds the path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) state with [`dapm_set_mixer_path_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L398):

```c
/* sound/soc/soc-dapm.c:482 */
static int dapm_connect_mixer(struct snd_soc_dapm_context *dapm,
			      struct snd_soc_dapm_path *path, const char *control_name)
{
	int i, nth_path = 0;

	/* search for mixer kcontrol */
	for (i = 0; i < path->sink->num_kcontrols; i++) {
		if (!strcmp(control_name, path->sink->kcontrol_news[i].name)) {
			path->name = path->sink->kcontrol_news[i].name;
			dapm_set_mixer_path_status(path, i, nth_path++);
			return 0;
		}
	}
	return -ENODEV;
}
```

Before any of this, [`dapm_check_dynamic_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L558) has already rejected a control on a pair of widgets that is neither a demux source nor a mux/mixer/switch sink, so a control string only reaches a widget that can interpret it:

```c
/* sound/soc/soc-dapm.c:558 */
	switch (sink->id) {
	case snd_soc_dapm_mux:
	case snd_soc_dapm_switch:
	case snd_soc_dapm_mixer:
	case snd_soc_dapm_mixer_named_ctl:
		dynamic_sink = true;
		break;
	default:
		break;
	}

	if (dynamic_source && dynamic_sink) {
		dev_err(dev,
			"Direct connection between demux and mixer/mux not supported ...");
		return -EINVAL;
	} else if (!dynamic_source && !dynamic_sink) {
		dev_err(dev,
			"Control not supported for path %s -> [%s] -> %s\n",
			source->name, control, sink->name);
		return -EINVAL;
	}
```

### Linking the path onto the card and both widgets

Once the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is decided, [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) threads the path onto the card's global [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) list and onto each endpoint widget's [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) list, then recomputes the widget flags and marks both ends dirty:

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

The loop over [`enum snd_soc_dapm_direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600) adds the path to the sink's incoming edges and the source's outgoing edges through the symmetric [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510) entries. For the rt722-sdca codec the routes in [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) build the whole graph this way. A static triple `{"FU 42", NULL, "DP1RX"}` becomes a permanently connected edge from the AIF widget into the DAC, while a gated triple `{"ADC 22 Mux", "MIC2", "MIC2"}` becomes an edge whose [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is seeded from the `"ADC 22 Mux"` mux kcontrol's `"MIC2"` selection, so the same array of strings the codec declares becomes the directed graph [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) later walks.

```
    One path links onto three lists at once (dapm_add_path)
    ───────────────────────────────────────────────────────

                   ┌───────────────────┐
                   │ snd_soc_dapm_path │
                   └─────────┬─────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────────┐┌──────────────┐┌──────────────┐
      │ card->paths  ││ sink  widget ││ source widget│
      │ list         ││ edges[IN]    ││ edges[OUT]   │
      │ (every edge) ││ list_node[IN]││list_node[OUT]│
      └──────────────┘└──────────────┘└──────────────┘
```

### Adding a path invalidates cached endpoint counts

The last thing [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) does when the card is already running is call [`dapm_path_invalidate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L314), which clears the memoized input and output endpoint counts on the widgets the new edge touches so the next power walk recomputes them:

```c
/* sound/soc/soc-dapm.c:314 */
static void dapm_path_invalidate(struct snd_soc_dapm_path *p)
{
	/*
	 * Weak paths or supply paths do not influence the number of input or
	 * output paths of their neighbors.
	 */
	if (p->is_supply)
		return;

	/*
	 * The number of connected endpoints is the sum of the number of
	 * connected endpoints of all neighbors. If a node with 0 connected
	 * endpoints is either connected or disconnected that sum won't change,
	 * so there is no need to re-check the path.
	 */
	if (p->source->endpoints[SND_SOC_DAPM_DIR_IN] != 0)
		dapm_widget_invalidate_input_paths(p->sink);
	if (p->sink->endpoints[SND_SOC_DAPM_DIR_OUT] != 0)
		dapm_widget_invalidate_output_paths(p->source);
}
```

A supply path is skipped because it does not change a neighbor's signal endpoint count, and a neighbor that already has zero connected endpoints cannot have that sum change, so [`dapm_path_invalidate()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L314) only walks the [`endpoints[]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) cache outward when it can actually shift. The same call runs whenever a path is added, removed, or has its [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) state flipped, keeping the cache the walk reads in step with the graph.

### The connected-endpoint walk follows only connected non-supply edges

[`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) is the inlined core shared by the input and output endpoint checks; it is what reads the directed graph the routes built. It memoizes per-direction via [`endpoints[dir]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549), stops at a connected terminal endpoint, and otherwise recurses across each neighbour edge, following the edge only when its [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set and skipping any [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) edge:

```c
/* sound/soc/soc-dapm.c:1487 */
static __always_inline int dapm_is_connected_ep(struct snd_soc_dapm_widget *widget,
	struct list_head *list, enum snd_soc_dapm_direction dir,
	int (*fn)(struct snd_soc_dapm_widget *, struct list_head *,
		  bool (*custom_stop_condition)(struct snd_soc_dapm_widget *,
						enum snd_soc_dapm_direction)),
	bool (*custom_stop_condition)(struct snd_soc_dapm_widget *,
				      enum snd_soc_dapm_direction))
{
	enum snd_soc_dapm_direction rdir = DAPM_DIR_REVERSE(dir);
	struct snd_soc_dapm_path *path;
	int con = 0;

	if (widget->endpoints[dir] >= 0)
		return widget->endpoints[dir];
	...
	snd_soc_dapm_widget_for_each_path(widget, rdir, path) {
		DAPM_UPDATE_STAT(widget, neighbour_checks);

		if (path->is_supply)
			continue;

		if (path->walking)
			return 1;

		trace_snd_soc_dapm_path(widget, dir, path);

		if (path->connect) {
			path->walking = 1;
			con += fn(path->node[dir], list, custom_stop_condition);
			path->walking = 0;
		}
	}

	widget->endpoints[dir] = con;

	return con;
}
```

The walk reaches a path's far end through [`path->node[dir]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499), the same direction-indexed pointer [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) filled in. A path with [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) clear is invisible to it, which is exactly how a mux or mixer that has not selected this leg disconnects a branch of the graph, and the [`walking`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L504) bit set around the recursion guards against cycles.

```
    dapm_is_connected_ep: follow connect=1 edges, skip is_supply edges
    ─────────────────────────────────────────────────────────────────

      widget                neighbour            terminal endpoint
      ┌──────────┐  connect  ┌──────────┐ connect  ┌────────────┐
      │ start    │ ────────▶ │  mixer   │ ───────▶ │ output ep  │
      │ endpoints│   = 1     │ recurse  │   = 1    │ stops walk │
      └────┬─────┘           └──────────┘          └────────────┘
           │ is_supply edge
           ▼
      ┌──────────────┐
      │ supply       │  skipped (continue): never followed
      └──────────────┘
```

### A supply path consults its connected callback

The one place the route's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback is consulted is [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749), which decides whether a supply widget is needed by looking at its sink-side paths and treating a path as inactive when its [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback returns false:

```c
/* sound/soc/soc-dapm.c:1749 */
static int dapm_supply_check_power(struct snd_soc_dapm_widget *w)
{
	struct snd_soc_dapm_path *path;

	DAPM_UPDATE_STAT(w, power_checks);

	/* Check if one of our outputs is connected */
	snd_soc_dapm_widget_for_each_sink_path(w, path) {
		DAPM_UPDATE_STAT(w, neighbour_checks);

		if (path->connected &&
		    !path->connected(path->source, path->sink))
			continue;

		if (dapm_widget_power_check(path->sink))
			return 1;
	}

	return 0;
}
```

Because [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) only copies the route's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback to [`path->connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) for a supply source, this gate runs only on supply paths. The callback returning false skips that downstream sink, and the supply stays unpowered if no remaining sink needs it. This is the dynamic counterpart to the static [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit that gates the signal walk in [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487).

### Removing routes tears the edge back down

The reverse of adding is [`snd_soc_dapm_del_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3298), which mirrors [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): it takes the DAPM mutex and removes each entry one at a time through [`snd_soc_dapm_del_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3197):

```c
/* sound/soc/soc-dapm.c:3298 */
int snd_soc_dapm_del_routes(struct snd_soc_dapm_context *dapm,
			    const struct snd_soc_dapm_route *route, int num)
{
	int i;

	snd_soc_dapm_mutex_lock(dapm);
	for (i = 0; i < num; i++) {
		snd_soc_dapm_del_route(dapm, route);
		route++;
	}
	snd_soc_dapm_mutex_unlock(dapm);

	return 0;
}
```

[`snd_soc_dapm_del_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3197) refuses to remove a route that names a [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475), applies the same name prefix the add side does, then scans [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) for the one path whose [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497) names match the route's, marks both ends dirty, invalidates the cache, and frees the path:

```c
/* sound/soc/soc-dapm.c:3227 */
	path = NULL;
	list_for_each_entry(p, &dapm->card->paths, list) {
		if (strcmp(p->source->name, source) != 0)
			continue;
		if (strcmp(p->sink->name, sink) != 0)
			continue;
		path = p;
		break;
	}

	if (path) {
		struct snd_soc_dapm_widget *wsource = path->source;
		struct snd_soc_dapm_widget *wsink = path->sink;

		dapm_mark_dirty(wsource, "Route removed");
		dapm_mark_dirty(wsink, "Route removed");
		if (path->connect)
			dapm_path_invalidate(path);

		dapm_free_path(path);

		/* Update any path related flags */
		dapm_update_widget_flags(wsource);
		dapm_update_widget_flags(wsink);
	} else {
		dev_warn(dev, "ASoC: Route %s->%s does not exist\n",
			 source, sink);
	}
```

The matching path is unlinked everywhere [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) linked it. [`dapm_free_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2835) removes the path's two [`list_node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L510) entries from both widgets' edge lists, its [`list_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L511) entry from any control it was tied to, and its [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L513) entry from the card, then frees the object:

```c
/* sound/soc/soc-dapm.c:2835 */
static void dapm_free_path(struct snd_soc_dapm_path *path)
{
	list_del(&path->list_node[SND_SOC_DAPM_DIR_IN]);
	list_del(&path->list_node[SND_SOC_DAPM_DIR_OUT]);
	list_del(&path->list_kcontrol);
	list_del(&path->list);
	kfree(path);
}
```

### Topology builds routes from a firmware graph

The firmware-driven consumer of the route API is [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026), which turns each [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L341) in a topology file into a heap-allocated [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), copying the firmware's [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476), [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474), and optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) strings into it:

```c
/* sound/soc/soc-topology.c:1026 */
static int soc_tplg_dapm_graph_elems_load(struct soc_tplg *tplg,
	struct snd_soc_tplg_hdr *hdr)
{
	struct snd_soc_dapm_context *dapm = snd_soc_component_to_dapm(tplg->comp);
	const size_t maxlen = SNDRV_CTL_ELEM_ID_NAME_MAXLEN;
	struct snd_soc_tplg_dapm_graph_elem *elem;
	struct snd_soc_dapm_route *route;
	int count, i;
	int ret = 0;

	count = le32_to_cpu(hdr->count);
	...
	for (i = 0; i < count; i++) {
		route = devm_kzalloc(tplg->dev, sizeof(*route), GFP_KERNEL);
		if (!route)
			return -ENOMEM;
		elem = (struct snd_soc_tplg_dapm_graph_elem *)tplg->pos;
		tplg->pos += sizeof(struct snd_soc_tplg_dapm_graph_elem);
		...
		route->source = devm_kstrdup(tplg->dev, elem->source, GFP_KERNEL);
		route->sink = devm_kstrdup(tplg->dev, elem->sink, GFP_KERNEL);
		...
		if (strnlen(elem->control, maxlen) != 0) {
			route->control = devm_kstrdup(tplg->dev, elem->control, GFP_KERNEL);
			...
		}
```

Each constructed route then flows through the same path-building machinery a driver's static array does. After recording the [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L483) for unload (shown above), the loader calls [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) on the single freshly built route, so a topology graph and a codec's [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) reach [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) by the same route.
