# DAPM widget types

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every node in an ASoC DAPM graph is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) whose first field [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) holds one value of [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), and that single value decides how the widget behaves during power sequencing, path tracing, and routing. The enum runs from [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424) at 0 through the path, supply, and stream types to the terminating [`SND_SOC_DAPM_TYPE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L464). A driver rarely assigns a value by hand; it instantiates a static template with a widget-creation macro from [`soc-dapm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h) (for example [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) for a pin, [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) for a power island, [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) for a converter), each a compound literal that fixes [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) and the type-specific fields. The core copies the template into a live widget through [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757), which switches on [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to attach the endpoint flag, the supply flag, and the power-check callback. This page catalogs every type and its constructor; the per-family pages cover how each family powers and connects.

```
    DAPM widget-type taxonomy (enum snd_soc_dapm_type)
    ──────────────────────────────────────────────────

    endpoint (board pin / generator / sink)
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_input    snd_soc_dapm_output              │
    │ snd_soc_dapm_mic      snd_soc_dapm_hp                  │
    │ snd_soc_dapm_spk      snd_soc_dapm_line                │
    │ snd_soc_dapm_siggen   snd_soc_dapm_sink                │
    └────────────────────────────────────────────────────────┘

    path-processing (route / mix / gain inside a component)
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_mux      snd_soc_dapm_demux               │
    │ snd_soc_dapm_mixer    snd_soc_dapm_mixer_named_ctl     │
    │ snd_soc_dapm_pga      snd_soc_dapm_out_drv             │
    │ snd_soc_dapm_switch                                    │
    └────────────────────────────────────────────────────────┘

    supply (power / clock / regulator / pinctrl island)
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_supply           snd_soc_dapm_micbias     │
    │ snd_soc_dapm_regulator_supply snd_soc_dapm_clock_supply│
    │ snd_soc_dapm_pinctrl          snd_soc_dapm_vmid        │
    │ snd_soc_dapm_kcontrol                                  │
    └────────────────────────────────────────────────────────┘

    stream (converters, AIF ports, DAI bindings)
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_dac      snd_soc_dapm_adc                 │
    │ snd_soc_dapm_aif_in   snd_soc_dapm_aif_out             │
    │ snd_soc_dapm_dai_in   snd_soc_dapm_dai_out             │
    │ snd_soc_dapm_dai_link                                  │
    └────────────────────────────────────────────────────────┘

    control / DSP-component (topology and machine sequencing)
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_dapm_pre      snd_soc_dapm_post                │
    │ snd_soc_dapm_buffer   snd_soc_dapm_scheduler           │
    │ snd_soc_dapm_effect   snd_soc_dapm_src                 │
    │ snd_soc_dapm_asrc     snd_soc_dapm_encoder             │
    │ snd_soc_dapm_decoder                                   │
    └────────────────────────────────────────────────────────┘

    SND_SOC_DAPM_TYPE_COUNT terminates the enum (not a widget type)
```

## SUMMARY

A DAPM widget is one [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), and its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) field of type [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) is the discriminator the DAPM core reads to decide the widget's role. The enum holds 38 named types plus the terminating [`SND_SOC_DAPM_TYPE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L464), grouping into endpoint pins ([`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424), [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425), [`snd_soc_dapm_mic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L435), [`snd_soc_dapm_hp`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L436), [`snd_soc_dapm_spk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L437)), path processors ([`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430)), supplies ([`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) and its variants), and stream converters ([`snd_soc_dapm_dac`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L433), [`snd_soc_dapm_adc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L432)).

A driver does not write the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) value directly. Each widget-creation macro expands to a `(struct snd_soc_dapm_widget){ ... }` compound literal that fixes [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) and fills the type-relevant fields, so [`SND_SOC_DAPM_PGA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) sets [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to [`snd_soc_dapm_pga`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L430) and [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) sets it to [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443). A driver places the literals in a `static const` array pointed to by [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), and the core registers each through [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932), which calls [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) once per template. That function switches on [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) twice; the first switch acquires a regulator, pinctrl, or clock for the three external-supply types, and the second sets the endpoint flag [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542), the supply flag [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541), and the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) callback. The DAI-binding types [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) and [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) have no public macro and are built by [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359), and the DSP-component types [`snd_soc_dapm_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L455) through [`snd_soc_dapm_decoder`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L461) arrive from topology files through the [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) translation table.

## SPECIFICATIONS

The [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) and the DAPM widget model are Linux kernel software constructs and have no standalone hardware specification. The widgets describe the routing and power topology of a card; the hardware blocks they represent (converters, amplifiers, microphone bias, regulators, clocks) are defined by the codec datasheet and the transport standard.

## LINUX KERNEL

### The type enum and the widget struct (soc-dapm.h)

- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the discriminator carried in every widget's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) field; 38 named values plus [`SND_SOC_DAPM_TYPE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L464)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the widget object; [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) is the first field, followed by the name, the DAPM register fields, the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541)/[`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) flags, and the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) and [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callbacks
- [`'\<enum snd_soc_dapm_direction\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L600): [`SND_SOC_DAPM_DIR_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L601) and [`SND_SOC_DAPM_DIR_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L602), the two edge sets and the basis for the endpoint flags

### Endpoint-domain macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_INPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) / [`'\<SND_SOC_DAPM_OUTPUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64): a board input or output pin; sets [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26)
- [`'\<SND_SOC_DAPM_MIC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68) / [`'\<SND_SOC_DAPM_HP\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73) / [`'\<SND_SOC_DAPM_SPK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78) / [`'\<SND_SOC_DAPM_LINE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83): a physical jack with an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback
- [`'\<SND_SOC_DAPM_SIGGEN\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52) / [`'\<SND_SOC_DAPM_SINK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56): an always-on source or sink terminating a path with no off-card connection

### Path-domain macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_PGA\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) / [`'\<SND_SOC_DAPM_OUT_DRV\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L100): a programmable-gain stage or output driver; both take a register, shift, and invert through [`SND_SOC_DAPM_INIT_REG_VAL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L89)
- [`'\<SND_SOC_DAPM_MIXER\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106) / [`'\<SND_SOC_DAPM_MIXER_NAMED_CTL\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L112): a mixer; the named-ctl form does not prefix the widget name onto its kcontrols
- [`'\<SND_SOC_DAPM_SWITCH\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124) / [`'\<SND_SOC_DAPM_MUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) / [`'\<SND_SOC_DAPM_DEMUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134): a one-control analog switch, an input selector, or an output distributor; each fixes [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) to 1
- [`'\<SND_SOC_DAPM_PGA_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L161) / [`'\<SND_SOC_DAPM_MIXER_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L175) / [`'\<SND_SOC_DAPM_MUX_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L196): the `_E` variants add an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback and [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549)
- [`'\<SND_SOC_DAPM_PGA_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L205): a PGA with a [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) ordering value within an event type

### Stream-domain macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_AIF_IN\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) / [`'\<SND_SOC_DAPM_AIF_OUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265): a digital audio interface receive or transmit port; carries a stream name and a [`channel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L569) index
- [`'\<SND_SOC_DAPM_DAC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L275) / [`'\<SND_SOC_DAPM_ADC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L286): a converter bound to a stream name
- [`'\<SND_SOC_DAPM_DAC_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) / [`'\<SND_SOC_DAPM_ADC_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290): the converters with an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback, used by the worked example
- [`'\<SND_SOC_DAPM_CLOCK_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L296): an external-clock widget; fixes [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) to [`snd_soc_dapm_clock_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702)

### Supply and generic macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_VMID\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L46): the codec bias/VMID widget, an always-on source that minimizes pops
- [`'\<SND_SOC_DAPM_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308): a generic power or clock island powered only when a downstream widget needs it
- [`'\<SND_SOC_DAPM_SUPPLY_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L212): a supply with a [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) sort key for ordering against other supplies
- [`'\<SND_SOC_DAPM_REGULATOR_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313): an external regulator; fixes [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) to [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) and stores the off delay in [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529)
- [`'\<SND_SOC_DAPM_PINCTRL\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L319): a pin-control state pair; fixes [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) to [`snd_soc_dapm_pinctrl_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677)
- [`'\<SND_SOC_DAPM_MICBIAS\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L119): a microphone-bias supply, marked DEPRECATED in favor of [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308)
- [`'\<SND_SOC_DAPM_REG\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L303): the one macro that takes the type as an argument, building a register-controlled widget of any [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423)
- [`'\<SND_SOC_DAPM_PRE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L243) / [`'\<SND_SOC_DAPM_POST\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L248): machine-specific widgets run first and last in a power sequence

### Creation and dispatch (soc-dapm.c, soc-topology.c)

- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932): create a run of widgets from a template array; loops over [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757)
- [`'\<snd_soc_dapm_new_control\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909): create a single widget from one template under the DAPM mutex
- [`'\<snd_soc_dapm_new_control_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757): copy the template and switch on [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to acquire external supplies and set [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542), [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541), and [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546)
- [`'\<snd_soc_dapm_new_dai_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359): build the [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) and [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widgets that bind a graph to a DAI; there is no public macro for these
- [`'\<snd_soc_dapm_clock_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702) / [`'\<snd_soc_dapm_regulator_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) / [`'\<snd_soc_dapm_pinctrl_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677): the fixed event handlers the three external-supply macros wire in
- [`'dapm_map':'sound/soc/soc-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158): the table mapping each `SND_SOC_TPLG_DAPM_*` topology code to its [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value

### Event-flag and endpoint constants (soc-dapm.h)

- [`'\<SND_SOC_DAPM_PRE_PMU\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) (0x1) / [`'\<SND_SOC_DAPM_POST_PMU\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) (0x2) / [`'\<SND_SOC_DAPM_PRE_PMD\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) (0x4) / [`'\<SND_SOC_DAPM_POST_PMD\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) (0x8): the [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) bits selecting when a widget's [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) runs relative to power up and down
- [`'\<SND_SOC_DAPM_EP_SOURCE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) / [`'\<SND_SOC_DAPM_EP_SINK\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608): the [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) values marking a widget as a graph source or sink
- [`'\<SND_SOC_NOPM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) (-1): the [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) value for a widget with no direct power register

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the codec widget array mixing endpoint, supply, converter, mux, and AIF types
- [`'\<rt722_sdca_fu21_event\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L804): an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback wired into a [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) DAC widget

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM concept guide, listing the widget types by power domain and the creation macros
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC architecture overview placing DAPM among the codec, platform, and machine layers
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec driver guide covering the widget array a codec registers
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the pop and click suppression the supply and VMID ordering exists to provide
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where the DAI-binding widgets connect front-end and back-end graphs

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A widget-creation macro is the interface a driver uses, and each expands to a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) compound literal whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) is fixed to one [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value. The table maps every type to the macro that produces it, or to the core function or topology code that produces it when no macro exists.

| `enum snd_soc_dapm_type` | constructor | role |
|--------------------------|-------------|------|
| `snd_soc_dapm_input` | [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) | board input pin, a graph source |
| `snd_soc_dapm_output` | [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) | board output pin, a graph sink |
| `snd_soc_dapm_mic` | [`SND_SOC_DAPM_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L68) | microphone jack with event |
| `snd_soc_dapm_hp` | [`SND_SOC_DAPM_HP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L73) | headphone jack with event |
| `snd_soc_dapm_spk` | [`SND_SOC_DAPM_SPK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L78) | speaker with event |
| `snd_soc_dapm_line` | [`SND_SOC_DAPM_LINE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L83) | line in/out jack with event |
| `snd_soc_dapm_siggen` | [`SND_SOC_DAPM_SIGGEN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L52) | always-on signal generator source |
| `snd_soc_dapm_sink` | [`SND_SOC_DAPM_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L56) | always-on path sink |
| `snd_soc_dapm_mux` | [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) | select one input of many |
| `snd_soc_dapm_demux` | [`SND_SOC_DAPM_DEMUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L134) | route input to one of many outputs |
| `snd_soc_dapm_mixer` | [`SND_SOC_DAPM_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L106) | mix several inputs together |
| `snd_soc_dapm_mixer_named_ctl` | [`SND_SOC_DAPM_MIXER_NAMED_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L112) | mixer with un-prefixed control names |
| `snd_soc_dapm_pga` | [`SND_SOC_DAPM_PGA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) | programmable gain or attenuation |
| `snd_soc_dapm_out_drv` | [`SND_SOC_DAPM_OUT_DRV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L100) | output driver stage |
| `snd_soc_dapm_switch` | [`SND_SOC_DAPM_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L124) | one-control analog switch |
| `snd_soc_dapm_dac` | [`SND_SOC_DAPM_DAC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L275) | digital-to-analog converter |
| `snd_soc_dapm_adc` | [`SND_SOC_DAPM_ADC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L286) | analog-to-digital converter |
| `snd_soc_dapm_aif_in` | [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) | audio-interface receive port |
| `snd_soc_dapm_aif_out` | [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265) | audio-interface transmit port |
| `snd_soc_dapm_dai_in` | [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) | playback-side DAI binding (core-created) |
| `snd_soc_dapm_dai_out` | [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) | capture-side DAI binding (core-created) |
| `snd_soc_dapm_dai_link` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | link between two DAI graphs |
| `snd_soc_dapm_vmid` | [`SND_SOC_DAPM_VMID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L46) | codec bias/VMID, always-on source |
| `snd_soc_dapm_supply` | [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) | generic power/clock island |
| `snd_soc_dapm_micbias` | [`SND_SOC_DAPM_MICBIAS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L119) | microphone bias supply (deprecated) |
| `snd_soc_dapm_regulator_supply` | [`SND_SOC_DAPM_REGULATOR_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313) | external regulator island |
| `snd_soc_dapm_clock_supply` | [`SND_SOC_DAPM_CLOCK_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L296) | external clock island |
| `snd_soc_dapm_pinctrl` | [`SND_SOC_DAPM_PINCTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L319) | pin-control state pair |
| `snd_soc_dapm_kcontrol` | [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) | auto-disabled kcontrol supply (core-created) |
| `snd_soc_dapm_pre` | [`SND_SOC_DAPM_PRE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L243) | machine widget run first in a sequence |
| `snd_soc_dapm_post` | [`SND_SOC_DAPM_POST`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L248) | machine widget run last in a sequence |
| `snd_soc_dapm_buffer` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | DSP/codec internal buffer (topology) |
| `snd_soc_dapm_scheduler` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | DSP/codec internal scheduler (topology) |
| `snd_soc_dapm_effect` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | DSP/codec effect component (topology) |
| `snd_soc_dapm_src` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | DSP/codec sample-rate converter (topology) |
| `snd_soc_dapm_asrc` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | DSP/codec async SRC component (topology) |
| `snd_soc_dapm_encoder` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | firmware/software audio encoder (topology) |
| `snd_soc_dapm_decoder` | [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) | firmware/software audio decoder (topology) |
| `SND_SOC_DAPM_TYPE_COUNT` | (none) | enum terminator (count of widget types) |

## DETAILS

### The id field is the discriminator

A widget is a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516), and the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value in its first field [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) is what every DAPM pass reads to decide the widget's role. The struct also carries the type-specific state the macros populate. These include the power register fields, the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) and [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) flags, the [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback, and the attached [`regulator`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L524), [`pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L525), and [`clk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L567):

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
	...
	unsigned char is_supply:1;		/* Widget is a supply type widget */
	unsigned char is_ep:2;			/* Widget is a endpoint type widget */
	...
	int (*power_check)(struct snd_soc_dapm_widget *w);

	/* external events */
	unsigned short event_flags;		/* flags to specify event types */
	int (*event)(struct snd_soc_dapm_widget*, struct snd_kcontrol *, int);
	...
};
```

The full enum lists every value [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) can hold, and the inline comments are the authoritative one-line roles. The values run from [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424) at 0 to [`snd_soc_dapm_decoder`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L461), with [`SND_SOC_DAPM_TYPE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L464) closing the list under the comment "Don't edit below this line":

```c
/* include/sound/soc-dapm.h:423 */
/* dapm widget types */
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

Each of those enum values lands in the id at the top of this struct, where it drives the is_supply and is_ep role flags and the power check while the macros fill the register word below:

```
    struct snd_soc_dapm_widget: id discriminates, fields per type
    ──────────────────────────────────────────────────────────────

    ┌───────────────────────────────────────────────────────────┐
    │ id          enum snd_soc_dapm_type   (the discriminator)  │
    │ name sname  identity strings                              │
    ├───────────────────────────────────────────────────────────┤
    │ reg shift   DAPM power-control word (which bit, where)    │
    │ mask        on_val off_val   on/off bit pattern           │
    │ power:1     current block power state                     │
    ├───────────────────────────────────────────────────────────┤
    │ is_supply:1 is_ep:2          role flags set from id       │
    │ power_check                  decision callback set from id│
    │ event_flags event            hardware hooks per power edge│
    └───────────────────────────────────────────────────────────┘
    the macros below fill reg..off_val; creation fills the
    is_supply / is_ep / power_check row by switching on id
```

### A macro is a typed compound literal

The driver-facing constructor for each type expands to a `(struct snd_soc_dapm_widget){ ... }` compound literal, fixing [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to the matching enum value and setting only the fields that type uses. The pins are the simplest, with [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) and [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) carrying no kcontrols and no power register:

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

The path-domain macros add a register, shift, and invert through the shared [`SND_SOC_DAPM_INIT_REG_VAL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L89) helper and attach the widget's kcontrols. [`SND_SOC_DAPM_PGA`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L94) takes a control count while [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) hard-codes a single control:

```c
/* include/sound/soc-dapm.h:89 */
#define SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert) \
	.reg = wreg, .mask = 1, .shift = wshift, \
	.on_val = winvert ? 0 : 1, .off_val = winvert ? 1 : 0

/* path domain */
#define SND_SOC_DAPM_PGA(wname, wreg, wshift, winvert,\
	 wcontrols, wncontrols) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_pga, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.kcontrol_news = wcontrols, .num_kcontrols = wncontrols}
```

The stream-domain converter macros set a stream name in [`sname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L519) so the widget can be matched to a PCM, and the `_E` form adds the [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback the worked example relies on:

```c
/* include/sound/soc-dapm.h:275 */
#define SND_SOC_DAPM_DAC(wname, stname, wreg, wshift, winvert) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_dac, .name = wname, .sname = stname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert) }
#define SND_SOC_DAPM_DAC_E(wname, stname, wreg, wshift, winvert, \
			   wevent, wflags)				\
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_dac, .name = wname, .sname = stname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.event = wevent, .event_flags = wflags}
```

The supply-domain macros differ in how they reach the resource they gate. The generic [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) takes a register and a caller-supplied event, but the three external-resource macros hard-wire a fixed event handler and use [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) because the resource is outside the codec register map. [`SND_SOC_DAPM_REGULATOR_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313) fixes [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) to [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) and packs the off delay into [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529):

```c
/* include/sound/soc-dapm.h:308 */
#define SND_SOC_DAPM_SUPPLY(wname, wreg, wshift, winvert, wevent, wflags) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_supply, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.event = wevent, .event_flags = wflags}
#define SND_SOC_DAPM_REGULATOR_SUPPLY(wname, wdelay, wflags)	    \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_regulator_supply, .name = wname, \
	.reg = SND_SOC_NOPM, .shift = wdelay, .event = snd_soc_dapm_regulator_event, \
	.event_flags = SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMD, \
	.on_val = wflags}
```

The [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) value [`SND_SOC_DAPM_PRE_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) bitwise-ORed with [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) runs [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) before the regulator is needed and again after it is released, so the regulator turns on ahead of the path and off behind it. [`SND_SOC_DAPM_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L303) is the one macro that does not fix the type, taking the [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value as its first argument so a driver can build a register-controlled widget of any type:

```c
/* include/sound/soc-dapm.h:303 */
#define SND_SOC_DAPM_REG(wid, wname, wreg, wshift, wmask, won_val, woff_val) \
(struct snd_soc_dapm_widget) { \
	.id = wid, .name = wname, .kcontrol_news = NULL, .num_kcontrols = 0, \
	.reg = wreg, .shift = wshift, .mask = wmask, \
	.on_val = won_val, .off_val = woff_val, }
```

Whichever macro sets them, reg, shift, and winvert resolve to a single power bit, the shift placing it and winvert fixing the on and off patterns written there:

```
    SND_SOC_DAPM_INIT_REG_VAL builds the power-control word
    ───────────────────────────────────────────────────────

    bit position in reg:        shift
                                  │
        ┌───┬───┬───┬───┬───┬───┬─▼─┬───┐
        │ 7 │ 6 │ 5 │ 4 │ 3 │ 2 │ 1 │ 0 │   one reg, mask = 1
        └───┴───┴───┴───┴───┴───┴───┴───┘
                                  └ widget power bit (mask << shift)

    winvert decides the on/off pattern written to that bit:
    ┌──────────┬──────────┬──────────┐
    │ winvert  │ on_val   │ off_val  │
    ├──────────┼──────────┼──────────┤
    │   0      │   1      │   0      │
    │   1      │   0      │   1      │
    └──────────┴──────────┴──────────┘
        reg = SND_SOC_NOPM marks a widget with no direct register
```

### The id drives setup at creation time

A driver builds a `static const` array of these literals and registers it through [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932), which copies each template into a live widget with [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757). That function is where [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) becomes behavior. The first switch acquires the external resource for the three supply types that own one, calling [`devm_regulator_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/regulator/devres.c#L51), [`devm_pinctrl_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pinctrl/core.c#L1398), or [`devm_clk_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/clk/clk-devres.c#L63):

```c
/* sound/soc/soc-dapm.c:3769 */
	switch (w->id) {
	case snd_soc_dapm_regulator_supply:
		w->regulator = devm_regulator_get(dev, widget->name);
		if (IS_ERR(w->regulator)) {
			ret = PTR_ERR(w->regulator);
			goto request_failed;
		}
		...
		break;
	case snd_soc_dapm_pinctrl:
		w->pinctrl = devm_pinctrl_get(dev);
		...
		/* set to sleep_state when initializing */
		snd_soc_dapm_pinctrl_event(w, NULL, SND_SOC_DAPM_POST_PMD);
		break;
	case snd_soc_dapm_clock_supply:
		w->clk = devm_clk_get(dev, widget->name);
		...
	default:
		break;
	}
```

The second switch is the taxonomy made executable. It sorts every [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) value into an endpoint, path/stream, or supply group and assigns [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542), [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541), and [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546). The pins [`snd_soc_dapm_input`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L424) and [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425) become sources or sinks only when the card is not fully routed, the path, stream, and DAI types share [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737), and the supply types set [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) and take [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749):

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

	case snd_soc_dapm_mux:
	case snd_soc_dapm_demux:
	...
	case snd_soc_dapm_dai_in:
		w->power_check = dapm_generic_check_power;
		break;
	case snd_soc_dapm_supply:
	case snd_soc_dapm_regulator_supply:
	case snd_soc_dapm_pinctrl:
	case snd_soc_dapm_clock_supply:
	case snd_soc_dapm_kcontrol:
		w->is_supply = 1;
		w->power_check = dapm_supply_check_power;
		break;
	default:
		w->power_check = dapm_always_on_check_power;
		break;
	}
```

The codec-bias type [`snd_soc_dapm_vmid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L440) and the generator [`snd_soc_dapm_siggen`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L449) become always-on sources through [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770), holding power independent of downstream paths, and the DSP-component types from topology fall through to `default` and are also always-on.

```
    Creation sorts each id into is_ep / is_supply / power_check
    ───────────────────────────────────────────────────────────

    ┌──────────────────────────────┬────────┬─────────┬──────────────┐
    │ widget id                    │ is_ep  │ is_sup  │ power_check  │
    ├──────────────────────────────┼────────┼─────────┼──────────────┤
    │ mic                          │ SOURCE │   0     │ generic      │
    │ input    (!fully_routed)     │ SOURCE │   0     │ generic      │
    │ hp  spk                      │ SINK   │   0     │ generic      │
    │ output   (!fully_routed)     │ SINK   │   0     │ generic      │
    │ vmid  siggen                 │ SOURCE │   0     │ always_on    │
    │ sink                         │ SINK   │   0     │ always_on    │
    │ mux demux mixer pga dac adc  │   -    │   0     │ generic      │
    │ aif_in aif_out dai_in        │   -    │   0     │ generic      │
    │ supply regulator_supply      │   -    │   1     │ supply       │
    │ pinctrl clock_supply kcontrol│   -    │   1     │ supply       │
    │ default (DSP-component)      │   -    │   0     │ always_on    │
    └──────────────────────────────┴────────┴─────────┴──────────────┘
```

### DAI-binding widgets have no public macro

The DAI-related types are created by the core. When a card binds, [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) fills a local template, sets [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) for a DAI with a playback stream name and to [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) for one with a capture stream name, running each through the same [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757):

```c
/* sound/soc/soc-dapm.c:4359 */
int snd_soc_dapm_new_dai_widgets(struct snd_soc_dapm_context *dapm,
				 struct snd_soc_dai *dai)
{
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	struct snd_soc_dapm_widget template;
	struct snd_soc_dapm_widget *w;
	...
	if (dai->driver->playback.stream_name) {
		template.id = snd_soc_dapm_dai_in;
		template.name = dai->driver->playback.stream_name;
		template.sname = dai->driver->playback.stream_name;
		...
		w = snd_soc_dapm_new_control_unlocked(dapm, &template);
		if (IS_ERR(w))
			return PTR_ERR(w);

		w->priv = dai;
		snd_soc_dai_set_widget_playback(dai, w);
	}
	...
}
```

The DSP-component types ([`snd_soc_dapm_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L455) through [`snd_soc_dapm_decoder`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L461)) are not constructed in C by a generic driver; they come from a topology binary loaded for a DSP such as Sound Open Firmware, where the [`dapm_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L158) table translates each `SND_SOC_TPLG_DAPM_*` code into the matching enum value:

```c
/* sound/soc/soc-topology.c:158 */
static const struct soc_tplg_map dapm_map[] = {
	...
	{SND_SOC_TPLG_DAPM_DAI_IN, snd_soc_dapm_dai_in},
	{SND_SOC_TPLG_DAPM_DAI_OUT, snd_soc_dapm_dai_out},
	{SND_SOC_TPLG_DAPM_DAI_LINK, snd_soc_dapm_dai_link},
	{SND_SOC_TPLG_DAPM_BUFFER, snd_soc_dapm_buffer},
	{SND_SOC_TPLG_DAPM_SCHEDULER, snd_soc_dapm_scheduler},
	{SND_SOC_TPLG_DAPM_EFFECT, snd_soc_dapm_effect},
	{SND_SOC_TPLG_DAPM_SIGGEN, snd_soc_dapm_siggen},
	{SND_SOC_TPLG_DAPM_SRC, snd_soc_dapm_src},
	{SND_SOC_TPLG_DAPM_ASRC, snd_soc_dapm_asrc},
	{SND_SOC_TPLG_DAPM_ENCODER, snd_soc_dapm_encoder},
	{SND_SOC_TPLG_DAPM_DECODER, snd_soc_dapm_decoder},
};
```

### Worked example: the rt722-sdca widget array

The Realtek RT722 declares a [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) array that uses one constructor from each domain. It opens with pins from [`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64) and [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60), continues with supply islands from [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308), then converters from [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) and [`SND_SOC_DAPM_ADC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290), selectors from [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129), and the ports from [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) and [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265):

```c
/* sound/soc/codecs/rt722-sdca.c:996 */
static const struct snd_soc_dapm_widget rt722_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("MIC2"),
	...
	SND_SOC_DAPM_SUPPLY("PDE 23", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde23_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	...
	SND_SOC_DAPM_DAC_E("FU 21", NULL, SND_SOC_NOPM, 0, 0,
		rt722_sdca_fu21_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_ADC_E("FU 36", NULL, SND_SOC_NOPM, 0, 0,
		rt722_sdca_fu36_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_MUX("ADC 22 Mux", SND_SOC_NOPM, 0, 0,
		&rt722_sdca_adc22_mux),
	...
	SND_SOC_DAPM_AIF_IN("DP1RX", "DP1 Headphone Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP2TX", "DP2 Headset Capture", 0, SND_SOC_NOPM, 0, 0),
	...
};
```

Each `"PDE n"` supply uses [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) for its register because the power-domain entity is controlled over the SoundWire control bus rather than a codec register, so the [`rt722_sdca_pde23_event`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L921) callback the macro wires writes the function instead. The [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) value [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) bitwise-ORed with [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) runs the converter and supply callbacks after the widget powers up and before it powers down. When the card binds, [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) copies these templates and [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) reads each [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), so the two [`snd_soc_dapm_output`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L425) pins become sinks, the [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) widgets set [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541), and the converter, mux, and AIF widgets take [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737).
