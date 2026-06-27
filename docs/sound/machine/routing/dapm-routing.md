# Machine DAPM routing

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A machine (board) driver assembles one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) from several independent components, the SOF DSP that exposes the CPU and platform DAIs, the codec on the bus, and the amplifiers, and the routing that makes them one playable card is a graph of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) nodes joined by [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) edges that the core stitches together during card probe. The board contributes two arrays to that graph, [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) declaring its panel endpoints (a Speaker, a Headphone, a microphone) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) naming the edges from those endpoints to the pins each codec exports, and [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) instantiates them with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) after every codec's own widgets and routes are already in the card. The three sides of each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) carry the PCM data through the same card (the cpu, codec, and platform names each resolve to a registered component DAI), while the DAPM route table carries the analog signal across the codec boundary. On the Intel SoundWire reference board the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine builds this graph per codec at runtime, calling each codec's [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) from [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) so that [`asoc_sdw_rt_sdca_jack_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93) wires the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) headset and [`asoc_sdw_cs_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38) wires the [`cs35l56`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs35l56.c) amplifiers, all into one card named `"soundwire"`.

```
    One routed card: PCM data over dai_links, analog signal over dapm_routes
    ────────────────────────────────────────────────────────────────────────

    SOF DSP (platform + cpu DAIs)        codec components          board
    ┌────────────────────────┐                                  endpoints
    │ "SDW0 Pin0"  cpu DAI   │   dai_link 0                    (card->dapm_
    │ "SDW1 Pin2"  cpu DAI   │ ◀── cpu/codec/platform ──▶       widgets)
    │ "SDW2 Pin3"  cpu DAI   │     bound by name
    └───────────┬────────────┘                              ┌─────────────┐
                │ PCM data                                  │ "Headphone" │
                ▼                ┌───────────────────────┐  │   hp        │
        dai_link.codecs ───────▶ │ rt722-sdca codec      │  └──────▲──────┘
        "rt722-sdca-aif1"        │  pins: "rt722 HP"     │ ───────┘  route
                                 │        "rt722 MIC2"   │  ┌─────────────┐
                                 │  (internal audio map) │  │ "Headset Mic"
        dai_link.codecs ───────▶ │        "rt722 SPK"    │  │   mic       │
        "cs35l56-sdw1"           ├───────────────────────┤  └──────▲──────┘
        (amp 0, "AMP1")          │ cs35l56 amp 0         │ ───────┘
        dai_link.codecs ───────▶ │  pin: "AMP1 SPK"      │  ┌─────────────┐
        "cs35l56-sdw1"           ├───────────────────────┤  │ "Speaker"   │
        (amp 1, "AMP2")          │ cs35l56 amp 1         │  │   spk       │
                                 │  pin: "AMP2 SPK"      │ ─┴──────▲──────┘
                                 └───────────────────────┘  ───────┘ routes

    card->dapm_routes board edges (sink ◀── source):
      {"Headphone",   NULL, "rt722 HP"}    {"Speaker", NULL, "AMP1 SPK"}
      {"rt722 MIC2",  NULL, "Headset Mic"} {"Speaker", NULL, "AMP2 SPK"}

    snd_soc_bind_card() order:
      new codec widgets/routes (per component)
        ─▶ board widgets  ─▶ board controls  ─▶ board routes  ─▶ new_widgets
```

## SUMMARY

A card is the whole DAPM graph, and the machine driver owns the board slice of it. The [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) carries the board's panel endpoints in [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) with the count [`num_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1058), the board edges in [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) with [`num_dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1060), and the board kcontrols in [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) with [`num_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1051). Each board endpoint is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) of type [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), or [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435) built by [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78), [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73), and [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68), and each board edge is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) naming a board endpoint and a codec pin.

The assembly happens once, inside [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), in a fixed order. The card's own widget arrays go in first through [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932), then [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742) probes every codec and platform component through [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602), which applies the per-codec name prefix from [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557) and adds that codec's own [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) so its pins exist as prefixed widgets, then [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707) probes the DAIs and the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callbacks run, and finally [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521) adds [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) adds [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059). The generic route mechanism (how a route string resolves to two widgets and becomes one path edge) is the DAPM routing layer; this page covers which arrays the board supplies and the order in which the card stitches them.

On the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) board the board widgets, controls, and routes are added per codec from the link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback rather than from the card's static arrays, because the codec set varies per machine. [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918) walks each runtime's codec DAIs, adds that codec's board widgets ([`generic_jack_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L20), [`generic_spk_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L30)) with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) and controls with [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521), then calls the codec's [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) from [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), which is where [`asoc_sdw_rt_sdca_jack_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93) adds [`rt722_sdca_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L68) and [`asoc_sdw_cs_spk_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38) adds the per-amp Speaker route through [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272).

## SPECIFICATIONS

ASoC card-level routing is a Linux kernel software construct of the DAPM power graph and has no standalone hardware specification. The board endpoint widgets ([`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435)) describe the physical jacks and transducers a board carries, and the codec pins they route to come from each codec's SDCA function topology, but the route table itself is defined entirely by the [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) records the driver supplies.

## LINUX KERNEL

### Card routing fields (soc.h)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the board object; the routing assembly reads [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057)/[`num_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1058), [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059)/[`num_dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1060), and [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050)/[`num_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1051), and keeps the resulting graph in the [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) and [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) lists
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): a graph node; a board endpoint widget's [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518) is what a board route matches against, and its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) marks it a speaker, headphone, or mic endpoint
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): one board edge, the [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474)/[`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475)/[`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) name triple connecting a board endpoint to a codec pin
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget kinds; the board endpoints use [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435), and the codec pins use [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425)/[`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424)

### Endpoint widget and pin-switch macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_SPK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78): build a speaker endpoint widget, id [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), register [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26)
- [`'\<SND_SOC_DAPM_HP\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73): build a headphone endpoint widget, id [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436)
- [`'\<SND_SOC_DAPM_MIC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68): build a microphone endpoint widget, id [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435)
- [`'\<SOC_DAPM_PIN_SWITCH\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369): build a "<pin> Switch" kcontrol so userspace can force an endpoint widget on or off

### Card-probe routing assembly (soc-core.c)

- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): the single card probe; adds card widgets, probes components, runs link init, then adds [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) and [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) before [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322)
- [`'\<soc_probe_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602): probe one codec or platform; calls [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557), then adds the component's [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`'\<soc_set_name_prefix\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557): copy a codec's [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) from a matching [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) onto the component, so its pin widgets are renamed `"rt722 HP"`, `"AMP1 SPK"`, and so on
- [`'\<soc_probe_link_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707): probe every runtime's DAIs in component order, after which the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) runs
- [`'\<snd_soc_add_card_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521): add the board's [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) array of [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L131) to the card
- [`'\<snd_soc_register_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557): validate the card, allocate its DAPM context, init the [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) and [`paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) lists, then bind

### Route and widget instantiation (soc-dapm.c)

- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): take the DAPM mutex and turn each [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) into a path edge; called once for the card's [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) and once per codec for the component's routes
- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932): instantiate an array of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) templates onto the card; used for [`card->dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) and for each codec's component widgets
- [`'\<snd_soc_dapm_new_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322): finish each widget after the routes exist, build its mixer or mux kcontrols, read its initial power state, then run [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2090)

### sof_sdw board route assembly (intel/boards, sdw_utils)

- [`'\<mc_probe\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1434): set up the `"soundwire"` card, build its links and [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) (name prefixes), and register it
- [`'\<asoc_sdw_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918): the per-link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702); add each codec's board widgets and controls, then dispatch to its [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47)
- [`'\<asoc_sdw_rt_sdca_jack_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93): add [`rt722_sdca_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L68) connecting the board `"Headphone"`/`"Headset Mic"` to the rt722 pins, and create the headset jack
- [`'\<asoc_sdw_cs_spk_rtd_init\>':'sound/soc/sdw_utils/soc_sdw_cs_amp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs_amp.c#L38): add one `{"Speaker", NULL, "<prefix> SPK"}` route per cs35l56 amp on the link
- [`'codec_info_list':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74): the per-part table whose [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47), and [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) fields the rtd init reads for each codec
- [`'generic_jack_widgets':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L20) / [`'generic_spk_widgets':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L30): the board endpoint widget arrays (`"Headphone"`, `"Headset Mic"`, `"Speaker"`) added per codec
- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) / [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the codec's own pin widgets (`"HP"`, `"SPK"`, `"MIC2"`) and internal routes, added when the codec component probes

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver concept, the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and its DAI links and routing
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): a widget is part of the hardware that can be enabled, and a route is an interconnection that exists when sound can flow
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the component model that splits the codec, platform, and machine drivers into one card
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): jack detection that forces the board endpoint widgets the routes terminate at

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The machine driver supplies three board arrays on the card and the core consumes them at one point in the probe. The objects below are the board's contribution to the card graph, who fills each one, and when the core reads it.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`card->dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) | machine driver (static array, or per codec on [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c)) | read once by [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) during [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) |
| [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) | machine driver | applied once by [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) after components probe |
| [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) | machine driver | added once by [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521) |
| board endpoint [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) | [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78), [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73), [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68) | held on [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) until card free |
| codec pin [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) | the codec driver, renamed by [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557) | created in [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) |
| board edge [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) | machine driver | resolved to a path on [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071) |
| name prefix [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) | machine driver in [`card->codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) | read by [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557) per component |

## DETAILS

### The card is one DAPM graph, the board owns three arrays of it

A card's audio routing is a single directed graph of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) nodes held on [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) and [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) edges held on [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071), and every component on the card contributes nodes and edges into that one graph. The codec drivers contribute the widgets inside each chip and the edges between them, and the machine driver contributes the board's physical endpoints and the edges that bridge a board endpoint to a codec pin. The [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) carries the board's contribution in three array-plus-count pairs:

```c
/* include/sound/soc.h:1050 */
	const struct snd_kcontrol_new *controls;
	int num_controls;

	/*
	 * Card-specific routes and widgets.
	 * Note: of_dapm_xxx for Device Tree; Otherwise for driver build-in.
	 */
	const struct snd_soc_dapm_widget *dapm_widgets;
	int num_dapm_widgets;
	const struct snd_soc_dapm_route *dapm_routes;
	int num_dapm_routes;
	const struct snd_soc_dapm_widget *of_dapm_widgets;
	int num_of_dapm_widgets;
	const struct snd_soc_dapm_route *of_dapm_routes;
	int num_of_dapm_routes;
```

The comment names the split between the two widget and route sets. On an x86-64 ACPI system a machine driver fills [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057), [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059), and [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050), and the [`of_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1061) and [`of_dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1063) arrays stay empty. The graph the routes build is later kept in the two list heads the card carries alongside them:

```c
/* include/sound/soc.h:1070 */
	struct list_head widgets;
	struct list_head paths;
	struct list_head dapm_list;
	struct list_head dapm_dirty;
```

Those two list heads receive the graph the board's three array-and-count pairs declare, the widgets list taking the built nodes and the paths list the built edges:

```
    snd_soc_card: the board's three array+count pairs
    ─────────────────────────────────────────────────
    ┌──────────────────────────────────────────────────────┐
    │ struct snd_soc_card                                  │
    │ ──────────────────────────────────────────────────   │
    │ controls         num_controls       (kcontrols)      │
    │ dapm_widgets     num_dapm_widgets   (endpoints)      │
    │ dapm_routes      num_dapm_routes    (board edges)    │
    │ ──────────────────────────────────────────────────   │
    │ widgets  (list)   ◀── built graph nodes              │
    │ paths    (list)   ◀── built graph edges              │
    └──────────────────────────────────────────────────────┘
```

### A board endpoint is a speaker, headphone, or mic widget

Each entry of [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) template built by one of the endpoint macros, which set the widget [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to the physical kind and the register to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) because a panel jack has no backing register of its own:

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
#define SND_SOC_DAPM_SPK(wname, wevent) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_spk, .name = wname, .kcontrol_news = NULL, \
	.num_kcontrols = 0, .reg = SND_SOC_NOPM, .event = wevent, \
	.event_flags = SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD}
```

The [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518) string passed to the macro (`"Speaker"`, `"Headphone"`, `"Headset Mic"`) is what a board [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) names as its source or sink, and the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) marks the node as an output ([`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436)) or an input ([`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435)) endpoint of the graph, so the DAPM power walk knows where signal paths terminate:

```c
/* include/sound/soc-dapm.h:435 */
	snd_soc_dapm_mic,		/* microphone */
	snd_soc_dapm_hp,		/* headphones */
	snd_soc_dapm_spk,		/* speaker */
```

A board usually pairs each endpoint with a [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) entry in [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1050) so userspace can force the endpoint on or off by name. The macro builds a `"<pin> Switch"` kcontrol whose get/put act on the named widget's connected state:

```c
/* include/sound/soc-dapm.h:369 */
#define SOC_DAPM_PIN_SWITCH(xname) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname " Switch", \
	.info = snd_soc_dapm_info_pin_switch, \
	.get = snd_soc_dapm_get_pin_switch, \
	.put = snd_soc_dapm_put_pin_switch, \
	.private_value = (unsigned long)xname }
```

Each endpoint macro stamps a widget id that marks the node an output or an input, the speaker and headphone macros giving output endpoints and the mic macro an input:

```
    endpoint macro to widget id (reg always SND_SOC_NOPM)
    ─────────────────────────────────────────────────────
    ┌─────────────────────────────────────────────────────────────┐
    │ macro              id                  matched by a route as│
    │ ─────────────────  ──────────────────  ─────────────────────│
    │ SND_SOC_DAPM_SPK   snd_soc_dapm_spk    output endpoint      │
    │ SND_SOC_DAPM_HP    snd_soc_dapm_hp     output endpoint      │
    │ SND_SOC_DAPM_MIC   snd_soc_dapm_mic    input  endpoint      │
    └─────────────────────────────────────────────────────────────┘
    .name ("Speaker" / "Headphone" / "Headset Mic") is the
    string a board snd_soc_dapm_route names as source or sink;
    a paired SOC_DAPM_PIN_SWITCH adds a "<name> Switch" kcontrol
```

### A board route names a board endpoint and a codec pin

A board edge is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), the same three-string DAPM route record, and its two named widgets straddle the codec boundary. One end is a board endpoint widget the machine declared, and the other end is a pin widget the codec driver declared.

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

The [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) is `NULL` for a board route, because the connection between a jack and a codec pin is a fixed wire on the board (a permanent connection rather than a switchable mux leg). The codec pin name carries the codec's name prefix, which is how a board route addresses a specific chip among several of the same type. The [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec exports its pins as plain widget names:

```c
/* sound/soc/codecs/rt722-sdca.c:996 */
static const struct snd_soc_dapm_widget rt722_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("MIC2"),
	SND_SOC_DAPM_INPUT("LINE1"),
	SND_SOC_DAPM_INPUT("LINE2"),
```

By the time the board route runs, those names have been rewritten to `"rt722 HP"`, `"rt722 SPK"`, `"rt722 MIC2"` by the name-prefix step, so the board route `{"Headphone", NULL, "rt722 HP"}` resolves cleanly.

```
    A board route bridges a board endpoint and a codec pin
    ─────────────────────────────────────────────────────────

      board endpoint widget          codec pin widget
      (machine declares it)          (codec pin, renamed by prefix)
      ┌─────────────────────┐        ┌────────────────────────┐
      │ "Headphone"  (sink) │        │ "rt722 HP"   (source)  │
      │ snd_soc_dapm_hp     │        │ snd_soc_dapm_output    │
      └──────────┬──────────┘        └───────────┬────────────┘
                 └─────────────────┬──────────────┘
                                   ▼
                   ┌───────────────────────────┐
                   │ struct snd_soc_dapm_route │
                   └───────────────────────────┘
        { "Headphone", NULL, "rt722 HP" }
          control = NULL → a fixed board wire (no mux / switch leg)
          source "rt722 HP" = codec "HP" pin after the "rt722" prefix
          add_route resolves both names to one snd_soc_dapm_path edge
```

### snd_soc_bind_card stitches the slices in a fixed order

The whole card graph is assembled once, inside [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), and a board route can only resolve after both its endpoint widget and the codec pin it names already exist, so the order is fixed. The function first instantiates the card's own widget arrays, before any component is probed:

```c
/* sound/soc/soc-core.c:2204 */
	ret = snd_soc_dapm_new_controls(dapm, card->dapm_widgets,
					card->num_dapm_widgets);
	if (ret < 0)
		goto probe_end;
```

It then probes every component the DAI links name, and each component brings its own widgets and routes into the same graph. [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) renames the component's widgets with [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557), instantiates the component's [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and then adds the component's [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67):

```c
/* sound/soc/soc-core.c:1628 */
	component->card = card;
	soc_set_name_prefix(card, component);

	soc_init_component_debugfs(component);

	snd_soc_dapm_init(dapm, card, component);

	ret = snd_soc_dapm_new_controls(dapm,
					component->driver->dapm_widgets,
					component->driver->num_dapm_widgets);
	...
	ret = snd_soc_dapm_add_routes(dapm,
				      component->driver->dapm_routes,
				      component->driver->num_dapm_routes);
	if (ret < 0)
		goto err_probe;
```

After the components and their DAIs are probed by [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707) and the per-runtime init runs, the function adds the board's own controls and routes, then finalizes every widget:

```c
/* sound/soc/soc-core.c:2253 */
	ret = snd_soc_add_card_controls(card, card->controls,
					card->num_controls);
	if (ret < 0)
		goto probe_end;

	ret = snd_soc_dapm_add_routes(dapm, card->dapm_routes,
				      card->num_dapm_routes);
	if (ret < 0)
		goto probe_end;

	ret = snd_soc_dapm_add_routes(dapm, card->of_dapm_routes,
				      card->num_of_dapm_routes);
	if (ret < 0)
		goto probe_end;
```

The board's [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) run here, after both the card widgets (added at the top) and every codec's prefixed pin widgets (added during component probe) are present, so a board edge naming `"Headphone"` and `"rt722 HP"` finds both ends. Near the end of the bind, [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) finishes every widget once the whole graph exists, building each one's mixer or mux kcontrols and reading its initial power state:

```c
/* sound/soc/soc-core.c:2291 */
	ret = snd_soc_card_late_probe(card);
	if (ret < 0)
		goto probe_end;

	snd_soc_dapm_new_widgets(card);
	snd_soc_card_fixup_controls(card);

	ret = snd_card_register(card->snd_card);
```

According to the kernel-doc on [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322), it "Checks the codec for any new dapm widgets and creates them if found", and its body runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2090) once at the end so the assembled graph reaches a consistent power state:

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
		w->new = 1;

		dapm_mark_dirty(w, "new widget");
		dapm_debugfs_add_widget(w);
	}

	dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, NULL);
	snd_soc_dapm_mutex_unlock(card);
	return 0;
}
```

### snd_soc_dapm_add_routes turns the board table into path edges

[`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) is the one entry point that consumes a route table, whether the table is a codec's internal map or the board's cross-boundary map. It takes the card DAPM mutex and adds each [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) in turn, keeping the last error so the caller can free the partial graph:

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

Each [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100) resolves the source and sink names to live widgets and builds one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) edge between them, the generic DAPM routing mechanism. For a board route the resolution crosses the codec boundary because both the board endpoint widget and the prefixed codec pin widget are on the same [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) list by the time the board routes run, so the board endpoint and the codec pin become the two ends of one path on [`card->paths`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1071).

### soc_set_name_prefix makes a route address one chip among many

A board with two amplifiers needs to address each one separately, and the [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) mechanism gives every codec component a distinct prefix on its widget names. The machine driver supplies a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946) per codec in [`card->codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039), pairing a component name with the prefix it should wear:

```c
/* include/sound/soc.h:946 */
struct snd_soc_codec_conf {
	/*
	 * specify device either by device name, or by
	 * DT/OF node, but not both.
	 */
	struct snd_soc_dai_link_component dlc;

	/*
	 * optional map of kcontrol, widget and path name prefixes that are
	 * associated per device
	 */
	const char *name_prefix;
};
```

When [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) brings up a codec it calls [`soc_set_name_prefix()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1557), which walks [`card->codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) for an entry matching this component and copies the prefix onto it:

```c
/* sound/soc/soc-core.c:1557 */
static void soc_set_name_prefix(struct snd_soc_card *card,
				struct snd_soc_component *component)
{
	struct device_node *of_node = soc_component_to_node(component);
	const char *str;
	int ret, i;

	for (i = 0; i < card->num_configs; i++) {
		struct snd_soc_codec_conf *map = &card->codec_conf[i];

		if (snd_soc_is_matching_component(&map->dlc, component) &&
		    map->name_prefix) {
			component->name_prefix = map->name_prefix;
			return;
		}
	}
	...
}
```

The prefix is then prepended to every widget the component instantiates, so the first cs35l56's `"SPK"` becomes `"AMP1 SPK"` and the second's becomes `"AMP2 SPK"`. A board Speaker route written `{"Speaker", NULL, "AMP1 SPK"}` therefore reaches exactly one amplifier, and the two amps wired to the same `"Speaker"` board endpoint mix into it. On the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) board the prefixes are filled into [`codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1039) as the links are built, from each endpoint's [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L78):

```c
/* sound/soc/intel/boards/sof_sdw.c:891 */
		if (sof_end->name_prefix) {
			(*codec_conf)->dlc.name = sof_end->codec_name;
			(*codec_conf)->name_prefix = sof_end->name_prefix;
			(*codec_conf)++;
		}
```

Once a codec carries its prefix the setter prepends it to every pin the component makes, turning SPK into AMP1 SPK so a Speaker route lands on that one amplifier:

```
    name_prefix renames a codec's pins so a route hits one chip
    ──────────────────────────────────────────────────────────
    ┌────────────────────────────────────────┐
    │ struct snd_soc_codec_conf              │
    │   dlc        (which component)         │
    │   name_prefix  e.g. "AMP1"             │
    └───────────────────┬────────────────────┘
                        ▼ soc_set_name_prefix() (match by dlc)
    ┌────────────────────────────────────────┐
    │ struct snd_soc_component               │
    │   name_prefix = "AMP1"                 │
    └───────────────────┬────────────────────┘
                        ▼ prepended to every widget it makes
    ┌────────────────────────────────────────┐
    │ pin widget "SPK"  ─▶  "AMP1 SPK"       │
    └────────────────────────────────────────┘
    route {"Speaker", NULL, "AMP1 SPK"} now reaches amp 0 only
```

### The sof_sdw board adds its endpoints and routes per codec

The [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine leaves [`card->dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1057) and [`card->dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1059) unset, because the codec set is discovered at runtime from the ACPI machine description and differs per laptop. Instead the board widgets, controls, and routes are added per codec from the link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback, [`asoc_sdw_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L918), which runs once per runtime during the same bind. It looks up the matched codec record in [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74), adds that codec's board widgets and controls, then calls the codec's [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:918 */
int asoc_sdw_rtd_init(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	struct asoc_sdw_codec_info *codec_info;
	struct snd_soc_dai *dai;
	...
	for_each_rtd_codec_dais(rtd, i, dai) {
		...
		if (codec_info->dais[dai_index].controls) {
			ret = snd_soc_add_card_controls(card, codec_info->dais[dai_index].controls,
							codec_info->dais[dai_index].num_controls);
			...
		}
		if (codec_info->dais[dai_index].widgets) {
			ret = snd_soc_dapm_new_controls(dapm,
							codec_info->dais[dai_index].widgets,
							codec_info->dais[dai_index].num_widgets);
			...
		}

skip_add_controls_widgets:
		if (codec_info->dais[dai_index].rtd_init) {
			ret = codec_info->dais[dai_index].rtd_init(rtd, dai);
			if (ret)
				return ret;
		}
		...
	}
	...
}
```

The board endpoint widgets the rtd init adds come from the shared arrays in the SoundWire utils, which declare exactly the panel endpoints a generic headset codec and a generic speaker amp need. The jack widgets give a `"Headphone"` and a `"Headset Mic"`, the speaker widget gives a `"Speaker"`, and each pairs with a [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) control:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:20 */
static const struct snd_soc_dapm_widget generic_jack_widgets[] = {
	SND_SOC_DAPM_HP("Headphone", NULL),
	SND_SOC_DAPM_MIC("Headset Mic", NULL),
};

static const struct snd_kcontrol_new generic_jack_controls[] = {
	SOC_DAPM_PIN_SWITCH("Headphone"),
	SOC_DAPM_PIN_SWITCH("Headset Mic"),
};

static const struct snd_soc_dapm_widget generic_spk_widgets[] = {
	SND_SOC_DAPM_SPK("Speaker", NULL),
};

static const struct snd_kcontrol_new generic_spk_controls[] = {
	SOC_DAPM_PIN_SWITCH("Speaker"),
};
```

The [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) entry for the rt722-sdca part wires these arrays and the codec's [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) to the jack DAI, so the rtd init adds the jack widgets and then calls [`asoc_sdw_rt_sdca_jack_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93):

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:469 */
	{
		.part_id = 0x722,
		.name_prefix = "rt722",
		.version_id = 3,
		.dais = {
			{
				.direction = {true, true},
				.dai_name = "rt722-sdca-aif1",
				.dai_type = SOC_SDW_DAI_TYPE_JACK,
				.dailink = {SOC_SDW_JACK_OUT_DAI_ID, SOC_SDW_JACK_IN_DAI_ID},
				.init = asoc_sdw_rt_sdca_jack_init,
				.exit = asoc_sdw_rt_sdca_jack_exit,
				.rtd_init = asoc_sdw_rt_sdca_jack_rtd_init,
				.controls = generic_jack_controls,
				.num_controls = ARRAY_SIZE(generic_jack_controls),
				.widgets = generic_jack_widgets,
				.num_widgets = ARRAY_SIZE(generic_jack_widgets),
			},
			...
```

The per-link init reads the matched entry's three fields and dispatches each, adding the controls and the widgets to the card and calling the codec's rtd_init to add its routes:

```
    asoc_sdw_rtd_init fans one codec_info_list entry three ways
    ───────────────────────────────────────────────────────────
    ┌────────────────────────────────────────────┐
    │ codec_info_list[part].dais[i]              │
    │   .controls   .widgets   .rtd_init         │
    └──────────────────────────────┬─────────────┘
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ controls         │ │ widgets          │ │ routes           │
    └──────────────────┘ └──────────────────┘ └──────────────────┘
     add_card_      new_controls   rtd_init() adds
     controls()     ()             dapm routes
```

### asoc_sdw_rt_sdca_jack_rtd_init wires the rt722-sdca headset

The rt722 jack rtd init selects a per-part route map and adds it with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272). For the rt722 the map joins the board `"Headphone"` endpoint to the codec's `"rt722 HP"` output pin and the codec's `"rt722 MIC2"` input pin to the board `"Headset Mic"` endpoint:

```c
/* sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c:68 */
static const struct snd_soc_dapm_route rt722_sdca_map[] = {
	{ "Headphone", NULL, "rt722 HP" },
	{ "rt722 MIC2", NULL, "Headset Mic" },
};
```

The function picks the map by matching the component's name prefix, adds the routes, then creates the headset jack on the same runtime:

```c
/* sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c:93 */
int asoc_sdw_rt_sdca_jack_rtd_init(struct snd_soc_pcm_runtime *rtd, struct snd_soc_dai *dai)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	struct asoc_sdw_mc_private *ctx = snd_soc_card_get_drvdata(card);
	struct snd_soc_component *component;
	struct snd_soc_jack *jack;
	int ret;
	int i;

	component = dai->component;
	...
	} else if (strstr(component->name_prefix, "rt722")) {
		ret = snd_soc_dapm_add_routes(dapm, rt722_sdca_map,
					      ARRAY_SIZE(rt722_sdca_map));
	} else {
		dev_err(card->dev, "%s is not supported\n", component->name_prefix);
		return -EINVAL;
	}

	if (ret) {
		dev_err(card->dev, "rt sdca jack map addition failed: %d\n", ret);
		return ret;
	}
	...
}
```

The source `"rt722 HP"` is the codec's `"HP"` widget after the `"rt722"` prefix; the codec also declares the internal edges from its function units to that pin, so once both maps are added the full path runs from the SoundWire data port through the codec's FU and PDE widgets to `"HP"` and out to the board `"Headphone"`:

```c
/* sound/soc/codecs/rt722-sdca.c:1062 */
	{"HP", NULL, "PDE 47"},
	{"HP", NULL, "FU 42"},
	{"SPK", NULL, "PDE 23"},
	{"SPK", NULL, "FU 21"},
```

The two board edges meet those internal pins at the codec boundary, one carrying HP out to the Headphone endpoint and one bringing the Headset Mic in to MIC2:

```
    rt722_sdca_map: two edges across the codec boundary
    ───────────────────────────────────────────────────
    board endpoint           rt722 pin (after "rt722" prefix)

    ┌──────────────┐  out   ┌──────────────────────────────┐
    │ "Headphone"  │ ◀───── │ "rt722 HP" ◀ FU 42, PDE 47   │
    └──────────────┘  route └──────────────────────────────┘
    ┌──────────────┐  in    ┌──────────────────────────────┐
    │ "Headset Mic"│ ─────▶ │ "rt722 MIC2"                 │
    └──────────────┘  route └──────────────────────────────┘
    edges: {"Headphone", NULL, "rt722 HP"}
           {"rt722 MIC2", NULL, "Headset Mic"}
```

### asoc_sdw_cs_spk_rtd_init wires each cs35l56 amplifier

The cs35l56 amplifiers are codecs on their own DAI links, and each one's speaker pin is routed to the single board `"Speaker"` endpoint. The amp rtd init builds one route per amp on the runtime, with the source name computed from the amp's prefix so two amps reach the same endpoint without a name collision:

```c
/* sound/soc/sdw_utils/soc_sdw_cs_amp.c:38 */
int asoc_sdw_cs_spk_rtd_init(struct snd_soc_pcm_runtime *rtd, struct snd_soc_dai *dai)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	char widget_name[16];
	struct snd_soc_dapm_route route = { "Speaker", NULL, widget_name };
	struct snd_soc_dai *codec_dai;
	int i, ret;

	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		if (!strstr(codec_dai->name, "cs35l56"))
			continue;

		snprintf(widget_name, sizeof(widget_name), "%s SPK",
			 codec_dai->component->name_prefix);

		ret = asoc_sdw_cs35l56_volume_limit(card, codec_dai->component->name_prefix);
		if (ret)
			return ret;

		ret = snd_soc_dapm_add_routes(dapm, &route, 1);
		if (ret)
			return ret;
	}

	return 0;
}
```

The loop over the runtime's codec DAIs builds a `widget_name` of `"<prefix> SPK"` (so `"AMP1 SPK"`, `"AMP2 SPK"`) and adds a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) whose sink is the board `"Speaker"` and whose source is that amp's prefixed pin. The cs35l56 codec declares the internal edge from its `"AMP"` widget to its `"SPK"` output, so each per-amp board route extends the codec's internal path out to the shared board endpoint:

```c
/* sound/soc/codecs/cs35l56.c:314 */
	{ "SPK", NULL, "AMP" },
```

Both amps end at the one `"Speaker"` board endpoint, so the DAPM graph has two paths converging on it, and the board's single `"Speaker Switch"` control gates the endpoint for the whole stereo pair. The [`codec_info_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L74) entry for the cs35l56 part wires its [`generic_spk_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L30) and its [`rtd_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc_sdw_utils.h#L47) the same way the rt722 entry does:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:573 */
	{
		.part_id = 0x3556,
		.name_prefix = "AMP",
		.dais = {
			{
				.direction = {true, false},
				.dai_name = "cs35l56-sdw1",
				.component_name = "cs35l56",
				.dai_type = SOC_SDW_DAI_TYPE_AMP,
				.dailink = {SOC_SDW_AMP_OUT_DAI_ID, SOC_SDW_UNUSED_DAI_ID},
				.init = asoc_sdw_cs_amp_init,
				.rtd_init = asoc_sdw_cs_spk_rtd_init,
				.controls = generic_spk_controls,
				.num_controls = ARRAY_SIZE(generic_spk_controls),
				.widgets = generic_spk_widgets,
				.num_widgets = ARRAY_SIZE(generic_spk_widgets),
			},
			...
```

The same entry drives both amplifiers, so each instance wears its own prefix and its renamed SPK pin routes to the shared Speaker endpoint that one Speaker Switch gates:

```
    Two cs35l56 amps reach one "Speaker" endpoint via the name prefix
    ──────────────────────────────────────────────────────────────────
    (same codec driver; codec_conf gives each instance its own prefix)

      cs35l56 #0  (prefix "AMP1")    cs35l56 #1  (prefix "AMP2")
      ┌─────────────────────┐        ┌─────────────────────┐
      │ pin "SPK"           │        │ pin "SPK"           │
      │   renamed "AMP1 SPK"│        │   renamed "AMP2 SPK"│
      └──────────┬──────────┘        └──────────┬──────────┘
                 │ {"Speaker",NULL,             │ {"Speaker",NULL,
                 │   "AMP1 SPK"}                │   "AMP2 SPK"}
                 └───────────────┬──────────────┘
                                 ▼
                      ┌─────────────────────┐
                      │ "Speaker"           │  one board endpoint;
                      │ snd_soc_dapm_spk    │  "Speaker Switch" gates
                      └─────────────────────┘  the stereo pair
```

### The codec, amp, and cpu DAI form one routed card

The three sides of each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) carry the PCM samples and the board route table carries the analog signal, and together they make the codecs, amps, and DSP one playable card. A playback stream opens a front-end PCM, the DSP routes the samples down a SoundWire back-end link whose [`codecs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) entry is the rt722 or a cs35l56, and the codec converts them to analog at its `"HP"` or `"SPK"` pin; from there the board route carries the signal to the `"Headphone"` or `"Speaker"` endpoint, and the DAPM power walk that starts at the endpoint widget powers up every widget on the connected path back to the data port. The data-link binding resolves `"rt722-sdca-aif1"` and `"cs35l56-sdw1"` to runtime DAIs, the machine ops and the [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback host the rtd init, and the per-route path mechanics are handled by the DAPM routing layer; the assembly this page describes is the board's three arrays and the fixed order in which [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) stitches the board endpoints to the codec pins so the separate components read as one routed card.
