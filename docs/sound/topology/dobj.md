# ASoC topology dynamic objects

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every object the ASoC topology loader builds from a firmware file embeds a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), a generic dynamic-object header that records the object's [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) drawn from [`enum snd_soc_dobj_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35), an [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback the component supplied through its [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and a [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) node that threads the object onto the component's [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232), so that [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) can walk that one list and dispatch each object to its typed remover ([`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345), [`soc_tplg_remove_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L361), [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374), [`soc_tplg_remove_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398), [`soc_tplg_remove_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419), and [`remove_backend_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L440)) to tear the whole topology back down when the firmware that created it is removed. The Intel SOF driver on x86-64 ACPI is the reference consumer, calling [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) from [`sof_pcm_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L797) and supplying its per-type [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) handlers through [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305).

```
    one snd_soc_component, one dobj_list of mixed object types
    ──────────────────────────────────────────────────────────

    struct snd_soc_component
    ┌────────────────────────────────────────────────────────────┐
    │  dobj_list ─┐                                              │
    └─────────────┼──────────────────────────────────────────────┘
                  │  list_add at each creator
       ┌──────────┼───────────┬───────────────┬──────────────┐
       ▼          ▼           ▼               ▼              ▼
    soc_mixer_  soc_enum   soc_bytes_ext  snd_soc_dapm_  snd_soc_dai_
    control     .dobj      .dobj          widget.dobj    driver.dobj
    .dobj                                 (also link,    (PCM FE)
    { type=MIXER}{type=ENUM}{type=BYTES}  route, dai)
       │          │           │               │              │
       │          │           │               │              │   each dobj:
       │          │           │               │              │   { type, list,
       │          │           │               │              │     unload, union }
       └──────────┴───────────┴───────────────┴──────────────┘
                  │
                  │  snd_soc_tplg_component_remove walks dobj_list,
                  │  pass = END..START, switch (dobj->type)
                  ▼
       SND_SOC_DOBJ_MIXER ─▶ soc_tplg_remove_kcontrol
       SND_SOC_DOBJ_BYTES ─▶ soc_tplg_remove_kcontrol
       SND_SOC_DOBJ_ENUM  ─▶ soc_tplg_remove_kcontrol
       SND_SOC_DOBJ_GRAPH ─▶ soc_tplg_remove_route
       SND_SOC_DOBJ_WIDGET─▶ soc_tplg_remove_widget
       SND_SOC_DOBJ_PCM   ─▶ soc_tplg_remove_dai
       SND_SOC_DOBJ_DAI_LINK ─▶ soc_tplg_remove_link
       SND_SOC_DOBJ_BACKEND_LINK ─▶ remove_backend_link
                  │
                  ▼  each remover: dobj->unload(comp, dobj), then release
                     the ASoC object and list_del(&dobj->list)
```

## SUMMARY

A topology file is parsed into live ASoC objects (kcontrols, DAPM widgets, DAPM routes, front-end DAIs and DAI links) by the per-block creators, and each of those objects has to be removable on its own when the firmware is unloaded, because a card outlives any one topology and several topologies may load under one card. The mechanism is a single generic header, [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), embedded in every topology-created object. Its comment reads "generic dynamic object - all dynamic objects belong to this struct". The header carries a [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) discriminator from [`enum snd_soc_dobj_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35), a [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) node, an [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) function pointer, a union of a [`struct snd_soc_dobj_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) and a [`struct snd_soc_dobj_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L56), and a [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) pointer the core never touches.

The header is embedded inside the owning struct. A topology mixer keeps its dobj inside its [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1244), an enum inside its [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1283), a bytes control inside its [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1257), a DAPM widget inside its [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), a DAPM route inside its [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L811), a front-end DAI inside its [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and a DAI link inside its [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). Each per-block creator fills in the dobj it owns, sets its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to the matching [`enum snd_soc_dobj_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35) value, copies the component's per-type unload op into [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), and links the dobj onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) with [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175). [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905), [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939), and [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) do this for the three control kinds; the widget, route, DAI, and link creators do it for their kinds. The block parsing and the creator bodies are documented separately.

Teardown is the inverse, and runs through one function. [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) loops the pass counter from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), and within each pass walks [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) with [`list_for_each_entry_safe()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L868), switching on each dobj's [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to call the matching remover. [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37), [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38), and [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39) share [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345); [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40) uses [`soc_tplg_remove_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L361), [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41) uses [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374), [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43) uses [`soc_tplg_remove_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398), [`SND_SOC_DOBJ_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L42) uses [`soc_tplg_remove_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419), and [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45) uses [`remove_backend_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L440). Every remover runs the component's recorded [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback first, then releases the live ASoC object and unlinks the dobj with [`list_del()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L235).

## SPECIFICATIONS

The [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) header and its teardown are an internal ASoC software construct and have no external hardware specification. The dobj exists only to give the topology core a handle on objects it created from a firmware file, so they can be removed without disturbing objects the card created statically. The on-disk block types the dobj [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) values mirror are the ASoC topology ABI in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h), but the dobj header itself is never serialized; it is a runtime structure embedded in the kernel-side object. On x86-64 the Intel SOF firmware package ships the binary topology that [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) later unwinds, and the per-object [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) pointer holds SOF's IPC bookkeeping for that object.

## LINUX KERNEL

### The generic dobj header and its types (soc-topology.h)

- [`'\<struct snd_soc_dobj\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61): the generic dynamic object embedded in every topology-created object; holds [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) node, the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback, the control/widget union, and the [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) pointer
- [`'\<enum snd_soc_dobj_type\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35): the object-kind discriminator from [`SND_SOC_DOBJ_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L36) through [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45); the value [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) switches on
- [`'\<struct snd_soc_dobj_control\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49): the control arm of the union; holds the back pointer [`kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) to the created [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) plus the duplicated [`dtexts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) and [`dvalues`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) for an enum
- [`'\<struct snd_soc_dobj_widget\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L56): the widget arm of the union; holds [`kcontrol_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L56), the per-embedded-control kind array (mixer, enum, bytes)
- [`'\<struct snd_soc_tplg_ops\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108): the component's function pointer struct supplying the per-type unload callbacks ([`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`link_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)) recorded in each dobj's [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61)

### Host objects that embed a dobj (soc.h, soc-dapm.h, soc-dai.h)

- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231): a topology mixer's private data; its trailing [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1244) is set to [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37)
- [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): a topology enum's private data; its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1283) is set to [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39)
- [`'\<struct soc_bytes_ext\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254): a topology bytes control's private data; its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1257) is set to [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): a DAPM widget; its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L556) is set to [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41), and [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) reaches the widget from the dobj with [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19)
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): a front-end DAI driver; its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L408) is set to [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43)
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): a DAI link; its [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L811) is set to [`SND_SOC_DOBJ_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L42)
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the component owning the topology; its [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) field is the one list every dobj joins

### Teardown driver and typed removers (soc-topology.c)

- [`'\<snd_soc_tplg_component_remove\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161): walk [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) once per pass from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) and switch on each dobj's [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to its remover; returns nonzero while objects remain
- [`'\<soc_tplg_remove_kcontrol\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345): the remover shared by mixer, bytes, and enum dobjs; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), then [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) on [`dobj->control.kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) and [`list_del()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L235)
- [`'\<soc_tplg_remove_route\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L361): the [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40) remover; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and unlinks the dobj
- [`'\<soc_tplg_remove_widget\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374): the [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41) remover; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), removes the widget's [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618), and unlinks the dobj (the widget itself is freed by soc-dapm.c)
- [`'\<soc_tplg_remove_dai\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398): the [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43) remover; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and [`snd_soc_unregister_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2685) on the DAIs matching the driver
- [`'\<soc_tplg_remove_link\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419): the [`SND_SOC_DOBJ_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L42) remover; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and [`snd_soc_remove_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1147) for the link it owns
- [`'\<remove_backend_link\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L440): the [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45) remover; runs [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), resets the dobj [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to [`SND_SOC_DOBJ_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L36), and unlinks the dobj without freeing the link

### Creators that set dobj.type and dobj.unload (soc-topology.c)

- [`'\<soc_tplg_dmixer_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905): set the mixer's [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1244) [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37) and [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), then [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175) it onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232)
- [`'\<soc_tplg_denum_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939): the same for an enum, tagging the [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1283) with [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39)
- [`'\<soc_tplg_dbytes_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871): the same for a bytes control, tagging the [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1257) with [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38)
- [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) / [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51): the pass bounds the remover loop runs between, in reverse of the load order

### List and release primitives

- [`'\<list_add\>':'include/linux/list.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175): each creator links its dobj onto the head of [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232)
- [`'\<list_del\>':'include/linux/list.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L235): each remover unlinks the dobj after releasing the ASoC object
- [`'\<list_for_each_entry_safe\>':'include/linux/list.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L868): the safe-against-removal walk [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) uses over [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232)
- [`'\<container_of\>':'include/linux/container_of.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19): how the widget, DAI, and link removers recover the host object from the embedded dobj pointer
- [`'\<snd_ctl_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618): remove one kcontrol from the card and release it; used by the kcontrol and widget removers
- [`'\<snd_soc_unregister_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2685): unregister a DAI; used by [`soc_tplg_remove_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398)
- [`'\<snd_soc_remove_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1147): remove the PCM runtime of a link; used by [`soc_tplg_remove_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419)
- [`'\<snd_soc_dapm_free_widget\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2850): free a DAPM widget; the soc-dapm.c side of widget release the dobj remover defers to

### SOF consumer (sof/topology.c, sof/pcm.c)

- [`'\<sof_pcm_remove\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L797): the SOF component remove callback; calls [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) to drop the whole topology
- [`'sof_tplg_ops':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305): SOF's [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) wiring the per-type unload callbacks the dobjs record
- [`'\<sof_control_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1038): the [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler; reads [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) as a [`struct snd_sof_control`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L114) and frees its IPC payload
- [`'\<sof_widget_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628): the [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler; reads [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) as a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422) and frees its IPC component
- [`'\<sof_dai_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842): the [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler for a PCM dobj
- [`'\<sof_route_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1611): the [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler for a graph dobj
- [`'\<sof_link_unload\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2068): the [`link_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler for a DAI-link dobj

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component model whose objects topology creates and the dobj makes removable
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget and route model that the widget and graph dobjs wrap
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end DAI and link a PCM dobj covers
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA control model behind [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618), the per-control free a kcontrol dobj triggers

## OTHER SOURCES

- [Sound Open Firmware topology documentation](https://thesofproject.github.io/latest/architectures/firmware/sof-common/topology.html)
- [ALSA topology project documentation](https://www.alsa-project.org/wiki/ASoC/Dynamic_Audio_Architecture)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

Each topology-created object embeds a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) inside a different host struct, is created by a different per-block creator (documented separately), and is released by a different typed remover keyed on its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61). The dobj for a mixer, an enum, and a bytes control all route to one remover, so the table below collapses those three rows onto [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345). Every dobj lives from the moment its creator links it onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) until [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) reaches it in the pass matching its kind.

| dobj type | host struct (dobj field) | created by | removed by |
|-----------|--------------------------|------------|------------|
| [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) | [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345) |
| [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39) | [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) | [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939) | [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345) |
| [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38) | [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) | [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) | [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345) |
| [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40) | [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L811) | graph creator | [`soc_tplg_remove_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L361) |
| [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41) | [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) | widget creator | [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) |
| [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43) | [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) | DAI creator | [`soc_tplg_remove_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398) |
| [`SND_SOC_DOBJ_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L42) | [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) | FE link creator | [`soc_tplg_remove_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419) |
| [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45) | [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) | link config | [`remove_backend_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L440) |

The [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) member of each dobj is the component's optional per-type callback, recorded at creation from the matching field of [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108). Every remover tests [`dobj->unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) for NULL before calling it, so a component that does not need per-object cleanup sets no unload op and the core still removes the object. SOF wires every unload op, because each topology object owns a matching IPC structure on the DSP that the unload callback frees through [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61).

| dobj type | unload op field in [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | SOF handler |
|-----------|---------------------------------|-------------|
| mixer / enum / bytes | [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | [`sof_control_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1038) |
| graph | [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | [`sof_route_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1611) |
| widget | [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628) |
| PCM | [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | [`sof_dai_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842) |
| DAI link / backend link | [`link_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | [`sof_link_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2068) |

## DETAILS

### The generic dobj header

A [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) is the topology layer's handle on one object it created. Its comment states it is the common base every dynamic object embeds. It carries the type discriminator, a group [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) that records which loaded topology the object belongs to, the list node that threads it onto the component, the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback, a union holding either the control or the widget arm, and a [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) pointer reserved for the component:

```c
/* include/sound/soc-topology.h:60 */
/* generic dynamic object - all dynamic objects belong to this struct */
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

The two arms of the union hold the kind-specific back references. According to its comment the control arm is the "dynamic control object", and it stores the back pointer to the created [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) plus the heap-duplicated [`dtexts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) and [`dvalues`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) an enum needs. The widget arm is the "dynamic widget object" and holds only the per-embedded-control [`kcontrol_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L56) array:

```c
/* include/sound/soc-topology.h:48 */
/* dynamic control object */
struct snd_soc_dobj_control {
	struct snd_kcontrol *kcontrol;
	char **dtexts;
	unsigned long *dvalues;
};

/* dynamic widget object */
struct snd_soc_dobj_widget {
	unsigned int *kcontrol_type;	/* kcontrol type: mixer, enum, bytes */
};
```

The control arm's [`kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) back pointer lets the kcontrol remover delete exactly the control this dobj created, without scanning the card's whole control list. The widget arm has no back pointer because a widget dobj is embedded inside the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) itself, so [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) reaches the widget back from the dobj with [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19).

```
    struct snd_soc_dobj: header fields, one union, one discriminator
    ─────────────────────────────────────────────────────────────────

    struct snd_soc_dobj
    ┌──────────────────────────────────────────────────────────────┐
    │ type     enum snd_soc_dobj_type  selects the union arm       │
    │ index    which loaded topology the object belongs to         │
    │ list     node threaded onto component dobj_list              │
    │ unload   per-type callback from snd_soc_tplg_ops             │
    │ union {                                                      │
    │  ┌────────────────────────────┬───────────────────────────┐  │
    │  │ control                    │ widget                    │  │
    │  │ snd_soc_dobj_control       │ snd_soc_dobj_widget       │  │
    │  │   kcontrol ─▶ snd_kcontrol │   kcontrol_type           │  │
    │  │   dtexts                   │   mixer/enum/bytes        │  │
    │  │   dvalues                  │                           │  │
    │  └────────────────────────────┴───────────────────────────┘  │
    │ }                                                            │
    │ private  component-owned, core never touches                 │
    └──────────────────────────────────────────────────────────────┘

    type = MIXER / BYTES / ENUM ─▶ control arm  (kcontrol back ptr)
    type = WIDGET               ─▶ widget arm   (via container_of)
```

### The type discriminator

The [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) field is an [`enum snd_soc_dobj_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35), one value per object kind the loader can create, with [`SND_SOC_DOBJ_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L36) reserved for a host struct whose dobj is not (or no longer) a live dynamic object:

```c
/* include/sound/soc-topology.h:34 */
/* dynamic object type */
enum snd_soc_dobj_type {
	SND_SOC_DOBJ_NONE		= 0,	/* object is not dynamic */
	SND_SOC_DOBJ_MIXER,
	SND_SOC_DOBJ_BYTES,
	SND_SOC_DOBJ_ENUM,
	SND_SOC_DOBJ_GRAPH,
	SND_SOC_DOBJ_WIDGET,
	SND_SOC_DOBJ_DAI_LINK,
	SND_SOC_DOBJ_PCM,
	SND_SOC_DOBJ_CODEC_LINK,
	SND_SOC_DOBJ_BACKEND_LINK,
};
```

This single value is the only thing [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) consults to decide which remover to run, which is why every object kind can share one [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) despite being a different host struct.

### Every host object embeds the dobj

The dobj is not allocated on its own; it is a member of the host struct, so the host and its dobj share one allocation and one lifetime. A control's host is its private-value struct. [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) places the dobj behind a [`CONFIG_SND_SOC_TOPOLOGY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/Kconfig) guard, so a kernel without topology support pays nothing:

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

A bytes control embeds it the same way in [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254), and an enum in [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273):

```c
/* include/sound/soc.h:1254 */
struct soc_bytes_ext {
	int max;
#ifdef CONFIG_SND_SOC_TOPOLOGY
	struct snd_soc_dobj dobj;
#endif
	/* used for TLV byte control */
	int (*get)(struct snd_kcontrol *kcontrol, unsigned int __user *bytes,
			unsigned int size);
	int (*put)(struct snd_kcontrol *kcontrol, const unsigned int __user *bytes,
			unsigned int size);
};
```

A DAPM widget embeds the dobj after its kcontrol array, so [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) can reach both the [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) and the dobj from one widget pointer:

```c
/* include/sound/soc-dapm.h:552 */
	/* kcontrols that relate to this widget */
	int num_kcontrols;
	const struct snd_kcontrol_new *kcontrol_news;
	struct snd_kcontrol **kcontrols;
	struct snd_soc_dobj dobj;
```

A front-end DAI embeds it in [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and a DAI link in [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), each commented as the topology hook on that struct. The host for a graph route is the [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L811), whose dobj the graph creator fills. The shape is the same in each case. One host struct holds one embedded dobj, with a single entry on [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232).

```
    Each host struct embeds one snd_soc_dobj at a fixed offset
    ──────────────────────────────────────────────────────────
    (boxes are structs; the inner dobj is an embedded member)

    ┌────────────────────────────────────────────────────────────┐
    │ struct soc_mixer_control   (one host; others alike)        │
    │   min  max  reg  shift  ...                                │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │ struct snd_soc_dobj dobj                             │  │
    │  │   type = SND_SOC_DOBJ_MIXER                          │  │
    │  │   list  ─▶ component dobj_list                       │  │
    │  └──────────────────────────────────────────────────────┘  │
    └────────────────────────────────────────────────────────────┘

    container_of(dobj, host, dobj) recovers the host struct:

    ┌───────────────────────┬───────────────────────────┐
    │ dobj.type             │ host struct (embeds dobj) │
    ├───────────────────────┼───────────────────────────┤
    │ SND_SOC_DOBJ_MIXER    │ soc_mixer_control         │
    │ SND_SOC_DOBJ_BYTES    │ soc_bytes_ext             │
    │ SND_SOC_DOBJ_ENUM     │ soc_enum                  │
    │ SND_SOC_DOBJ_GRAPH    │ snd_soc_dapm_route        │
    │ SND_SOC_DOBJ_WIDGET   │ snd_soc_dapm_widget       │
    │ SND_SOC_DOBJ_PCM      │ snd_soc_dai_driver        │
    │ SND_SOC_DOBJ_DAI_LINK │ snd_soc_dai_link          │
    └───────────────────────┴───────────────────────────┘
```

### The component owns the one list

Every dobj from one topology load joins the [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) of the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) the firmware was loaded against. The list head sits in the component, commented as the attached dynamic objects:

```c
/* include/sound/soc-component.h:207 */
struct snd_soc_component {
	const char *name;
	const char *name_prefix;
	struct device *dev;
	struct snd_soc_card *card;
	...
	struct mutex io_mutex;

	/* attached dynamic objects */
	struct list_head dobj_list;
	...
};
```

Because the list belongs to the component and not to the card, a component can unload its topology and reload a different one while the card stays up, and the unload reaches only the objects this component created.

### A creator tags the dobj and links it

The per-block creators are documented separately; what matters to teardown is the three lines every one of them runs after building its object. [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) is representative. It recovers the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) from the control's [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), initializes the dobj list node, sets [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37), copies the component's [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op into [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), creates the kcontrol, and links the dobj onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232):

```c
/* sound/soc/soc-topology.c:905 */
static int soc_tplg_dmixer_create(struct soc_tplg *tplg, size_t size)
{
	struct snd_kcontrol_new kc = {0};
	struct soc_mixer_control *sm;
	int ret;

	if (soc_tplg_check_elem_count(tplg,
				      sizeof(struct snd_soc_tplg_mixer_control),
				      1, size, "mixers"))
		return -EINVAL;

	ret = soc_tplg_control_dmixer_create(tplg, &kc);
	if (ret)
		return ret;

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

The enum and bytes creators differ only in the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) value and the host struct. [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939) sets [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39) on a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) sets [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38) on a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254), each storing the control back pointer in [`sm->dobj.control.kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) and the per-type [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) in [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61). The widget, route, DAI, and link creators each set their own [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and the matching [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), or [`link_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op. Once linked, the object is fully removable from the dobj alone.

### Teardown walks the list once per pass in reverse

[`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) is the inverse of the load and the single entry point a component calls to drop a topology. Its comment reads "remove dynamic controls from the component driver". It runs the pass counter from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), and inside each pass walks [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) with [`list_for_each_entry_safe()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L868), switching on [`dobj->type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to call the matching remover:

```c
/* sound/soc/soc-topology.c:2160 */
/* remove dynamic controls from the component driver */
int snd_soc_tplg_component_remove(struct snd_soc_component *comp)
{
	struct snd_soc_dobj *dobj, *next_dobj;
	int pass;

	/* process the header types from end to start */
	for (pass = SOC_TPLG_PASS_END; pass >= SOC_TPLG_PASS_START; pass--) {

		/* remove mixer controls */
		list_for_each_entry_safe(dobj, next_dobj, &comp->dobj_list,
			list) {

			switch (dobj->type) {
			case SND_SOC_DOBJ_BYTES:
			case SND_SOC_DOBJ_ENUM:
			case SND_SOC_DOBJ_MIXER:
				soc_tplg_remove_kcontrol(comp, dobj, pass);
				break;
			case SND_SOC_DOBJ_GRAPH:
				soc_tplg_remove_route(comp, dobj, pass);
				break;
			case SND_SOC_DOBJ_WIDGET:
				soc_tplg_remove_widget(comp, dobj, pass);
				break;
			case SND_SOC_DOBJ_PCM:
				soc_tplg_remove_dai(comp, dobj, pass);
				break;
			case SND_SOC_DOBJ_DAI_LINK:
				soc_tplg_remove_link(comp, dobj, pass);
				break;
			case SND_SOC_DOBJ_BACKEND_LINK:
				/*
				 * call link_unload ops if extra
				 * deinitialization is needed.
				 */
				remove_backend_link(comp, dobj, pass);
				break;
			default:
				dev_err(comp->dev, "ASoC: invalid component type %d for removal\n",
					dobj->type);
				break;
			}
		}
	}

	/* let caller know if FW can be freed when no objects are left */
	return !list_empty(&comp->dobj_list);
}
```

Two properties of this loop carry the teardown ordering. The outer loop runs the passes in reverse of the load, so routes come down before the widgets they reference and links before the DAIs they bind, and each remover early-returns unless the current pass matches its kind, so an object is removed in exactly one pass even though the list is walked once per pass. The [`list_for_each_entry_safe()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L868) variant caches the next node before the body runs, so a remover may [`list_del()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L235) the current dobj mid-walk. The return value is the result of [`list_empty()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L325) negated, which tells the caller whether any object survived (a backend link reset to [`SND_SOC_DOBJ_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L36) is unlinked, so a fully unwound topology leaves the list empty).

```
    Teardown order: passes run END ─▶ START, one kind per pass
    ──────────────────────────────────────────────────────────
    (snd_soc_tplg_component_remove walks dobj_list once per pass;
     each remover early-returns unless pass matches its kind)

    higher pass = removed first   (reverse of the load order)

    ┌───────────────────────┬──────────────────┬──────────────────────────┐
    │ pass (high ─▶ low)    │ kind             │ remover                  │
    ├───────────────────────┼──────────────────┼──────────────────────────┤
    │ SOC_TPLG_PASS_LINK    │ BACKEND_LINK     │ remove_backend_link      │
    │ SOC_TPLG_PASS_GRAPH   │ GRAPH            │ soc_tplg_remove_route    │
    │ SOC_TPLG_PASS_PCM_DAI │ PCM / DAI_LINK   │ remove_dai / remove_link │
    │ SOC_TPLG_PASS_WIDGET  │ WIDGET           │ soc_tplg_remove_widget   │
    │ SOC_TPLG_PASS_CONTROL │ MIXER/BYTES/ENUM │ soc_tplg_remove_kcontrol │
    └───────────────────────┴──────────────────┴──────────────────────────┘
       ▼  each pass: run dobj->unload, release object, list_del
    routes fall before widgets; links/DAIs before widgets too;
    controls last, so nothing is freed before its referrers
```

### The kcontrol remover deletes one control by its back pointer

Mixer, bytes, and enum dobjs share [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345). It only acts during [`SOC_TPLG_PASS_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L43), runs the component's [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) if one was recorded, then removes exactly the control the dobj points at with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) and unlinks the dobj:

```c
/* sound/soc/soc-topology.c:344 */
/* remove kcontrol */
static void soc_tplg_remove_kcontrol(struct snd_soc_component *comp, struct snd_soc_dobj *dobj,
				     int pass)
{
	struct snd_card *card = comp->card->snd_card;

	if (pass != SOC_TPLG_PASS_CONTROL)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	snd_ctl_remove(card, dobj->control.kcontrol);
	list_del(&dobj->list);
}
```

The [`dobj->control.kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L49) back pointer is the link into the ALSA control list. [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) unlinks that one control from the card and frees it; its kernel-doc notes it takes the card control lock internally and that a NULL argument is a no-op. Because the dobj names a single control, a topology unload removes only its own controls and never disturbs a control the codec registered statically.

### The route remover only runs the unload

A graph dobj has no separately allocated resource for the core to free; the route was added through DAPM and is owned there. [`soc_tplg_remove_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L361) therefore acts during [`SOC_TPLG_PASS_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L46) by running the component's [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and unlinking the dobj:

```c
/* sound/soc/soc-topology.c:360 */
/* remove a route */
static void soc_tplg_remove_route(struct snd_soc_component *comp,
			 struct snd_soc_dobj *dobj, int pass)
{
	if (pass != SOC_TPLG_PASS_GRAPH)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	list_del(&dobj->list);
}
```

For SOF the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) here is [`sof_route_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1611), which tears down the DSP-side connection the route described before the dobj is dropped.

### The widget remover recovers the widget by container_of

A widget dobj is embedded in the [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), so [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) recovers the widget from the dobj with [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19). It acts during [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44), runs the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), removes each of the widget's embedded [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) with [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618), and unlinks the dobj. According to the trailing comment the widget itself is freed by soc-dapm.c at widget teardown:

```c
/* sound/soc/soc-topology.c:373 */
/* remove a widget and it's kcontrols - routes must be removed first */
static void soc_tplg_remove_widget(struct snd_soc_component *comp,
	struct snd_soc_dobj *dobj, int pass)
{
	struct snd_card *card = comp->card->snd_card;
	struct snd_soc_dapm_widget *w =
		container_of(dobj, struct snd_soc_dapm_widget, dobj);
	int i;

	if (pass != SOC_TPLG_PASS_WIDGET)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	if (w->kcontrols)
		for (i = 0; i < w->num_kcontrols; i++)
			snd_ctl_remove(card, w->kcontrols[i]);

	list_del(&dobj->list);

	/* widget w is freed by soc-dapm.c */
}
```

The leading comment, "routes must be removed first", is satisfied by the reverse pass order: [`SOC_TPLG_PASS_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L46) is numerically above [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44), so the descending loop in [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) reaches every route before any widget. The same [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) is also called on the error-unwind path of the widget creator, which passes [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44) directly and then calls [`snd_soc_dapm_free_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2850) to do the soc-dapm.c-side free the comment refers to:

```c
/* sound/soc/soc-topology.c:1247 */
ready_err:
	soc_tplg_remove_widget(snd_soc_dapm_to_component(widget->dapm),
			       &widget->dobj, SOC_TPLG_PASS_WIDGET);
	snd_soc_dapm_free_widget(widget);
```

### The DAI remover recovers the driver and unregisters its DAIs

A PCM dobj is embedded in the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) that the FE-DAI creator built. [`soc_tplg_remove_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L398) recovers the driver by [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19), acts during [`SOC_TPLG_PASS_PCM_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L45), runs the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), and unregisters every DAI on the component that was instantiated from that driver with [`snd_soc_unregister_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2685):

```c
/* sound/soc/soc-topology.c:397 */
/* remove DAI configurations */
static void soc_tplg_remove_dai(struct snd_soc_component *comp,
	struct snd_soc_dobj *dobj, int pass)
{
	struct snd_soc_dai_driver *dai_drv =
		container_of(dobj, struct snd_soc_dai_driver, dobj);
	struct snd_soc_dai *dai, *_dai;

	if (pass != SOC_TPLG_PASS_PCM_DAI)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	for_each_component_dais_safe(comp, dai, _dai)
		if (dai->driver == dai_drv)
			snd_soc_unregister_dai(dai);

	list_del(&dobj->list);
}
```

The [`for_each_component_dais_safe()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L259) walk is safe against removal because [`snd_soc_unregister_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2685) unlinks the DAI it is given. For SOF the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) is [`sof_dai_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1842), which frees the [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352) that the DAI's [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) held.

### The link remover frees the FE link, the backend remover does not

A DAI-link dobj is embedded in the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702). [`soc_tplg_remove_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L419) recovers the link by [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19), runs the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), unlinks the dobj, and removes the link's PCM runtime with [`snd_soc_remove_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1147), unless the link was ignored and never added:

```c
/* sound/soc/soc-topology.c:418 */
/* remove link configurations */
static void soc_tplg_remove_link(struct snd_soc_component *comp,
	struct snd_soc_dobj *dobj, int pass)
{
	struct snd_soc_dai_link *link =
		container_of(dobj, struct snd_soc_dai_link, dobj);

	if (pass != SOC_TPLG_PASS_PCM_DAI)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	list_del(&dobj->list);

	/* Ignored links do not need to be removed, they are not added */
	if (!link->ignore)
		snd_soc_remove_pcm_runtime(comp->card,
				snd_soc_get_pcm_runtime(comp->card, link));
}
```

A backend link is handled apart because, according to its comment, "BE links are not allocated by topology". [`remove_backend_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L440) runs the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), but instead of freeing the link it resets the dobj [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to [`SND_SOC_DOBJ_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L36) so the link reverts to a non-dynamic object, then unlinks the dobj:

```c
/* sound/soc/soc-topology.c:439 */
/* unload dai link */
static void remove_backend_link(struct snd_soc_component *comp,
	struct snd_soc_dobj *dobj, int pass)
{
	if (pass != SOC_TPLG_PASS_LINK)
		return;

	if (dobj->unload)
		dobj->unload(comp, dobj);

	/*
	 * We don't free the link here as what soc_tplg_remove_link() do since BE
	 * links are not allocated by topology.
	 * We however need to reset the dobj type to its initial values
	 */
	dobj->type = SND_SOC_DOBJ_NONE;
	list_del(&dobj->list);
}
```

A backend link runs in [`SOC_TPLG_PASS_LINK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L48), the highest pass, so it is the first kind reached on the reverse walk, before the FE links and DAIs in [`SOC_TPLG_PASS_PCM_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L45).

### The unload callback comes from the component's tplg_ops

The [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) function each remover calls is the component's own, recorded into the dobj at creation from the matching field of [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108). Each load callback in that struct is paired with an unload callback taking a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61):

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
};
```

Each unload callback receives only the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), which is sufficient because the component stored everything it needs in [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) during the corresponding load callback. The core never reads or writes [`private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61); it is the component's slot.

```
    snd_soc_tplg_ops pairs a load op with an unload op per kind
    ──────────────────────────────────────────────────────────
    (creator copies the unload arm into dobj.unload; the remover
     later calls dobj->unload, NULL-checked, then frees the object)

    ┌─────────┬─────────────────┬────────────────────────────┐
    │ kind    │ load op (build) │ unload op  ─▶  dobj.unload │
    ├─────────┼─────────────────┼────────────────────────────┤
    │ control │ control_load    │ control_unload             │
    │ graph   │ dapm_route_load │ dapm_route_unload          │
    │ widget  │ widget_ready    │ widget_unload              │
    │ FE DAI  │ dai_load        │ dai_unload                 │
    │ link    │ link_load       │ link_unload                │
    └─────────┴─────────────────┴────────────────────────────┘

    component supplies the struct; SOF wires every unload arm,
    each freeing the DSP IPC object stashed in dobj->private
```

### SOF triggers and implements the unload path on x86-64

On an Intel SOF platform the topology is loaded against the SOF PCM component, and the component's remove callback drops it. [`sof_pcm_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L797) calls [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) directly:

```c
/* sound/soc/sof/pcm.c:797 */
static void sof_pcm_remove(struct snd_soc_component *component)
{
	/* remove topology */
	snd_soc_tplg_component_remove(component);
}
```

The per-type [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) ops the removers invoke come from [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), SOF's [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108). Every object kind SOF creates has a matching unload op, because each one owns a DSP-side IPC structure that the op frees:

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
	...
};
```

When [`soc_tplg_remove_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L345) runs the recorded [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), it reaches [`sof_control_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1038). It reads [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) as the [`struct snd_sof_control`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L114) it stashed at load, runs the IPC control-free op, and frees its payload:

```c
/* sound/soc/sof/topology.c:1038 */
static int sof_control_unload(struct snd_soc_component *scomp,
			      struct snd_soc_dobj *dobj)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	struct snd_sof_control *scontrol = dobj->private;
	int ret = 0;

	dev_dbg(scomp->dev, "tplg: unload control name : %s\n", scontrol->name);

	if (tplg_ops && tplg_ops->control_free) {
		ret = tplg_ops->control_free(sdev, scontrol);
		if (ret < 0)
			dev_err(scomp->dev, "failed to free control: %s\n", scontrol->name);
	}

	/* free all data before returning in case of error too */
	kfree(scontrol->ipc_control_data);
	kfree(scontrol->priv);
	kfree(scontrol->name);
	list_del(&scontrol->list);
	kfree(scontrol);

	return ret;
}
```

The widget unload follows the same shape on a larger object. When [`soc_tplg_remove_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L374) runs the recorded [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`sof_widget_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1628) reads [`dobj->private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) as a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), frees the per-embedded-control SOF state it tracked through the dobj union's [`kcontrol_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L56), runs the IPC widget free, and frees the SOF widget:

```c
/* sound/soc/sof/topology.c:1628 */
static int sof_widget_unload(struct snd_soc_component *scomp,
			     struct snd_soc_dobj *dobj)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	const struct sof_ipc_tplg_widget_ops *widget_ops;
	const struct snd_kcontrol_new *kc;
	struct snd_soc_dapm_widget *widget;
	struct snd_sof_control *scontrol;
	struct snd_sof_widget *swidget;
	...
	swidget = dobj->private;
	if (!swidget)
		return 0;

	widget = swidget->widget;
	...
	for (i = 0; i < widget->num_kcontrols; i++) {
		kc = &widget->kcontrol_news[i];
		switch (widget->dobj.widget.kcontrol_type[i]) {
		case SND_SOC_TPLG_TYPE_MIXER:
			sm = (struct soc_mixer_control *)kc->private_value;
			scontrol = sm->dobj.private;
			...
		}
		...
	}
out:
	/* free IPC related data */
	widget_ops = tplg_ops ? tplg_ops->widget : NULL;
	if (widget_ops && widget_ops[swidget->id].ipc_free)
		widget_ops[swidget->id].ipc_free(swidget);
	...
	/* remove and free swidget object */
	list_del(&swidget->list);
	kfree(swidget);

	return 0;
}
```

The DSP-side IPC programming the SOF unload callbacks run is the subject of a separate page; the topology framework's contribution ends at walking [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232), invoking each [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), and releasing the live ASoC objects so the card is left exactly as it was before the topology loaded.
