# Dynamic PCM front ends and back ends (snd_soc_dpcm)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Dynamic PCM (DPCM) splits one application-facing PCM from the DAI links it drives, so a DSP can route a single host stream to a back end chosen at runtime from the DAPM graph. A DAI link marked [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795) is a front end (FE) that presents a [`pcmC%dD%dp`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c) node to userspace, and a link marked [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) is a back end (BE) that carries a physical DAI (an SSP port, a SoundWire link) with no node of its own. When the FE opens, [`dpcm_path_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484) walks the DAPM graph to find which BEs the current mixer settings connect, and [`dpcm_be_connect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1299) links each one to the FE with a [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) node. From then on every FE operation propagates to the connected BEs through the `dpcm_be_dai_*` family, which reuses the ordinary [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854), [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070), and [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) bodies on each BE substream. On an x86-64 ACPI system the `sof_sdw` machine driver builds the FE links the DSP host PCMs use and the BE links the SoundWire codec DAIs sit on, and Sound Open Firmware is the platform component on both.

```
    Dynamic PCM: front ends, dpcm link nodes, and back ends
    ────────────────────────────────────────────────────────

    struct snd_soc_pcm_runtime (FE0, dynamic)   struct snd_soc_pcm_runtime (FE1)
    ┌────────────────────────────────┐          ┌────────────────────────────┐
    │ dpcm[PLAYBACK]                 │          │ dpcm[PLAYBACK]             │
    │   be_clients ──┐               │          │   be_clients ──┐          │
    └────────────────┼───────────────┘          └────────────────┼──────────┘
                     │                                            │
                     ▼ struct snd_soc_dpcm                        ▼
              ┌─────────────┐                              ┌─────────────┐
              │ fe = FE0    │                              │ fe = FE1    │
              │ be = BE     │                              │ be = BE     │
              │ list_be ────┼──────┐          ┌────────────┼─ list_be    │
              └─────────────┘      │          │            └─────────────┘
                                   ▼          ▼
                  struct snd_soc_pcm_runtime (BE, no_pcm)
                  ┌──────────────────────────────────────┐
                  │ dpcm[PLAYBACK]                       │
                  │   fe_clients ─▶ FE0, FE1            │
                  │   users        (open refcount)      │
                  │   be_start     (start refcount)     │
                  │   state = SND_SOC_DPCM_STATE_*       │
                  └──────────────────────────────────────┘
                         physical DAI: SSP / SoundWire

    One BE shared by two FEs: users counts openers, be_start counts
    starters, so the BE opens on the first FE and stops on the last.
```

## SUMMARY

A DPCM front end is an ordinary [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) whose link sets [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795), and [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) gives it the `dpcm_fe_dai_*` operation set instead of the ordinary handlers. Each FE carries a [`struct snd_soc_dpcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) per direction in its `dpcm[]` array, holding the [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) list of connected BEs, the FE [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), and the [`runtime_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) flag that serializes route changes against PCM operations. A BE carries the same structure with a [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) list, a [`users`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) open refcount, and a [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) start refcount so a BE shared by several FEs opens once and starts once. Each FE-to-BE pair is a [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) node threaded onto both the FE [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and the BE [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) lists.

[`dpcm_fe_dai_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760) resolves the route with [`dpcm_path_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484), which calls [`snd_soc_dapm_dai_get_connected_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1596) to honor the current mixer and mux settings, then connects the matching BEs with [`dpcm_add_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1558) and opens them through [`dpcm_fe_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1946). [`dpcm_fe_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151) and the FE trigger propagate to the BEs first or last in the order the link's [`enum snd_soc_dpcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58) selects, and each BE advances through the [`enum snd_soc_dpcm_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) values from [`SND_SOC_DPCM_STATE_NEW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) through open, hw_params, prepare, start, and back. [`dpcm_be_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) gates each BE command on its current state and the [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) refcount, so a shared BE only sees a hardware start on the first FE that starts it and a hardware stop on the last. [`dpcm_be_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1378) frees the [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) nodes whose link state went to [`SND_SOC_DPCM_LINK_STATE_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30) when the FE closes or the route changes.

## SPECIFICATIONS

Dynamic PCM is a Linux kernel software construct and has no standalone hardware specification. The FE and BE operations it sequences are the ALSA PCM operations, and the routing it follows is the ASoC DAPM graph.

## LINUX KERNEL

### DPCM types and state enums (soc-dpcm.h)

- [`'\<struct snd_soc_dpcm\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68): one FE-to-BE link node, holding [`fe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68), [`be`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68), the link [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68), and the [`list_be`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68)/[`list_fe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) nodes
- [`'\<struct snd_soc_dpcm_runtime\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88): the per-direction DPCM state on a runtime, holding [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), [`users`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), [`runtime_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), and [`be_pause`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88)
- [`'\<enum snd_soc_dpcm_state\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38): the per-link PCM state, from [`SND_SOC_DPCM_STATE_NEW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) to [`SND_SOC_DPCM_STATE_CLOSE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38)
- [`'\<enum snd_soc_dpcm_link_state\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30): [`SND_SOC_DPCM_LINK_STATE_NEW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30) and [`SND_SOC_DPCM_LINK_STATE_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30), the connect/disconnect marker on a [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68)
- [`'\<enum snd_soc_dpcm_trigger\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58): [`SND_SOC_DPCM_TRIGGER_PRE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58) and [`SND_SOC_DPCM_TRIGGER_POST`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58), whether the FE triggers before or after its BEs
- [`'\<enum snd_soc_dpcm_update\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L21): [`SND_SOC_DPCM_UPDATE_NO`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L21), [`SND_SOC_DPCM_UPDATE_BE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L21), [`SND_SOC_DPCM_UPDATE_FE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L21), recording who drives a route change
- [`'\<for_each_dpcm_be\>':'include/sound/soc-dpcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L109): iterate the BE link nodes of one FE direction

### Route resolution and connection (soc-pcm.c, soc-dapm.c)

- [`'\<dpcm_path_get\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484): walk the DAPM graph from the FE CPU DAI to list the connected widgets
- [`'\<snd_soc_dapm_dai_get_connected_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1596): the DAPM walk that honors current mixer and mux settings
- [`'\<dpcm_add_paths\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1558): turn the connected DAI widgets into FE-to-BE connections
- [`'\<dpcm_be_connect\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1299): allocate a [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) and add it to both lists
- [`'\<dpcm_be_disconnect\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1378): free the link nodes marked [`SND_SOC_DPCM_LINK_STATE_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30), reparenting any BE still in use
- [`'\<snd_soc_dpcm_can_be_update\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L48): gate a BE operation on whether the current update is for this FE or BE

### Front-end handlers (soc-pcm.c)

- [`'\<dpcm_fe_dai_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760): resolve the path, connect the BEs, and start the FE and BEs
- [`'\<dpcm_fe_dai_startup\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1946): start the BEs, start the FE, and derive the FE hardware from the BE capabilities
- [`'\<dpcm_fe_dai_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151): propagate hw_params to the BEs, then apply it to the FE
- [`'\<dpcm_fe_dai_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2450): defer a trigger that races a route update, otherwise run [`dpcm_fe_dai_do_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2386)
- [`'\<dpcm_fe_dai_do_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2386): order the FE and BE triggers by the link's PRE or POST setting and advance the FE state

### Back-end fan-out (soc-pcm.c)

- [`'\<dpcm_be_dai_startup\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1679): open each connected BE once, counting [`users`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and reusing [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854)
- [`'\<dpcm_be_dai_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073): apply hw_params to each connected BE through [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070)
- [`'\<dpcm_be_dai_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184): trigger each connected BE through [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198), gated by state and the [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) refcount

### Link kind and operation install (soc.h, soc-pcm.c)

- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the per-link runtime carrying the `dpcm[]` array of [`struct snd_soc_dpcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88)
- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): install the `dpcm_fe_dai_*` ops on a [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795) link and no application ops on a [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) link

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): the Dynamic PCM design, the FE and BE link kinds, and the runtime routing model
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget graph [`dpcm_path_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484) walks to find the connected BEs
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the component, DAI, and machine model the FE and BE links sit in

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A DPCM front end installs its own operation set, and each FE operation has a matching BE fan-out function. The FE op runs the FE-specific work and the BE op walks [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) applying the ordinary single-link body to each connected BE substream.

| FE operation | FE handler | BE fan-out | BE body reused |
|--------------|------------|------------|----------------|
| `open()` | [`dpcm_fe_dai_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760) | [`dpcm_be_dai_startup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1679) | [`__soc_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) |
| `hw_params` | [`dpcm_fe_dai_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151) | [`dpcm_be_dai_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073) | [`__soc_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) |
| `trigger` | [`dpcm_fe_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2450) | [`dpcm_be_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) | [`soc_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) |

The BE per-link [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) advances through [`enum snd_soc_dpcm_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) as these operations run.

| State | Set by | Meaning |
|-------|--------|---------|
| [`SND_SOC_DPCM_STATE_NEW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | [`dpcm_be_connect`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1299) | link created, BE not yet opened |
| [`SND_SOC_DPCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | [`dpcm_be_dai_startup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1679) | BE substream opened |
| [`SND_SOC_DPCM_STATE_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | [`dpcm_be_dai_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073) | parameters applied to the BE |
| [`SND_SOC_DPCM_STATE_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | [`dpcm_be_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) | BE running |
| [`SND_SOC_DPCM_STATE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) / [`SND_SOC_DPCM_STATE_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | [`dpcm_be_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) | BE paused or stopped |
| [`SND_SOC_DPCM_STATE_CLOSE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38) | BE shutdown | BE closed, link eligible to free |

## DETAILS

### The two runtime structures

A FE and a BE are both an ordinary [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143); what makes them DPCM is the per-direction [`struct snd_soc_dpcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) in the runtime's `dpcm[]` array. The FE uses [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) to list its BEs and the BE uses [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) to list its FEs, and the refcounts and state live here:

```c
/* include/sound/soc-dpcm.h:88 */
struct snd_soc_dpcm_runtime {
	struct list_head be_clients;
	struct list_head fe_clients;

	int users;
	struct snd_pcm_hw_params hw_params;

	/* state and update */
	enum snd_soc_dpcm_update runtime_update;
	enum snd_soc_dpcm_state state;

	int trigger_pending; /* trigger cmd + 1 if pending, 0 if not */

	int be_start; /* refcount protected by BE stream pcm lock */
	int be_pause; /* refcount protected by BE stream pcm lock */
	bool fe_pause; /* used to track STOP after PAUSE */
};
```

Each FE-to-BE connection is a separate [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) node carrying back pointers to both runtimes and two list nodes, so the one allocation appears on the FE's [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) list through [`list_be`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) and on the BE's [`fe_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) list through [`list_fe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68):

```c
/* include/sound/soc-dpcm.h:68 */
struct snd_soc_dpcm {
	/* FE and BE DAIs*/
	struct snd_soc_pcm_runtime *be;
	struct snd_soc_pcm_runtime *fe;

	/* link state */
	enum snd_soc_dpcm_link_state state;

	/* list of BE and FE for this DPCM link */
	struct list_head list_be;
	struct list_head list_fe;
	...
};
```

The node's list_be and list_fe members thread the one allocation onto the FE be_clients list and the BE fe_clients list, so each side reaches it from its own end:

```
    One snd_soc_dpcm node is an element of two lists at once
    ───────────────────────────────────────────────────────

    FE snd_soc_dpcm_runtime[stream]      BE snd_soc_dpcm_runtime[stream]
    ┌────────────────────────────┐       ┌────────────────────────────┐
    │ be_clients (list head)  ─┐ │       │ fe_clients (list head)  ─┐ │
    └──────────────────────────┼─┘       └──────────────────────────┼─┘
                               │                                    │
                               └─────────────┐      ┌───────────────┘
                                             ▼      ▼
                                  ┌─────────────────────────────┐
                                  │ struct snd_soc_dpcm         │
                                  │   fe      ─▶ FE runtime     │
                                  │   be      ─▶ BE runtime     │
                                  │   state (LINK_NEW / FREE)   │
                                  │   list_be ◀ on FE be_clients│
                                  │   list_fe ◀ on BE fe_clients│
                                  └─────────────────────────────┘

    dpcm_be_connect():  list_add(&dpcm->list_be, &fe->...be_clients)
                        list_add(&dpcm->list_fe, &be->...fe_clients)
    One allocation, reached from the FE side and the BE side at once.
```

### Connecting a front end to its back ends

When the FE opens, [`dpcm_fe_dai_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760) resolves which BEs the current routing connects, refuses to start if there are none, and then starts the FE and its BEs. It takes the card [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001) once for the whole tree:

```c
/* sound/soc/soc-pcm.c:2760 */
static int dpcm_fe_dai_open(struct snd_pcm_substream *fe_substream)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(fe_substream);
	struct snd_soc_dapm_widget_list *list;
	int ret;
	int stream = fe_substream->stream;

	snd_soc_dpcm_mutex_lock(fe);

	ret = dpcm_path_get(fe, stream, &list);
	if (ret < 0)
		goto open_end;

	/* calculate valid and active FE <-> BE dpcms */
	dpcm_add_paths(fe, stream, &list);

	/* There is no point starting up this FE if there are no BEs. */
	if (list_empty(&fe->dpcm[stream].be_clients)) {
		...
		ret = -EINVAL;
		goto put_path;
	}

	ret = dpcm_fe_dai_startup(fe_substream);
	if (ret < 0)
		dpcm_fe_dai_cleanup(fe_substream);

	dpcm_clear_pending_state(fe, stream);
put_path:
	dpcm_path_put(&list);
open_end:
	snd_soc_dpcm_mutex_unlock(fe);
	return ret;
}
```

[`dpcm_path_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484) asks DAPM for the widgets reachable from the FE CPU DAI, stopping the walk at a BE DAI widget unless the card chains components. The walk honors the live mixer and mux state, so a userspace route change selects which BEs a later open connects:

```c
/* sound/soc/soc-pcm.c:1484 */
int dpcm_path_get(struct snd_soc_pcm_runtime *fe,
	int stream, struct snd_soc_dapm_widget_list **list)
{
	struct snd_soc_dai *cpu_dai = snd_soc_rtd_to_cpu(fe, 0);
	int paths;
	...
	/* get number of valid DAI paths and their widgets */
	paths = snd_soc_dapm_dai_get_connected_widgets(cpu_dai, stream, list,
			fe->card->component_chaining ?
				NULL : dpcm_end_walk_at_be);
	...
	return paths;
}
```

[`dpcm_add_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1558) turns the connected DAI widgets into FE-to-BE links. For each [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h) or [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h) widget in the right direction it finds the owning BE runtime and calls [`dpcm_be_connect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1299):

```c
/* sound/soc/soc-pcm.c:1558 */
	/* Create any new FE <--> BE connections */
	for_each_dapm_widgets(list, i, widget) {

		switch (widget->id) {
		case snd_soc_dapm_dai_in:
			if (stream != SNDRV_PCM_STREAM_PLAYBACK)
				continue;
			break;
		case snd_soc_dapm_dai_out:
			if (stream != SNDRV_PCM_STREAM_CAPTURE)
				continue;
			break;
		default:
			continue;
		}

		/* is there a valid BE rtd for this widget */
		be = dpcm_get_be(card, widget, stream);
		...
		/* newly connected FE and BE */
		err = dpcm_be_connect(fe, be, stream);
		...
	}
```

[`dpcm_be_connect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1299) skips a pair already connected, allocates the link node, sets it to [`SND_SOC_DPCM_LINK_STATE_NEW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30), and threads it onto both lists under the FE stream lock:

```c
/* sound/soc/soc-pcm.c:1299 */
	/* only add new dpcms */
	for_each_dpcm_be(fe, stream, dpcm)
		if (dpcm->be == be)
			return 0;
	...
	dpcm = kzalloc_obj(struct snd_soc_dpcm);
	if (!dpcm)
		return -ENOMEM;

	dpcm->be = be;
	dpcm->fe = fe;
	dpcm->state = SND_SOC_DPCM_LINK_STATE_NEW;
	snd_pcm_stream_lock_irq(fe_substream);
	list_add(&dpcm->list_be, &fe->dpcm[stream].be_clients);
	list_add(&dpcm->list_fe, &be->dpcm[stream].fe_clients);
	snd_pcm_stream_unlock_irq(fe_substream);
```

### Starting the back ends once

[`dpcm_fe_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1946) marks the direction as a FE-driven update, opens the BEs, then opens the FE, and derives the FE hardware capabilities from the union of the BEs:

```c
/* sound/soc/soc-pcm.c:1946 */
static int dpcm_fe_dai_startup(struct snd_pcm_substream *fe_substream)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(fe_substream);
	int stream = fe_substream->stream, ret = 0;

	dpcm_set_fe_update_state(fe, stream, SND_SOC_DPCM_UPDATE_FE);

	ret = dpcm_be_dai_startup(fe, stream);
	if (ret < 0)
		goto be_err;
	...
	/* start the DAI frontend */
	ret = __soc_pcm_open(fe, fe_substream);
	if (ret < 0)
		goto unwind;

	fe->dpcm[stream].state = SND_SOC_DPCM_STATE_OPEN;

	dpcm_runtime_setup_fe(fe_substream);

	dpcm_runtime_setup_be_format(fe_substream);
	dpcm_runtime_setup_be_chan(fe_substream);
	dpcm_runtime_setup_be_rate(fe_substream);

	ret = dpcm_apply_symmetry(fe_substream, stream);
	...
}
```

[`dpcm_be_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1679) is where the shared-BE refcount earns its place. It walks [`be_clients`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88), and for each BE that this update applies to it increments [`users`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88); only the first user actually runs [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) and moves the BE to [`SND_SOC_DPCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38). The BE substream borrows the FE substream's runtime so the two share one ring buffer:

```c
/* sound/soc/soc-pcm.c:1679 */
		/* is this op for this BE ? */
		if (!snd_soc_dpcm_can_be_update(fe, be, stream))
			continue;
		...
		if (be->dpcm[stream].users++ != 0)
			continue;

		if ((be->dpcm[stream].state != SND_SOC_DPCM_STATE_NEW) &&
		    (be->dpcm[stream].state != SND_SOC_DPCM_STATE_CLOSE))
			continue;
		...
		be_substream->runtime = fe_substream->runtime;
		err = __soc_pcm_open(be, be_substream);
		if (err < 0) {
			be->dpcm[stream].users--;
			...
			be->dpcm[stream].state = SND_SOC_DPCM_STATE_CLOSE;
			goto unwind;
		}
		be->dpcm[stream].be_start = 0;
		be->dpcm[stream].state = SND_SOC_DPCM_STATE_OPEN;
		count++;
```

[`snd_soc_dpcm_can_be_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L48) is the gate that keeps a BE-driven route change from disturbing a BE that the change does not touch. It allows the operation when the update is FE-driven, or when it is BE-driven and this BE is the one being updated:

```c
/* sound/soc/soc-pcm.c:48 */
static int snd_soc_dpcm_can_be_update(struct snd_soc_pcm_runtime *fe,
			       struct snd_soc_pcm_runtime *be, int stream)
{
	if ((fe->dpcm[stream].runtime_update == SND_SOC_DPCM_UPDATE_FE) ||
	    ((fe->dpcm[stream].runtime_update == SND_SOC_DPCM_UPDATE_BE) &&
	     be->dpcm[stream].runtime_update))
		return 1;
	return 0;
}
```

The BE fan-out functions advance a back-end through these states in turn, each box labeled with the function that sets it:

```
    BE per-link state machine (be->dpcm[stream].state)
    ──────────────────────────────────────────────────
    (right of each box: the function that sets that state)

    ┌──────────────────┐
    │ STATE_NEW        │  set by dpcm_be_connect()
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │ STATE_OPEN       │  set by dpcm_be_dai_startup()  (first user)
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │ STATE_HW_PARAMS  │  set by dpcm_be_dai_hw_params()
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │ STATE_PREPARE    │  set on the FE prepare path
    └────────┬─────────┘
             ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ STATE_START      │ ───▶ │ STATE_PAUSED     │
    └────────┬─────────┘ ◀─── └──────────────────┘
             ▼            all three set by dpcm_be_dai_trigger(),
    ┌──────────────────┐  gated on be_start and the current state
    │ STATE_STOP       │
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │ STATE_CLOSE      │  set on BE shutdown (link eligible to free)
    └──────────────────┘
```

### hw_params flows to the back ends first

[`dpcm_fe_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2151) saves the FE parameters, applies them to every BE through [`dpcm_be_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073), and only then applies them to the FE itself, so a BE that cannot accept the parameters fails the operation before the FE is touched:

```c
/* sound/soc/soc-pcm.c:2151 */
static int dpcm_fe_dai_hw_params(struct snd_pcm_substream *substream,
				 struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(substream);
	int ret, stream = substream->stream;

	snd_soc_dpcm_mutex_lock(fe);
	dpcm_set_fe_update_state(fe, stream, SND_SOC_DPCM_UPDATE_FE);

	memcpy(&fe->dpcm[stream].hw_params, params,
			sizeof(struct snd_pcm_hw_params));
	ret = dpcm_be_dai_hw_params(fe, stream);
	if (ret < 0)
		goto out;
	...
	/* call hw_params on the frontend */
	ret = __soc_pcm_hw_params(substream, params);
	if (ret < 0)
		dpcm_be_dai_hw_free(fe, stream);
	else
		fe->dpcm[stream].state = SND_SOC_DPCM_STATE_HW_PARAMS;
out:
	dpcm_set_fe_update_state(fe, stream, SND_SOC_DPCM_UPDATE_NO);
	snd_soc_dpcm_mutex_unlock(fe);

	return soc_pcm_ret(fe, ret);
}
```

[`dpcm_be_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2073) reuses the ordinary [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) body on each BE substream and advances the BE to [`SND_SOC_DPCM_STATE_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L38):

```c
/* sound/soc/soc-pcm.c:2073 */
int dpcm_be_dai_hw_params(struct snd_soc_pcm_runtime *fe, int stream)
{
	struct snd_soc_pcm_runtime *be;
	struct snd_pcm_substream *be_substream;
	struct snd_soc_dpcm *dpcm;
	int ret;

	for_each_dpcm_be(fe, stream, dpcm) {
		struct snd_pcm_hw_params hw_params;

		be = dpcm->be;
		be_substream = snd_soc_dpcm_get_substream(be, stream);
		...
		ret = __soc_pcm_hw_params(be_substream, &hw_params);
		if (ret < 0)
			goto unwind;

		be->dpcm[stream].state = SND_SOC_DPCM_STATE_HW_PARAMS;
	}
	return 0;
	...
}
```

The front-end saves its parameters and applies them to every BE before applying them to itself, so the all-BEs-ok branch reaches the FE and the any-BE-fails branch unwinds with the FE untouched:

```
    hw_params order: all BEs first, then the FE
    ───────────────────────────────────────────

    dpcm_fe_dai_hw_params()
    ┌──────────────────────────────────────────────────────┐
    │ 1. memcpy params ─▶ fe->dpcm[stream].hw_params       │
    └────────────────────────────┬─────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────┐
    │ 2. dpcm_be_dai_hw_params(fe, stream)                 │
    │      for_each_dpcm_be: __soc_pcm_hw_params(be)       │
    │      each BE ─▶ STATE_HW_PARAMS                      │
    └────────────────────────────┬─────────────────────────┘
                   ┌─────────────┴────────────────────┐
             any BE fails                        all BEs ok
                   │                                  │
                   ▼                                  ▼
    ┌────────────────────────────┐  ┌──────────────────────────────────┐
    │ unwind: stop, FE untouched │  │ 3. __soc_pcm_hw_params(FE)       │
    └────────────────────────────┘  │      FE ─▶ STATE_HW_PARAMS       │
                                    │    (on FE error: hw_free BEs)    │
                                    └──────────────────────────────────┘
```

### Trigger orders the front end against the back ends

The FE trigger first guards against a race with a route update. If a [`runtime_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) is already in progress, [`dpcm_fe_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2450) stashes the command in [`trigger_pending`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and returns, leaving the update path to run it on exit:

```c
/* sound/soc/soc-pcm.c:2450 */
static int dpcm_fe_dai_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(substream);
	int stream = substream->stream;

	/* if FE's runtime_update is already set, we're in race;
	 * process this trigger later at exit
	 */
	if (fe->dpcm[stream].runtime_update != SND_SOC_DPCM_UPDATE_NO) {
		fe->dpcm[stream].trigger_pending = cmd + 1;
		return 0; /* delayed, assuming it's successful */
	}

	/* we're alone, let's trigger */
	return dpcm_fe_dai_do_trigger(substream, cmd);
}
```

[`dpcm_fe_dai_do_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2386) reads the link's [`enum snd_soc_dpcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L58) setting to decide whether the FE triggers before or after its BEs. On a start it uses that order directly and on a stop it inverts it, so a DSP that must see its host pipeline start before the DAI gets the order it needs:

```c
/* sound/soc/soc-pcm.c:2386 */
static int dpcm_fe_dai_do_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *fe = snd_soc_substream_to_rtd(substream);
	int stream = substream->stream;
	int ret = 0;
	int fe_first;
	enum snd_soc_dpcm_trigger trigger = fe->dai_link->trigger[stream];

	fe->dpcm[stream].runtime_update = SND_SOC_DPCM_UPDATE_FE;

	switch (trigger) {
	case SND_SOC_DPCM_TRIGGER_PRE:
		fe_first = true;
		break;
	case SND_SOC_DPCM_TRIGGER_POST:
		fe_first = false;
		break;
	...
	}

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_DRAIN:
		ret = dpcm_dai_trigger_fe_be(substream, cmd, fe_first);
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		ret = dpcm_dai_trigger_fe_be(substream, cmd, !fe_first);
		break;
	...
	}
	...
out:
	fe->dpcm[stream].runtime_update = SND_SOC_DPCM_UPDATE_NO;
	return ret;
}
```

The link's PRE or POST setting fixes fe_first and the command family then holds or inverts that order, producing the four orderings the table pairs:

```
    Trigger order: link trigger[stream] (PRE/POST) and command kind
    ──────────────────────────────────────────────────────────────

      link trigger[stream]   command         order applied
      ┌───────────────────┬───────────────┬───────────────────────┐
      │ TRIGGER_PRE       │ START family  │ FE first, then BEs    │
      │ (fe_first = true) │ STOP family   │ BEs first, then FE    │
      ├───────────────────┼───────────────┼───────────────────────┤
      │ TRIGGER_POST      │ START family  │ BEs first, then FE    │
      │ (fe_first = false)│ STOP family   │ FE first, then BEs    │
      └───────────────────┴───────────────┴───────────────────────┘

    START family = START / RESUME / PAUSE_RELEASE / DRAIN
                   → dpcm_dai_trigger_fe_be(cmd, fe_first)
    STOP  family = STOP / SUSPEND / PAUSE_PUSH
                   → dpcm_dai_trigger_fe_be(cmd, !fe_first)  (inverted)
```

### The back-end trigger refcount

[`dpcm_be_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) is where a BE shared by several FEs is started exactly once and stopped exactly once. On a start it increments [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and only the first starter calls [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198); on a stop it decrements [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) and only the last stopper actually stops the hardware. Each command is also gated on the BE's current [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) so a stop on a BE that never started is a no-op:

```c
/* sound/soc/soc-pcm.c:2184 */
		switch (cmd) {
		case SNDRV_PCM_TRIGGER_START:
			if (!be->dpcm[stream].be_start &&
			    (be->dpcm[stream].state != SND_SOC_DPCM_STATE_PREPARE) &&
			    (be->dpcm[stream].state != SND_SOC_DPCM_STATE_STOP) &&
			    (be->dpcm[stream].state != SND_SOC_DPCM_STATE_PAUSED))
				goto next;

			be->dpcm[stream].be_start++;
			if (be->dpcm[stream].be_start != 1)
				goto next;
			...
			ret = soc_pcm_trigger(be_substream,
					      SNDRV_PCM_TRIGGER_START);
			...
			be->dpcm[stream].state = SND_SOC_DPCM_STATE_START;
			break;
		case SNDRV_PCM_TRIGGER_STOP:
			if ((be->dpcm[stream].state != SND_SOC_DPCM_STATE_START) &&
			    (be->dpcm[stream].state != SND_SOC_DPCM_STATE_PAUSED))
				goto next;

			if (be->dpcm[stream].state == SND_SOC_DPCM_STATE_START)
				be->dpcm[stream].be_start--;

			if (be->dpcm[stream].be_start != 0)
				goto next;
			...
			ret = soc_pcm_trigger(be_substream, SNDRV_PCM_TRIGGER_STOP);
			...
			be->dpcm[stream].state = SND_SOC_DPCM_STATE_STOP;

			break;
		}
```

Each BE is locked individually with [`snd_pcm_stream_lock_irqsave_nested()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h) during the walk, and [`snd_soc_dpcm_can_be_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L48) skips a BE the current update does not target, so two FEs sharing a BE serialize on the BE stream lock and the refcount stays consistent.

```
    be_start refcount: a shared BE starts once and stops once
    ─────────────────────────────────────────────────────────
    (two FEs trigger the same BE; only the edges touch hardware)

      command       be_start       hardware action (soc_pcm_trigger)
      ┌───────────┬─────────────┬──────────────────────────────────┐
      │ START     │  0 ─▶ 1     │ soc_pcm_trigger(START); →START   │
      │ START     │  1 ─▶ 2     │ (skip: be_start != 1)            │
      ├───────────┼─────────────┼──────────────────────────────────┤
      │ STOP      │  2 ─▶ 1     │ (skip: be_start != 0)            │
      │ STOP      │  1 ─▶ 0     │ soc_pcm_trigger(STOP);  →STOP    │
      └───────────┴─────────────┴──────────────────────────────────┘

    START is also gated on state ∈ {PREPARE, STOP, PAUSED};
    STOP is gated on state ∈ {START, PAUSED}, and decrements
    be_start only from STATE_START.  First starter and last
    stopper are the only callers that reach the hardware.
```

### Disconnecting and freeing the link nodes

A route change or an FE close marks the stale link nodes [`SND_SOC_DPCM_LINK_STATE_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L30), and [`dpcm_be_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1378) sweeps them. It unlinks each freed node from both lists under the FE stream lock, reparents any BE still used by another FE, and frees the [`struct snd_soc_dpcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L68) after dropping the lock:

```c
/* sound/soc/soc-pcm.c:1378 */
void dpcm_be_disconnect(struct snd_soc_pcm_runtime *fe, int stream)
{
	struct snd_soc_dpcm *dpcm, *d;
	struct snd_pcm_substream *substream = snd_soc_dpcm_get_substream(fe, stream);
	LIST_HEAD(deleted_dpcms);

	snd_soc_dpcm_mutex_assert_held(fe);

	snd_pcm_stream_lock_irq(substream);
	for_each_dpcm_be_safe(fe, stream, dpcm, d) {
		...
		if (dpcm->state != SND_SOC_DPCM_LINK_STATE_FREE)
			continue;
		...
		/* BEs still alive need new FE */
		dpcm_be_reparent(fe, dpcm->be, stream);

		list_del(&dpcm->list_be);
		list_move(&dpcm->list_fe, &deleted_dpcms);
	}
	snd_pcm_stream_unlock_irq(substream);

	while (!list_empty(&deleted_dpcms)) {
		dpcm = list_first_entry(&deleted_dpcms, struct snd_soc_dpcm,
					list_fe);
		list_del(&dpcm->list_fe);
		dpcm_remove_debugfs_state(dpcm);
		kfree(dpcm);
	}
}
```

### Worked example: SOF host PCM and SoundWire back end on x86 ACPI

On an Intel x86-64 ACPI platform the `sof_sdw` machine driver builds the FE and BE links DPCM uses. A host PCM link is marked [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795) and presents the playback or capture node, and a SoundWire codec link is marked [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) so it carries the codec DAI without a node of its own. Sound Open Firmware is the platform component on the FE, so when [`dpcm_fe_dai_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2760) runs [`dpcm_fe_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1946) and that reaches [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) on the FE, the SOF component sets up the host DSP pipeline; when the same path reaches [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) on each BE through [`dpcm_be_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1679), the SoundWire codec DAI and the DSP DAI pipeline are opened. Because a single output BE (a speaker amplifier link) can be reached from more than one FE (a media stream and a tone stream), the [`be_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dpcm.h#L88) refcount in [`dpcm_be_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2184) is what keeps the amplifier running while either stream plays and stops it only when both have stopped. The route from the FE to the chosen BE is exactly the DAPM path [`dpcm_path_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1484) walks, so changing a mixer that gates the speaker path changes which BE the next open connects.
