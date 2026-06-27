# SOF topology consumer

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Sound Open Firmware (SOF) is a consumer of the generic ASoC topology loader. The binary topology file describes the DSP audio graph as DAPM widgets, graph routes, PCMs, kcontrols, and DAI links, and the ASoC core parses that file and hands each decoded object to a driver through a registered [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) function pointer struct, which SOF supplies as [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) and passes into [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) from [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494), so the load-time callbacks [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628), [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087), [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726), [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873), [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961), and [`sof_manifest()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279) build the SOF objects [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), and [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) onto the per-device lists, parsing each element's vendor tokens into the target object with [`sof_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810) against a [`struct sof_topology_token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) table, with the per-widget DSP message build deferred to the IPC-version stage [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) whose [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) the runtime PCM path calls to turn each loaded widget into a live module on an Intel Meteor Lake or Lunar Lake DSP.

```
    SOF turns a loaded topology widget into a live DSP module
    ─────────────────────────────────────────────────────────

    topology .tplg file
    ┌────────────────────────────────┐
    │ struct snd_soc_tplg_dapm_widget│
    │   id (DAPM type)               │
    │   name / sname                 │
    │   num_kcontrols                │
    │   struct snd_soc_tplg_private  │  ──▶  vendor tuple arrays
    │     (vendor tuple arrays)      │
    └───────────────┬────────────────┘
                    │ snd_soc_tplg_component_load()
                    │   (generic parse loop)
                    ▼
            sof_tplg_ops.widget_ready
            ┌──────────────────────────┐
            │ sof_widget_ready()       │
            │   sof_parse_tokens()     │
            └───────────────┬──────────┘
                            ▼
                struct snd_sof_widget          on sdev->widget_list
                ┌──────────────────────────┐
                │ scomp, comp_id, id       │
                │ pipeline_id, core        │
                │ num_tuples, tuples       │
                │ private  ──▶ IPC4 blob   │   (copier / gain / pipeline)
                └───────────────┬──────────┘
                                │ ipc4_tplg_ops.widget_setup
                                │   (runtime, at PCM open)
                                ▼
                       sof_ipc4_widget_setup()
                       ┌──────────────────────────┐
                       │ build struct sof_ipc4_msg│
                       │ assign instance_id       │
                       │ send IPC to DSP          │
                       └───────────────┬──────────┘
                                       ▼
                                 live DSP module
```

## SUMMARY

The ASoC topology core owns the binary file format and the parse loop. A component driver registers a [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) and the core calls one member of it per object it decodes from the topology blob. SOF defines that struct as the file-scope [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) and hands its address to [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) inside [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494), which is the bridge from the generic loader to the SOF object model. The bound load callbacks are [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961) for kcontrols, [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087) for graph routes, [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) for DAPM widgets, [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) for front-end DAIs, [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873) for DAI links, and [`sof_manifest()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279) for the topology manifest header, with [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628) and [`sof_dai_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842) bound as the matching unload paths. The [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123) slot is left unset; according to the comment in [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), "/* .widget_load is not currently used */", so SOF builds its widget object from the [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) callback that fires after the core has fully created the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516).

Each load callback allocates one SOF object and threads it onto a per-device list held in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547). [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) creates a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and adds it to [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626), [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087) creates a [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) on [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630), [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) creates a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) on [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624), and a DAI-type widget additionally creates a [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) on [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L628) through [`sof_connect_dai_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068). The vendor data attached to each object is decoded by [`sof_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810), which walks a [`struct sof_topology_token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) definition table and writes each decoded value into the target object at the table entry's [`offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305). SOF does not register the [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154) member; instead [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) calls [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192) explicitly once the loader returns.

The IPC-version layer is the second function pointer struct. [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) holds the per-widget [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op array and the runtime [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) members that translate a loaded SOF object into the wire IPC the firmware understands, and on an x86-64 ACPI Meteor Lake or Lunar Lake machine the IPC4 firmware binds [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973). The two stages are distinct in time. The LOAD stage runs once when the topology file is parsed and builds every [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) through [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305); the runtime SETUP stage instantiates DSP modules from those objects through [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) when a PCM is opened, reached from [`sof_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251) and [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258). This page owns the LOAD stage and the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) construction; the IPC4 message build that [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) performs is documented in depth on the SOF IPC4 topology load and runtime pages.

## SPECIFICATIONS

The [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) loader contract and the SOF [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) object model are Linux kernel software constructs and have no standalone hardware specification. The binary topology file format is defined by the ASoC topology UAPI in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h), where [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) and [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) are the on-disk records the loader decodes, each carrying a trailing [`struct snd_soc_tplg_private`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L236) vendor tuple block. The vendor tokens those blocks carry, the module and pipeline structure of the graph, and the IPC4 messages the second stage emits come from the Intel Audio DSP firmware interface that Sound Open Firmware implements as open firmware on the Cadence-based Audio DSP shipped on Intel SoC platforms from Tiger Lake and Meteor Lake onward, rather than from a ratified public standard, and the project documentation is public.

## LINUX KERNEL

### Generic loader interface (soc-topology.h, soc-topology.c)

- [`'\<struct snd_soc_tplg_ops\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108): the public function pointer struct a component registers; the core invokes one member per decoded topology object ([`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L111), [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L117), [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123), [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126), [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L133), [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L141), [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154), [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L157))
- [`'\<snd_soc_tplg_component_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122): the entry a consumer calls with its ops and the firmware blob; sets up the parse context and runs [`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2073), which dispatches into the registered callbacks
- [`'\<soc_tplg_widget_ready\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L269): the core helper that calls [`ops->widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) after [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) has built the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516)
- [`'\<struct snd_soc_tplg_dapm_widget\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480): the on-disk widget record carrying the DAPM [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480), name, kcontrol count, and a trailing [`struct snd_soc_tplg_private`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L236) vendor block
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the runtime DAPM widget the core has fully built by the time [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) is called; SOF stores its [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) back into the [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) field
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the DAPM widget type enum copied verbatim into [`swidget->id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422); the cases [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) dispatches on include [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451), [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452), and [`snd_soc_dapm_scheduler`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L456)

### SOF registered ops and the load entry (topology.c)

- [`'sof_tplg_ops':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305): the SOF instance of [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108); binds [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961), [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087), [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628), [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726), [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873), and [`sof_manifest()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279); leaves [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123) and [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154) unset
- [`'\<snd_sof_load_topology\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494): requests each topology firmware file and calls [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) with [`&sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), then runs [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192) explicitly; called from [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L786)
- [`'\<sof_widget_ready\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409): allocates a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), parses widget and pin tokens, dispatches by DAPM [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) to build the per-widget private data, and links it onto [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626)
- [`'\<sof_widget_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628): the [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L129) callback; reverses [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), frees the per-widget kcontrols and IPC data through the [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) op, and removes the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) from [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626)
- [`'\<sof_route_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087): allocates a [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), resolves source and sink to [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) with [`snd_sof_find_swidget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L956), and drops edges whose endpoint is [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425) or [`snd_soc_dapm_out_drv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L431)
- [`'\<sof_dai_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726): allocates a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) for a front-end DAI, copies the topology PCM record, parses [`stream_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L409), and allocates the DMA page tables
- [`'\<sof_dai_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842): the [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L138) callback; frees the PCM DMA pages, runs the [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) IPC op, and removes the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) from [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624)
- [`'\<sof_link_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873): for a back-end link, calls the IPC-version [`link_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op, allocates a [`struct snd_sof_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410), and parses the [`common_dai_link_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1867) plus per-DAI hardware-config tokens
- [`'\<sof_control_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961): builds a [`struct snd_sof_control`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373) for a volume, enum, or bytes kcontrol and links it onto [`kcontrol_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L625)
- [`'\<sof_manifest\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279): forwards the topology manifest header to the IPC-version [`parse_manifest`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op
- [`'\<sof_complete\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192): run after the whole file is loaded; updates the IPC structs for every kcontrol and widget through the [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) op and assigns each widget its pipeline
- [`'\<sof_connect_dai_widget\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068): for a [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) or [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widget, matches the widget stream name to a card DAI link and records the link name in the new [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547)

### Token parsing (topology.c, sof-audio.h)

- [`'\<struct sof_topology_token\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305): one token definition; carries the [`token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) number, its wire [`type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305), a [`get_token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) decode function pointer, and the [`offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) within the target object where the value is stored
- [`'\<sof_parse_tokens\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810): parses one set of vendor tuples against a token definition table into a target object; a thin wrapper over [`sof_parse_token_sets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L724) with one set
- [`'\<sof_parse_token_sets\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L724): the multi-set parser; walks consecutive vendor arrays and dispatches by tuple type into [`sof_parse_word_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L673), [`sof_parse_string_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L627), or [`sof_parse_uuid_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L456)
- [`'dapm_widget_tokens':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1403) / [`'comp_pin_tokens':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L428) / [`'stream_tokens':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L409) / [`'common_dai_link_tokens':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1867): the [`struct sof_topology_token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) tables for widget identity, widget pin counts, PCM streams, and DAI links

### SOF objects (sof-audio.h)

- [`'\<struct snd_sof_widget\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422): the SOF view of a DAPM widget; carries [`comp_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), [`pipeline_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) (DAPM type), the parsed [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), the [`spipe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) pipeline back pointer, and the IPC4 [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) blob
- [`'\<struct snd_sof_route\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531): a graph edge; holds [`src_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), [`sink_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), the negotiated [`src_queue_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) and [`dst_queue_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), and the [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag set once the DSP connection exists
- [`'\<struct snd_sof_dai\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547): the SOF DAI object; carries the DAI [`name`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), the DAI [`type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), and the IPC4 [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) copier data; a DAI widget's [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) points here
- [`'\<struct snd_sof_pcm\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352): an ALSA PCM device; carries the per-direction [`stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) state and a trailing copy of the topology [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) record
- [`'\<struct snd_sof_dai_link\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410): a back-end DAI link; carries the [`link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410) pointer, the [`hw_configs`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410) array, and the parsed [`tuples`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410)
- [`'\<struct snd_sof_control\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373): an ALSA kcontrol device; carries the [`info_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373), the topology [`priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373) blob, and the [`ipc_control_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373) built at completion
- [`'\<struct snd_sof_dev\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547): the per-device root holding [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624), [`kcontrol_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L625), [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626), [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L627), [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L628), [`dai_link_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L629), and [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630)

### IPC-version layer (sof-audio.h, sof-audio.c, ipc4-topology.c)

- [`'\<struct sof_ipc_tplg_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221): the IPC-version function pointer struct holding the per-widget-type [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op array, the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and the runtime [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) members
- [`'\<struct sof_ipc_tplg_widget_ops\>':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181): one widget type's IPC ops; carries the load-time [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) and [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), the per-widget [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181), and [`bind_event`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181)
- [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973): the IPC4 instance bound on x86-64 ACPI; points [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) at [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925) and [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) at [`ipc4_token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L197)
- [`'\<sof_ipc4_widget_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103): the runtime [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op; builds a [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) from the widget's private blob and sends the module-init IPC to the DSP
- [`'\<sof_ipc4_route_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472): the runtime [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op; sends the module-bind IPC connecting the source module output pin to the sink module input pin
- [`'\<sof_ipc4_dai_config\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628): the runtime [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op; programs the gateway and DMA node into a DAI copier
- [`'sof_ipc_get_ops':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541): the accessor macro reaching the active [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) through [`sdev->ipc->ops->tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503)

### Runtime setup callers (sof-audio.c)

- [`'\<sof_widget_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251): the runtime entry that instantiates one widget in the DSP; takes the widget's [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and calls [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144)
- [`'\<sof_widget_setup_unlocked\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144): the per-widget setup driver; skips a widget with no private data, increments a use count, then invokes [`tplg_ops->widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) and, for DAI widgets, [`tplg_ops->dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221)
- [`'\<sof_route_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258): the runtime entry that establishes one DSP connection; finds the [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) for a source/sink widget pair and calls [`tplg_ops->route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221)
- [`'\<snd_sof_find_swidget\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L956): walks [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) to look up a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) by DAPM widget name, used by [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087) to wire route endpoints

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget and route model the topology file encodes and the SOF callbacks consume
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI link split that [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) and [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873) handle separately
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and DAI link description whose links the topology back ends complete in [`sof_connect_dai_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068)
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept underlying the DAI widgets and links SOF loads
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle a SoundWire back-end link drives on an x86-64 ACPI SOF card

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF topology and the IPC4 ABI](https://thesofproject.github.io/latest/architectures/firmware/sof-common/topology.html)
- [SOF introduction and architecture](https://thesofproject.github.io/latest/introduction/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The two function pointer structs are the seam. The generic loader is driven by [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), which SOF fills as [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305); the IPC-version stage is driven by [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), bound as [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973) on an Intel MTL or LNL machine. The table below maps each topology element the loader decodes to the SOF load callback that builds the corresponding SOF object, the object it creates, and the per-device list it lands on. Each SOF object has exactly one creator and is freed by the matching unload callback or, where none is listed, when the device's lists are torn down.

| Topology element | SOF load callback ([`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305)) | SOF object created | Device list | Freed by |
|------------------|------------------|--------------------|-------------|----------|
| DAPM widget | [`sof_widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) | [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) | [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) | [`sof_widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628) |
| graph route | [`sof_route_load`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087) | [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) | [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630) | [`sof_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1611) |
| front-end PCM | [`sof_dai_load`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) | [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) | [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624) | [`sof_dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842) |
| DAI widget | [`sof_widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) (via [`sof_connect_dai_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068)) | [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) | [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L628) | [`sof_widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628) |
| back-end DAI link | [`sof_link_load`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873) | [`struct snd_sof_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410) | [`dai_link_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L629) | [`sof_link_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2068) |
| kcontrol | [`sof_control_load`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961) | [`struct snd_sof_control`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373) | [`kcontrol_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L625) | [`sof_control_unload`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1038) |
| manifest | [`sof_manifest`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279) | (forwarded to IPC layer) | (none) | (none) |

The runtime instantiation goes through the second struct, separately in time. The PCM open path calls [`sof_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251) for each widget on the connected DAPM path and [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) for each edge between them, and these reach the IPC4 functions [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103), [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472), and [`sof_ipc4_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3628) through the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221), and [`dai_config`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) members of [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973). The bodies of those three are the subject of the SOF IPC4 topology load and runtime pages.

### widget_ready

[`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) is bound to [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409). The core calls it once per DAPM widget after [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) has constructed the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), so SOF reads a finished widget rather than a template. It allocates one [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), parses the identity and pin tokens into it, builds the per-widget private data for the widget type, and links the object onto [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) while also recording it back into [`w->dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516).

### widget_unload

[`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L129) is bound to [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628). It recovers the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) from the [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) pointer, unwinds the DAI or scheduler special case, frees every per-widget kcontrol, releases the IPC4 private data through the widget type's [`ipc_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) op, and removes the object from [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626).

### route_load

[`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L117) is bound to [`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087). It allocates a [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531), resolves the source and sink names to existing [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) objects with [`snd_sof_find_swidget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L956), and either drops a route that touches a virtual output widget or links it onto [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630) with the [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag clear.

### dai_load

[`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L133) is bound to [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726). It builds one [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) per front-end PCM, copies the on-disk [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) record into it, runs the IPC-version [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) op, parses [`stream_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L409), and allocates the playback and capture DMA page tables before linking the object onto [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624). According to the comment in the body, "nothing to do for BEs atm", so a back-end DAI returns early.

### link_load

[`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L141) is bound to [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873). It runs the IPC-version [`link_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op for every link, returns early for a front-end link with no back-end PCM, and for a back-end link allocates a [`struct snd_sof_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410), copies the topology hardware configs into it, and parses the [`common_dai_link_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1867) plus the SSP, DMIC, or ALH per-DAI tokens selected from the [`token_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221).

### control_load

[`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L111) is bound to [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961). It allocates a [`struct snd_sof_control`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L373), copies the kcontrol name, dispatches by the topology control info type to [`sof_control_load_volume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L830), [`sof_control_load_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L932), or [`sof_control_load_enum()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L910), stores the control in the kcontrol's [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), and links it onto [`kcontrol_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L625).

### manifest

[`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L157) is bound to [`sof_manifest()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279). It owns no SOF object; it forwards the topology manifest header to the IPC-version [`parse_manifest`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op, which on IPC4 reads the firmware ABI version and library counts.

### complete

[`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154) is the one member SOF deliberately leaves NULL. According to the comment in [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), "No need to set the complete callback. sof_complete will be called explicitly after topology loading is complete", so [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) invokes [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192) itself after every file has been loaded, so the per-widget [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) build runs once across all files rather than once per file.

## DETAILS

### SOF registers one function pointer struct into the generic loader

The ASoC topology core exposes [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) as the contract a component fills in. The core decodes the binary file and calls one member per object, so the member set is exactly the list of topology elements a driver chooses to handle:

```c
/* include/sound/soc-topology.h:108 */
struct snd_soc_tplg_ops {

	/* external kcontrol init - used for any driver specific init */
	int (*control_load)(struct snd_soc_component *, int index,
		struct snd_kcontrol_new *, struct snd_soc_tplg_ctl_hdr *);
	int (*control_unload)(struct snd_soc_component *,
		struct snd_soc_dobj *);

	/* DAPM graph route element loading and unloading */
	int (*dapm_route_load)(struct snd_soc_component *, int index,
		struct snd_soc_dapm_route *route);
	int (*dapm_route_unload)(struct snd_soc_component *,
		struct snd_soc_dobj *);

	/* external widget init - used for any driver specific init */
	int (*widget_load)(struct snd_soc_component *, int index,
		struct snd_soc_dapm_widget *,
		struct snd_soc_tplg_dapm_widget *);
	int (*widget_ready)(struct snd_soc_component *, int index,
		struct snd_soc_dapm_widget *,
		struct snd_soc_tplg_dapm_widget *);
	int (*widget_unload)(struct snd_soc_component *,
		struct snd_soc_dobj *);

	/* FE DAI - used for any driver specific init */
	int (*dai_load)(struct snd_soc_component *, int index,
		struct snd_soc_dai_driver *dai_drv,
		struct snd_soc_tplg_pcm *pcm, struct snd_soc_dai *dai);

	int (*dai_unload)(struct snd_soc_component *,
		struct snd_soc_dobj *);

	/* DAI link - used for any driver specific init */
	int (*link_load)(struct snd_soc_component *, int index,
		struct snd_soc_dai_link *link,
		struct snd_soc_tplg_link_config *cfg);
	int (*link_unload)(struct snd_soc_component *,
		struct snd_soc_dobj *);
	...
	/* completion - called at completion of firmware loading */
	int (*complete)(struct snd_soc_component *comp);

	/* manifest - optional to inform component of manifest */
	int (*manifest)(struct snd_soc_component *, int index,
		struct snd_soc_tplg_manifest *);
	...
};
```

The generic model pairs a `*_load` (or `*_ready`) member with a `*_unload` member. The load member builds driver state for one decoded object, and the core records the unload member in that object's [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) so it can be called when the topology is removed. SOF supplies this struct as the file-scope [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), and a parallel DSP-less debug instance [`sof_dspless_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2473) handles the case where no DSP is driven. It binds the [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) member rather than [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123) and leaves [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154) unset:

```c
/* sound/soc/sof/topology.c:2305 */
static const struct snd_soc_tplg_ops sof_tplg_ops = {
	/* external kcontrol init - used for any driver specific init */
	.control_load	= sof_control_load,
	.control_unload	= sof_control_unload,

	/* external kcontrol init - used for any driver specific init */
	.dapm_route_load	= sof_route_load,
	.dapm_route_unload	= sof_route_unload,

	/* external widget init - used for any driver specific init */
	/* .widget_load is not currently used */
	.widget_ready	= sof_widget_ready,
	.widget_unload	= sof_widget_unload,

	/* FE DAI - used for any driver specific init */
	.dai_load	= sof_dai_load,
	.dai_unload	= sof_dai_unload,

	/* DAI link - used for any driver specific init */
	.link_load	= sof_link_load,
	.link_unload	= sof_link_unload,

	/*
	 * No need to set the complete callback. sof_complete will be called explicitly after
	 * topology loading is complete.
	 */

	/* manifest - optional to inform component of manifest */
	.manifest	= sof_manifest,
	...
};
```

The split between [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123) and [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L126) is a timing distinction the core enforces in [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097). The core calls [`soc_tplg_widget_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L257) with a widget template before [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L630) builds the live widget, and [`soc_tplg_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L269) only after:

```c
/* sound/soc/soc-topology.c:1216 */
	ret = soc_tplg_widget_load(tplg, &template, w);
	if (ret < 0)
		goto hdr_err;
	...
	if (snd_soc_card_is_instantiated(card))
		widget = snd_soc_dapm_new_control(dapm, &template);
	else
		widget = snd_soc_dapm_new_control_unlocked(dapm, &template);
	...
	widget->dobj.type = SND_SOC_DOBJ_WIDGET;
	widget->dobj.widget.kcontrol_type = kcontrol_type;
	if (tplg->ops)
		widget->dobj.unload = tplg->ops->widget_unload;
	widget->dobj.index = tplg->index;
	list_add(&widget->dobj.list, &tplg->comp->dobj_list);

	ret = soc_tplg_widget_ready(tplg, widget, w);
```

[`soc_tplg_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L269) is a one-line forward into the registered member:

```c
/* sound/soc/soc-topology.c:269 */
static int soc_tplg_widget_ready(struct soc_tplg *tplg,
				 struct snd_soc_dapm_widget *w,
				 struct snd_soc_tplg_dapm_widget *tplg_w)
{
	if (tplg->ops && tplg->ops->widget_ready)
		return tplg->ops->widget_ready(tplg->comp, tplg->index, w,
			tplg_w);

	return 0;
}
```

SOF binds the later member because [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) copies fields out of the finished [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) (its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), name, and kcontrol count) and writes its own object back into [`w->dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), neither of which exists at [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L123) time. The [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) carries a [`tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L623) field for a cached pointer, but the live path passes the address of the file-scope [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) straight into the loader, so the seam between the generic loader and SOF is this one argument.

### snd_sof_load_topology hands the ops to the core

[`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) is called from the SOF component probe [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L786). It resolves the topology filename, requests each firmware blob, and runs the whole parse loop inside the one [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) call before invoking its own completion pass:

```c
/* sound/soc/sof/topology.c:2554 */
	for (i = 0; i < tplg_cnt; i++) {
		...
		ret = request_firmware(&fw, tplg_files[i], scomp->dev);
		if (ret < 0) {
			...
			goto out;
		}

		if (sdev->dspless_mode_selected)
			ret = snd_soc_tplg_component_load(scomp, &sof_dspless_tplg_ops, fw);
		else
			ret = snd_soc_tplg_component_load(scomp, &sof_tplg_ops, fw);

		release_firmware(fw);

		if (ret < 0) {
			dev_err(scomp->dev, "tplg %s component load failed %d\n",
				tplg_files[i], ret);
			goto out;
		}
	}

	/* call sof_complete when topologies are loaded successfully */
	ret = sof_complete(scomp);
```

The full-DSP path passes [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305); a DSP-less debug path passes [`sof_dspless_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2473) instead. On an x86-64 ACPI MTL or LNL card the DSP is present, so the full ops are used. [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) installs the ops into the parse context and runs [`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110), so by the time it returns every object in the file has already been turned into a SOF object on the device lists by the callbacks below:

```c
/* sound/soc/soc-topology.c:2122 */
int snd_soc_tplg_component_load(struct snd_soc_component *comp,
	const struct snd_soc_tplg_ops *ops, const struct firmware *fw)
{
	struct soc_tplg tplg;
	int ret;
	...
	/* setup parsing context */
	memset(&tplg, 0, sizeof(tplg));
	tplg.fw = fw;
	tplg.dev = comp->card->dev;
	tplg.comp = comp;
	if (ops) {
		tplg.ops = ops;
		tplg.io_ops = ops->io_ops;
		tplg.io_ops_count = ops->io_ops_count;
		tplg.bytes_ext_ops = ops->bytes_ext_ops;
		tplg.bytes_ext_ops_count = ops->bytes_ext_ops_count;
	}

	ret = soc_tplg_load(&tplg);
	/* free the created components if fail to load topology */
	if (ret)
		snd_soc_tplg_component_remove(comp);

	return ret;
}
```

Because the loop loads each file under the same [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) and [`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192) runs only after the loop, the explicit completion call performs the per-widget [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) build once across all function topologies rather than once per file, which a registered [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L154) member would do.

### sof_widget_ready builds a snd_sof_widget and parses its tokens

[`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) allocates a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), copies the identity fields from the already-built [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), assigns a firmware component id, and parses the widget identity and pin tokens:

```c
/* sound/soc/sof/topology.c:1409 */
static int sof_widget_ready(struct snd_soc_component *scomp, int index,
			    struct snd_soc_dapm_widget *w,
			    struct snd_soc_tplg_dapm_widget *tw)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	const struct sof_ipc_tplg_widget_ops *widget_ops;
	struct snd_soc_tplg_private *priv = &tw->priv;
	enum sof_tokens *token_list = NULL;
	struct snd_sof_widget *swidget;
	struct snd_sof_dai *dai;
	int token_list_size = 0;
	int ret = 0;

	swidget = kzalloc_obj(*swidget);
	if (!swidget)
		return -ENOMEM;

	swidget->scomp = scomp;
	swidget->widget = w;
	swidget->comp_id = sdev->next_comp_id++;
	swidget->id = w->id;
	swidget->pipeline_id = index;
	swidget->private = NULL;
	mutex_init(&swidget->setup_mutex);

	ida_init(&swidget->output_queue_ida);
	ida_init(&swidget->input_queue_ida);

	ret = sof_parse_tokens(scomp, w, dapm_widget_tokens, ARRAY_SIZE(dapm_widget_tokens),
			       priv->array, le32_to_cpu(priv->size));
	if (ret < 0) {
		dev_err(scomp->dev, "failed to parse dapm widget tokens for %s\n",
			w->name);
		goto widget_free;
	}

	ret = sof_parse_tokens(scomp, swidget, comp_pin_tokens,
			       ARRAY_SIZE(comp_pin_tokens), priv->array,
			       le32_to_cpu(priv->size));
	...
```

The [`id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) field is the DAPM widget type, copied verbatim from [`w->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), and the [`pipeline_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is the topology index passed by the core. The two [`sof_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810) calls have different targets. The [`dapm_widget_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1403) table parses into the DAPM widget `w`, while the [`comp_pin_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L428) table parses into the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) `swidget` and fills its [`num_input_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and [`num_output_pins`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) counts.

The same function obtains the IPC-version layer through [`sof_ipc_get_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L541) so it can read the per-widget-type token list, then dispatches on the widget type. A DAI widget gets the extra [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) allocation and connection:

```c
/* sound/soc/sof/topology.c:1489 */
	widget_ops = tplg_ops ? tplg_ops->widget : NULL;
	if (widget_ops) {
		token_list = widget_ops[w->id].token_list;
		token_list_size = widget_ops[w->id].token_list_size;
	}

	/* handle any special case widgets */
	switch (w->id) {
	case snd_soc_dapm_dai_in:
	case snd_soc_dapm_dai_out:
		dai = kzalloc_obj(*dai);
		if (!dai) {
			ret = -ENOMEM;
			goto widget_free;
		}

		ret = sof_widget_parse_tokens(scomp, swidget, tw, token_list, token_list_size);
		if (!ret)
			ret = sof_connect_dai_widget(scomp, w, tw, dai);
		if (ret < 0) {
			kfree(dai);
			break;
		}
		list_add(&dai->list, &sdev->dai_list);
		swidget->private = dai;
		break;
	...
```

A DAPM widget of type [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) or [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) gets a [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) allocated, tied to the card DAI by [`sof_connect_dai_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068), placed on [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L628), and stored in the widget's [`private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) pointer. The module widget types ([`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447), [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_src`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L458), and the rest) take the shared [`sof_widget_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1210) path, which parses that type's token list into the per-widget IPC4 private blob. A [`snd_soc_dapm_scheduler`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L456) widget additionally allocates a [`struct snd_sof_pipeline`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L519) and links it onto [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L627).

At the end the widget records itself in both directions, onto [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) and back into the DAPM widget's [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516):

```c
/* sound/soc/sof/topology.c:1600 */
	w->dobj.private = swidget;
	list_add(&swidget->list, &sdev->widget_list);
	return ret;
free:
	kfree(swidget->private);
	kfree(swidget->tuples);
widget_free:
	kfree(swidget);
	return ret;
}
```

The back pointer in [`w->dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) lets the runtime path recover the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) from a DAPM widget when a PCM is opened (both [`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) and the PCM widget walk read it), and [`snd_sof_find_swidget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L956) walks the [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) membership to resolve a route by widget name.

```
    sof_widget_ready: switch (w->id) ─▶ extra object on a list
    ──────────────────────────────────────────────────────────────
    w->id                       extra object        added to
    ──────────────────────────  ─────────────────   ──────────────
    dai_in / dai_out            struct snd_sof_dai  dai_list
      (via sof_connect_dai_widget; stored in swidget->private)
    scheduler                   struct snd_sof_     pipeline_list
                                pipeline
    aif_in / pga / mixer / src  (none; private =    ──
    and other module types       per-type IPC4 blob via parse_tokens)
    ──────────────────────────────────────────────────────────────
    every w->id ─▶ struct snd_sof_widget on widget_list,
    and back into w->dobj.private
```

### sof_parse_tokens decodes vendor tuples into the object

The vendor data behind every topology object is a flat array of tuples carried in the [`struct snd_soc_tplg_private`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L236) block that trails the element. [`sof_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810) decodes one set of them against a token definition table and writes each decoded value into the target object:

```c
/* sound/soc/sof/topology.c:810 */
static int sof_parse_tokens(struct snd_soc_component *scomp,  void *object,
			    const struct sof_topology_token *tokens, int num_tokens,
			    struct snd_soc_tplg_vendor_array *array,
			    int array_size)

{
	/*
	 * sof_parse_tokens is used when topology contains only a single set of
	 * identical tuples arrays. So additional parameters to
	 * sof_parse_token_sets are sets = 1 (only 1 set) and
	 * object_size = 0 (irrelevant).
	 */
	return sof_parse_token_sets(scomp, object, tokens, num_tokens, array,
				    array_size, 1, 0);
}
```

Each entry in the [`tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L810) array is a [`struct sof_topology_token`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305), which names the token, its wire type, the decode function, and the byte offset in the target object where the decoded value is stored:

```c
/* sound/soc/sof/sof-audio.h:305 */
struct sof_topology_token {
	u32 token;
	u32 type;
	int (*get_token)(void *elem, void *object, u32 offset);
	u32 offset;
};
```

The [`offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L305) lets one parser fill any object. The [`comp_pin_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L428) table, for example, gives each token an [`offsetof`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/stddef.h#L16) into [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422):

```c
/* sound/soc/sof/topology.c:428 */
static const struct sof_topology_token comp_pin_tokens[] = {
	{SOF_TKN_COMP_NUM_INPUT_PINS, SND_SOC_TPLG_TUPLE_TYPE_WORD, get_token_u32,
		offsetof(struct snd_sof_widget, num_input_pins)},
	{SOF_TKN_COMP_NUM_OUTPUT_PINS, SND_SOC_TPLG_TUPLE_TYPE_WORD, get_token_u32,
		offsetof(struct snd_sof_widget, num_output_pins)},
};
```

[`sof_parse_token_sets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L724) walks consecutive vendor arrays and dispatches each by its tuple type to the matching value parser, applying the running offset so multiple identical sets land in consecutive sub-objects:

```c
/* sound/soc/sof/topology.c:724 */
	while (array_size > 0 && total < count * token_instance_num) {
		asize = le32_to_cpu(array->size);
		...
		/* call correct parser depending on type */
		switch (le32_to_cpu(array->type)) {
		case SND_SOC_TPLG_TUPLE_TYPE_UUID:
			found += sof_parse_uuid_tokens(scomp, object, offset, tokens, count,
						       array);
			break;
		case SND_SOC_TPLG_TUPLE_TYPE_STRING:
			ret = sof_parse_string_tokens(scomp, object, offset, tokens, count,
						      array);
			...
			found += ret;
			break;
		case SND_SOC_TPLG_TUPLE_TYPE_BOOL:
		case SND_SOC_TPLG_TUPLE_TYPE_BYTE:
		case SND_SOC_TPLG_TUPLE_TYPE_WORD:
		case SND_SOC_TPLG_TUPLE_TYPE_SHORT:
			found += sof_parse_word_tokens(scomp, object, offset, tokens, count,
						       array);
			break;
		...
		}

		/* next array */
		array = (struct snd_soc_tplg_vendor_array *)((u8 *)array
			+ asize);

		/* move to next target struct */
		if (found >= count) {
			offset += object_size;
			total += found;
			found = 0;
		}
	}
```

[`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) parses the [`dapm_widget_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1403) table into the DAPM widget and the [`comp_pin_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L428) table into the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) parses [`stream_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L409) into the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352), and [`sof_link_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1873) parses [`common_dai_link_tokens`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1867) into the [`struct snd_sof_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L410). The per-widget-type IPC4 token tables collected through the [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op array are parsed by [`sof_widget_parse_tokens()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1210) into the per-widget IPC4 private blob.

```
    One token definition writes one decoded tuple into the object
    ──────────────────────────────────────────────────────────────
    struct snd_soc_tplg_private           struct sof_topology_token
    (vendor tuple arrays, on disk)        ┌────────────────────────┐
    ┌───────────────────────────┐         │ token   (which tuple)  │
    │ array: type, size, value  │ ──────▶ │ type    (wire type)    │
    │ array: type, size, value  │ get_    │ get_token (decoder)    │
    │ ...                       │ token() │ offset  (where in obj) │
    └───────────────────────────┘         └───────────┬────────────┘
                                                      │ writes value
                                                      ▼  at +offset
    token table          parsed by               into target object
    ──────────────────   ───────────────────────  ──────────────────
    dapm_widget_tokens   sof_widget_ready         struct snd_soc_dapm_widget
    comp_pin_tokens      sof_widget_ready         struct snd_sof_widget
    stream_tokens        sof_dai_load             struct snd_sof_pcm
    common_dai_link_..   sof_link_load            struct snd_sof_dai_link
```

### sof_route_load builds a snd_sof_route between two widgets

[`sof_route_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087) allocates a [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) and resolves the source and sink widget names to the [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) objects built earlier, dropping any edge that touches a virtual output widget the firmware does not model:

```c
/* sound/soc/sof/topology.c:2087 */
static int sof_route_load(struct snd_soc_component *scomp, int index,
			  struct snd_soc_dapm_route *route)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	struct snd_sof_widget *source_swidget, *sink_swidget;
	struct snd_soc_dobj *dobj = &route->dobj;
	struct snd_sof_route *sroute;
	int ret = 0;

	/* allocate memory for sroute and connect */
	sroute = kzalloc_obj(*sroute);
	if (!sroute)
		return -ENOMEM;

	sroute->scomp = scomp;
	...
	/* source component */
	source_swidget = snd_sof_find_swidget(scomp, (char *)route->source);
	if (!source_swidget) {
		dev_err(scomp->dev, "source %s for sink %s is not found\n",
			route->source, route->sink);
		ret = -EINVAL;
		goto err;
	}

	/*
	 * Virtual widgets of type output/out_drv may be added in topology
	 * for compatibility. These are not handled by the FW.
	 * So, don't send routes whose source/sink widget is of such types
	 * to the DSP.
	 */
	if (source_swidget->id == snd_soc_dapm_out_drv ||
	    source_swidget->id == snd_soc_dapm_output)
		goto err;
	...
	sroute->route = route;
	dobj->private = sroute;
	sroute->src_widget = source_swidget;
	sroute->sink_widget = sink_swidget;

	/* add route to route list */
	list_add(&sroute->list, &sdev->route_list);

	return 0;
err:
	kfree(sroute);
	return ret;
}
```

The resolved [`src_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) and [`sink_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) pointers are what the IPC4 route setup later reads to find each end's firmware module handle. According to the comment "Virtual widgets of type output/out_drv may be added in topology for compatibility. These are not handled by the FW", a route ending in [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425) or [`snd_soc_dapm_out_drv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L431) is freed at load time through the `err` path and never reaches the DSP. The other edges land on [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630) with the [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag still clear, to be set when the connection is established at runtime.

```
    struct snd_sof_route links two earlier-built widgets by name
    ──────────────────────────────────────────────────────────────
              ┌────────────────────────────┐
              │ struct snd_sof_route       │
              │   route, setup = 0         │   on route_list
              │   src_widget   sink_widget │
              └────────┬───────────┬───────┘
                       │           │  resolved by snd_sof_find_swidget
              route->  ▼           ▼  route->
              source   │           │  sink
          ┌────────────────────┐  ┌────────────────────┐
          │ snd_sof_widget src │  │ snd_sof_widget sink│
          └────────────────────┘  └────────────────────┘
    drop the route when source or sink id is output or out_drv
```

### sof_dai_load builds a snd_sof_pcm for a front-end DAI

[`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726) is the [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L133) callback. It builds one [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) per front-end PCM, copies the on-disk PCM record into the trailing flex member, runs the IPC-version [`pcm_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) op, parses its stream tokens, and allocates the DMA page tables:

```c
/* sound/soc/sof/topology.c:1726 */
static int sof_dai_load(struct snd_soc_component *scomp, int index,
			struct snd_soc_dai_driver *dai_drv,
			struct snd_soc_tplg_pcm *pcm, struct snd_soc_dai *dai)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_pcm_ops *ipc_pcm_ops = sof_ipc_get_ops(sdev, pcm);
	struct snd_soc_tplg_stream_caps *caps;
	struct snd_soc_tplg_private *private = &pcm->priv;
	struct snd_sof_pcm *spcm;
	int stream;
	int ret;

	/* nothing to do for BEs atm */
	if (!pcm)
		return 0;

	spcm = kzalloc_obj(*spcm);
	if (!spcm)
		return -ENOMEM;

	spcm->scomp = scomp;
	...
	spcm->pcm = *pcm;
	dev_dbg(scomp->dev, "tplg: load pcm %s\n", pcm->dai_name);

	/* perform pcm set op */
	if (ipc_pcm_ops && ipc_pcm_ops->pcm_setup) {
		ret = ipc_pcm_ops->pcm_setup(sdev, spcm);
		if (ret < 0) {
			kfree(spcm);
			return ret;
		}
	}

	dai_drv->dobj.private = spcm;
	list_add(&spcm->list, &sdev->pcm_list);

	ret = sof_parse_tokens(scomp, spcm, stream_tokens,
			       ARRAY_SIZE(stream_tokens), private->array,
			       le32_to_cpu(private->size));
	...
```

According to the comment "nothing to do for BEs atm", a back-end DAI link reaches this callback with a NULL `pcm` and returns immediately, so only front-end PCMs create a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352). The object is stored in the DAI driver's [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) and linked onto [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624). After the tokens are parsed the function allocates a playback and a capture page table with [`snd_dma_alloc_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/memalloc.h#L76) and binds each stream to its host component, so the PCM is ready to be opened. The matching [`sof_dai_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842) frees those page tables, runs the [`pcm_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) op, and removes the object from [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L624).

### sof_connect_dai_widget ties a DAI widget to a card DAI

A DAI-type widget needs more than its own object. [`sof_connect_dai_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1068), called from the DAI case of [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), matches the widget stream name to a card DAI link and binds the DAPM widget to the link's CPU DAI so the back-end PCM connects to the right widget:

```c
/* sound/soc/sof/topology.c:1068 */
static int sof_connect_dai_widget(struct snd_soc_component *scomp,
				  struct snd_soc_dapm_widget *w,
				  struct snd_soc_tplg_dapm_widget *tw,
				  struct snd_sof_dai *dai)
{
	struct snd_soc_card *card = scomp->card;
	struct snd_soc_pcm_runtime *rtd, *full, *partial;
	struct snd_soc_dai *cpu_dai;
	int stream;
	int i;

	if (!w->sname) {
		dev_err(scomp->dev, "Widget %s does not have stream\n", w->name);
		return -EINVAL;
	}

	if (w->id == snd_soc_dapm_dai_out)
		stream = SNDRV_PCM_STREAM_CAPTURE;
	else if (w->id == snd_soc_dapm_dai_in)
		stream = SNDRV_PCM_STREAM_PLAYBACK;
	else
		goto end;
	...
	rtd = full ? full : partial;
	if (rtd) {
		for_each_rtd_cpu_dais(rtd, i, cpu_dai) {
			...
			if (!snd_soc_dai_get_widget(cpu_dai, stream)) {
				snd_soc_dai_set_widget(cpu_dai, stream, w);
				break;
			}
		}
		...
		dai->name = rtd->dai_link->name;
		dev_dbg(scomp->dev, "tplg: connected widget %s -> DAI link %s\n",
			w->name, rtd->dai_link->name);
	}
end:
	/* check we have a connection */
	if (!dai->name) {
		dev_err(scomp->dev, "error: can't connect DAI %s stream %s\n",
			w->name, w->sname);
		return -EINVAL;
	}

	return 0;
}
```

The direction follows from the DAPM type. A [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) widget is a playback CPU DAI and a [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widget a capture CPU DAI. The function records the matched DAI link name in [`dai->name`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547), which is the handle [`snd_sof_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L993) later uses to locate the [`struct snd_sof_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L547) for a back-end stream, and [`snd_soc_dai_set_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L490) wires the card CPU DAI to the DAPM widget so the DPCM back end reaches the right node.

### sof_complete runs the per-widget IPC build once, at the end

[`sof_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2192) is the explicit completion pass [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) calls after the loader returns. It walks the lists [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409) and [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961) built and runs the IPC-version setup ops that turn each parsed object's tokens into the wire IPC structure the firmware expects, then assigns each non-scheduler widget to its pipeline:

```c
/* sound/soc/sof/topology.c:2192 */
static int sof_complete(struct snd_soc_component *scomp)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	const struct sof_ipc_tplg_widget_ops *widget_ops;
	struct snd_sof_control *scontrol;
	struct snd_sof_pipeline *spipe;
	int ret;

	widget_ops = tplg_ops ? tplg_ops->widget : NULL;

	/* first update all control IPC structures based on the IPC version */
	if (tplg_ops && tplg_ops->control_setup)
		list_for_each_entry(scontrol, &sdev->kcontrol_list, list) {
			ret = tplg_ops->control_setup(sdev, scontrol);
			...
		}

	/* set up the IPC structures for the pipeline widgets */
	list_for_each_entry(spipe, &sdev->pipeline_list, list) {
		struct snd_sof_widget *pipe_widget = spipe->pipe_widget;
		struct snd_sof_widget *swidget;

		pipe_widget->instance_id = -EINVAL;

		/* Update the scheduler widget's IPC structure */
		if (widget_ops && widget_ops[pipe_widget->id].ipc_setup) {
			ret = widget_ops[pipe_widget->id].ipc_setup(pipe_widget);
			...
		}

		/* set the pipeline and update the IPC structure for the non scheduler widgets */
		list_for_each_entry(swidget, &sdev->widget_list, list)
			if (swidget->widget->id != snd_soc_dapm_scheduler &&
			    swidget->pipeline_id == pipe_widget->pipeline_id) {
				ret = sof_set_widget_pipeline(sdev, spipe, swidget);
				if (ret < 0)
					return ret;

				if (widget_ops && widget_ops[swidget->id].ipc_setup) {
					ret = widget_ops[swidget->id].ipc_setup(swidget);
					...
				}
			}
	}
	...
	/* set up static pipelines */
	if (tplg_ops && tplg_ops->set_up_all_pipelines)
		return tplg_ops->set_up_all_pipelines(sdev, false);

	return 0;
}
```

The [`ipc_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L181) op called here is the IPC4 load-time per-widget builder, the [`tplg_ipc4_widget_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3925) member for each widget type, which allocates the copier, gain, mixer, or pipeline private struct on [`swidget->private`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and pre-builds its [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) header without sending any IPC. On an IPC4 platform [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) is left unassigned in [`ipc4_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973), so this completion pass ends after building the structs, and the actual create-module and create-pipeline messages are sent later, per widget, by [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) when a PCM is opened.

```
    sof_complete groups widgets under a pipeline by pipeline_id
    ─────────────────────────────────────────────────────────────
    for each spipe on pipeline_list:

    ┌───────────────────────────────────────────────────────────┐
    │ struct snd_sof_pipeline (spipe)                           │
    │   pipe_widget ─▶ scheduler widget  (ipc_setup runs first) │
    │                                                           │
    │   member widgets: every swidget on widget_list with       │
    │     swidget->pipeline_id == pipe_widget->pipeline_id      │
    │     and id != snd_soc_dapm_scheduler                      │
    │       ├─ sof_set_widget_pipeline(spipe, swidget)          │
    │       └─ widget_ops[swidget->id].ipc_setup(swidget)       │
    └───────────────────────────────────────────────────────────┘
    controls first: control_setup over every kcontrol_list entry
```

### The runtime stage reaches ipc4_tplg_ops through the same widget object

The load stage leaves a fully populated [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) on [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L626) with its private IPC4 blob built. When a PCM is opened, [`sof_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251) takes the widget's [`setup_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and calls [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144), which reaches the IPC-version members:

```c
/* sound/soc/sof/sof-audio.c:251 */
int sof_widget_setup(struct snd_sof_dev *sdev, struct snd_sof_widget *swidget)
{
	guard(mutex)(&swidget->setup_mutex);
	return sof_widget_setup_unlocked(sdev, swidget);
}
```

[`sof_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L258) is the companion for a graph edge. It takes the two DAPM widgets, recovers their [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) objects from [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), finds the matching [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) on [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L630), and calls the [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op only once:

```c
/* sound/soc/sof/sof-audio.c:258 */
int sof_route_setup(struct snd_sof_dev *sdev, struct snd_soc_dapm_widget *wsource,
		    struct snd_soc_dapm_widget *wsink)
{
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	struct snd_sof_widget *src_widget = wsource->dobj.private;
	struct snd_sof_widget *sink_widget = wsink->dobj.private;
	struct snd_sof_route *sroute;
	bool route_found = false;
	...
	/* find route matching source and sink widgets */
	list_for_each_entry(sroute, &sdev->route_list, list)
		if (sroute->src_widget == src_widget && sroute->sink_widget == sink_widget) {
			route_found = true;
			break;
		}
	...
	/* nothing to do if route is already set up */
	if (sroute->setup)
		return 0;

	if (tplg_ops && tplg_ops->route_setup) {
		int ret = tplg_ops->route_setup(sdev, sroute);

		if (ret < 0)
			return ret;
	}

	sroute->setup = true;
	return 0;
}
```

On an x86-64 ACPI MTL or LNL machine the [`route_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member resolves to [`sof_ipc4_route_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3472), and the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) member invoked from [`sof_widget_setup_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L144) resolves to [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103). The [`setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) flag on the [`struct snd_sof_route`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L531) is the load-stage field that the runtime stage flips, so a route is bound on the DSP exactly once even when several PCM paths share it. Those two functions are the entry into the IPC4 message build covered on the SOF IPC4 topology load and runtime pages; this page ends where the loaded [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) is handed to them.

### From on-disk widget record to live DSP module

The generic [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) parse loop hands each on-disk [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) to [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), which builds a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) on the device list, and the runtime PCM path later calls [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) to send a [`struct sof_ipc4_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/ipc4/header.h#L32) that instantiates the module on the DSP.

```
    SOF turns a loaded topology widget into a live DSP module
    ─────────────────────────────────────────────────────────

    topology .tplg file
    ┌────────────────────────────────┐
    │ struct snd_soc_tplg_dapm_widget│
    │   id (DAPM type)               │
    │   name / sname                 │
    │   num_kcontrols                │
    │   struct snd_soc_tplg_private  │   ──▶  vendor tuple arrays
    │     (vendor tuple arrays)      │
    └───────────────┬────────────────┘
                    │ snd_soc_tplg_component_load
                    ▼
            sof_tplg_ops.widget_ready
            ┌──────────────────────────┐
            │ sof_widget_ready()       │
            │   sof_parse_tokens()     │
            └───────────────┬──────────┘
                            ▼
                struct snd_sof_widget          on sdev->widget_list
                ┌──────────────────────────┐
                │ scomp, comp_id, id       │
                │ pipeline_id, core        │
                │ num_tuples, tuples       │
                │ private  ──▶ IPC4 blob   │   (copier / gain / pipeline)
                └───────────────┬──────────┘
                                │ ipc4_tplg_ops.widget_setup
                                ▼
                       sof_ipc4_widget_setup()
                       ┌──────────────────────────┐
                       │ build struct sof_ipc4_msg│
                       │ send IPC to DSP          │
                       │ assign instance_id       │
                       └──────────────────────────┘
                                ▼
                          live DSP module
```
