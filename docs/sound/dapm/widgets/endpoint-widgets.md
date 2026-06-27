# DAPM endpoint widgets

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An endpoint widget is a DAPM graph node at the boundary of the routing graph, where a physical connection (a headphone jack, a speaker, a microphone, a line input, or an off-chip signal source) enters or leaves the codec. DAPM treats it as a terminal that anchors the power walk rather than an interior node that merely passes signal. The endpoint role is encoded in two places. The [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value gives the widget its kind ([`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) and [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424) for raw pins; [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), [`snd_soc_dapm_line`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L438) for named jacks; [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449) and [`snd_soc_dapm_sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L450) for synthetic terminals), and the [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) field of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) records, as a two-bit mask of [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) and [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608), whether the node feeds or drains the graph. The walk in [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) stops at any widget whose [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) bit matches the direction being walked and whose [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag is set, so the set of enabled endpoints decides which interior widgets carry power.

```
    DAPM graph boundary: endpoints anchor the power walk
    ─────────────────────────────────────────────────────

    source endpoints          interior widgets        sink endpoints
    (EP_SOURCE)                                        (EP_SINK)

    ┌──────────┐                                       ┌──────────┐
    │ MIC2 in  │──┐                                 ┌──│ HP out   │
    └──────────┘  │   ┌─────┐   ┌─────┐   ┌─────┐   │  └──────────┘
    ┌──────────┐  ├──▶│ ADC │──▶│ Mux │──▶│ AIF │   │  ┌──────────┐
    │ DMIC in  │──┘   └─────┘   └─────┘   └─────┘   ├──│ SPK out  │
    └──────────┘                                    │  └──────────┘
    ┌──────────┐   ┌─────┐   ┌─────┐   ┌─────┐      │  ┌──────────┐
    │ SIGGEN   │──▶│ AIF │──▶│ DAC │──▶│ PGA │──────┴──│ LINE out │
    └──────────┘   └─────┘   └─────┘   └─────┘         └──────────┘

      ▲ walk inward from a sink          walk outward to a source ▲
      stops at an EP_SOURCE that          stops at an EP_SINK that
      is connected                        is connected
```

## SUMMARY

A DAPM endpoint is a widget at the edge of the routing graph that marks where audio crosses the chip boundary. The [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) and [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) macros declare the raw analog pins; [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68), [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73), [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78), and [`SND_SOC_DAPM_LINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83) declare the named jacks a machine driver wires to physical connectors; and [`SND_SOC_DAPM_SIGGEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52) and [`SND_SOC_DAPM_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56) declare synthetic terminals for a permanently-present source or drain. Each macro fixes the widget's [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) id and sets [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), so the node has no power register of its own and its power state is derived from graph connectivity.

When the card instantiates a widget, [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) reads the type id and assigns the [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) mask and a [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) callback. A [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) or [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435) becomes [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607); a [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), or [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437) becomes [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608); and [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) powers the node only when a complete path reaches a connected source endpoint and a connected sink endpoint. The walk runs in [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) over the per-direction [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) path lists using [`snd_soc_dapm_widget_for_each_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717), caching each result in [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565). A machine driver or jack handler flips an endpoint's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag with [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684), [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800), or [`snd_soc_dapm_force_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4756), each invalidating the cached counts through [`dapm_widget_invalidate_input_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L281) and [`dapm_widget_invalidate_output_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L298) so the next [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L682) recomputes power. The Realtek rt722-sdca codec on an x86-64 ACPI SoundWire link is the worked example, declaring [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) endpoints for its microphones and [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) endpoints for its headphone and speaker.

## SPECIFICATIONS

The DAPM endpoint widget is a Linux kernel software construct and has no standalone hardware specification. The physical connections it represents (a 3.5 mm headphone or microphone jack, an internal speaker amplifier, a digital-microphone PDM input) are defined by the codec datasheet and the board schematic; on a SoundWire codec the data ports the endpoints feed are addressed as SDCA function entities, and the codec is enumerated on x86-64 through ACPI.

## LINUX KERNEL

### Endpoint declaration macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_INPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60): raw analog input pin; sets id [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) and [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) = [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26)
- [`'\<SND_SOC_DAPM_OUTPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64): raw analog output pin; sets id [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424)
- [`'\<SND_SOC_DAPM_MIC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68): microphone endpoint with an event; sets id [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435) and fires before power-up and after power-down
- [`'\<SND_SOC_DAPM_HP\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73): headphone endpoint; sets id [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436) and fires after power-up and before power-down
- [`'\<SND_SOC_DAPM_SPK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78): speaker endpoint; sets id [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437)
- [`'\<SND_SOC_DAPM_LINE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83): line in/out endpoint; sets id [`snd_soc_dapm_line`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L438)
- [`'\<SND_SOC_DAPM_SIGGEN\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52): synthetic always-present source; sets id [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449)
- [`'\<SND_SOC_DAPM_SINK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56): synthetic always-present drain; sets id [`snd_soc_dapm_sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L450)

### Endpoint role flags and direction (soc-dapm.h)

- [`'\<enum snd_soc_dapm_direction\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600): the two edge directions, [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) (0) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602) (1)
- [`'\<SND_SOC_DAPM_DIR_TO_EP\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L605): `BIT(x)`, turns a direction into an endpoint-mask bit
- [`'\<SND_SOC_DAPM_EP_SOURCE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607): endpoint feeds the graph; `BIT(SND_SOC_DAPM_DIR_IN)` = 0x1
- [`'\<SND_SOC_DAPM_EP_SINK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608): endpoint drains the graph; `BIT(SND_SOC_DAPM_DIR_OUT)` = 0x2
- [`'\<SND_SOC_NOPM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26): -1, marks a widget with no power register

### Widget and path types (soc-dapm.h)

- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): a graph node; carries the [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) endpoint mask, the [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag, the [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) path lists, and the cached [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) path counts
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): an edge; the [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) union aliases [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497), and [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) records whether it is live
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): the `{sink, control, source}` triple a driver lists to wire endpoints into the graph

### Path iteration (soc-dapm.h)

- [`'\<snd_soc_dapm_widget_for_each_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717): iterate the [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) path list of a widget in one direction
- [`'\<snd_soc_dapm_widget_for_each_sink_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L741) / [`'\<snd_soc_dapm_widget_for_each_source_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L750): direction-specialized iteration

### Connectivity walk and power check (soc-dapm.c)

- [`'\<dapm_is_connected_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487): the recursive walk; stops at a connected endpoint matching the direction, else recurses over reverse-direction paths and sums complete routes
- [`'\<dapm_is_connected_output_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1550) / [`'\<dapm_is_connected_input_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1568): the two direction-specialized entry points
- [`'\<dapm_generic_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737): power a node when both input-side and output-side walks find at least one complete path
- [`'\<dapm_always_on_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770): power a node whenever it is [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535); given to [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449) and [`snd_soc_dapm_sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L450)
- [`'\<dapm_suspend_check\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1405): the value an endpoint returns; 1 when running, [`ignore_suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L538) under `D3hot`/`D3cold`

### Path-count invalidation (soc-dapm.c)

- [`'\<dapm_widget_invalidate_input_paths\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L281) / [`'\<dapm_widget_invalidate_output_paths\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L298): reset the cached [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) count for a widget and everything reachable in the reverse direction
- [`'\<dapm_widget_invalidate_paths\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L240): the shared inline both specializations call
- [`'\<snd_soc_dapm_mark_endpoints_dirty\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L335): re-check every endpoint widget on the card, by [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) role

### Pin marking and creation (soc-dapm.c)

- [`'\<snd_soc_dapm_new_control_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757): instantiate a widget; the per-id switch sets [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) and [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) and seeds [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) to -1
- [`'\<snd_soc_dapm_enable_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) / [`'\<snd_soc_dapm_disable_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800): mark an endpoint pin connected or disconnected
- [`'\<snd_soc_dapm_force_enable_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4756): force an endpoint on regardless of route, used for microphone bias during jack detection; sets [`force`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L537)
- [`'\<snd_soc_dapm_get_pin_status\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4824): read back an endpoint's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag
- [`'\<__dapm_set_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932): the common setter both enable and disable reach through [`dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2964); flips [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) and invalidates both path caches

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the widget table with two [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) and five [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) endpoints
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the route table joining the endpoints to the interior functional units

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget types, the audio path map, and the four power domains
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): jack detection, where a handler enables and disables the endpoint pins
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide that lists the widget and route tables a codec provides
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver guide, where board-level endpoint pins are wired to physical connectors

## OTHER SOURCES

- [ALSA System on Chip (ASoC) section of the ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The endpoint macros and the [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) mask are the public contract a codec or machine driver uses to mark the graph boundary. A driver declares an endpoint with one of the macros and never sets [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) directly; [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) derives the mask from the type id at instantiation.

| Macro | enum id | is_ep role | power_check |
|-------|---------|------------|-------------|
| [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) | snd_soc_dapm_input | EP_SOURCE (0x1, unless fully_routed) | dapm_generic_check_power |
| [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68) | snd_soc_dapm_mic | EP_SOURCE (0x1) | dapm_generic_check_power |
| [`SND_SOC_DAPM_SIGGEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52) | snd_soc_dapm_siggen | EP_SOURCE (0x1) | dapm_always_on_check_power |
| [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) | snd_soc_dapm_output | EP_SINK (0x2, unless fully_routed) | dapm_generic_check_power |
| [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73) | snd_soc_dapm_hp | EP_SINK (0x2) | dapm_generic_check_power |
| [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78) | snd_soc_dapm_spk | EP_SINK (0x2) | dapm_generic_check_power |
| [`SND_SOC_DAPM_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56) | snd_soc_dapm_sink | EP_SINK (0x2) | dapm_always_on_check_power |
| [`SND_SOC_DAPM_LINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83) | snd_soc_dapm_line | (set from route direction) | dapm_generic_check_power |

[`SND_SOC_DAPM_LINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83) is the one entry that does not pin its [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) bit in the type switch, because a line connector can carry audio in either direction and its role is resolved later from the routes that attach to it. A machine driver flips a declared endpoint with [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) and [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800), forces one permanently on with [`snd_soc_dapm_force_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4756), reads its state with [`snd_soc_dapm_get_pin_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4824), and commits the change with [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L682).

## DETAILS

### The endpoint macros expand to widget initializers

Each endpoint macro expands to a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) compound literal with the type id set and the power register suppressed. [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) and [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) take only a name and set [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26):

```c
/* include/sound/soc-dapm.h:60 */
#define SND_SOC_DAPM_INPUT(wname) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_input, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM }
#define SND_SOC_DAPM_OUTPUT(wname) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_output, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM }
```

The named jacks add an event callback and the flags that fire it at the right point in the power sequence. [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68) requests its event before power-up and after power-down, while [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73) requests it after power-up and before power-down:

```c
/* include/sound/soc-dapm.h:68 */
#define SND_SOC_DAPM_MIC(wname, wevent) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_mic, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM, .event = wevent, \
	.event_flags = SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMD}
#define SND_SOC_DAPM_HP(wname, wevent) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_hp, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM, .event = wevent, \
	.event_flags = SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD}
```

The two synthetic terminals carry no event and exist only to terminate a graph that has no physical pin on one side. [`SND_SOC_DAPM_SIGGEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52) is an always-present source (a tone generator, a sidetone), and [`SND_SOC_DAPM_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56) is an always-present drain:

```c
/* include/sound/soc-dapm.h:52 */
#define SND_SOC_DAPM_SIGGEN(wname) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_siggen, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM }
#define SND_SOC_DAPM_SINK(wname) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_sink, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM }
```

Reading down the macro column gathers what the separate expansions set, each id, the event flags on the named jacks, and the NOPM reg shared by all six:

```
    Each endpoint macro fixes id and reg; named jacks add an event
    ──────────────────────────────────────────────────────────────

    macro                 ┌─────────────────────────────────────┐
    SND_SOC_DAPM_INPUT  ─▶│ .id = snd_soc_dapm_input            │
                          │ .reg = SND_SOC_NOPM                 │
    SND_SOC_DAPM_OUTPUT ─▶│ .id = snd_soc_dapm_output           │
                          │ .reg = SND_SOC_NOPM                 │
    SND_SOC_DAPM_MIC    ─▶│ .id = snd_soc_dapm_mic   .event     │
                          │ PRE_PMU, POST_PMD                   │
    SND_SOC_DAPM_HP     ─▶│ .id = snd_soc_dapm_hp    .event     │
                          │ POST_PMU, PRE_PMD                   │
    SND_SOC_DAPM_SIGGEN ─▶│ .id = snd_soc_dapm_siggen (no event)│
    SND_SOC_DAPM_SINK   ─▶│ .id = snd_soc_dapm_sink   (no event)│
                          └─────────────────────────────────────┘
        reg = SND_SOC_NOPM on all: no power register of its own
```

### Routes wire endpoints into the graph

A declared endpoint is inert until a route attaches it to the interior. A driver lists [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) triples, each naming a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) widget, an optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) that gates the edge, and a [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) widget, and DAPM builds one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) edge per route into the [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists the walk later follows:

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

A route whose [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) is an [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) pin and whose [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) names an interior converter makes that endpoint reachable from the [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) walk; the optional [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) predicate lets a supply route decide its liveness at run time. The [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string, when non-NULL, ties the edge's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit to a mux or mixer setting, so a route can carry audio only when both the kcontrol selects it and the endpoint pin is enabled.

### Instantiation assigns the endpoint role from the type id

The endpoint role is computed when [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) instantiates the widget. It copies the driver's compound-literal template into a heap [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) with [`dapm_cnew_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3739), then switches on the type id the macro fixed:

```c
/* sound/soc/soc-dapm.c:3756 */
struct snd_soc_dapm_widget *
snd_soc_dapm_new_control_unlocked(struct snd_soc_dapm_context *dapm,
			 const struct snd_soc_dapm_widget *widget)
{
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	enum snd_soc_dapm_direction dir;
	struct snd_soc_dapm_widget *w;
	int ret = -ENOMEM;

	w = dapm_cnew_widget(widget, dapm_prefix(dapm));
	if (!w)
		goto cnew_failed;
```

A switch on [`w->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) sets [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) and the matching [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546):

```c
/* sound/soc/soc-dapm.c:3806 */
	switch (w->id) {
	case snd_soc_dapm_mic:
		w->is_ep = SND_SOC_DAPM_EP_SOURCE;
		w->power_check = dapm_generic_check_power;
		break;
	case snd_soc_dapm_input:
		if (!dapm->card->fully_routed)
			w->is_ep = SND_SOC_DAPM_EP_SOURCE;
		w->power_check = dapm_generic_check_power;
		break;
	case snd_soc_dapm_spk:
	case snd_soc_dapm_hp:
		w->is_ep = SND_SOC_DAPM_EP_SINK;
		w->power_check = dapm_generic_check_power;
		break;
	case snd_soc_dapm_output:
		if (!dapm->card->fully_routed)
			w->is_ep = SND_SOC_DAPM_EP_SINK;
		w->power_check = dapm_generic_check_power;
		break;
	case snd_soc_dapm_vmid:
	case snd_soc_dapm_siggen:
		w->is_ep = SND_SOC_DAPM_EP_SOURCE;
		w->power_check = dapm_always_on_check_power;
		break;
	case snd_soc_dapm_sink:
		w->is_ep = SND_SOC_DAPM_EP_SINK;
		w->power_check = dapm_always_on_check_power;
		break;
	...
```

A raw [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) or [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424) becomes an endpoint only when the card's [`fully_routed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h) flag is clear; a fully-routed card declares every connection in its route table, so its raw pins are interior nodes rather than terminals, while the named [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), and [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437) widgets stay endpoints unconditionally. After the switch the function initializes both edge lists, sets the cached counts to -1 to mark them stale, and sets [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) to 1 so a pin is live until the machine layer disables it:

```c
/* sound/soc/soc-dapm.c:3879 */
	dapm_for_each_direction(dir) {
		INIT_LIST_HEAD(&w->edges[dir]);
		w->endpoints[dir] = -1;
	}

	/* machine layer sets up unconnected pins and insertions */
	w->connected = 1;
	return w;
```

Each case of that switch settles one id into an is_ep role and a power_check, which the rows gather side by side:

```
    snd_soc_dapm_new_control_unlocked switch: w->id ▶ is_ep + power_check
    ────────────────────────────────────────────────────────────────────

    ┌──────────────────────┬──────────────────────┬──────────────────────┐
    │ w->id                │ is_ep                │ power_check          │
    ├──────────────────────┼──────────────────────┼──────────────────────┤
    │ snd_soc_dapm_mic     │ EP_SOURCE (0x1)      │ generic_check_power  │
    │ snd_soc_dapm_input   │ EP_SOURCE if !fully_ │ generic_check_power  │
    │                      │   routed             │                      │
    │ snd_soc_dapm_hp      │ EP_SINK   (0x2)      │ generic_check_power  │
    │ snd_soc_dapm_spk     │ EP_SINK   (0x2)      │ generic_check_power  │
    │ snd_soc_dapm_output  │ EP_SINK if !fully_   │ generic_check_power  │
    │                      │   routed             │                      │
    │ snd_soc_dapm_siggen  │ EP_SOURCE (0x1)      │ always_on_check_power│
    │ snd_soc_dapm_sink    │ EP_SINK   (0x2)      │ always_on_check_power│
    └──────────────────────┴──────────────────────┴──────────────────────┘
        after the switch: endpoints[dir] = -1, connected = 1
```

### The connectivity walk stops at connected endpoints

The power state of every interior widget is decided by [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487), which counts complete paths from a starting widget out to the boundary in one direction. It returns the cached [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) value when valid, and otherwise recurses. The terminating condition is the endpoint test, where a widget whose [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) bit matches the walk direction and whose [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag is set ends the recursion with the value [`dapm_suspend_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1405) returns:

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
	if ((widget->is_ep & SND_SOC_DAPM_DIR_TO_EP(dir)) && widget->connected) {
		widget->endpoints[dir] = dapm_suspend_check(widget);
		return widget->endpoints[dir];
	}

	snd_soc_dapm_widget_for_each_path(widget, rdir, path) {
		...
		if (path->is_supply)
			continue;
		...
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

The walk iterates the reverse-direction edge list with [`snd_soc_dapm_widget_for_each_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717), skipping supply edges and following only paths whose [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set, recursing through [`path->node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) and summing the counts each branch returns. The expression `widget->is_ep & SND_SOC_DAPM_DIR_TO_EP(dir)` marks an endpoint terminal. [`SND_SOC_DAPM_DIR_TO_EP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L605) is `BIT(dir)`, so an outward walk ([`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602)) stops at a widget carrying [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608) and an inward walk ([`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601)) stops at a widget carrying [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607). The two named entry points each fix the direction and pass themselves as the recursion callback:

```c
/* sound/soc/soc-dapm.c:1550 */
static int dapm_is_connected_output_ep(struct snd_soc_dapm_widget *widget,
	struct list_head *list,
	bool (*custom_stop_condition)(struct snd_soc_dapm_widget *i,
				      enum snd_soc_dapm_direction))
{
	return dapm_is_connected_ep(widget, list, SND_SOC_DAPM_DIR_OUT,
			dapm_is_connected_output_ep, custom_stop_condition);
}
```

### Direction-specialized path iterators

The walk reaches a widget's neighbours through [`snd_soc_dapm_widget_for_each_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717), which is a [`list_for_each_entry()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h) over one of the two [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists, indexed by an [`enum snd_soc_dapm_direction`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600). Two wrappers bake the direction in so callers that always mean one side need not name it:

```c
/* include/sound/soc-dapm.h:741 */
#define snd_soc_dapm_widget_for_each_sink_path(w, p) \
	snd_soc_dapm_widget_for_each_path(w, SND_SOC_DAPM_DIR_IN, p)
```

```c
/* include/sound/soc-dapm.h:750 */
#define snd_soc_dapm_widget_for_each_source_path(w, p) \
	snd_soc_dapm_widget_for_each_path(w, SND_SOC_DAPM_DIR_OUT, p)
```

The naming is from the edge's point of view rather than the walk's. [`snd_soc_dapm_widget_for_each_sink_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L741) walks the [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) list, the paths where this widget is the source feeding a downstream sink, and [`snd_soc_dapm_widget_for_each_source_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L750) walks the [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602) list, the paths where this widget is the sink drained from an upstream source. An [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) endpoint therefore has only sink paths, an [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608) endpoint only source paths, and the boundary nodes sit at one end of every chain the iterators traverse.

### The endpoint walk decides whether a node is powered

[`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) is the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) callback every interior widget and named jack endpoint is given. It powers the node only when there is a complete path to a connected source endpoint on the input side and a connected sink endpoint on the output side:

```c
/* sound/soc/soc-dapm.c:1737 */
static int dapm_generic_check_power(struct snd_soc_dapm_widget *w)
{
	int in, out;

	DAPM_UPDATE_STAT(w, power_checks);

	in  = dapm_is_connected_input_ep(w, NULL, NULL);
	out = dapm_is_connected_output_ep(w, NULL, NULL);
	return out != 0 && in != 0;
}
```

A node with audio reaching it from a microphone but no enabled output endpoint draining it returns 0 and stays unpowered, and the reverse holds too, so a single disconnected endpoint at either boundary collapses the power of the whole interior chain between it and the other boundary. The synthetic terminals instead use [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770), which powers a [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449) or [`snd_soc_dapm_sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L450) whenever it is [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535):

```c
/* sound/soc/soc-dapm.c:1770 */
static int dapm_always_on_check_power(struct snd_soc_dapm_widget *w)
{
	return w->connected;
}
```

The value an endpoint returns from the walk is the result of [`dapm_suspend_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1405), which returns 1 while the card is running and the widget's [`ignore_suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L538) value when the card is suspended into `D3hot` or `D3cold`, so an endpoint that should keep audio alive across suspend is marked accordingly:

```c
/* sound/soc/soc-dapm.c:1405 */
static int dapm_suspend_check(struct snd_soc_dapm_widget *widget)
{
	struct device *dev = snd_soc_dapm_to_dev(widget->dapm);
	int level = snd_power_get_state(widget->dapm->card->snd_card);

	switch (level) {
	case SNDRV_CTL_POWER_D3hot:
	case SNDRV_CTL_POWER_D3cold:
		if (widget->ignore_suspend)
			dev_dbg(dev, "ASoC: %s ignoring suspend\n",
				widget->name);
		return widget->ignore_suspend;
	default:
		return 1;
	}
}
```

Each walk sums the value an endpoint returns, and the power check grants power only when both the source side and the sink side come back nonzero:

```
    dapm_generic_check_power: a node powers only when both walks reach
    ──────────────────────────────────────────────────────────────────

    in  = dapm_is_connected_input_ep(w)    out = dapm_is_connected_output_ep(w)

    ┌──────────────┬──────────────┬───────────┐
    │ in (source)  │ out (sink)   │ powered?  │
    ├──────────────┼──────────────┼───────────┤
    │   0          │   0          │   no      │
    │   0          │  >0          │   no      │
    │  >0          │   0          │   no      │
    │  >0          │  >0          │   yes     │
    └──────────────┴──────────────┴───────────┘
        one disconnected endpoint at either boundary collapses the
        whole interior chain between it and the other boundary
```

### Marking a pin invalidates the cached path counts

The walk caches its per-direction result in [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565), so any change at an endpoint that could alter connectivity clears the affected caches before the next power scan. [`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932) is reached from both [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) and [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800) through [`dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2964), and when it changes [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) it invalidates both path caches and marks the widget dirty:

```c
/* sound/soc/soc-dapm.c:2932 */
static int __dapm_set_pin(struct snd_soc_dapm_context *dapm,
			  const char *pin, int status)
{
	struct snd_soc_dapm_widget *w = dapm_find_widget(dapm, pin, true);
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	int ret = 0;
	...
	if (w->connected != status) {
		dapm_mark_dirty(w, "pin configuration");
		dapm_widget_invalidate_input_paths(w);
		dapm_widget_invalidate_output_paths(w);
		ret = 1;
	}

	w->connected = status;
	if (status == 0)
		w->force = 0;

	return ret;
}
```

[`dapm_widget_invalidate_input_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L281) and [`dapm_widget_invalidate_output_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L298) are thin wrappers over the shared [`dapm_widget_invalidate_paths()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L240) inline, which resets [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) to -1 for the widget and for every widget reachable through the reverse direction, because a connectivity change at an endpoint propagates outward to every node whose cached count depended on it:

```c
/* sound/soc/soc-dapm.c:240 */
static __always_inline void dapm_widget_invalidate_paths(
	struct snd_soc_dapm_widget *w, enum snd_soc_dapm_direction dir)
{
	enum snd_soc_dapm_direction rdir = DAPM_DIR_REVERSE(dir);
	struct snd_soc_dapm_widget *node;
	struct snd_soc_dapm_path *p;
	LIST_HEAD(list);

	dapm_assert_locked(w->dapm);

	if (w->endpoints[dir] == -1)
		return;

	list_add_tail(&w->work_list, &list);
	w->endpoints[dir] = -1;

	list_for_each_entry(w, &list, work_list) {
		snd_soc_dapm_widget_for_each_path(w, dir, p) {
			if (p->is_supply || !p->connect)
				continue;
			node = p->node[rdir];
			if (node->endpoints[dir] != -1) {
				node->endpoints[dir] = -1;
				list_add_tail(&node->work_list, &list);
			}
		}
	}
}
```

The early return when [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) is already -1 prunes the propagation, since an already-stale subtree needs no further visiting. The body is a worklist breadth-first sweep that follows the [`dir`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600) edges with [`snd_soc_dapm_widget_for_each_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L717) and reaches each neighbour through the reverse-direction [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L499) alias, so disabling one endpoint clears exactly the cached counts that depended on it without recomputing any power.

### Pin marking flips the connected flag

The machine layer and jack handlers reach the [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag through a small family of exported helpers, each of which takes the lock and defers the actual count reset to [`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932). [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) and [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800) are the conditional pair, passing 1 or 0 to [`dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2964) so the endpoint powers only when a route and stream warrant it:

```c
/* sound/soc/soc-dapm.c:4684 */
int snd_soc_dapm_enable_pin(struct snd_soc_dapm_context *dapm, const char *pin)
{
	int ret;

	snd_soc_dapm_mutex_lock(dapm);

	ret = dapm_set_pin(dapm, pin, 1);

	snd_soc_dapm_mutex_unlock(dapm);

	return ret;
}
```

```c
/* sound/soc/soc-dapm.c:4800 */
int snd_soc_dapm_disable_pin(struct snd_soc_dapm_context *dapm,
			     const char *pin)
{
	int ret;

	snd_soc_dapm_mutex_lock(dapm);

	ret = dapm_set_pin(dapm, pin, 0);

	snd_soc_dapm_mutex_unlock(dapm);

	return ret;
}
```

[`snd_soc_dapm_force_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4756) is the unconditional case. It routes through [`snd_soc_dapm_force_enable_pin_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4708), which sets the widget's [`force`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L537) flag so the node powers regardless of any complete route, the form a microphone bias supply needs during jack detection before a stream exists:

```c
/* sound/soc/soc-dapm.c:4756 */
int snd_soc_dapm_force_enable_pin(struct snd_soc_dapm_context *dapm,
				  const char *pin)
{
	int ret;

	snd_soc_dapm_mutex_lock(dapm);

	ret = snd_soc_dapm_force_enable_pin_unlocked(dapm, pin);

	snd_soc_dapm_mutex_unlock(dapm);

	return ret;
}
```

[`snd_soc_dapm_get_pin_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4824) is the read side, returning the endpoint's current [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag so a driver can query whether a pin is live without forcing a power scan:

```c
/* sound/soc/soc-dapm.c:4824 */
int snd_soc_dapm_get_pin_status(struct snd_soc_dapm_context *dapm,
				const char *pin)
{
	struct snd_soc_dapm_widget *w = dapm_find_widget(dapm, pin, true);

	if (w)
		return w->connected;

	return 0;
}
```

Three of these helpers reach one shared setter while the read side only returns connected, the enable and disable pair passing 1 or 0 and the force path setting force:

```
    The exported pin helpers converge on one setter
    ───────────────────────────────────────────────

    snd_soc_dapm_enable_pin  ──▶ dapm_set_pin(.., 1) ─┐
    snd_soc_dapm_disable_pin ──▶ dapm_set_pin(.., 0) ─┤
                                                      ▼
                                            ┌───────────────────┐
                                            │ __dapm_set_pin    │
                                            │ flips connected,  │
                                            │ invalidate in+out │
                                            │ paths, mark dirty │
                                            └───────────────────┘
    snd_soc_dapm_force_enable_pin ──▶ _unlocked: sets force = 1
    snd_soc_dapm_get_pin_status   ──▶ reads connected (no change)
```

### Rechecking every endpoint after a topology change

When something can have changed connectivity card-wide rather than at one named pin, [`snd_soc_dapm_mark_endpoints_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L335) sweeps every widget and invalidates the cache of those carrying an [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) bit, choosing the input or output direction from the endpoint role:

```c
/* sound/soc/soc-dapm.c:335 */
void snd_soc_dapm_mark_endpoints_dirty(struct snd_soc_card *card)
{
	struct snd_soc_dapm_widget *w;

	snd_soc_dapm_mutex_lock_root(card);

	for_each_card_widgets(card, w) {
		if (w->is_ep) {
			dapm_mark_dirty(w, "Rechecking endpoints");
			if (w->is_ep & SND_SOC_DAPM_EP_SINK)
				dapm_widget_invalidate_output_paths(w);
			if (w->is_ep & SND_SOC_DAPM_EP_SOURCE)
				dapm_widget_invalidate_input_paths(w);
		}
	}

	snd_soc_dapm_mutex_unlock(card);
}
```

An [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608) endpoint invalidates its output-side cache and an [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) its input-side cache, matching the single direction each terminal can reach the interior through, so the next [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L682) rebuilds the whole power picture from a clean slate.

### Worked example: rt722-sdca endpoints

The Realtek RT722, reached over SoundWire, declares its boundary in the head of [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): two [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) sinks for the headphone and speaker and five [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) sources for the analog and digital microphones:

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
	...
};
```

These pins carry [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), so DAPM never writes a register to power them; their state comes from the walk. When the card binds, [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) turns `HP` and `SPK` into [`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608) endpoints and the `MIC2` and `DMIC` pins into [`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) endpoints. The route table [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) wires each endpoint to the interior functional units, so a capture walk inward from a SoundWire output port stops at the connected `MIC2` source and a playback walk outward from the input port stops at the connected `HP` sink, and [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) powers exactly the converters and muxes between them. Disabling the `SPK` pin with [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800) then collapses the speaker path on the next [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L682), leaving the headphone path powered.

```
    rt722-sdca pin widgets resolved to endpoint roles at bind
    ─────────────────────────────────────────────────────────

    ┌────────────┬─────────────────────┬──────────────────┐
    │ pin name   │ macro / id          │ is_ep role       │
    ├────────────┼─────────────────────┼──────────────────┤
    │ "HP"       │ OUTPUT / output     │ EP_SINK   (0x2)  │
    │ "SPK"      │ OUTPUT / output     │ EP_SINK   (0x2)  │
    │ "MIC2"     │ INPUT  / input      │ EP_SOURCE (0x1)  │
    │ "DMIC1_2"  │ INPUT  / input      │ EP_SOURCE (0x1)  │
    │ "DMIC3_4"  │ INPUT  / input      │ EP_SOURCE (0x1)  │
    └────────────┴─────────────────────┴──────────────────┘
        playback walk out stops at connected "HP" sink;
        capture walk in stops at connected "MIC2" source
```
