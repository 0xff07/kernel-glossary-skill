# DAPM passthrough widgets

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAPM passthrough widget sits in the path domain of the audio graph and processes a signal between two endpoints rather than producing or consuming it. It routes the signal ([`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426), [`snd_soc_dapm_demux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427), [`snd_soc_dapm_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L439)), mixes several signals ([`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_mixer_named_ctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L429)), or gains it ([`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430), [`snd_soc_dapm_out_drv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L431)). Each is one [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) holds the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value, declared with a one-line macro such as [`SND_SOC_DAPM_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106) or [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129), and a mixer or mux couples to its userspace controls through the [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) array and [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) count. The power walk in [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) follows only paths whose [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set, so a passthrough widget draws power only when a connected route runs through it, and the put handlers [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) and [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) re-evaluate the graph each time a control changes. The Realtek rt722-sdca codec, reached over SoundWire on an x86 ACPI platform, supplies the worked example with its three ADC input muxes.

```
    Capture path through a selector, a mixer, and a gain stage
    ──────────────────────────────────────────────────────────

       MIC2 ─┐
       LINE1 ┼─▶ ┌─────────────┐      ┌─────────────┐      ┌──────────┐
       LINE2 ┘   │    MUX      │─────▶│   MIXER     │─────▶│   PGA    │─▶ out
                 │ (snd_soc_   │      │ (snd_soc_   │      │(snd_soc_ │
                 │  dapm_mux)  │      │ dapm_mixer) │      │dapm_pga) │
                 └──────┬──────┘      └──────┬──────┘      └────┬─────┘
                        │                    │                 │
                kcontrol_news[0]      kcontrol_news[0..n]   kcontrol_news[0]
                  SOC_DAPM_ENUM       SOC_DAPM_SINGLE per     SOC_DAPM_SINGLE
                  (one selector)        input (n inputs)       (gain switch)
                        │                    │
                 put_enum_double      put_volsw per input
                 (gates one path)     (gates that input path)

    A control write flips one path->connect bit, then re-runs the power walk.
```

## SUMMARY

The path domain holds the widgets that act on a signal in transit. A mux ([`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426)) selects one input from several, a demux ([`snd_soc_dapm_demux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L427)) routes one input to one of several outputs, a switch ([`snd_soc_dapm_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L439)) gates a single path, a mixer ([`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), and the variant [`snd_soc_dapm_mixer_named_ctl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L429) that omits the widget-name prefix) sums several inputs, and a programmable gain amplifier ([`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430)) or output driver ([`snd_soc_dapm_out_drv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L431)) scales it. A driver declares each with a designated-initializer macro that stamps the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) with the matching [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value and records the control register, shift, and inversion through [`SND_SOC_DAPM_INIT_REG_VAL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L89). The base macros are [`SND_SOC_DAPM_PGA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94), [`SND_SOC_DAPM_OUT_DRV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L100), [`SND_SOC_DAPM_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106), [`SND_SOC_DAPM_MIXER_NAMED_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L112), [`SND_SOC_DAPM_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124), [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129), and [`SND_SOC_DAPM_DEMUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134).

A mixer or mux ties its controls to the widget through [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) and [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553). A mixer carries one [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) per summed input, while a mux and a switch carry one control (an enumerated [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) for the mux and a single [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) for the switch), so [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) and [`SND_SOC_DAPM_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124) hardcode [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) to 1. The power of a passthrough widget is derived from its connected paths at evaluation time. [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) powers the widget only when a complete chain of connected paths reaches both an input endpoint and an output endpoint, computed by the recursive [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487) walk that descends a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) only when its [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set. A mux selection or switch toggle sets or clears that bit through the put handlers [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) and [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453), which call [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) or [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) to re-run [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) over the whole card.

## SPECIFICATIONS

The DAPM widget graph is a Linux kernel software construct and has no standalone hardware specification. The register fields a passthrough widget toggles (the gain-mute bit of a PGA, the selector of a multiplexer) are defined by the codec datasheet.

## LINUX KERNEL

### Path-domain widget types (soc-dapm.h)

- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget-kind tag stored in [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517); the path-domain values are `snd_soc_dapm_mux` (2), `snd_soc_dapm_demux` (3), `snd_soc_dapm_mixer` (4), `snd_soc_dapm_mixer_named_ctl` (5), `snd_soc_dapm_pga` (6), `snd_soc_dapm_out_drv` (7), and `snd_soc_dapm_switch` (15)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): one graph node, carrying [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), the register control fields, the per-run [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533)/[`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) flags, the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) hook, and the [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555)/[`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) binding
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): a directed edge between a [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L496) and a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L497) widget, gated by the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit a mux or switch control flips
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): the static `{sink, control, source}` triple; the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string names the mux enum value or mixer switch that gates the path

### Base widget macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_PGA\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94): a `snd_soc_dapm_pga` widget with a register/shift/invert gain control and an explicit control array and count
- [`'\<SND_SOC_DAPM_OUT_DRV\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L100): a `snd_soc_dapm_out_drv` widget, the same shape as PGA but tagged so it powers later in the sequence
- [`'\<SND_SOC_DAPM_MIXER\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106): a `snd_soc_dapm_mixer` widget with an array of per-input controls
- [`'\<SND_SOC_DAPM_MIXER_NAMED_CTL\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L112): a mixer whose kcontrol names are used verbatim without the widget-name prefix
- [`'\<SND_SOC_DAPM_SWITCH\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124): a `snd_soc_dapm_switch` widget with exactly one gating control ([`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) fixed at 1)
- [`'\<SND_SOC_DAPM_MUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129): a `snd_soc_dapm_mux` widget with one enumerated selector ([`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) fixed at 1)
- [`'\<SND_SOC_DAPM_DEMUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134): a `snd_soc_dapm_demux` widget that routes the input to one of several outputs
- [`'\<SOC_PGA_ARRAY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L141) / [`'\<SOC_MIXER_ARRAY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L147): array forms that set [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) to `ARRAY_SIZE(wcontrols)`

### Event and sequenced macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_PGA_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L161) / [`'\<SND_SOC_DAPM_MIXER_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L175) / [`'\<SND_SOC_DAPM_MUX_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L196): the `_E` variants add an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback and an [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) mask run at power transitions
- [`'\<SND_SOC_DAPM_SWITCH_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L189): switch with an event callback
- [`'\<SND_SOC_DAPM_PGA_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L205): the `_S` sequenced variant adds a [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) sort key that orders power-up within the PGA widget type

### Control macros and payloads (soc-dapm.h, soc.h, control.h)

- [`'\<SOC_DAPM_SINGLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336): a one-bit mixer or switch control wired to [`snd_soc_dapm_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3395)/[`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453); expands through [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234)
- [`'\<SOC_DAPM_ENUM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351): a mux selector wired to [`snd_soc_dapm_get_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3542)/[`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578); expands through [`SOC_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L314)
- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231): the `private_value` payload of a [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336), holding [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231)
- [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): the `private_value` payload of a [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351), holding [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), the shifts, the [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) count, and the [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) the mux matches paths against
- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the control template an element of [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) is

### Power walk and path gating (soc-dapm.c)

- [`'\<dapm_is_connected_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487): the recursive endpoint search; descends a neighbour path only when its [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set
- [`'\<dapm_is_connected_input_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1568) / [`'\<dapm_is_connected_output_ep\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1550): the two direction wrappers
- [`'\<dapm_generic_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737): the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) hook a passthrough widget uses; powered only when both endpoint counts are non-zero
- [`'\<dapm_widget_power_check\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721): the memoizing wrapper that caches the result in [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539)
- [`'\<dapm_connect_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621): set a path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit and mark both endpoints dirty
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): the full-card power scan that applies the register writes

### Mixer and mux put handlers (soc-dapm.c)

- [`'\<snd_soc_dapm_put_volsw\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453): the set callback for a mixer or switch; records the value and calls [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680)
- [`'\<snd_soc_dapm_put_enum_double\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578): the set callback for a mux; records the item and calls [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634)
- [`'\<dapm_mixer_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680): re-gate each path attached to a mixer/switch control, then re-run the scan
- [`'\<dapm_mux_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634): connect the path whose enum text matches the new selection and disconnect the rest, then re-run the scan
- [`'\<dapm_kcontrol_set_value\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L901): store the new control value and report whether it changed
- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) / [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): instantiate the widget array and add the route array a codec registers

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the widget array declaring the ADC muxes with [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129)
- [`'rt722_sdca_adc22_mux':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L766): the [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) control bound to the "ADC 22 Mux" widget, built over [`rt722_adc22_enum`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L754)
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the route array whose triples gate each mux input by enum text

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the Dynamic Audio Power Management overview, the widget taxonomy, and the route concept
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC design overview placing DAPM among the codec, platform, and machine layers
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide, where a driver lists its widgets, controls, and routes
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the pop and click suppression DAPM provides by sequencing widget power transitions

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A passthrough widget exposes its behavior through the kcontrols in [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555), and the put callback the control macro selects is what couples a userspace write to a graph re-power. The mapping from widget kind to build macro, [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) value, control macro, and put handler is fixed.

| Widget kind | Build macro | id value | Control macro | Put handler |
|-------------|-------------|----------|---------------|-------------|
| selector (mux) | [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) | snd_soc_dapm_mux | [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) | [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) |
| de-selector (demux) | [`SND_SOC_DAPM_DEMUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134) | snd_soc_dapm_demux | [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) | [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) |
| on/off (switch) | [`SND_SOC_DAPM_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124) | snd_soc_dapm_switch | [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) |
| summer (mixer) | [`SND_SOC_DAPM_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106) | snd_soc_dapm_mixer | [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) per input | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) |
| named mixer | [`SND_SOC_DAPM_MIXER_NAMED_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L112) | snd_soc_dapm_mixer_named_ctl | [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) per input | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) |
| gain (PGA) | [`SND_SOC_DAPM_PGA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) | snd_soc_dapm_pga | [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) |
| output driver | [`SND_SOC_DAPM_OUT_DRV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L100) | snd_soc_dapm_out_drv | [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) |

A mux and a demux both carry one [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) control and run [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578); they differ in which end of the path the single connected edge sits on. A mixer carries one [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) per input so several edges into it can be connected at once, whereas a mux keeps exactly one input edge connected. A PGA and an output driver usually carry one [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) gain-mute control, or none when the gain is fixed and only the power state matters.

## DETAILS

### The widget kind tag selects the path-domain behavior

Every node of the graph is one [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), and its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) field tells the core what role the widget plays. The path-domain values sit between the endpoint pins at the top of the enum and the stream-domain converters lower down:

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
	...
	snd_soc_dapm_switch,		/* analog switch */
	...
};
```

The widget struct keeps the register control fields the macro fills, the per-run power flags the walk computes, the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) hook, and the control binding that ties a mux or mixer to its kcontrols:

```c
/* include/sound/soc-dapm.h:516 */
struct snd_soc_dapm_widget {
	enum snd_soc_dapm_type id;
	const char *name;			/* widget name */
	...
	/* dapm control */
	int reg;				/* negative reg = no direct dapm */
	unsigned char shift;			/* bits to shift */
	unsigned int mask;			/* non-shifted mask */
	unsigned int on_val;			/* on state value */
	unsigned int off_val;			/* off state value */
	unsigned char power:1;			/* block power status */
	...
	unsigned char new_power:1;		/* power from this run */
	unsigned char power_checked:1;		/* power checked this run */
	...
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
	...
	int endpoints[2];
	...
};
```

The two [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists, indexed by [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), hold the paths into and out of the widget, and [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) caches the per-direction connected-path count.

```
    struct snd_soc_dapm_widget field groups a passthrough uses
    ──────────────────────────────────────────────────────────

    ┌────────────────────────────────────────────────────┐
    │ identity                                           │
    │   id          enum snd_soc_dapm_type               │
    │   name                                             │
    ├────────────────────────────────────────────────────┤
    │ register control  (filled by the build macro)      │
    │   reg  shift  mask  on_val  off_val                │
    ├────────────────────────────────────────────────────┤
    │ per-run power  (computed by the walk)              │
    │   power:1   new_power:1   power_checked:1          │
    │   power_check(w)                                   │
    ├────────────────────────────────────────────────────┤
    │ control binding  (mixer / mux kcontrols)           │
    │   num_kcontrols   kcontrol_news[]   kcontrols[]    │
    ├────────────────────────────────────────────────────┤
    │ graph edges                                        │
    │   edges[IN]   edges[OUT]   endpoints[2]            │
    └────────────────────────────────────────────────────┘
```

### The build macros are designated initializers

A driver uses a path-domain macro that expands to a compound literal stamping the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), the name, the register control fields, and the control binding. The mixer and mux macros differ in the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) they set and in how they treat [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553):

```c
/* include/sound/soc-dapm.h:106 */
#define SND_SOC_DAPM_MIXER(wname, wreg, wshift, winvert, \
	 wcontrols, wncontrols)\
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_mixer, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.kcontrol_news = wcontrols, .num_kcontrols = wncontrols}
```

```c
/* include/sound/soc-dapm.h:129 */
#define SND_SOC_DAPM_MUX(wname, wreg, wshift, winvert, wcontrols) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_mux, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.kcontrol_news = wcontrols, .num_kcontrols = 1}
```

A mixer takes both a control array and an explicit count, because it sums an arbitrary number of inputs and carries one control per input. A mux takes only the control array and hardcodes [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) to 1, because a mux has exactly one enumerated selector regardless of how many inputs the enum lists. The [`SND_SOC_DAPM_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124) and [`SND_SOC_DAPM_DEMUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134) macros use the same one-control shape. To keep the count in step with the array, a mixer can use the array form, which derives the count with `ARRAY_SIZE`:

```c
/* include/sound/soc-dapm.h:147 */
#define SOC_MIXER_ARRAY(wname, wreg, wshift, winvert, \
	 wcontrols)\
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_mixer, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.kcontrol_news = wcontrols, .num_kcontrols = ARRAY_SIZE(wcontrols)}
```

The `_E` variants append an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback and an [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) mask so the driver runs code at power transitions, and [`SND_SOC_DAPM_PGA_S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L205) adds a [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) sort key that orders power-up among widgets of the same type, which a driver needs when one PGA stage must enable before another in a single sequence.

```
    SND_SOC_DAPM_MIXER vs SND_SOC_DAPM_MUX field stamping
    ─────────────────────────────────────────────────────

    SND_SOC_DAPM_MIXER             SND_SOC_DAPM_MUX
    ┌───────────────────────────┐  ┌───────────────────────────┐
    │ .id = snd_soc_dapm_mixer  │  │ .id = snd_soc_dapm_mux    │
    │ .kcontrol_news = wcontrols│  │ .kcontrol_news = wcontrols│
    │ .num_kcontrols = wncontrol│  │ .num_kcontrols = 1        │
    └───────────────────────────┘  └───────────────────────────┘
       one SOC_DAPM_SINGLE            one SOC_DAPM_ENUM selector
       per summed input                 regardless of inputs

    SOC_MIXER_ARRAY derives num_kcontrols = ARRAY_SIZE(wcontrols)
    SND_SOC_DAPM_SWITCH and SND_SOC_DAPM_DEMUX share the 1-control shape
```

### A control macro carries the register decode for one path gate

A mixer's per-input control and a switch's single control are both [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336), a thin wrapper over the generic [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) that fixes the get and put callbacks to the DAPM variants, and a mux's selector is [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) wrapping [`SOC_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L314):

```c
/* include/sound/soc-dapm.h:336 */
#define SOC_DAPM_SINGLE(xname, reg, shift, max, invert) \
	SOC_SINGLE_EXT(xname, reg, shift, max, invert, \
		       snd_soc_dapm_get_volsw, snd_soc_dapm_put_volsw)
#define SOC_DAPM_ENUM(xname, xenum) \
	SOC_ENUM_EXT(xname, xenum, snd_soc_dapm_get_enum_double, \
		     snd_soc_dapm_put_enum_double)
```

The control's `private_value` points at the register-decode payload, a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) for a [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) and a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) for a [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) whose [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) table the mux matches each path name against. The [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) payload names the one register bit that gates a mixer input or a switch path:

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

For a passthrough mixer the [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) name the single hardware bit that admits one summed input, [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is 1 for a plain on/off mixer or switch, and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) flips the sense when the register clears to enable. The enum payload serves the mux selector instead:

```c
/* include/sound/soc.h:1273 */
struct soc_enum {
	int reg;
	unsigned char shift_l;
	unsigned char shift_r;
	unsigned int items;
	unsigned int mask;
	const char * const *texts;
	const unsigned int *values;
	unsigned int autodisable:1;
#ifdef CONFIG_SND_SOC_TOPOLOGY
	struct snd_soc_dobj dobj;
#endif
};
```

The full field meanings of these payloads are the subject of the widget-kcontrols page; here it matters only that each control names the register field that gates one or more paths and that [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) points the widget at that control.

```
    Control macro to register-decode payload (private_value)
    ────────────────────────────────────────────────────────

    kcontrol_news[]  (struct snd_kcontrol_new)
         │
    ┌────┴───────────────────────┐
    │                            │
    │ SOC_DAPM_SINGLE            │ SOC_DAPM_ENUM
    │ (mixer leg / switch)       │ (mux selector)
    │ private_value              │ private_value
    ▼                            ▼
    ┌──────────────────────┐     ┌──────────────────────┐
    │ struct               │     │ struct soc_enum      │
    │ soc_mixer_control    │     │   reg                │
    │   reg                │     │   shift_l  shift_r   │
    │   shift              │     │   items   mask       │
    │   max   invert       │     │   texts[] matched    │
    │ (one gating bit)     │     │   per path name      │
    └──────────────────────┘     └──────────────────────┘
```

### A route triple names the control that gates an edge

The static description of an edge into or out of a passthrough widget is a [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), a `{sink, control, source}` triple a codec lists in its audio map:

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

The [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) name the two widgets the edge joins, and the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) string is what ties the edge to a path gate. For a mux the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) is the enum text that selects this input, the string [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) compares against `e->texts[mux]`; for a mixer or switch it is the kcontrol name whose [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) gates this input; and a `NULL` [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) makes a direct edge a PGA or output driver carries, always connected. The optional [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L479) callback handles supply links and is not used by an ordinary passthrough path.

### The power walk follows only connected paths

A passthrough widget has no power state to read from hardware; its power is derived from whether a complete chain of connected paths runs through it. The [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) hook is [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737), which powers the widget only when both an input endpoint and an output endpoint are reachable:

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

Both counts come from [`dapm_is_connected_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1487), one `__always_inline` body shared by the input and output direction wrappers. It takes the widget, the recursion direction, and a `fn` pointer that is itself the same routine for the reverse direction, and it returns early with a cached count from [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) when the widget was already visited this run:

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
```

The recursion gates the whole scheme on a mux or switch connection, because it descends a neighbour path only when that path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit is set:

```c
/* sound/soc/soc-dapm.c:1487 */
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
```

When a mux selects input A, only the path from A through the mux carries a set [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit; the paths from unselected inputs B and C have it clear, so the `if (path->connect)` guard skips them and they contribute nothing to the endpoint count. The result is cached in [`endpoints`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L565) for the walk so a widget reached by several routes is counted once, and [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) memoizes the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) result:

```c
/* sound/soc/soc-dapm.c:1721 */
static int dapm_widget_power_check(struct snd_soc_dapm_widget *w)
{
	if (w->power_checked)
		return w->new_power;

	if (w->force)
		w->new_power = 1;
	else
		w->new_power = w->power_check(w);

	w->power_checked = true;

	return w->new_power;
}
```

The check resolves to whether a connected leg reaches an endpoint, and with MIC2 selected only its leg carries the set connect bit while LINE1 and LINE2 stay clear:

```
    ADC 22 Mux selects MIC2: which input paths the walk descends
    ────────────────────────────────────────────────────────────

    ┌────────────┬───────────────┬──────────────────────────┐
    │ mux input  │ path->connect │ if (path->connect) walk? │
    ├────────────┼───────────────┼──────────────────────────┤
    │ MIC2  (sel)│      1        │  yes, fn() descends it   │
    │ LINE1      │      0        │  no, skipped             │
    │ LINE2      │      0        │  no, skipped             │
    └────────────┴───────────────┴──────────────────────────┘

    endpoints[dir] = sum of descended legs = 1 (MIC2 only)
    generic_check_power needs in != 0 and out != 0 to power the mux
```

### A control write re-gates the path, then re-powers the card

When userspace writes a mux selector, the ALSA core invokes [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578). It reads the chosen item, records it with [`dapm_kcontrol_set_value()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L901), and, if the value changed, hands the new item to [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634):

```c
/* sound/soc/soc-dapm.c:3578 */
int snd_soc_dapm_put_enum_double(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_dapm_context *dapm = snd_soc_dapm_kcontrol_to_dapm(kcontrol);
	struct snd_soc_card *card = dapm->card;
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;
	unsigned int *item = ucontrol->value.enumerated.item;
	...
	snd_soc_dapm_mutex_lock(card);

	change = dapm_kcontrol_set_value(kcontrol, val);
	...
	if (change || reg_change) {
		...
		ret = dapm_mux_update_power(card, kcontrol, pupdate, item[0], e);
	}

	snd_soc_dapm_mutex_unlock(card);
	...
	return change;
}
```

[`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) walks every path the kcontrol gates, sets [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) on the one path whose enum text matches the new selection and clears it on the rest, then re-runs the card-wide power scan:

```c
/* sound/soc/soc-dapm.c:2634 */
static int dapm_mux_update_power(struct snd_soc_card *card,
				 struct snd_kcontrol *kcontrol,
				 struct snd_soc_dapm_update *update,
				 int mux, struct soc_enum *e)
{
	struct snd_soc_dapm_path *path;
	int found = 0;
	bool connect;
	...
	dapm_kcontrol_for_each_path(path, kcontrol) {
		found = 1;
		/* we now need to match the string in the enum to the path */
		if (e && !(strcmp(path->name, e->texts[mux])))
			connect = true;
		else
			connect = false;

		dapm_connect_path(path, connect, "mux update");
	}

	if (found)
		dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, update);

	return found;
}
```

The bit flip is [`dapm_connect_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621), which sets [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) and marks both endpoint widgets dirty so the next walk re-checks them, returning early when the bit already holds the requested value:

```c
/* sound/soc/soc-dapm.c:2621 */
static void dapm_connect_path(struct snd_soc_dapm_path *path,
	bool connect, const char *reason)
{
	if (path->connect == connect)
		return;

	path->connect = connect;
	dapm_mark_dirty(path->source, reason);
	dapm_mark_dirty(path->sink, reason);
	dapm_path_invalidate(path);
}
```

A mixer or switch write follows the same shape through [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) and [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680). The mixer variant does not pick a single winning path; each path attached to a mixer control is gated independently, so several mixer inputs can be on at once:

```c
/* sound/soc/soc-dapm.c:2680 */
static int dapm_mixer_update_power(struct snd_soc_card *card,
				   struct snd_kcontrol *kcontrol,
				   struct snd_soc_dapm_update *update,
				   int connect, int rconnect)
{
	struct snd_soc_dapm_path *path;
	int found = 0;

	snd_soc_dapm_mutex_assert_held(card);

	/* find dapm widget path assoc with kcontrol */
	dapm_kcontrol_for_each_path(path, kcontrol) {
		...
		if (found && rconnect >= 0)
			dapm_connect_path(path, rconnect, "mixer update");
		else
			dapm_connect_path(path, connect, "mixer update");
		found = 1;
	}

	if (found)
		dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, update);

	return found;
}
```

Where [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) matches the enum text to find the one path to connect, [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) sets every path the control gates to the same `connect` value (or the second `rconnect` value for the right channel of a stereo control), then re-runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) over the card. The worked example is the Realtek RT722, whose `"ADC 22 Mux"` is declared with [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) over the [`rt722_sdca_adc22_mux`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L766) selector, and whose route triples in [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) name `MIC2`, `LINE1`, and `LINE2` as the mux inputs the enum text gates, so selecting `MIC2` connects only that path and the power walk drops the LINE inputs.

### A codec instantiates its widgets and then its routes

A codec probe turns the static arrays into a live graph in two calls. [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) walks the widget template array and instantiates each entry, so a passthrough mux, mixer, or PGA becomes a real [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) node with its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) and control binding carried over from the build macro:

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

With the nodes in place, [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) walks the route array and creates one [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) edge per triple, looking up the named [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L476) and [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L474) widgets and binding the edge to the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L475) that will gate it:

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

A route names its widgets by string, so every widget a triple references must already exist from the [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) pass, which is why that pass runs first. The RT722 codec runs exactly this pair, registering [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) and then [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043), after which a control write can flip a path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit and re-power the graph.

```
    Codec probe order: nodes before edges
    ─────────────────────────────────────

    step 1                          step 2
    ┌──────────────────────────┐    ┌──────────────────────────┐
    │ snd_soc_dapm_new_controls│    │ snd_soc_dapm_add_routes   │
    │ rt722_sdca_dapm_widgets[]│ ─▶ │ rt722_sdca_audio_map[]    │
    │ builds widget nodes      │    │ builds path edges by name │
    │ (id, kcontrol binding)   │    │ (resolves source / sink)  │
    └──────────────────────────┘    └──────────────────────────┘

    edges resolve widgets by string, so every node must exist first;
    a later control write then flips path->connect and re-powers
```
