# ASoC topology loader

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A component driver hands a binary topology blob to [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) with a [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and the loader copies the caller's ops into a [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) parse context, then walks the file's typed blocks, each introduced by a [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), through a fixed sequence of passes ([`SOC_TPLG_PASS_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L41) to [`SOC_TPLG_PASS_LINK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L48)) so that manifest and vendor data are parsed before the controls, widgets, graph, and links that reference them.

```
    topology blob (struct firmware)              parse context
    ───────────────────────────────              ─────────────
    ───────────────────────────────────────────────────────────────────────

    fw->data ──▶ ┌───────────────────────┐   struct soc_tplg
                 │ hdr: type=MANIFEST    │    ┌─────────────────────────┐
                 │   manifest payload    │    │ fw   = firmware blob    │
                 ├───────────────────────┤   │ pos  ──▶ block payload   │
                 │ hdr: type=MIXER/ENUM  │    │ hdr_pos ──▶ block header │
                 │   ctl payload  [count]│    │ pass = 0..7             │
                 ├───────────────────────┤   │ comp = component        │
                 │ hdr: type=DAPM_WIDGET │    │ ops, io_ops, ...        │
                 │   widget payload [N]  │    └─────────────────────────┘
                 ├───────────────────────┤
                 │ hdr: type=DAPM_GRAPH  │
                 │   graph payload  [N]  │
                 ├───────────────────────┤       per-pass walk of the blob
                 │ hdr: type=PCM         │        ───────────────────────────
                 │   pcm payload    [N]  │
                 ├───────────────────────┤   for pass = MANIFEST .. LINK:
                 │ hdr: type=VENDOR_FW   │      hdr_pos = fw->data
                 │   bespoke payload     │      while not eof:
                 └───────────────────────┘       valid_header(hdr)
                                                  load_header(hdr):  ─────┐
                            soc_tplg_process_headers                      │
                                                  hdr_pos += payload_size │
                                                            + sizeof(hdr) │
                                                                          ▼
       soc_tplg_load_header: switch (hdr->type) ─▶ (loader, hdr_pass)
       ────────────────────────────────────────────────────────────────────
         MANIFEST            ─▶ soc_tplg_manifest_load        @ pass 0
         (vendor, default)   ─▶ soc_tplg_vendor_load          @ pass 1
         MIXER/ENUM/BYTES    ─▶ soc_tplg_kcontrol_elems_load   @ pass 2
         DAPM_WIDGET         ─▶ soc_tplg_dapm_widget_elems_load @ pass 3
         PCM                 ─▶ soc_tplg_pcm_elems_load        @ pass 4
         DAPM_GRAPH          ─▶ soc_tplg_dapm_graph_elems_load @ pass 5
         DAI                 ─▶ soc_tplg_dai_elems_load        @ pass 6
         DAI_LINK/BACKEND    ─▶ soc_tplg_link_elems_load       @ pass 7

       loader runs only when tplg->pass == hdr_pass, so each block is
       parsed once, in its assigned pass, though the blob is walked 8 times.
       The per-block elem loaders create the ASoC objects (sibling page);
       each object carries a snd_soc_dobj on dobj_list (sibling page).
```

## SUMMARY

The loader is the generic half of the ASoC topology framework. It does not know what a SOF IPC4 module is or how a Realtek codec wires a control; it walks a flat file of typed blocks, validates each block header, and dispatches the block to a per-type elem loader in a fixed pass. A component such as Sound Open Firmware (SOF) supplies the type-specific behavior through a [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) and through its own block creators, which are documented on the sibling pages.

[`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) validates the component chain and the [`struct firmware`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/firmware.h#L11), zeroes a [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) on its own stack, copies the caller's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), [`io_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), and [`bytes_ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) into it, and calls [`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110). That wrapper runs [`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067) and, only on success, [`soc_tplg_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L302). If any step returns an error the entry point calls [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) to unwind whatever the partial load created.

[`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067) is the pass driver. It loops [`pass`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) from [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) to [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51), resets [`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) to the start of the data at the top of every pass, and steps block by block to end of file, calling [`soc_tplg_valid_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1947) then [`soc_tplg_load_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004) on each [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), and advancing past a block by adding [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) plus the header size. End of file is the test [`soc_tplg_is_eof()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L103). After the last pass it calls [`soc_tplg_dapm_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1304) to materialize the new DAPM widgets.

[`soc_tplg_load_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004) is the dispatch point. It positions [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) just past the header, switches on [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) to select both an `elem_load` function pointer and the `hdr_pass` that loader runs in, and calls the loader only when the current pass equals that block's assigned pass. The block-type constants ([`SND_SOC_TPLG_TYPE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L102), [`SND_SOC_TPLG_TYPE_DAPM_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L106), [`SND_SOC_TPLG_TYPE_DAPM_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L105), [`SND_SOC_TPLG_TYPE_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L108), [`SND_SOC_TPLG_TYPE_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L109)) map to the elem loaders [`soc_tplg_kcontrol_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973), [`soc_tplg_dapm_widget_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258), [`soc_tplg_dapm_graph_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026), [`soc_tplg_pcm_elems_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560), and [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927). Any block type the core does not own falls through the switch default to [`soc_tplg_vendor_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L233), which hands the raw header to the component's [`vendor_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) callback. The per-block creators those loaders invoke are owned by the sibling elements page, and the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) those creators attach is owned by the sibling dobj page.

## SPECIFICATIONS

The topology file format is the ASoC topology ABI defined entirely in [`include/uapi/sound/asoc.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h); it is a Linux/ASoC software construct with no external hardware standard. A file is a flat byte stream of blocks, each block prefixed by a [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) carrying the magic, ABI version, block type, payload size, block index, and element count. The current ABI is [`SND_SOC_TPLG_ABI_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L90) (0x5), the oldest supported is [`SND_SOC_TPLG_ABI_VERSION_MIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L91) (also 0x5 in v7.0), and the file magic is [`SND_SOC_TPLG_MAGIC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L84) (0x41536F43, the little-endian bytes "CoSA"). Generic block types up to [`SND_SOC_TPLG_TYPE_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L114) are parsed by the core; vendor block types from [`SND_SOC_TPLG_TYPE_VENDOR_FW`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L117) (1000) upward are passed to the component. The blob is produced offline by the alsatplg compiler from text; on x86-64 ACPI the Intel SOF firmware package ships the binary topology that matches a given DSP firmware, and the SOF topology consumer (the IPC4 [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)) is the subject of the sibling SOF consumer page.

## LINUX KERNEL

### Loader entry and exit (soc-topology.c, soc-topology.h)

- [`'\<snd_soc_tplg_component_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122): the public entry; validate the component and firmware, build the [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) context from the caller's ops, run [`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110), and unwind on failure
- [`'\<soc_tplg_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110): the two-step wrapper that runs [`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067), then [`soc_tplg_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L302) only when the header walk returns 0
- [`'\<soc_tplg_complete\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L302): invoke the optional [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op so the component finalizes loading; treats an absent op as success
- [`'\<snd_soc_tplg_component_remove\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161): walk [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) and dispatch each [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to its type-specific remove helper (the dobj teardown detail is the sibling dobj page)

### Pass driver and header validation (soc-topology.c)

- [`'\<soc_tplg_process_headers\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067): loop [`pass`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) over every value from start to end, and within each pass walk every block header from the start of the file
- [`'\<soc_tplg_load_header\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004): switch on [`hdr->type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) to choose the elem loader and the pass it runs in, then call the loader only when the current pass matches
- [`'\<soc_tplg_valid_header\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1947): reject a header whose [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) is wrong, whose [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) runs past the blob, whose [`magic`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) is big-endian or wrong, or whose [`abi`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) is out of range
- [`'\<soc_tplg_is_eof\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L103): the loop terminator; returns true once [`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) reaches the end of the firmware buffer
- [`'\<soc_tplg_get_hdr_offset\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L112): the byte offset of the current header from the start of the blob, used in the validation error messages
- [`'\<soc_tplg_get_offset\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L117): the byte offset of the current payload cursor [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), used by the elem loaders when iterating a block
- [`'\<soc_tplg_dapm_complete\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1304): after all passes, call [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) to power up the widgets the widget pass created

### Dispatch targets (soc-topology.c)

These are the elem loaders the dispatch switch names. Their bodies (the per-block element creators they call) are owned by the sibling elements page; the loader framework only selects and gates them.

- [`'\<soc_tplg_manifest_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927): size-check the [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) and pass it to the component's [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op; runs in [`SOC_TPLG_PASS_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L41)
- [`'\<soc_tplg_vendor_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L233): hand an unrecognized block's raw [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) to the component's [`vendor_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op, returning `-EINVAL` when none is set; runs in [`SOC_TPLG_PASS_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L42)
- [`'\<soc_tplg_kcontrol_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L973): the mixer/enum/bytes loader; runs in [`SOC_TPLG_PASS_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L43) (creators on the elements page)
- [`'\<soc_tplg_dapm_widget_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1258): the DAPM widget loader; runs in [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44) (creators on the elements page)
- [`'\<soc_tplg_pcm_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1560): the PCM (FE DAI + DAI link) loader; runs in [`SOC_TPLG_PASS_PCM_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L45) (creators on the elements page)
- [`'\<soc_tplg_dapm_graph_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1026): the DAPM route loader; runs in [`SOC_TPLG_PASS_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L46) (creators on the elements page)
- [`'\<soc_tplg_dai_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1896): the BE DAI loader; runs in [`SOC_TPLG_PASS_BE_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L47) (creators on the elements page)
- [`'\<soc_tplg_link_elems_load\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1782): the physical DAI-link loader; runs in [`SOC_TPLG_PASS_LINK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L48) (creators on the elements page)

### Parse context and client ops (soc-topology.c, soc-topology.h)

- [`'\<struct soc_tplg\>':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54): the parse context; holds the [`fw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), the read cursors [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) and [`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), the current [`pass`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), the [`comp`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) being populated, the current block [`index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), and the copied [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), [`io_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), and [`bytes_ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) tables
- [`'\<struct snd_soc_tplg_ops\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108): the component's function pointer struct; the loader reads only its presence and forwards to its callbacks ([`control_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`widget_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)/[`widget_ready`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`dai_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`link_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`vendor_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108)) and the [`io_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) and [`bytes_ext_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) tables
- [`'\<struct snd_soc_dobj\>':'include/sound/soc-topology.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61): the dynamic-object header every created object carries; named here only as the thing on [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) that [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) walks (lifecycle on the sibling dobj page)

### On-disk block ABI (include/uapi/sound/asoc.h)

- [`'\<struct snd_soc_tplg_hdr\>':'include/uapi/sound/asoc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190): the block header preceding every payload, with [`magic`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), [`abi`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), and [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190)
- block-type constants: [`SND_SOC_TPLG_TYPE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L102), [`SND_SOC_TPLG_TYPE_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L103), [`SND_SOC_TPLG_TYPE_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L104), [`SND_SOC_TPLG_TYPE_DAPM_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L105), [`SND_SOC_TPLG_TYPE_DAPM_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L106), [`SND_SOC_TPLG_TYPE_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L107), [`SND_SOC_TPLG_TYPE_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L108), [`SND_SOC_TPLG_TYPE_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L109), [`SND_SOC_TPLG_TYPE_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L111), [`SND_SOC_TPLG_TYPE_DAI`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L113)
- [`SND_SOC_TPLG_MAGIC`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L84), [`SND_SOC_TPLG_ABI_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L90), [`SND_SOC_TPLG_ABI_VERSION_MIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L91): the magic and ABI bounds [`soc_tplg_valid_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1947) checks
- [`SND_SOC_TPLG_TYPE_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L114), [`SND_SOC_TPLG_TYPE_VENDOR_FW`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L117): the boundary between core-owned generic types and component-owned vendor types

### Pass-order constants (soc-topology.c)

- [`SOC_TPLG_PASS_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L41) (0), [`SOC_TPLG_PASS_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L42) (1), [`SOC_TPLG_PASS_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L43) (2), [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44) (3), [`SOC_TPLG_PASS_PCM_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L45) (4), [`SOC_TPLG_PASS_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L46) (5), [`SOC_TPLG_PASS_BE_DAI`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L47) (6), [`SOC_TPLG_PASS_LINK`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L48) (7): the fixed total order of the walk
- [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51): aliases for the first and last pass, the loop bounds in [`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067) and [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161)

### Loader callers (sof/topology.c, intel/avs/topology.c)

- [`'\<snd_sof_load_topology\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494): the SOF caller; requests the topology firmware and calls [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) with [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) (the SOF [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) is the sibling SOF consumer page)
- [`'\<avs_load_topology\>':'sound/soc/intel/avs/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/avs/topology.c#L2223): the Intel AVS caller, a second in-tree consumer that calls the same entry point with [`avs_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/avs/topology.c#L2197)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC layering of codec, platform, and machine that the topology loader populates dynamically from a file
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget and route model the widget and graph passes build
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end split the PCM and link passes instantiate
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and DAI link structure a topology PCM block stands in for

## OTHER SOURCES

- [Sound Open Firmware topology documentation](https://thesofproject.github.io/latest/architectures/firmware/sof-common/topology.html)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project: ASoC Dynamic Audio Architecture](https://www.alsa-project.org/wiki/ASoC/Dynamic_Audio_Architecture)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The loader exposes one public entry, one public teardown, and one parse context. Every interface a component implements is a field of [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and the loader treats every callback as optional, testing the pointer before each call and treating an absent op as success. The [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) context exists only for the duration of one [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) call; it is a stack variable in that function and is gone when the call returns. The objects the loaded topology leaves behind outlive the context, hung on the component's [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) and released by [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161).

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) parse context | [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) on its own stack | one load call; freed when the call returns |
| [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) | the component driver (static, e.g. [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305)) | the driver's lifetime; only borrowed by the loader |
| per-block ASoC objects | the elem loaders (sibling elements page) | on [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) until [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) |

### snd_soc_tplg_component_load

The single public entry takes the component, the optional ops, and the firmware. It validates the parameters, builds the context, runs the load, and unwinds on failure. It is reached by every in-tree topology consumer; SOF reaches it through [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) and Intel AVS through [`avs_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/avs/topology.c#L2223).

### snd_soc_tplg_component_remove

The teardown is symmetric with the load. The load walks the blob from [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) to [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51), and the remove walks [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) back down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), so links come down before the widgets and controls they referenced. The entry point calls it on any load failure; a consumer also calls it explicitly when it unloads a topology. The per-type remove helpers it dispatches to and the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) they consume are the sibling dobj page.

### struct soc_tplg

The context is the entire parse state. The loader does not store any of it on the component; the cursors, the pass number, and the copied op tables exist only while the walk runs, which is why a re-load is a fresh call with a fresh context.

## DETAILS

### The component hands a firmware blob to the loader

A topology load begins when a component driver passes itself, its [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), and the loaded firmware to [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122). The function validates the component chain (the component, its card, and the card's device must exist, and the firmware must be non-NULL), zeroes a [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) on its own stack, copies the firmware pointer, device, and component into it, and when the caller supplied ops copies the ops pointer and the two handler tables. It then runs [`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110) and, if that returns non-zero, calls [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) so a partial load does not leave half-built objects on the component:

```c
/* sound/soc/soc-topology.c:2122 */
int snd_soc_tplg_component_load(struct snd_soc_component *comp,
	const struct snd_soc_tplg_ops *ops, const struct firmware *fw)
{
	struct soc_tplg tplg;
	int ret;

	/*
	 * check if we have sane parameters:
	 * comp - needs to exist to keep and reference data while parsing
	 * comp->card - used for setting card related parameters
	 * comp->card->dev - used for resource management and prints
	 * fw - we need it, as it is the very thing we parse
	 */
	if (!comp || !comp->card || !comp->card->dev || !fw)
		return -EINVAL;

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

The [`struct soc_tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) is the entire parse state. It holds the firmware, two read cursors, the current pass number, the component being populated, the index of the block in progress, and the copied ops and handler tables. According to its comment it is the "topology context":

```c
/* sound/soc/soc-topology.c:54 */
struct soc_tplg {
	const struct firmware *fw;

	/* runtime FW parsing */
	const u8 *pos;		/* read position */
	const u8 *hdr_pos;	/* header position */
	unsigned int pass;	/* pass number */

	/* component caller */
	struct device *dev;
	struct snd_soc_component *comp;
	u32 index;	/* current block index */

	/* vendor specific kcontrol operations */
	const struct snd_soc_tplg_kcontrol_ops *io_ops;
	int io_ops_count;

	/* vendor specific bytes ext handlers, for TLV bytes controls */
	const struct snd_soc_tplg_bytes_ext_ops *bytes_ext_ops;
	int bytes_ext_ops_count;

	/* optional fw loading callbacks to component drivers */
	const struct snd_soc_tplg_ops *ops;
};
```

[`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) points at the [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) of the block in progress and [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) points at the payload that follows it. The two helpers [`soc_tplg_get_hdr_offset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L112) and [`soc_tplg_get_offset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L117) turn either cursor into a byte offset from the start of the blob for diagnostics:

```c
/* sound/soc/soc-topology.c:103 */
static inline bool soc_tplg_is_eof(struct soc_tplg *tplg)
{
	const u8 *end = tplg->hdr_pos;

	if (end >= tplg->fw->data + tplg->fw->size)
		return true;
	return false;
}

static inline unsigned long soc_tplg_get_hdr_offset(struct soc_tplg *tplg)
{
	return (unsigned long)(tplg->hdr_pos - tplg->fw->data);
}

static inline unsigned long soc_tplg_get_offset(struct soc_tplg *tplg)
{
	return (unsigned long)(tplg->pos - tplg->fw->data);
}
```

[`soc_tplg_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2110) is a two-step wrapper. It walks the headers and, only if that succeeds, signals completion through the optional [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op:

```c
/* sound/soc/soc-topology.c:2110 */
static int soc_tplg_load(struct soc_tplg *tplg)
{
	int ret;

	ret = soc_tplg_process_headers(tplg);
	if (ret == 0)
		return soc_tplg_complete(tplg);

	return ret;
}
```

[`soc_tplg_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L302) only forwards to the component when the op is present, so a consumer that finalizes elsewhere can leave it NULL:

```c
/* sound/soc/soc-topology.c:302 */
static int soc_tplg_complete(struct soc_tplg *tplg)
{
	if (tplg->ops && tplg->ops->complete)
		return tplg->ops->complete(tplg->comp);

	return 0;
}
```

### The file is a sequence of typed blocks behind a header

The on-disk format is a flat stream of blocks, each prefixed by a [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190). The header names the block magic, the ABI version, the block [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), the [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) of the header itself, the [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) of the element array that follows, the block [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), and the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) of elements in that payload. According to its comment, "This header precedes all object and object arrays below":

```c
/* include/uapi/sound/asoc.h:190 */
struct snd_soc_tplg_hdr {
	__le32 magic;		/* magic number */
	__le32 abi;		/* ABI version */
	__le32 version;		/* optional vendor specific version details */
	__le32 type;		/* SND_SOC_TPLG_TYPE_ */
	__le32 size;		/* size of this structure */
	__le32 vendor_type;	/* optional vendor specific type info */
	__le32 payload_size;	/* data bytes, excluding this header */
	__le32 index;		/* identifier for block */
	__le32 count;		/* number of elements in block */
} __attribute__((packed));
```

The [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) field is one of the block-type constants. The generic types up to [`SND_SOC_TPLG_TYPE_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L114) are handled by the core, and the high-numbered vendor types from [`SND_SOC_TPLG_TYPE_VENDOR_FW`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L117) upward are passed to the component. The fields are little-endian on the wire, which is why every read goes through `le32_to_cpu`:

```c
/* include/uapi/sound/asoc.h:102 */
#define SND_SOC_TPLG_TYPE_MIXER		1
#define SND_SOC_TPLG_TYPE_BYTES		2
#define SND_SOC_TPLG_TYPE_ENUM		3
#define SND_SOC_TPLG_TYPE_DAPM_GRAPH	4
#define SND_SOC_TPLG_TYPE_DAPM_WIDGET	5
#define SND_SOC_TPLG_TYPE_DAI_LINK	6
#define SND_SOC_TPLG_TYPE_PCM		7
#define SND_SOC_TPLG_TYPE_MANIFEST	8
#define SND_SOC_TPLG_TYPE_CODEC_LINK	9
#define SND_SOC_TPLG_TYPE_BACKEND_LINK	10
#define SND_SOC_TPLG_TYPE_PDATA		11
#define SND_SOC_TPLG_TYPE_DAI		12
#define SND_SOC_TPLG_TYPE_MAX		SND_SOC_TPLG_TYPE_DAI
```

Each block opens with this fixed header, every field a little-endian word, the magic and abi validated, the type selecting the loader and pass, and payload_size giving the stride to the next block:

```
    struct snd_soc_tplg_hdr on the wire (packed, every field __le32)
    ─────────────────────────────────────────────────────────────────
    off  field          checked / used by

    +0   magic          == SND_SOC_TPLG_MAGIC ("CoSA"), reject big-endian
    +4   abi            in [ABI_VERSION_MIN .. ABI_VERSION]
    +8   version        vendor specific, ignored
    +12  type           SND_SOC_TPLG_TYPE_* selects loader and pass
    +16  size           == sizeof(struct snd_soc_tplg_hdr)
    +20  vendor_type    vendor specific
    +24  payload_size   bytes of element array following this header
    +28  index          block identifier
    +32  count          number of elements in the payload
    ─────────────────────────────────────────────────────────────────
    next block = hdr_pos + payload_size + sizeof(snd_soc_tplg_hdr)
```

### Every header is validated before it is loaded

[`soc_tplg_valid_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1947) runs on each block before the dispatch. It rejects a header whose [`size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) is not the expected structure size, a [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) that would run to or past the end of the blob, a big-endian or wrong [`magic`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190), an [`abi`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) outside the supported range, or a zero payload:

```c
/* sound/soc/soc-topology.c:1947 */
static int soc_tplg_valid_header(struct soc_tplg *tplg,
	struct snd_soc_tplg_hdr *hdr)
{
	if (le32_to_cpu(hdr->size) != sizeof(*hdr)) {
		dev_err(tplg->dev,
			"ASoC: invalid header size for type %d at offset 0x%lx size 0x%zx.\n",
			le32_to_cpu(hdr->type), soc_tplg_get_hdr_offset(tplg),
			tplg->fw->size);
		return -EINVAL;
	}

	if (soc_tplg_get_hdr_offset(tplg) + le32_to_cpu(hdr->payload_size) >= tplg->fw->size) {
		dev_err(tplg->dev,
			"ASoC: invalid header of type %d at offset %ld payload_size %d\n",
			le32_to_cpu(hdr->type), soc_tplg_get_hdr_offset(tplg),
			hdr->payload_size);
		return -EINVAL;
	}

	/* big endian firmware objects not supported atm */
	if (le32_to_cpu(hdr->magic) == SOC_TPLG_MAGIC_BIG_ENDIAN) {
		...
		return -EINVAL;
	}

	if (le32_to_cpu(hdr->magic) != SND_SOC_TPLG_MAGIC) {
		...
		return -EINVAL;
	}

	/* Support ABI from version 4 */
	if (le32_to_cpu(hdr->abi) > SND_SOC_TPLG_ABI_VERSION ||
	    le32_to_cpu(hdr->abi) < SND_SOC_TPLG_ABI_VERSION_MIN) {
		...
		return -EINVAL;
	}

	if (hdr->payload_size == 0) {
		dev_err(tplg->dev, "ASoC: header has 0 size at offset 0x%lx.\n",
			soc_tplg_get_hdr_offset(tplg));
		return -EINVAL;
	}

	return 0;
}
```

The payload-size bound is what stops a malformed file from reading past the blob in a later elem loader. Because [`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) advances by [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) plus the header size, an attacker-controlled oversized payload would otherwise carry the cursor out of bounds.

```
    soc_tplg_valid_header: each test that rejects with -EINVAL
    ───────────────────────────────────────────────────────────────
    field         accept when                            else
    ────────────  ─────────────────────────────────────  ──────────
    size          == sizeof(struct snd_soc_tplg_hdr)      -EINVAL
    payload_size  hdr_offset + payload_size < fw->size    -EINVAL
    magic         != SOC_TPLG_MAGIC_BIG_ENDIAN            -EINVAL
    magic         == SND_SOC_TPLG_MAGIC                   -EINVAL
    abi           ABI_VERSION_MIN <= abi <= ABI_VERSION   -EINVAL
    payload_size  != 0                                    -EINVAL
    ───────────────────────────────────────────────────────────────
    all pass ─▶ 0, then soc_tplg_load_header dispatches the block
```

### Headers are walked once per pass

[`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067) reads the whole file once for each pass from [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50) to [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51). At the top of each pass it resets [`hdr_pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) to the start of the data and steps forward block by block while [`soc_tplg_is_eof()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L103) is false, validating then loading each header, and advances to the next block by adding [`payload_size`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) plus the header size. After the final pass it calls [`soc_tplg_dapm_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1304):

```c
/* sound/soc/soc-topology.c:2067 */
static int soc_tplg_process_headers(struct soc_tplg *tplg)
{
	int ret;

	/* process the header types from start to end */
	for (tplg->pass = SOC_TPLG_PASS_START; tplg->pass <= SOC_TPLG_PASS_END; tplg->pass++) {
		struct snd_soc_tplg_hdr *hdr;

		tplg->hdr_pos = tplg->fw->data;
		hdr = (struct snd_soc_tplg_hdr *)tplg->hdr_pos;

		while (!soc_tplg_is_eof(tplg)) {

			/* make sure header is valid before loading */
			ret = soc_tplg_valid_header(tplg, hdr);
			if (ret < 0)
				return ret;

			/* load the header object */
			ret = soc_tplg_load_header(tplg, hdr);
			if (ret < 0) {
				if (ret != -EPROBE_DEFER) {
					dev_err(tplg->dev,
						"ASoC: topology: could not load header: %d\n",
						ret);
				}
				return ret;
			}

			/* goto next header */
			tplg->hdr_pos += le32_to_cpu(hdr->payload_size) +
				sizeof(struct snd_soc_tplg_hdr);
			hdr = (struct snd_soc_tplg_hdr *)tplg->hdr_pos;
		}

	}

	/* signal DAPM we are complete */
	ret = soc_tplg_dapm_complete(tplg);

	return ret;
}
```

An error from [`soc_tplg_load_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004) aborts the whole walk, and `-EPROBE_DEFER` is passed up quietly rather than logged, so a consumer whose dependency is not ready can be retried by the driver core without a spurious error in the log.

The pass numbers are a fixed total order. The manifest is seen first and the physical links last, so controls and widgets exist before the graph that references them by name and before the PCM links that bind to them:

```c
/* sound/soc/soc-topology.c:41 */
#define SOC_TPLG_PASS_MANIFEST		0
#define SOC_TPLG_PASS_VENDOR		1
#define SOC_TPLG_PASS_CONTROL		2
#define SOC_TPLG_PASS_WIDGET		3
#define SOC_TPLG_PASS_PCM_DAI		4
#define SOC_TPLG_PASS_GRAPH		5
#define SOC_TPLG_PASS_BE_DAI		6
#define SOC_TPLG_PASS_LINK		7

#define SOC_TPLG_PASS_START	SOC_TPLG_PASS_MANIFEST
#define SOC_TPLG_PASS_END	SOC_TPLG_PASS_LINK
```

The ordering is the reason the loader walks the file eight times instead of once. A graph route names a source and a sink widget by string, so all widgets have to be created in [`SOC_TPLG_PASS_WIDGET`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L44) (pass 3) before the graph is built in [`SOC_TPLG_PASS_GRAPH`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L46) (pass 5), and a widget's embedded kcontrols refer to controls created in [`SOC_TPLG_PASS_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L43) (pass 2). Putting each block kind in its own pass lets the file itself be in any order while the dependencies are still satisfied. The teardown in [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) runs the same order in reverse, from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), so links and graph come down before the widgets and controls underneath them.

```
    Pass order (load 0 ▶ 7) and the dependency each later pass needs
    ─────────────────────────────────────────────────────────────────
    load ▼                                                  teardown ▲
    0  MANIFEST   sizes global allocations
    1  VENDOR     bespoke vendor blocks
    2  CONTROL    creates kcontrols
    3  WIDGET     creates widgets; their kcontrols need pass 2
    4  PCM_DAI    FE DAI + dai_link
    5  GRAPH      routes name source/sink widgets, need pass 3
    6  BE_DAI     BE DAI
    7  LINK       physical dai_link binds widgets, need pass 3
    ─────────────────────────────────────────────────────────────────
    remove walks 7 ▶ 0: links and graph fall before widgets/controls
```

### A block type selects its loader and its pass

[`soc_tplg_load_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004) is the dispatch point. It positions [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) just past the header, records the block [`index`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54), switches on the block type to choose both an `elem_load` function pointer and the `hdr_pass` that loader runs in, and calls the loader only when the current pass matches the chosen one. An unknown type falls through to the vendor loader:

```c
/* sound/soc/soc-topology.c:2004 */
static int soc_tplg_load_header(struct soc_tplg *tplg,
	struct snd_soc_tplg_hdr *hdr)
{
	int (*elem_load)(struct soc_tplg *tplg,
			 struct snd_soc_tplg_hdr *hdr);
	unsigned int hdr_pass;

	tplg->pos = tplg->hdr_pos + sizeof(struct snd_soc_tplg_hdr);

	tplg->index = le32_to_cpu(hdr->index);

	switch (le32_to_cpu(hdr->type)) {
	case SND_SOC_TPLG_TYPE_MIXER:
	case SND_SOC_TPLG_TYPE_ENUM:
	case SND_SOC_TPLG_TYPE_BYTES:
		hdr_pass = SOC_TPLG_PASS_CONTROL;
		elem_load = soc_tplg_kcontrol_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_DAPM_GRAPH:
		hdr_pass = SOC_TPLG_PASS_GRAPH;
		elem_load = soc_tplg_dapm_graph_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_DAPM_WIDGET:
		hdr_pass = SOC_TPLG_PASS_WIDGET;
		elem_load = soc_tplg_dapm_widget_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_PCM:
		hdr_pass = SOC_TPLG_PASS_PCM_DAI;
		elem_load = soc_tplg_pcm_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_DAI:
		hdr_pass = SOC_TPLG_PASS_BE_DAI;
		elem_load = soc_tplg_dai_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_DAI_LINK:
	case SND_SOC_TPLG_TYPE_BACKEND_LINK:
		/* physical link configurations */
		hdr_pass = SOC_TPLG_PASS_LINK;
		elem_load = soc_tplg_link_elems_load;
		break;
	case SND_SOC_TPLG_TYPE_MANIFEST:
		hdr_pass = SOC_TPLG_PASS_MANIFEST;
		elem_load = soc_tplg_manifest_load;
		break;
	default:
		/* bespoke vendor data object */
		hdr_pass = SOC_TPLG_PASS_VENDOR;
		elem_load = soc_tplg_vendor_load;
		break;
	}

	if (tplg->pass == hdr_pass) {
		dev_dbg(tplg->dev,
			"ASoC: Got 0x%x bytes of type %d version %d vendor %d at pass %d\n",
			hdr->payload_size, hdr->type, hdr->version,
			hdr->vendor_type, tplg->pass);
		return elem_load(tplg, hdr);
	}

	return 0;
}
```

Because the loader is chosen but skipped when the pass does not match, each block is parsed exactly once, in its assigned pass, even though the file is walked [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) plus one times. The control types [`SND_SOC_TPLG_TYPE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L102), [`SND_SOC_TPLG_TYPE_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L104), and [`SND_SOC_TPLG_TYPE_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L103) share one loader and one pass; [`SND_SOC_TPLG_TYPE_DAI_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L107) and [`SND_SOC_TPLG_TYPE_BACKEND_LINK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L111) likewise. The bodies of these loaders, where the actual ASoC objects are built, are the subject of the sibling elements page; this page is responsible only for the framework that picks and gates them.

### The manifest and vendor loaders forward to the component

Two of the dispatch targets do almost nothing in the core and exist to hand control to the component. [`soc_tplg_manifest_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1927) runs first of all, in [`SOC_TPLG_PASS_MANIFEST`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L41). It points a [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) at the payload, checks its size against the ABI, and forwards it to the optional [`manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op so the component can size global allocations from the element counts before any object arrives:

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

[`soc_tplg_vendor_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L233) is the default case of the dispatch switch, reached for any block type the core does not own. It hands the raw [`struct snd_soc_tplg_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L190) to the component's [`vendor_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) op with [`pos`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L54) pointing at the payload, and fails the whole load with `-EINVAL` when no such op is set, since the core cannot interpret the bytes itself:

```c
/* sound/soc/soc-topology.c:233 */
static int soc_tplg_vendor_load(struct soc_tplg *tplg,
				struct snd_soc_tplg_hdr *hdr)
{
	int ret = 0;

	if (tplg->ops && tplg->ops->vendor_load)
		ret = tplg->ops->vendor_load(tplg->comp, tplg->index, hdr);
	else {
		dev_err(tplg->dev, "ASoC: no vendor load callback for ID %d\n",
			hdr->vendor_type);
		return -EINVAL;
	}

	if (ret < 0)
		dev_err(tplg->dev,
			"ASoC: vendor load failed at hdr offset %ld/0x%lx for type %d:%d\n",
			soc_tplg_get_hdr_offset(tplg),
			soc_tplg_get_hdr_offset(tplg),
			hdr->type, hdr->vendor_type);
	return ret;
}
```

This is the path by which SOF receives its IPC component descriptions; the SOF [`vendor_load`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) handler is documented on the sibling SOF consumer page.

### After all passes, DAPM is materialized

The widget pass adds widget templates but does not power the DAPM graph. [`soc_tplg_dapm_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L1304) runs once at the end of [`soc_tplg_process_headers()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2067), after every pass, and calls [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) to bring the newly created widgets into the running power graph. It returns success early if the parent card is not yet instantiated, deferring the binding:

```c
/* sound/soc/soc-topology.c:1304 */
static int soc_tplg_dapm_complete(struct soc_tplg *tplg)
{
	struct snd_soc_card *card = tplg->comp->card;
	int ret;

	/* Card might not have been registered at this point.
	 * If so, just return success.
	*/
	if (!snd_soc_card_is_instantiated(card)) {
		dev_warn(tplg->dev, "ASoC: Parent card not yet available, widget card binding deferred\n");
		return 0;
	}

	ret = snd_soc_dapm_new_widgets(card);
	if (ret < 0)
		dev_err(tplg->dev, "ASoC: failed to create new widgets %d\n", ret);

	return ret;
}
```

### Teardown walks the dobj list in reverse pass order

When a load fails, or when a consumer unloads a topology, [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) walks the component's [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232) once per pass from [`SOC_TPLG_PASS_END`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L51) down to [`SOC_TPLG_PASS_START`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L50), switching on each [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) to call the matching per-type remove helper:

```c
/* sound/soc/soc-topology.c:2161 */
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

Each per-type remove helper acts only when the current `pass` is the one its object kind unloads in, mirroring the gate in [`soc_tplg_load_header()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2004), so the reverse pass order tears down links and graph before widgets and controls. What each helper does to its object, and how the [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) carries the [`unload`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) callback it invokes, is the subject of the sibling dobj page.

```
    snd_soc_tplg_component_remove: switch (dobj->type) ─▶ helper
    ─────────────────────────────────────────────────────────────
    dobj->type                          remove helper
    ──────────────────────────────────  ─────────────────────────
    DOBJ_BYTES / DOBJ_ENUM / DOBJ_MIXER soc_tplg_remove_kcontrol
    DOBJ_GRAPH                          soc_tplg_remove_route
    DOBJ_WIDGET                         soc_tplg_remove_widget
    DOBJ_PCM                            soc_tplg_remove_dai
    DOBJ_DAI_LINK                       soc_tplg_remove_link
    DOBJ_BACKEND_LINK                   remove_backend_link
    ─────────────────────────────────────────────────────────────
    each helper acts only on its own pass (END ▶ START order)
```

### Worked example: SOF requests and loads its topology on x86-64 ACPI

On an x86-64 ACPI machine the SOF driver loads its topology from [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494). For each topology file it requests the firmware blob, then calls the generic loader with the SOF ops, releasing the firmware afterward:

```c
/* sound/soc/sof/topology.c:2559 */
		ret = request_firmware(&fw, tplg_files[i], scomp->dev);
		if (ret < 0) {
			/*
			 * snd_soc_tplg_component_remove(scomp) will be called
			 * if snd_soc_tplg_component_load(scomp) failed and all
			 * objects in the scomp will be removed. No need to call
			 * snd_soc_tplg_component_remove(scomp) here.
			 */
			dev_err(scomp->dev, "tplg request firmware %s failed err: %d\n",
				tplg_files[i], ret);
			goto out;
		}

		if (sdev->dspless_mode_selected)
			ret = snd_soc_tplg_component_load(scomp, &sof_dspless_tplg_ops, fw);
		else
			ret = snd_soc_tplg_component_load(scomp, &sof_tplg_ops, fw);

		release_firmware(fw);
```

The [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305) passed in is a [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108), the function pointer struct whose callbacks the loader forwards to during the walk; its contents are the sibling SOF consumer page. The comment quoted above records that on a firmware-request failure the consumer relies on the loader's own unwind, because [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) calls [`snd_soc_tplg_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2161) on any load error. Intel AVS uses the same entry point from [`avs_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/avs/topology.c#L2223) with its own [`avs_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/avs/topology.c#L2197), which is the second in-tree topology consumer on x86-64 ACPI hardware.

### Topology firmware blob mapped to ASoC objects

The on-disk blob carries a [`struct snd_soc_tplg_manifest`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L370) and typed block sections (a [`struct snd_soc_tplg_ctl_hdr`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L286) for mixer/bytes/enum controls, a [`struct snd_soc_tplg_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L480), a [`struct snd_soc_tplg_dapm_graph_elem`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L458), and a [`struct snd_soc_tplg_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asoc.h#L513)) that load into ASoC objects on the [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), each object holding a [`struct snd_soc_dobj`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L61) on the component's [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232).

```
    topology firmware file (on disk)            ASoC objects (on the card)
    ┌────────────────────────────────┐         ┌──────────────────────────┐
    │ hdr ▶ MANIFEST                 │         │ snd_soc_component        │
    │   snd_soc_tplg_manifest        │  ─────▶ │   dobj_list ─┐           │
    ├────────────────────────────────┤  load   └──────────────┼───────────┘
    │ hdr ▶ MIXER / BYTES / ENUM     │                        │
    │   snd_soc_tplg_ctl_hdr   [N]   │  ─────▶  kcontrols  ◀──┤
    ├────────────────────────────────┤                        │
    │ hdr ▶ DAPM_WIDGET              │                        │
    │   snd_soc_tplg_dapm_widget [N] │  ─────▶  DAPM widgets ◀┤
    ├────────────────────────────────┤                        │
    │ hdr ▶ DAPM_GRAPH               │                        │
    │   ..._dapm_graph_elem      [N] │  ─────▶  DAPM routes  ◀┤
    ├────────────────────────────────┤                        │
    │ hdr ▶ PCM                      │                        │
    │   snd_soc_tplg_pcm         [N] │  ─────▶  dai_drv +    ◀┤
    │                                │          dai_link      │
    ├────────────────────────────────┤                        │
    │ hdr ▶ VENDOR_FW (bespoke)      │  ─────▶  ops->vendor_load (component)
    └────────────────────────────────┘
                                              each object holds a snd_soc_dobj
                                              { type, unload } on dobj_list
```
