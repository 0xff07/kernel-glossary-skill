# ASoC topology elements

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Each typed block in a topology firmware file is turned into a live ASoC object by a per-block element loader in [`soc-topology.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c): a control block runs [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973) and dispatches to [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905), [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939), or [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) to build a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) whose handlers [`soc_tplg_kcontrol_bind_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459) resolves and [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335) registers; a widget block runs [`soc_tplg_dapm_widget_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258) and [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) to build a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516); a graph block runs [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026); PCM, DAI, and link blocks run [`soc_tplg_pcm_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560) (yielding a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)), [`soc_tplg_dai_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896), and [`soc_tplg_link_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782); and the manifest runs [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927), with each loader calling the matching [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback the consumer (Intel SOF here) registered.

```
    typed block            element loader (soc-topology.c)        ASoC object
    ───────────            ───────────────────────────────        ───────────

    MIXER ────────────┐
    ENUM  ────────────┼──▶ soc_tplg_kcontrol_elems_load
    BYTES ────────────┘         │
                                ├─▶ soc_tplg_dmixer_create ──┐
                                ├─▶ soc_tplg_denum_create  ──┼──▶ struct
                                └─▶ soc_tplg_dbytes_create ──┘    snd_kcontrol
                                       (bind_io, add_kcontrol)

    DAPM_WIDGET ──────────▶ soc_tplg_dapm_widget_elems_load
                                └─▶ soc_tplg_dapm_widget_create ─▶ struct
                                       (snd_soc_dapm_new_control)    snd_soc_dapm_widget

    DAPM_GRAPH ───────────▶ soc_tplg_dapm_graph_elems_load ──────▶ struct
                                  (snd_soc_dapm_add_routes)         snd_soc_dapm_route

    PCM ──────────────────▶ soc_tplg_pcm_elems_load
                                └─▶ soc_tplg_dai_create ─────────▶ struct
                                │      (snd_soc_register_dai)        snd_soc_dai_driver
                                └─▶ soc_tplg_fe_link_create ─────▶ struct
                                       (snd_soc_add_pcm_runtimes)    snd_soc_dai_link

    DAI ──────────────────▶ soc_tplg_dai_elems_load ─────────────▶ (configures
    DAI_LINK / BE_LINK ───▶ soc_tplg_link_elems_load ────────────▶  existing DAI/link)

    MANIFEST ─────────────▶ soc_tplg_manifest_load ──────────────▶ ops->manifest only

    every created object embeds a struct snd_soc_dobj { type, unload }
    on the component dobj_list; teardown is the dobj layer's job
```

## SUMMARY

The pass driver and header walk dispatch a block to its element loader; this page begins where that loader runs and stops at the created ASoC object. The dispatch maps a control block to [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973), a widget block to [`soc_tplg_dapm_widget_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258), a graph block to [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026), a PCM block to [`soc_tplg_pcm_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560), a physical-DAI block to [`soc_tplg_dai_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896), a physical-link block to [`soc_tplg_link_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782), and the manifest to [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927).

A control element loader is a per-block iterator. [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973) reads each [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) and switches on its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) to one of three creators. [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) handles a [`SND_SOC_TPLG_TYPE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L102) block, [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939) a [`SND_SOC_TPLG_TYPE_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L104) block, and [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) a [`SND_SOC_TPLG_TYPE_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L103) block. Each creator builds a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) by delegating to a helper ([`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637), [`soc_tplg_control_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L761), or [`soc_tplg_control_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L830)), which fills the private value, calls [`soc_tplg_kcontrol_bind_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459) to map the on-disk get/put/info IDs to real handlers, and runs the consumer's [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) through [`soc_tplg_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L575). The creator then tags the embedded [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), registers the control with [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335), and links the dobj onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232).

A widget element loader translates the on-disk [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) into a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) template. [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) maps the firmware widget id to a kernel [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) with [`get_widget_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L211), builds any embedded kcontrols with the same three control helpers, runs the consumer's [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), creates the live widget with [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909), and then runs [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108). A graph element loader, [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026), reads each [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), copies its source, sink, and control strings into a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), runs the consumer's [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and adds it with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272).

A PCM element loader, [`soc_tplg_pcm_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560), turns a [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) into two objects through [`soc_tplg_pcm_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1548): a front-end [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) built and registered by [`soc_tplg_dai_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364) with [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) (after running [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)), and a DPCM-enabled [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) built and added by [`soc_tplg_fe_link_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1462) with [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) (after running [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)). The physical-DAI and physical-link loaders do not allocate new objects; [`soc_tplg_dai_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896) finds an already-registered DAI and reconfigures it, and [`soc_tplg_link_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782) finds an existing back-end link and rewrites its format and flags. The manifest loader runs first and creates nothing; [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927) size-checks the [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) and forwards it to the consumer's [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback. The pass model and the header walk that select these loaders, and the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) teardown that releases what they create, are documented separately.

## SPECIFICATIONS

The element loaders parse the ASoC topology ABI defined in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h). Each typed block carries one on-disk element type ([`struct snd_soc_tplg_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L392), [`struct snd_soc_tplg_enum_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414), [`struct snd_soc_tplg_bytes_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L437), [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480), [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513), or [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370)), and the consumer contract is the [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) function pointer struct. Both the ABI and the ASoC objects the loaders produce are Linux kernel software constructs with no external hardware specification. On x86-64 ACPI platforms the Intel SOF firmware package ships the binary topology that the alsatplg compiler produced from text, paired with a given DSP firmware image.

## LINUX KERNEL

### Control element loader and creators (soc-topology.c)

- [`'\<soc_tplg_kcontrol_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973): iterate a control block's [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) elements and switch on the per-control type to the mixer, enum, or bytes creator
- [`'\<soc_tplg_dmixer_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905): build a mixer [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), tag its [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37), and register it
- [`'\<soc_tplg_denum_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939): build an enumerated control over a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and tag the dobj [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39)
- [`'\<soc_tplg_dbytes_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871): build a bytes control over a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) and tag the dobj [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38)
- [`'\<soc_tplg_control_dmixer_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637): allocate a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), fill its reg/shift/min/max from the [`struct snd_soc_tplg_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L392), bind IO, create TLV, run [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)
- [`'\<soc_tplg_control_denum_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L761): allocate a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), build its texts and optional values tables, bind IO, run [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)
- [`'\<soc_tplg_control_dbytes_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L830): allocate a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254), set its max, bind IO (which may pick up TLV-bytes ext handlers), run [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)
- [`'\<soc_tplg_kcontrol_bind_io\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459): handle the TLV-bytes case, then match the on-disk get/put/info IDs against the consumer's [`io_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) table first and the built-in [`io_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L123) second
- [`'\<soc_tplg_add_kcontrol\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335): hand the template to [`soc_tplg_add_dcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311) and store the resulting [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) back pointer in the dobj
- [`'\<soc_tplg_add_dcontrol\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311): create the runtime control with [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and add it with [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546)
- [`'\<soc_tplg_control_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L575): call the consumer's [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the built [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286)
- [`'\<soc_tplg_create_tlv\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L610): attach a dB-scale TLV array to the mixer kcontrol when the control's access bits request one
- [`io_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L123): the built-in table pairing each `SND_SOC_TPLG_CTL_*` and `SND_SOC_TPLG_DAPM_CTL_*` ID with the standard ALSA SoC handlers ([`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375), [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396), and so on)

### Widget element loader and creator (soc-topology.c)

- [`'\<soc_tplg_dapm_widget_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258): bounds-check each [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) against the firmware size and hand it to the creator
- [`'\<soc_tplg_dapm_widget_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097): fill a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) template, build embedded kcontrols, run [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), create the live widget, tag the dobj [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41), run [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)
- [`'\<get_widget_id\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L211): translate the firmware widget [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) to a kernel [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value through the [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) table
- [`'\<soc_tplg_widget_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L257): call the consumer's [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the template before the live widget is created
- [`'\<soc_tplg_widget_ready\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L269): call the consumer's [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the live widget after it is added
- [`'\<snd_soc_dapm_new_control\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909): copy the widget template into a live [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) under the DAPM mutex

### Graph element loader (soc-topology.c)

- [`'\<soc_tplg_dapm_graph_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026): build a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) from each [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), tag the dobj [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40), run [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and add the route
- [`'\<soc_tplg_add_route\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1016): call the consumer's [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the built [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) just before the core adds it
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): link the route's named source and sink widgets together in the DAPM graph

### PCM, DAI, and link element loaders (soc-topology.c)

- [`'\<soc_tplg_pcm_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560): size-check each [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) and call [`soc_tplg_pcm_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1548)
- [`'\<soc_tplg_pcm_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1548): create the FE DAI driver, then the FE DAI link, from one PCM block
- [`'\<soc_tplg_dai_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364): allocate a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), fill its stream caps, run [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), tag the dobj [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43), register it with [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706), and create its DAI widgets with [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359)
- [`'\<soc_tplg_fe_link_create\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1462): allocate a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), set [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) to enable DPCM, default the codec and platform to the dummy component, run [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and add it with [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269)
- [`'\<soc_tplg_dai_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L280): call the consumer's [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)
- [`'\<soc_tplg_dai_link_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L292): call the consumer's [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702)
- [`'\<soc_tplg_dai_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896): iterate each [`struct snd_soc_tplg_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L630) and reconfigure an already-registered BE DAI with [`soc_tplg_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1834)
- [`'\<soc_tplg_dai_config\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1834): find the physical DAI by name with [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L800), overwrite its stream caps and flags, and run [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)
- [`'\<soc_tplg_link_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782): iterate each [`struct snd_soc_tplg_link_config`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L541) and reconfigure an existing back-end link with [`soc_tplg_link_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1721)
- [`'\<soc_tplg_link_config\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1721): find the link by id and name with [`snd_soc_find_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L596), set its hw format and flags, run [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and tag the dobj [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45)

### Manifest element loader (soc-topology.c)

- [`'\<soc_tplg_manifest_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927): size-check the [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) and forward it to the consumer's [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback; no ASoC object is created

### Produced ASoC types (control.h, soc.h, soc-dapm.h, soc-dai.h)

- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the control template the control creators build on the stack before [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335) instantiates it
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the widget object whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) the widget creator fills from [`get_widget_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L211), carrying the embedded [`dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516)
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): the route object the graph loader fills from a graph element's source, sink, and control strings
- [`'\<struct snd_soc_dai_link\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702): the FE DAI link [`soc_tplg_fe_link_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1462) allocates with [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) set
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the FE DAI driver [`soc_tplg_dai_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364) allocates and registers
- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) / [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) / [`'\<struct soc_bytes_ext\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254): the private-value structs the three control helpers allocate, each embedding a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61)

### On-disk element types (include/uapi/sound/asoc.h)

- [`'\<struct snd_soc_tplg_ctl_hdr\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286): the per-control header carrying the control [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286), and the get/put/info [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286)
- [`'\<struct snd_soc_tplg_mixer_control\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L392): the mixer element with min/max/invert and a [`channel`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L392) map
- [`'\<struct snd_soc_tplg_enum_control\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414): the enum element with [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414), [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414), [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414), and [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L414)
- [`'\<struct snd_soc_tplg_bytes_control\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L437): the bytes element with [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L437) and an [`ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L437) selector
- [`'\<struct snd_soc_tplg_dapm_widget\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480): the widget element with [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480), name, power-register fields, [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480), and trailing private data
- [`'\<struct snd_soc_tplg_dapm_graph_elem\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458): the graph element of [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458) names
- [`'\<struct snd_soc_tplg_pcm\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513): the PCM element with [`pcm_name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513), [`dai_name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513), the [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513)/[`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) flags, and per-direction [`caps`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513)
- [`'\<struct snd_soc_tplg_manifest\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370): the manifest element of payload counts ([`control_elems`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370), [`widget_elems`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370), [`graph_elems`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370), [`pcm_elems`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370))

### SOF consumer callbacks (sof/topology.c)

- [`'sof_tplg_ops':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305): SOF's [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), wiring the control, route, widget, DAI, link, and manifest callbacks each element loader invokes
- [`'\<sof_control_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961): the [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback the control creators run after [`soc_tplg_kcontrol_bind_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459)
- [`'\<sof_route_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2087): the [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback the graph loader runs per route
- [`'\<sof_widget_ready\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409): the [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback the widget creator runs on the live widget, building a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422)
- [`'\<sof_dai_load\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726): the [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback [`soc_tplg_dai_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364) runs, allocating a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352)
- [`'\<sof_manifest\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279): the [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927) runs first

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget and route model that the widget and graph element loaders build
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): the Dynamic PCM front-end and back-end split the PCM element loader instantiates
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the DAI link structure the PCM and link loaders populate
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the kcontrol and widget arrays that the control and widget loaders produce dynamically

## OTHER SOURCES

- [Sound Open Firmware topology documentation](https://thesofproject.github.io/latest/architectures/firmware/sof-common/topology.html)
- [ALSA topology project documentation](https://www.alsa-project.org/wiki/ASoC/Dynamic_Audio_Architecture)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

Each element loader produces a different ASoC object and records a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) of the matching [`enum snd_soc_dobj_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L35) so the teardown path can find and free it. The control and widget creators build a stack template first, the graph loader builds a route in place, and the PCM loader allocates two objects. The physical-DAI and physical-link loaders create nothing new; they locate an already-present object and rewrite it, which is why they tag no dobj for the DAI and tag the BE link only so it can be unloaded.

| created object | created by | dobj type | lifetime |
|----------------|-----------|-----------|----------|
| mixer [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) | [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37) | freed at topology unload via dobj |
| enum [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | [`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939) | [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39) | freed at topology unload via dobj |
| bytes [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) | [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38) | freed at topology unload via dobj |
| [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) | [`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) | [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41) | freed at topology unload via dobj |
| [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) | [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026) | [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40) | freed at topology unload via dobj |
| FE [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) | [`soc_tplg_dai_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364) | [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43) | freed at topology unload via dobj |
| FE [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) | [`soc_tplg_fe_link_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1462) | [`SND_SOC_DOBJ_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L42) | freed at topology unload via dobj |
| existing BE DAI (reconfigured) | [`soc_tplg_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1834) | (none) | owned by the platform driver |
| existing BE link (reconfigured) | [`soc_tplg_link_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1721) | [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45) | link owned by machine, dobj for unload |
| (manifest) | [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927) | (none) | passed to [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) only |

## DETAILS

### Control blocks: one loader, three creators

The control element loader is a per-block iterator over [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) elements. [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973) reads the per-control header at [`tplg->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), validates its size, and switches on its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) to call the mixer, enum, or bytes creator. The header type is the per-element discriminator, separate from the block type the header walk used to reach this loader:

```c
/* sound/soc/soc-topology.c:973 */
static int soc_tplg_kcontrol_elems_load(struct soc_tplg *tplg,
	struct snd_soc_tplg_hdr *hdr)
{
	int ret;
	int i;

	dev_dbg(tplg->dev, "ASoC: adding %d kcontrols at 0x%lx\n", hdr->count,
		soc_tplg_get_offset(tplg));

	for (i = 0; i < le32_to_cpu(hdr->count); i++) {
		struct snd_soc_tplg_ctl_hdr *control_hdr = (struct snd_soc_tplg_ctl_hdr *)tplg->pos;

		if (le32_to_cpu(control_hdr->size) != sizeof(*control_hdr)) {
			dev_err(tplg->dev, "ASoC: invalid control size\n");
			return -EINVAL;
		}

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

		if (ret < 0) {
			dev_err(tplg->dev, "ASoC: invalid control type: %d, index: %d at 0x%lx\n",
				control_hdr->type, i, soc_tplg_get_offset(tplg));
			return ret;
		}
	}

	return 0;
}
```

Each creator follows the same three-part shape, and [`soc_tplg_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L905) is the template for the other two. It checks the element count, delegates the actual kcontrol build to [`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637), recovers the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the helper allocated, sets the embedded [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) type to [`SND_SOC_DOBJ_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L37) and its [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to the consumer's [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), instantiates the control with [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335), and links the dobj onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232):

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

[`soc_tplg_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L939) and [`soc_tplg_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L871) differ only in the private struct, the element type they size-check, and the dobj type they stamp. The enum creator recovers a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and stamps [`SND_SOC_DOBJ_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L39); the bytes creator recovers a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) and stamps [`SND_SOC_DOBJ_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L38):

```c
/* sound/soc/soc-topology.c:939 */
static int soc_tplg_denum_create(struct soc_tplg *tplg, size_t size)
{
	struct snd_kcontrol_new kc = {0};
	struct soc_enum *se;
	int ret;

	if (soc_tplg_check_elem_count(tplg,
				      sizeof(struct snd_soc_tplg_enum_control),
				      1, size, "enums"))
		return -EINVAL;

	ret = soc_tplg_control_denum_create(tplg, &kc);
	if (ret)
		return ret;

	/* register dynamic object */
	se = (struct soc_enum *)kc.private_value;

	INIT_LIST_HEAD(&se->dobj.list);
	se->dobj.type = SND_SOC_DOBJ_ENUM;
	se->dobj.index = tplg->index;
	if (tplg->ops)
		se->dobj.unload = tplg->ops->control_unload;

	/* create control directly */
	ret = soc_tplg_add_kcontrol(tplg, &kc, &se->dobj.control.kcontrol);
	if (ret < 0)
		return ret;

	list_add(&se->dobj.list, &tplg->comp->dobj_list);

	return ret;
}
```

### The control helper builds the template and binds IO

The helper a creator delegates to does the work that turns an on-disk element into a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47). [`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637) reads the [`struct snd_soc_tplg_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L392) at [`tplg->pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), allocates the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) that becomes the template's [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), advances the cursor past the element and its private data, copies the name and access bits, derives the register and shift from the channel map, copies the min/max/invert, then binds the IO handlers and runs the consumer's [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108):

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

	sm = devm_kzalloc(tplg->dev, sizeof(*sm), GFP_KERNEL);
	if (!sm)
		return -ENOMEM;

	tplg->pos += sizeof(struct snd_soc_tplg_mixer_control) + le32_to_cpu(mc->priv.size);

	dev_dbg(tplg->dev, "ASoC: adding mixer kcontrol %s with access 0x%x\n",
		mc->hdr.name, mc->hdr.access);

	kc->name = devm_kstrdup(tplg->dev, mc->hdr.name, GFP_KERNEL);
	if (!kc->name)
		return -ENOMEM;
	kc->private_value = (long)sm;
	kc->iface = SNDRV_CTL_ELEM_IFACE_MIXER;
	kc->access = le32_to_cpu(mc->hdr.access);

	/* we only support FL/FR channel mapping atm */
	sm->reg = tplg_chan_get_reg(tplg, mc->channel, SNDRV_CHMAP_FL);
	sm->rreg = tplg_chan_get_reg(tplg, mc->channel, SNDRV_CHMAP_FR);
	sm->shift = tplg_chan_get_shift(tplg, mc->channel, SNDRV_CHMAP_FL);
	sm->rshift = tplg_chan_get_shift(tplg, mc->channel, SNDRV_CHMAP_FR);

	sm->max = le32_to_cpu(mc->max);
	sm->min = le32_to_cpu(mc->min);
	sm->invert = le32_to_cpu(mc->invert);
	sm->platform_max = le32_to_cpu(mc->platform_max);
	sm->num_channels = le32_to_cpu(mc->num_channels);

	/* map io handlers */
	err = soc_tplg_kcontrol_bind_io(&mc->hdr, kc, tplg);
	if (err) {
		soc_control_err(tplg, &mc->hdr, mc->hdr.name);
		return err;
	}

	/* create any TLV data */
	err = soc_tplg_create_tlv(tplg, kc, &mc->hdr);
	if (err < 0) {
		dev_err(tplg->dev, "ASoC: failed to create TLV %s\n", mc->hdr.name);
		return err;
	}

	/* pass control to driver for optional further init */
	return soc_tplg_control_load(tplg, kc, &mc->hdr);
}
```

A topology control names its handlers by numeric ID rather than by symbol, so the template's [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) pointers are filled by a lookup. [`soc_tplg_kcontrol_bind_io()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L459) first handles the TLV-bytes special case (where the bytes control carries its own ext get/put through [`bytes_ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)), then scans the consumer's [`io_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) table for any unset pointer whose ID matches, and only when a handler is still unset falls through to the built-in [`io_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L123):

```c
/* sound/soc/soc-topology.c:513 */
	/* try and map vendor specific kcontrol handlers first */
	ops = tplg->io_ops;
	num_ops = tplg->io_ops_count;
	for (i = 0; i < num_ops; i++) {

		if (k->put == NULL && ops[i].id == le32_to_cpu(hdr->ops.put))
			k->put = ops[i].put;
		if (k->get == NULL && ops[i].id == le32_to_cpu(hdr->ops.get))
			k->get = ops[i].get;
		if (k->info == NULL && ops[i].id == le32_to_cpu(hdr->ops.info))
			k->info = ops[i].info;
	}

	/* vendor specific handlers found ? */
	if (k->put && k->get && k->info)
		return 0;

	/* none found so try standard kcontrol handlers */
	ops = io_ops;
	num_ops = ARRAY_SIZE(io_ops);
	for (i = 0; i < num_ops; i++) {

		if (k->put == NULL && ops[i].id == le32_to_cpu(hdr->ops.put))
			k->put = ops[i].put;
		if (k->get == NULL && ops[i].id == le32_to_cpu(hdr->ops.get))
			k->get = ops[i].get;
		if (k->info == NULL && ops[i].id == le32_to_cpu(hdr->ops.info))
			k->info = ops[i].info;
	}
```

The built-in [`io_ops[]`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L123) table pairs each standard control-type ID with the same ALSA SoC handlers a static C control would wire, so a topology that uses only standard control types needs no consumer IO ops at all:

```c
/* sound/soc/soc-topology.c:123 */
static const struct snd_soc_tplg_kcontrol_ops io_ops[] = {
	{SND_SOC_TPLG_CTL_VOLSW, snd_soc_get_volsw,
		snd_soc_put_volsw, snd_soc_info_volsw},
	{SND_SOC_TPLG_CTL_VOLSW_SX, snd_soc_get_volsw_sx,
		snd_soc_put_volsw_sx, NULL},
	{SND_SOC_TPLG_CTL_ENUM, snd_soc_get_enum_double,
		snd_soc_put_enum_double, snd_soc_info_enum_double},
	{SND_SOC_TPLG_CTL_ENUM_VALUE, snd_soc_get_enum_double,
		snd_soc_put_enum_double, NULL},
	{SND_SOC_TPLG_CTL_BYTES, snd_soc_bytes_get,
		snd_soc_bytes_put, snd_soc_bytes_info},
	{SND_SOC_TPLG_CTL_RANGE, snd_soc_get_volsw,
		snd_soc_put_volsw, snd_soc_info_volsw},
	{SND_SOC_TPLG_CTL_VOLSW_XR_SX, snd_soc_get_xr_sx,
		snd_soc_put_xr_sx, snd_soc_info_xr_sx},
	{SND_SOC_TPLG_CTL_STROBE, snd_soc_get_strobe,
		snd_soc_put_strobe, NULL},
	{SND_SOC_TPLG_DAPM_CTL_VOLSW, snd_soc_dapm_get_volsw,
		snd_soc_dapm_put_volsw, snd_soc_info_volsw},
	{SND_SOC_TPLG_DAPM_CTL_ENUM_DOUBLE, snd_soc_dapm_get_enum_double,
		snd_soc_dapm_put_enum_double, snd_soc_info_enum_double},
	{SND_SOC_TPLG_DAPM_CTL_ENUM_VIRT, snd_soc_dapm_get_enum_double,
		snd_soc_dapm_put_enum_double, NULL},
	{SND_SOC_TPLG_DAPM_CTL_ENUM_VALUE, snd_soc_dapm_get_enum_double,
		snd_soc_dapm_put_enum_double, NULL},
	{SND_SOC_TPLG_DAPM_CTL_PIN, snd_soc_dapm_get_pin_switch,
		snd_soc_dapm_put_pin_switch, snd_soc_dapm_info_pin_switch},
};
```

The enum helper [`soc_tplg_control_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L761) follows the same path but builds the texts and (for a value-mapped enum) values tables before binding IO. It switches on the control's info ID so a [`SND_SOC_TPLG_CTL_ENUM_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h) enum gets both a values table and a texts table, while a plain enum gets only texts:

```c
/* sound/soc/soc-topology.c:795 */
	switch (le32_to_cpu(ec->hdr.ops.info)) {
	case SND_SOC_TPLG_CTL_ENUM_VALUE:
	case SND_SOC_TPLG_DAPM_CTL_ENUM_VALUE:
		err = soc_tplg_denum_create_values(tplg, se, ec);
		if (err < 0) {
			dev_err(tplg->dev, "ASoC: could not create values for %s\n", ec->hdr.name);
			return err;
		}
		fallthrough;
	case SND_SOC_TPLG_CTL_ENUM:
	case SND_SOC_TPLG_DAPM_CTL_ENUM_DOUBLE:
	case SND_SOC_TPLG_DAPM_CTL_ENUM_VIRT:
		err = soc_tplg_denum_create_texts(tplg, se, ec);
		if (err < 0) {
			dev_err(tplg->dev, "ASoC: could not create texts for %s\n", ec->hdr.name);
			return err;
		}
		break;
	default:
		dev_err(tplg->dev, "ASoC: invalid enum control type %d for %s\n",
			ec->hdr.ops.info, ec->hdr.name);
		return -EINVAL;
	}
```

The bind step turns the on-disk get, put, and info IDs into handler pointers, trying the consumer table first and the built-in table for whatever it leaves unset:

```
    bind_io resolves a control's get/put/info by numeric ID
    ──────────────────────────────────────────────────────────
    (on-disk hdr.ops.{get,put,info} are numeric IDs; each
     pointer is filled once, by the first tier whose id matches)

    hdr.ops.{get, put, info}   numeric IDs from firmware
              │
              ▼
    ┌────────────────────────────────────────────────────────────┐
    │ tier 1  consumer io_ops[]   (vendor handlers, optional)    │
    └────────────────────────────────────────────────────────────┘
              │  any pointer still NULL falls through
              ▼
    ┌────────────────────────────────────────────────────────────┐
    │ tier 2  built-in io_ops[]   (standard ALSA SoC handlers)   │
    └────────────────────────────────────────────────────────────┘

    built-in io_ops[]:  control-type ID ─▶ handler triple
    ┌───────────────────────────┬─────────────────────────┐
    │ SND_SOC_TPLG_CTL_VOLSW    │ get/put/info_volsw      │
    │ SND_SOC_TPLG_CTL_ENUM     │ get/put_enum_double     │
    │ SND_SOC_TPLG_CTL_BYTES    │ bytes_get/put/info      │
    │ SND_SOC_TPLG_CTL_RANGE    │ get/put_volsw           │
    │ SND_SOC_TPLG_DAPM_CTL_PIN │ dapm_get/put_pin_switch │
    └───────────────────────────┴─────────────────────────┘
```

### Instantiation and the consumer control_load callback

Once a creator has the template and dobj, [`soc_tplg_add_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L335) turns it into a live [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and stores the back pointer in the dobj's control union. It is a thin wrapper over [`soc_tplg_add_dcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311), passing the component's name prefix so two instances of the same component do not collide:

```c
/* sound/soc/soc-topology.c:335 */
static int soc_tplg_add_kcontrol(struct soc_tplg *tplg,
	struct snd_kcontrol_new *k, struct snd_kcontrol **kcontrol)
{
	struct snd_soc_component *comp = tplg->comp;

	return soc_tplg_add_dcontrol(comp->card->snd_card,
				tplg->dev, k, comp->name_prefix, comp, kcontrol);
}
```

[`soc_tplg_add_dcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L311) is the same [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) plus [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) pair a statically declared control takes, so a topology control reaches the ALSA card by the same route as a C-declared one, differing only in that its template was assembled at runtime from firmware:

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

The consumer callback runs inside the helper, before the creator stamps the dobj, through [`soc_tplg_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L575). It calls the consumer's [`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the built [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and the on-disk [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286), treating an absent callback as success:

```c
/* sound/soc/soc-topology.c:575 */
static int soc_tplg_control_load(struct soc_tplg *tplg,
	struct snd_kcontrol_new *k, struct snd_soc_tplg_ctl_hdr *hdr)
{
	int ret = 0;

	if (tplg->ops && tplg->ops->control_load)
		ret = tplg->ops->control_load(tplg->comp, tplg->index, k, hdr);

	if (ret)
		dev_err(tplg->dev, "ASoC: failed to init %s\n", hdr->name);

	return ret;
}
```

On x86-64 SOF this reaches [`sof_control_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L961), which builds the IPC control payload (a volume, enum, or bytes structure) the DSP will later read, but the ASoC control object itself is fully formed by the time the callback runs.

### Widget blocks become DAPM widgets

The widget element loader [`soc_tplg_dapm_widget_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258) iterates the block, and for each [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) it checks that the element header and its private data fit inside the firmware file before handing it to the creator. The on-disk widget carries the widget name, the firmware widget id, the power-register fields, a kcontrol count, and trailing private data, with any embedded controls appended after that:

```c
/* include/uapi/sound/asoc.h:480 */
struct snd_soc_tplg_dapm_widget {
	__le32 size;		/* in bytes of this structure */
	__le32 id;		/* SND_SOC_DAPM_CTL */
	char name[SNDRV_CTL_ELEM_ID_NAME_MAXLEN];
	char sname[SNDRV_CTL_ELEM_ID_NAME_MAXLEN];

	__le32 reg;		/* negative reg = no direct dapm */
	__le32 shift;		/* bits to shift */
	__le32 mask;		/* non-shifted mask */
	__le32 subseq;		/* sort within widget type */
	__le32 invert;		/* invert the power bit */
	__le32 ignore_suspend;	/* kept enabled over suspend */
	__le16 event_flags;
	__le16 event_type;
	__le32 num_kcontrols;
	struct snd_soc_tplg_private priv;
	/*
	 * kcontrols that relate to this widget
	 * follow here after widget private data
	 */
} __attribute__((packed));
```

[`soc_tplg_dapm_widget_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1097) fills a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) template field by field. It maps the firmware [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480) to a kernel [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) with [`get_widget_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L211), duplicates the name and stream name, copies the power-register fields, and derives [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516)/[`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) from the invert flag:

```c
/* sound/soc/soc-topology.c:1122 */
	memset(&template, 0, sizeof(template));

	/* map user to kernel widget ID */
	template.id = get_widget_id(le32_to_cpu(w->id));
	if ((int)template.id < 0)
		return template.id;

	/* strings are allocated here, but used and freed by the widget */
	template.name = kstrdup(w->name, GFP_KERNEL);
	if (!template.name)
		return -ENOMEM;
	template.sname = kstrdup(w->sname, GFP_KERNEL);
	if (!template.sname) {
		ret = -ENOMEM;
		goto err;
	}
	template.reg = le32_to_cpu(w->reg);
	template.shift = le32_to_cpu(w->shift);
	template.mask = le32_to_cpu(w->mask);
	template.subseq = le32_to_cpu(w->subseq);
	template.on_val = w->invert ? 0 : 1;
	template.off_val = w->invert ? 1 : 0;
	template.ignore_suspend = le32_to_cpu(w->ignore_suspend);
	template.event_flags = le16_to_cpu(w->event_flags);
	template.dobj.index = tplg->index;
```

[`get_widget_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L211) is the translation that lets a firmware file name a widget kind. It scans the [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) table for the on-disk uid and returns the kernel id, so a `SND_SOC_TPLG_DAPM_*` value on disk becomes a [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), or other [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value:

```c
/* sound/soc/soc-topology.c:211 */
static int get_widget_id(int tplg_type)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(dapm_map); i++) {
		if (tplg_type == dapm_map[i].uid)
			return dapm_map[i].kid;
	}

	return -EINVAL;
}
```

When the widget carries embedded kcontrols, the creator builds them with the very same three control helpers the control block uses, switching on each control header's type and tagging each with its index within the widget. A mixer control inside a widget runs [`soc_tplg_control_dmixer_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L637), an enum runs [`soc_tplg_control_denum_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L761), and bytes run [`soc_tplg_control_dbytes_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L830), into the per-widget [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) array:

```c
/* sound/soc/soc-topology.c:1171 */
	for (i = 0; i < le32_to_cpu(w->num_kcontrols); i++) {
		control_hdr = (struct snd_soc_tplg_ctl_hdr *)tplg->pos;

		switch (le32_to_cpu(control_hdr->type)) {
		case SND_SOC_TPLG_TYPE_MIXER:
			/* volume mixer */
			kc[i].index = mixer_count;
			kcontrol_type[i] = SND_SOC_TPLG_TYPE_MIXER;
			mixer_count++;
			ret = soc_tplg_control_dmixer_create(tplg, &kc[i]);
			if (ret < 0)
				goto hdr_err;
			break;
		case SND_SOC_TPLG_TYPE_ENUM:
			/* enumerated mixer */
			kc[i].index = enum_count;
			kcontrol_type[i] = SND_SOC_TPLG_TYPE_ENUM;
			enum_count++;
			ret = soc_tplg_control_denum_create(tplg, &kc[i]);
			if (ret < 0)
				goto hdr_err;
			break;
		case SND_SOC_TPLG_TYPE_BYTES:
			/* bytes control */
			kc[i].index = bytes_count;
			kcontrol_type[i] = SND_SOC_TPLG_TYPE_BYTES;
			bytes_count++;
			ret = soc_tplg_control_dbytes_create(tplg, &kc[i]);
			if (ret < 0)
				goto hdr_err;
			break;
		default:
			dev_err(tplg->dev, "ASoC: invalid widget control type %d:%d:%d\n",
				control_hdr->ops.get, control_hdr->ops.put,
				le32_to_cpu(control_hdr->ops.info));
			ret = -EINVAL;
			goto hdr_err;
		}
	}
```

The tail of the creator is where the live widget appears. It runs the consumer's [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the template, then creates the widget with [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909) (or the unlocked variant when the card is still initialising), stamps the dobj [`SND_SOC_DOBJ_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L41) with the consumer's [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) recorded, links it onto [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232), and runs [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the live widget:

```c
/* sound/soc/soc-topology.c:1215 */
widget:
	ret = soc_tplg_widget_load(tplg, &template, w);
	if (ret < 0)
		goto hdr_err;

	/* card dapm mutex is held by the core if we are loading topology
	 * data during sound card init. */
	if (snd_soc_card_is_instantiated(card))
		widget = snd_soc_dapm_new_control(dapm, &template);
	else
		widget = snd_soc_dapm_new_control_unlocked(dapm, &template);
	if (IS_ERR(widget)) {
		ret = PTR_ERR(widget);
		goto hdr_err;
	}

	widget->dobj.type = SND_SOC_DOBJ_WIDGET;
	widget->dobj.widget.kcontrol_type = kcontrol_type;
	if (tplg->ops)
		widget->dobj.unload = tplg->ops->widget_unload;
	widget->dobj.index = tplg->index;
	list_add(&widget->dobj.list, &tplg->comp->dobj_list);

	ret = soc_tplg_widget_ready(tplg, widget, w);
	if (ret < 0)
		goto ready_err;
```

[`soc_tplg_widget_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L257) and [`soc_tplg_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L269) are the two guards reaching the consumer, one on the template before creation and one on the live widget after. SOF leaves [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) unset and uses [`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) because it needs the created widget pointer:

```c
/* sound/soc/soc-topology.c:269 */
static int soc_tplg_widget_ready(struct soc_tplg *tplg,
	struct snd_soc_dapm_widget *w, struct snd_soc_tplg_dapm_widget *tplg_w)
{
	if (tplg->ops && tplg->ops->widget_ready)
		return tplg->ops->widget_ready(tplg->comp, tplg->index, w,
			tplg_w);

	return 0;
}
```

On x86-64 SOF the callback is [`sof_widget_ready()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1409), which allocates a [`struct snd_sof_widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L422), assigns the DSP component id, stores the live DAPM widget pointer back in it, and parses the widget's vendor tokens into an IPC component description:

```c
/* sound/soc/sof/topology.c:1409 */
static int sof_widget_ready(struct snd_soc_component *scomp, int index,
			    struct snd_soc_dapm_widget *w,
			    struct snd_soc_tplg_dapm_widget *tw)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	...
	struct snd_sof_widget *swidget;
	struct snd_sof_dai *dai;
	int token_list_size = 0;
	int ret = 0;

	swidget = kzalloc(sizeof(*swidget), GFP_KERNEL);
	if (!swidget)
		return -ENOMEM;

	swidget->scomp = scomp;
	swidget->widget = w;
	swidget->comp_id = sdev->next_comp_id++;
	swidget->id = w->id;
	...
}
```

The widget creator copies the on-disk fields into a DAPM widget template, translating the firmware id to a kernel widget type and carrying name, registers, and flags across:

```
    Widget block: on-disk element mapped to a DAPM template
    ──────────────────────────────────────────────────────────
    (soc_tplg_dapm_widget_create copies field by field; the id
     is translated, the rest copied or derived)

    ┌──────────────────────────┬──────────────────────────────────────┐
    │ snd_soc_tplg_dapm_widget │    snd_soc_dapm_widget (template)    │
    ├──────────────────────────┼──────────────────────────────────────┤
    │ id                       │ ─▶ template.id   (via get_widget_id) │
    │ name / sname             │ ─▶ template.name / sname  (kstrdup)  │
    │ reg/shift/mask           │ ─▶ template.reg / shift / mask       │
    │ subseq                   │ ─▶ template.subseq                   │
    │ invert                   │ ─▶ on_val / off_val  (derived)       │
    │ event_flags              │ ─▶ template.event_flags              │
    │ + trailing priv          │ ─▶ embedded kcontrols (built next)   │
    └──────────────────────────┴──────────────────────────────────────┘

    get_widget_id: firmware uid ─▶ kernel enum snd_soc_dapm_type
    via the dapm_map[] table, e.g.
      SND_SOC_TPLG_DAPM_* ─▶ snd_soc_dapm_pga / _mixer / _mux / ...
```

### Graph blocks become DAPM routes

The graph element loader builds one [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) per [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458). The on-disk element is three fixed-length strings. They are a sink, an optional control, and a source. [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026) allocates a route, validates the string lengths, duplicates source and sink (and control when present) into the route, stamps the dobj [`SND_SOC_DOBJ_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L40) with the consumer's [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), links it, runs the consumer's [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) through [`soc_tplg_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1016), and adds the route with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272):

```c
/* sound/soc/soc-topology.c:1046 */
	for (i = 0; i < count; i++) {
		route = devm_kzalloc(tplg->dev, sizeof(*route), GFP_KERNEL);
		if (!route)
			return -ENOMEM;
		elem = (struct snd_soc_tplg_dapm_graph_elem *)tplg->pos;
		tplg->pos += sizeof(struct snd_soc_tplg_dapm_graph_elem);

		/* validate routes */
		if ((strnlen(elem->source, maxlen) == maxlen) ||
		    (strnlen(elem->sink, maxlen) == maxlen) ||
		    (strnlen(elem->control, maxlen) == maxlen)) {
			ret = -EINVAL;
			break;
		}

		route->source = devm_kstrdup(tplg->dev, elem->source, GFP_KERNEL);
		route->sink = devm_kstrdup(tplg->dev, elem->sink, GFP_KERNEL);
		if (!route->source || !route->sink) {
			ret = -ENOMEM;
			break;
		}

		if (strnlen(elem->control, maxlen) != 0) {
			route->control = devm_kstrdup(tplg->dev, elem->control, GFP_KERNEL);
			if (!route->control) {
				ret = -ENOMEM;
				break;
			}
		}

		/* add route dobj to dobj_list */
		route->dobj.type = SND_SOC_DOBJ_GRAPH;
		if (tplg->ops)
			route->dobj.unload = tplg->ops->dapm_route_unload;
		route->dobj.index = tplg->index;
		list_add(&route->dobj.list, &tplg->comp->dobj_list);

		ret = soc_tplg_add_route(tplg, route);
		if (ret < 0) {
			dev_err(tplg->dev, "ASoC: topology: add_route failed: %d\n", ret);
			break;
		}

		ret = snd_soc_dapm_add_routes(dapm, route, 1);
		if (ret)
			break;
	}
```

[`soc_tplg_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1016) runs the consumer's [`dapm_route_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) on the built route just before the core links the named widgets, which is how SOF records the source-to-sink connection it later programs over IPC:

```c
/* sound/soc/soc-topology.c:1016 */
static int soc_tplg_add_route(struct soc_tplg *tplg,
	struct snd_soc_dapm_route *route)
{
	if (tplg->ops && tplg->ops->dapm_route_load)
		return tplg->ops->dapm_route_load(tplg->comp, tplg->index,
			route);

	return 0;
}
```

### PCM blocks become a front-end DAI and a DAI link

The PCM element loader [`soc_tplg_pcm_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560) size-checks each [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513) and calls [`soc_tplg_pcm_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1548), which produces two objects from one block, the front-end DAI then the front-end link:

```c
/* sound/soc/soc-topology.c:1548 */
static int soc_tplg_pcm_create(struct soc_tplg *tplg,
	struct snd_soc_tplg_pcm *pcm)
{
	int ret;

	ret = soc_tplg_dai_create(tplg, pcm);
	if (ret < 0)
		return ret;

	return  soc_tplg_fe_link_create(tplg, pcm);
}
```

[`soc_tplg_dai_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1364) allocates a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), fills its playback and capture stream caps from the PCM block, runs the consumer's [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) through [`soc_tplg_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L280), stamps the dobj [`SND_SOC_DOBJ_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L43), registers the DAI with [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706), and creates its DAI binding widgets with [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359):

```c
/* sound/soc/soc-topology.c:1406 */
	/* pass control to component driver for optional further init */
	ret = soc_tplg_dai_load(tplg, dai_drv, pcm, NULL);
	if (ret < 0) {
		dev_err(tplg->dev, "ASoC: DAI loading failed\n");
		goto err;
	}

	dai_drv->dobj.index = tplg->index;
	dai_drv->dobj.type = SND_SOC_DOBJ_PCM;
	if (tplg->ops)
		dai_drv->dobj.unload = tplg->ops->dai_unload;
	list_add(&dai_drv->dobj.list, &tplg->comp->dobj_list);

	/* register the DAI to the component */
	dai = snd_soc_register_dai(tplg->comp, dai_drv, false);
	if (!dai)
		return -ENOMEM;

	/* Create the DAI widgets here */
	ret = snd_soc_dapm_new_dai_widgets(dapm, dai);
	if (ret != 0) {
		dev_err(dai->dev, "Failed to create DAI widgets %d\n", ret);
		snd_soc_unregister_dai(dai);
		return ret;
	}
```

The consumer DAI callback is [`soc_tplg_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L280), reached with the freshly allocated driver before it is registered. On x86-64 SOF this is [`sof_dai_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L1726), which allocates a [`struct snd_sof_pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L352), stores it in the driver's [`dobj.private`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), and allocates the host DMA page tables per direction:

```c
/* sound/soc/soc-topology.c:280 */
static int soc_tplg_dai_load(struct soc_tplg *tplg,
	struct snd_soc_dai_driver *dai_drv,
	struct snd_soc_tplg_pcm *pcm, struct snd_soc_dai *dai)
{
	if (tplg->ops && tplg->ops->dai_load)
		return tplg->ops->dai_load(tplg->comp, tplg->index, dai_drv,
			pcm, dai);

	return 0;
}
```

[`soc_tplg_fe_link_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1462) allocates a [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) with its CPU, codec, and platform components, names it from the PCM block, marks it a DPCM front end by setting [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), and defaults its codec and platform to the dummy component (which the consumer's [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) may overwrite), then runs that callback and registers the link runtime with [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269):

```c
/* sound/soc/soc-topology.c:1516 */
	/* enable DPCM */
	link->dynamic = 1;
	link->ignore_pmdown_time = 1;
	link->playback_only =  le32_to_cpu(pcm->playback) && !le32_to_cpu(pcm->capture);
	link->capture_only  = !le32_to_cpu(pcm->playback) &&  le32_to_cpu(pcm->capture);
	if (pcm->flag_mask)
		set_link_flags(link,
			       le32_to_cpu(pcm->flag_mask),
			       le32_to_cpu(pcm->flags));

	/* pass control to component driver for optional further init */
	ret = soc_tplg_dai_link_load(tplg, link, NULL);
	if (ret < 0) {
		dev_err(tplg->dev, "ASoC: FE link loading failed\n");
		goto err;
	}

	ret = snd_soc_add_pcm_runtimes(tplg->comp->card, link, 1);
	if (ret < 0) {
		if (ret != -EPROBE_DEFER)
			dev_err(tplg->dev, "ASoC: adding FE link failed\n");
		goto err;
	}

	list_add(&link->dobj.list, &tplg->comp->dobj_list);
```

### DAI and link blocks reconfigure existing objects

The physical-DAI and physical-link loaders do not allocate ASoC objects; the platform driver has already registered the back-end DAIs and links, and these loaders find and reconfigure them. [`soc_tplg_dai_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896) iterates each [`struct snd_soc_tplg_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L630) and calls [`soc_tplg_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1834):

```c
/* sound/soc/soc-topology.c:1896 */
static int soc_tplg_dai_elems_load(struct soc_tplg *tplg,
				   struct snd_soc_tplg_hdr *hdr)
{
	int count;
	int i;

	count = le32_to_cpu(hdr->count);

	/* config the existing BE DAIs */
	for (i = 0; i < count; i++) {
		struct snd_soc_tplg_dai *dai = (struct snd_soc_tplg_dai *)tplg->pos;
		int ret;

		if (le32_to_cpu(dai->size) != sizeof(*dai)) {
			dev_err(tplg->dev, "ASoC: invalid physical DAI size\n");
			return -EINVAL;
		}

		ret = soc_tplg_dai_config(tplg, dai);
		if (ret < 0) {
			dev_err(tplg->dev, "ASoC: failed to configure DAI\n");
			return ret;
		}

		tplg->pos += (sizeof(*dai) + le32_to_cpu(dai->priv.size));
	}

	dev_dbg(tplg->dev, "ASoC: Configure %d BE DAIs\n", count);
	return 0;
}
```

[`soc_tplg_dai_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1834) finds the registered DAI by name with [`snd_soc_find_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L800), checks the id matches, overwrites the playback and capture caps on its existing [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), applies any flag overrides, and runs the consumer's [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) with the existing DAI passed in:

```c
/* sound/soc/soc-topology.c:1846 */
	dai_component.dai_name = d->dai_name;
	dai = snd_soc_find_dai(&dai_component);
	if (!dai) {
		dev_err(tplg->dev, "ASoC: physical DAI %s not registered\n",
			d->dai_name);
		return -EINVAL;
	}

	if (le32_to_cpu(d->dai_id) != dai->id) {
		dev_err(tplg->dev, "ASoC: physical DAI %s id mismatch\n",
			d->dai_name);
		return -EINVAL;
	}

	dai_drv = dai->driver;
	if (!dai_drv)
		return -EINVAL;
```

[`soc_tplg_link_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782) is the link counterpart, iterating each [`struct snd_soc_tplg_link_config`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L541) and calling [`soc_tplg_link_config()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1721), which locates the existing back-end link with [`snd_soc_find_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L596), rewrites its hw format and flags, runs [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and then stamps the link's dobj [`SND_SOC_DOBJ_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L45) so the teardown path can run the unload op even though the link itself is owned by the machine:

```c
/* sound/soc/soc-topology.c:1770 */
	/* for unloading it in snd_soc_tplg_component_remove */
	link->dobj.index = tplg->index;
	link->dobj.type = SND_SOC_DOBJ_BACKEND_LINK;
	if (tplg->ops)
		link->dobj.unload = tplg->ops->link_unload;
	list_add(&link->dobj.list, &tplg->comp->dobj_list);
```

### The manifest block creates nothing

The manifest is delivered first of all and produces no ASoC object. [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927) size-checks the [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) against the compiled-in type and forwards it to the consumer's [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback, so the consumer sees the element totals before any creator runs:

```c
/* sound/soc/soc-topology.c:1927 */
static int soc_tplg_manifest_load(struct soc_tplg *tplg,
				  struct snd_soc_tplg_hdr *hdr)
{
	struct snd_soc_tplg_manifest *manifest;
	int ret = 0;

	manifest = (struct snd_soc_tplg_manifest *)tplg->pos;

	/* check ABI version by size, create a new manifest if abi not match */
	if (le32_to_cpu(manifest->size) != sizeof(*manifest))
		return -EINVAL;

	/* pass control to component driver for optional further init */
	if (tplg->ops && tplg->ops->manifest)
		ret = tplg->ops->manifest(tplg->comp, tplg->index, manifest);

	return ret;
}
```

The element body the consumer receives is the per-payload element counts, which let the consumer size global allocations before any object arrives:

```c
/* include/uapi/sound/asoc.h:370 */
struct snd_soc_tplg_manifest {
	__le32 size;		/* in bytes of this structure */
	__le32 control_elems;	/* number of control elements */
	__le32 widget_elems;	/* number of widget elements */
	__le32 graph_elems;	/* number of graph elements */
	__le32 pcm_elems;	/* number of PCM elements */
	__le32 dai_link_elems;	/* number of DAI link elements */
	__le32 dai_elems;	/* number of physical DAI elements */
	__le32 reserved[20];	/* reserved for new ABI element types */
	struct snd_soc_tplg_private priv;
} __attribute__((packed));
```

On x86-64 SOF the callback is [`sof_manifest()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2279), which forwards the manifest to the IPC-version parse_manifest op so the firmware ABI in the topology can be checked against the running DSP before any pipeline object is created:

```c
/* sound/soc/sof/topology.c:2279 */
static int sof_manifest(struct snd_soc_component *scomp, int index,
			struct snd_soc_tplg_manifest *man)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);

	if (tplg_ops && tplg_ops->parse_manifest)
		return tplg_ops->parse_manifest(scomp, index, man);

	return 0;
}
```

The manifest gives a count for each block kind ahead of the data, one field per type so the consumer can size its allocations before the matching loader runs:

```
    Manifest counts: one field per payload block type
    ──────────────────────────────────────────────────────────
    (delivered first; creates nothing, but tells the consumer how
     many of each block follows, before any object is built)

    ┌────────────────┬──────────────────────┬────────────────────────┐
    │ manifest count │ block type           │ loader (soc_tplg_*)    │
    ├────────────────┼──────────────────────┼────────────────────────┤
    │ control_elems  │ MIXER / ENUM / BYTES │ kcontrol_elems_load    │
    │ widget_elems   │ DAPM_WIDGET          │ dapm_widget_elems_load │
    │ graph_elems    │ DAPM_GRAPH           │ dapm_graph_elems_load  │
    │ pcm_elems      │ PCM                  │ pcm_elems_load         │
    │ dai_link_elems │ DAI_LINK / BE_LINK   │ link_elems_load        │
    │ dai_elems      │ DAI (physical)       │ dai_elems_load         │
    └────────────────┴──────────────────────┴────────────────────────┘

    soc_tplg_manifest_load ─▶ ops->manifest only (no ASoC object)
```

### The consumer ops the loaders call

Every per-block callback the element loaders reach is a field of the consumer's [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and the loader treats a NULL field as success, so a consumer fills in only the callbacks its firmware model needs. SOF's [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) wires the control, route, widget-ready, DAI, link, and manifest callbacks each loader invokes, and leaves [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) and [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) unset:

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

Each loader stamps the created object's [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) with its [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) and records the matching unload op (the [`control_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dapm_route_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`widget_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dai_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), or [`link_unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)) in the dobj's [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) field:

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

How that dobj is walked in reverse-pass order to release the objects these loaders created, and how each type's remove helper runs the recorded [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61), is the teardown side of the framework and is documented separately.

```
    Each loader invokes one snd_soc_tplg_ops callback
    ──────────────────────────────────────────────────────────
    (a NULL field is treated as success; SOF wires the rest)

    ┌──────────┬────────────────────────┬──────────────────┐
    │ block    │ ops callback (NULL ok) │ SOF handler      │
    ├──────────┼────────────────────────┼──────────────────┤
    │ control  │ control_load           │ sof_control_load │
    │ graph    │ dapm_route_load        │ sof_route_load   │
    │ widget   │ widget_ready           │ sof_widget_ready │
    │ FE DAI   │ dai_load               │ sof_dai_load     │
    │ FE link  │ link_load              │ sof_link_load    │
    │ manifest │ manifest               │ sof_manifest     │
    └──────────┴────────────────────────┴──────────────────┘

    widget_load is left unset by SOF; widget_ready gets the live
    widget. Each created object also records the matching unload
    op in its snd_soc_dobj for teardown.
```
