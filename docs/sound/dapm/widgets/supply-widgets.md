# DAPM supply widgets

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAPM supply widget is a node in the codec power graph that gates a shared resource (a regulator rail, an external clock, a pin-mux state, or any register bit that enables a power island) instead of carrying audio samples, and the power engine keeps it on for exactly as long as one connected dependent still needs it. The five supply-domain widget types ([`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443), [`snd_soc_dapm_regulator_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L445), [`snd_soc_dapm_clock_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L446), [`snd_soc_dapm_pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L444), and the deprecated [`snd_soc_dapm_micbias`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L434)) all set the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) bit in [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) and all install [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) as their [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) function, so a supply reports it should be powered when at least one connected sink dependent reports the same. A supply joins the graph through routes that carry no kcontrol name, because a conditional path makes no sense for a resource that is either present or absent, and [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604) rejects a control on a supply edge. The Realtek rt722-sdca codec, an SDCA part reached over SoundWire on x86 platforms, is the worked example, declaring four [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) widgets named for SDCA Power Domain Entities and wiring each so the headphone, speaker, and microphone paths pull their power island up only while audio flows.

```
    One supply, many dependents (fan-out)
    ─────────────────────────────────────

                  ┌──────────────────────────┐
                  │   supply widget          │
                  │   id = snd_soc_dapm_*    │
                  │   is_supply = 1          │
                  │   power_check =          │
                  │   dapm_supply_check_power│
                  └────────────┬─────────────┘
                               │ sink paths (control == NULL)
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌───────────┐    ┌───────────┐     ┌───────────┐
        │ dependent │    │ dependent │     │ dependent │
        │   DAC     │    │   ADC     │     │   PGA     │
        └───────────┘    └───────────┘     └───────────┘

    supply powered   when any one dependent's power_check() returns 1
    last dependent down  ▶  supply event fires PMD, resource released
```

## SUMMARY

A supply widget exists so several audio widgets can share one power, clock, or regulator resource without each duplicating the enable and disable logic, and without the resource being toggled once per dependent. The supply-domain widget types are declared in [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423), and a codec instantiates one with a [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) macro (or the regulator, clock, pinctrl, or sequenced variant). When [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) instantiates one, it sets the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) bit and assigns [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) to [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546), and for the regulator, clock, and pinctrl kinds it also acquires the backing [`struct regulator`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L524), [`struct clk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L567), or [`struct pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L525) handle from the device.

The reference-counting effect comes from the direction of the check. [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) walks the supply's sink paths and returns 1 the instant it finds one connected dependent whose own [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) returns 1, so the supply stays powered while any dependent needs it and drops only after the last one goes down. The power engine in [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) treats a supply differently from an audio widget. A supply that should be on raises its DAPM context only to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) rather than to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419), and [`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176) skips a supply's sink paths when propagating a power change to neighbours, because a supply gates its dependents but is not part of their signal flow. The regulator, clock, and pinctrl kinds carry a built-in event handler ([`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642), [`snd_soc_dapm_clock_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702), [`snd_soc_dapm_pinctrl_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677)) that fires on the power-up and power-down edges, so the actual [`regulator_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/regulator/core.c#L3194), [`clk_prepare_enable()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/clk.h#L1165), or [`pinctrl_select_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pinctrl/core.c#L1377) call happens at the moment the engine decides the supply's power state changed.

## SPECIFICATIONS

The DAPM supply widget is a Linux kernel software construct and has no standalone hardware specification. The resources a supply gates are governed by their own kernel frameworks. An [`SND_SOC_DAPM_REGULATOR_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313) drives a rail through the regulator framework and an [`SND_SOC_DAPM_CLOCK_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L296) drives an input through the common clock framework. In the rt722-sdca worked example each [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) maps to an SDCA Power Domain Entity.

## LINUX KERNEL

### Widget types and the supply bit (soc-dapm.h)

- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget type tag; the supply-domain members are [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443), [`snd_soc_dapm_regulator_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L445), [`snd_soc_dapm_clock_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L446), [`snd_soc_dapm_pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L444), and the deprecated [`snd_soc_dapm_micbias`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L434)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the widget instance; the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) bit flags it, [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) decides whether it is on, and [`regulator`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L524), [`clk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L567), [`pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L525), and [`priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523) hold the backing resource
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): one edge; its [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) bit marks a supply edge and its [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback gates the supply conditionally
- [`'\<struct snd_soc_dapm_pinctrl_priv\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L595): the [`active_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L596) and [`sleep_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L597) names a pinctrl widget switches between

### Supply widget macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308): the generic supply, taking a register, shift, invert, event handler, and event flags
- [`'\<SND_SOC_DAPM_SUPPLY_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L212): the same with an explicit [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) ordering value to sequence supplies within the power passes
- [`'\<SND_SOC_DAPM_REGULATOR_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313): a regulator-backed supply; sets [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), stores the disable delay in [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529), and fixes the handler to [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642)
- [`'\<SND_SOC_DAPM_CLOCK_SUPPLY\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L296): a clock-backed supply; sets [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) to [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) and the handler to [`snd_soc_dapm_clock_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702)
- [`'\<SND_SOC_DAPM_PINCTRL\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L319): a pinctrl-backed supply; stores a [`struct snd_soc_dapm_pinctrl_priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L595) in [`priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523) and the handler to [`snd_soc_dapm_pinctrl_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677)
- [`'\<SND_SOC_DAPM_MICBIAS\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L119): the deprecated microphone-bias widget that new code replaces with [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308)
- [`'\<SND_SOC_DAPM_REGULATOR_BYPASS\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L402): the [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531) flag that makes a regulator supply allow bypass while it is off

### Power decision (soc-dapm.c)

- [`'\<dapm_supply_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749): the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) installed on every supply; returns 1 when one connected sink dependent needs power
- [`'\<dapm_widget_power_check\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721): caches and returns a widget's power decision by calling its own [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546)
- [`'\<dapm_generic_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737): the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) for an ordinary audio widget, requiring a complete input-to-output path
- [`'\<dapm_power_one_widget\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176): runs the check for one dirty widget and queues it up or down; skips a supply's sink paths when propagating to neighbours
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): the power engine; a powered supply only raises the context to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417)

### Supply event handlers (soc-dapm.c)

- [`'\<snd_soc_dapm_regulator_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642): on power-up calls [`regulator_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/regulator/core.c#L3194); on power-down calls [`regulator_disable_deferred()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/regulator/core.c#L3441) with the delay from [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529)
- [`'\<snd_soc_dapm_clock_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702): on power-up calls [`clk_prepare_enable()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/clk.h#L1165); on power-down calls [`clk_disable_unprepare()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/clk.h#L1180)
- [`'\<snd_soc_dapm_pinctrl_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677): looks up [`active_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L596) or [`sleep_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L597) and applies it with [`pinctrl_select_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pinctrl/core.c#L1377)

### Route attachment and creation (soc-dapm.c)

- [`'\<dapm_add_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604): builds one edge; marks it [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) when either end is a supply, and rejects a kcontrol on a supply edge
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): adds an array of [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) records, supply edges included
- [`'\<snd_soc_dapm_new_control_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757): instantiates a widget; sets [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) and [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) for the supply kinds and acquires the regulator, clock, or pinctrl handle
- [`'\<snd_soc_dapm_new_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322): finalizes new widgets and runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once to settle initial power

### Path iterators (soc-dapm.h)

- [`'\<snd_soc_dapm_widget_for_each_sink_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L741): iterates the edges where the widget is the source, the dependents a supply feeds
- [`'\<snd_soc_dapm_widget_for_each_source_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L750): iterates the edges where the widget is the sink

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the widget array; the four [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) entries "PDE 23", "PDE 47", "PDE 11", "PDE 12" begin at line 1005
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the route table; each PDE supply is wired to its dependents with no control name
- [`'\<rt722_sdca_pde47_event\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L896): the event handler that writes the SDCA power-state control on the power-up and power-down edges

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM concept and the widget-type catalog, including the supply and regulator-supply domains
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide, where a driver declares its widget and route tables
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the power-sequencing rationale the supply ordering and the bias-level handling serve

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A codec declares a supply widget with one of the supply macros and connects it with routes whose middle element is NULL. The macro chooses the widget type, the resource acquisition, and the event handler, while the route table decides which audio widgets the supply gates. The mapping from macro to type, backing resource, and handler is fixed.

| Macro | enum type | Backing resource | Built-in event handler |
|-------|-----------|------------------|------------------------|
| [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) | snd_soc_dapm_supply | a register bit, or none | caller-supplied |
| [`SND_SOC_DAPM_SUPPLY_S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L212) | snd_soc_dapm_supply | a register bit, or none | caller-supplied |
| [`SND_SOC_DAPM_REGULATOR_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L313) | snd_soc_dapm_regulator_supply | [`struct regulator`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L524) | [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) |
| [`SND_SOC_DAPM_CLOCK_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L296) | snd_soc_dapm_clock_supply | [`struct clk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L567) | [`snd_soc_dapm_clock_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702) |
| [`SND_SOC_DAPM_PINCTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L319) | snd_soc_dapm_pinctrl | [`struct pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L525) | [`snd_soc_dapm_pinctrl_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677) |
| [`SND_SOC_DAPM_MICBIAS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L119) | snd_soc_dapm_micbias | a register bit | caller-supplied (deprecated) |

[`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) builds a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L443) widget from a register, shift, invert, an optional [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback, and the [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) that select which edges call it; when the register is [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) the widget relies entirely on its event handler. [`SND_SOC_DAPM_SUPPLY_S`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L212) adds a [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) argument so a codec can order one supply before another within the same power pass. The three resource-backed macros fix their handler and use [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), and [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) acquires the handle by widget name. [`SND_SOC_DAPM_MICBIAS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L119) is deprecated in favor of a plain supply.

## DETAILS

### The supply-domain widget types

A widget's behaviour is selected by its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), a value of [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423). Five values name the supply domain, and the comments spell out what each gates:

```c
/* include/sound/soc-dapm.h:423 */
enum snd_soc_dapm_type {
	snd_soc_dapm_input = 0,		/* input pin */
	...
	snd_soc_dapm_micbias,		/* microphone bias (power) - DEPRECATED: use snd_soc_dapm_supply */
	...
	snd_soc_dapm_supply,		/* power/clock supply */
	snd_soc_dapm_pinctrl,		/* pinctrl */
	snd_soc_dapm_regulator_supply,	/* external regulator */
	snd_soc_dapm_clock_supply,	/* external clock */
	...
};
```

The widget instance carrying one of these types is [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516). The fields that make a supply work are the [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) bit, the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) pointer, the [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) pointer with its [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549), and the [`regulator`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L524), [`pinctrl`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L525), [`clk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L567), and [`priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523) handles for the gated resource:

```c
/* include/sound/soc-dapm.h:516 */
struct snd_soc_dapm_widget {
	enum snd_soc_dapm_type id;
	const char *name;			/* widget name */
	...
	void *priv;				/* widget specific data */
	struct regulator *regulator;		/* attached regulator */
	struct pinctrl *pinctrl;		/* attached pinctrl */

	/* dapm control */
	int reg;				/* negative reg = no direct dapm */
	unsigned char shift;			/* bits to shift */
	unsigned int mask;			/* non-shifted mask */
	unsigned int on_val;			/* on state value */
	unsigned int off_val;			/* off state value */
	...
	unsigned char is_supply:1;		/* Widget is a supply type widget */
	...
	int (*power_check)(struct snd_soc_dapm_widget *w);

	/* external events */
	unsigned short event_flags;		/* flags to specify event types */
	int (*event)(struct snd_soc_dapm_widget*, struct snd_kcontrol *, int);
	...
	struct clk *clk;

	int channel;
};
```

The same fields sort into rows the supply leans on, the is_supply flag and its power check, the register bits (NOPM when the resource is off-map), the event hooks, and one backing handle per kind:

```
    struct snd_soc_dapm_widget fields a supply uses
    ───────────────────────────────────────────────

    ┌──────────────────────────────────────────────┐
    │ identity                                     │
    │   id    enum snd_soc_dapm_type               │
    │   name  (regulator/clock get handle by name) │
    ├──────────────────────────────────────────────┤
    │ supply flag and decision                     │
    │   is_supply : 1                              │
    │   power_check  = dapm_supply_check_power     │
    ├──────────────────────────────────────────────┤
    │ register control  (SND_SOC_NOPM when none)   │
    │   reg  shift  mask  on_val  off_val          │
    ├──────────────────────────────────────────────┤
    │ event edge hooks                             │
    │   event_flags    event(w, kcontrol, ev)      │
    ├──────────────────────────────────────────────┤
    │ backing resource handle  (one per kind)      │
    │   regulator    clk    pinctrl    priv        │
    └──────────────────────────────────────────────┘
```

### Instantiation sets the supply bit and the power check

[`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) turns a static template into a live widget. It starts by copying the template with [`dapm_cnew_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L355), then runs two switches on [`w->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) before linking the widget into the card's list and marking it [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535):

```c
/* sound/soc/soc-dapm.c:3757 */
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

	switch (w->id) {
	...
	}

	switch (w->id) {
	...
	}

	w->dapm = dapm;
	INIT_LIST_HEAD(&w->list);
	INIT_LIST_HEAD(&w->dirty);
	/* see for_each_card_widgets */
	list_add_tail(&w->list, &dapm->card->widgets);

	dapm_for_each_direction(dir) {
		INIT_LIST_HEAD(&w->edges[dir]);
		w->endpoints[dir] = -1;
	}

	/* machine layer sets up unconnected pins and insertions */
	w->connected = 1;
	return w;

request_failed:
	dev_err_probe(dev, ret, "ASoC: Failed to request %s\n",
		      w->name);
	kfree_const(w->name);
	kfree_const(w->sname);
	kfree(w);
cnew_failed:
	return ERR_PTR(ret);
}
```

The two switches expand below. The first acquires the backing resource for the regulator, pinctrl, and clock kinds:

```c
/* sound/soc/soc-dapm.c:3771 */
	switch (w->id) {
	case snd_soc_dapm_regulator_supply:
		w->regulator = devm_regulator_get(dev, widget->name);
		if (IS_ERR(w->regulator)) {
			ret = PTR_ERR(w->regulator);
			goto request_failed;
		}

		if (w->on_val & SND_SOC_DAPM_REGULATOR_BYPASS) {
			ret = regulator_allow_bypass(w->regulator, true);
			if (ret != 0)
				dev_warn(dev,
					 "ASoC: Failed to bypass %s: %d\n",
					 w->name, ret);
		}
		break;
	case snd_soc_dapm_pinctrl:
		w->pinctrl = devm_pinctrl_get(dev);
		if (IS_ERR(w->pinctrl)) {
			ret = PTR_ERR(w->pinctrl);
			goto request_failed;
		}

		/* set to sleep_state when initializing */
		snd_soc_dapm_pinctrl_event(w, NULL, SND_SOC_DAPM_POST_PMD);
		break;
	case snd_soc_dapm_clock_supply:
		w->clk = devm_clk_get(dev, widget->name);
		if (IS_ERR(w->clk)) {
			ret = PTR_ERR(w->clk);
			goto request_failed;
		}
		break;
	default:
		break;
	}
```

The pinctrl case applies the sleep state immediately, so the pins are parked before any audio runs. The second switch is where the five supply types converge. They share one case label, set [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) to 1, and install [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749), while an ordinary audio widget gets [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770) or [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737):

```c
/* sound/soc/soc-dapm.c:3863 */
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
```

The deprecated [`snd_soc_dapm_micbias`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L434) does not appear in this list; it falls into the audio-widget group and receives [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737), which is why new codecs declare a microphone bias as a plain [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308).

### The supply power check counts dependents

[`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) is the function that produces the reference-counting effect. It walks the supply's sink paths (the edges where the supply is the source) with [`snd_soc_dapm_widget_for_each_sink_path()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L741), and the moment one connected dependent's [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) returns 1, it returns 1:

```c
/* sound/soc/soc-dapm.c:1749 */
/* Check to see if a power supply is needed */
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

The [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback, when a route supplies one, lets a machine skip a dependent that is wired but not currently routed. Because the loop returns on the first dependent that needs power, the supply stays up while any one of N dependents is up, and only when the last dependent's check returns 0 does the loop fall through to 0. The per-dependent decision is cached in [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) so each widget is evaluated once per run:

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

The contrast with an audio widget is the direction of the test. [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) requires a complete path, a connection from an input endpoint and to an output endpoint, before it powers the widget. A supply has no input side and is never part of a signal path, so it cannot use the generic check; it asks only whether something downstream needs it.

### The generic check requires a complete path

[`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) is the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) an ordinary audio widget receives, and it shows by contrast why a supply needs its own check. It powers the widget only when it is connected both to an input endpoint and to an output endpoint, so an audio widget stranded on either side stays down:

```c
/* sound/soc/soc-dapm.c:1737 */
/* Generic check to see if a widget should be powered. */
static int dapm_generic_check_power(struct snd_soc_dapm_widget *w)
{
	int in, out;

	DAPM_UPDATE_STAT(w, power_checks);

	in  = dapm_is_connected_input_ep(w, NULL, NULL);
	out = dapm_is_connected_output_ep(w, NULL, NULL);
	return out != 0 && in != 0;
}
```

[`dapm_is_connected_input_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1568) and [`dapm_is_connected_output_ep()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1550) walk the source and sink edges to the endpoints, so a `1` from both means audio can actually flow through the widget. A supply has neither an input endpoint nor a place in any signal path, so this test would always return 0 for it; that is why [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) installs [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) on a supply instead. The deprecated [`snd_soc_dapm_micbias`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L434) keeps this generic check, which is the historical reason a micbias had to sit on a complete path rather than gate dependents the way a real supply does.

```
    Two power_check directions: audio widget vs supply
    ──────────────────────────────────────────────────

    dapm_generic_check_power      dapm_supply_check_power
    (ordinary audio widget)       (supply widget)
    ┌─────────────────────────┐   ┌─────────────────────────┐
    │ in  = connected_input   │   │ for each sink path:     │
    │ out = connected_output  │   │   if a dependent's      │
    │                         │   │   power_check() == 1    │
    │ power = in != 0         │   │     return 1            │
    │     and out != 0        │   │ return 0                │
    └─────────────────────────┘   └─────────────────────────┘
       needs a complete            needs only one downstream
       input-to-output path        dependent that wants power
```

### Supply edges carry no control and never propagate inward

A supply attaches to its dependents through [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604), which validates the edge, allocates a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486), tags it when either end is a supply, and links it into the card's path list:

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

	...

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

	/* connect static paths */
	if (control == NULL) {
		path->connect = 1;
	} else {
		...
	}

	list_add(&path->list, &dapm->card->paths);

	dapm_for_each_direction(dir)
		list_add(&path->list_node[dir], &path->node[dir]->edges[dir]);

	dapm_for_each_direction(dir) {
		dapm_update_widget_flags(path->node[dir]);
		dapm_mark_dirty(path->node[dir], "Route added");
	}

	if (snd_soc_card_is_instantiated(dapm->card) && path->connect)
		dapm_path_invalidate(path);

	return 0;
err:
	kfree(path);
	return ret;
}
```

The [`path->is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L505) tag set here tells the rest of the engine to treat a supply edge specially, and because a supply route always passes `control == NULL` the path takes the [`path->connect = 1`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) branch with no kcontrol attached. Before any of that the validation guards run. A supply edge may not carry a kcontrol, and the [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L507) callback is allowed only when the source is a supply:

```c
/* sound/soc/soc-dapm.c:617 */
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

When either end is a supply the edge is tagged so the rest of the engine recognizes it, and the other half of keeping a supply out of the signal flow is in [`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176). The engine calls this once for each dirty widget. It asks [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) for the new power state, returns early when nothing changed, propagates the change to neighbours, and finally queues the widget on the up or down list with [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809):

```c
/* sound/soc/soc-dapm.c:2176 */
static void dapm_power_one_widget(struct snd_soc_dapm_widget *w,
				  struct list_head *up_list,
				  struct list_head *down_list)
{
	struct snd_soc_dapm_path *path;
	int power;

	switch (w->id) {
	case snd_soc_dapm_pre:
		power = 0;
		goto end;
	case snd_soc_dapm_post:
		power = 1;
		goto end;
	default:
		break;
	}

	power = dapm_widget_power_check(w);

	if (w->power == power)
		return;

	trace_snd_soc_dapm_widget_power(w, power);

	/*
	 * If we changed our power state perhaps our neigbours
	 * changed also.
	 */
	snd_soc_dapm_widget_for_each_source_path(w, path)
		dapm_widget_set_peer_power(path->source, power, path->connect);

	/*
	 * Supplies can't affect their outputs, only their inputs
	 */
	if (!w->is_supply)
		snd_soc_dapm_widget_for_each_sink_path(w, path)
			dapm_widget_set_peer_power(path->sink, power, path->connect);

end:
	if (power)
		dapm_seq_insert(w, up_list, true);
	else
		dapm_seq_insert(w, down_list, false);
}
```

The neighbour propagation is where a supply differs from an audio widget. When a widget changes power state the engine propagates the change to its neighbours, but for a supply it propagates only inward, to the supply's own sources, and skips the sink side:

```c
/* sound/soc/soc-dapm.c:2202 */
	snd_soc_dapm_widget_for_each_source_path(w, path)
		dapm_widget_set_peer_power(path->source, power, path->connect);

	/*
	 * Supplies can't affect their outputs, only their inputs
	 */
	if (!w->is_supply)
		snd_soc_dapm_widget_for_each_sink_path(w, path)
			dapm_widget_set_peer_power(path->sink, power, path->connect);
```

According to the comment, a supply cannot affect its outputs, only its inputs, so toggling a supply does not drag its dependents up or down. The dependents decide for themselves whether they need audio, and the supply follows them.

```
    dapm_power_one_widget: which peers a supply marks dirty
    ──────────────────────────────────────────────────────

         source peers                       sink peers
       (supply's inputs)                 (the dependents)
      ┌────────────────┐    ┌────────┐    ┌────────────────┐
      │ marked dirty   │ ◀──┤ supply │    │ NOT propagated │
      │ for_each_      │    │ w      │    │ skipped when   │
      │ source_path    │    │ power  │    │ w->is_supply   │
      └────────────────┘    └────────┘    └────────────────┘
            propagates            (sink side has no arrow:
            inward only            a supply never drives it)

      an audio widget propagates BOTH ways; a supply only inward,
      so a supply follows its dependents and never drives them
```

### Routes feed the supply its dependents

A codec hands its route table, including the supply edges, to [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272). It takes the lock once and adds each [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) in turn through [`snd_soc_dapm_add_route()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3100), which resolves the named source and sink widgets and calls [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604):

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

Each route names a sink, a source, and a control. For a supply edge the source is the supply and the control is NULL, so the dependent named as the sink becomes one of the sink paths [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) later walks. The loop keeps the first error but tries the remaining routes, and on failure the docstring directs the caller to free the partial graph when it tears the card down.

### The engine powers a supply only to STANDBY

[`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) is the engine itself. It resets every context's target bias, runs [`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176) over the dirty list to build the up and down sequences, raises each context's target bias for the widgets that will be on, and then runs the down sequence before the up sequence so power comes off before it goes on:

```c
/* sound/soc/soc-dapm.c:2252 */
static int dapm_power_widgets(struct snd_soc_card *card, int event,
			      struct snd_soc_dapm_update *update)
{
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	struct snd_soc_dapm_widget *w;
	struct snd_soc_dapm_context *d;
	LIST_HEAD(up_list);
	LIST_HEAD(down_list);
	...
	dapm_reset(card);

	...
	list_for_each_entry(w, &card->dapm_dirty, dirty) {
		dapm_power_one_widget(w, &up_list, &down_list);
	}

	for_each_card_widgets(card, w) {
		...
		if (w->new_power) {
			d = w->dapm;
			...
			switch (w->id) {
			...
			}
		}
	}
	...
	/* Power down widgets first; try to avoid amplifying pops. */
	dapm_seq_run(card, &down_list, event, false);

	dapm_widget_update(card, update);

	/* Now power up. */
	dapm_seq_run(card, &up_list, event, true);
	...
	return 0;
}
```

The target-bias switch inside that loop gives the supply kinds a lighter treatment than an audio widget. A supply that should be on raises its context only to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417), whereas a powered audio widget demands [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419):

```c
/* sound/soc/soc-dapm.c:2316 */
			switch (w->id) {
			case snd_soc_dapm_siggen:
			case snd_soc_dapm_vmid:
				break;
			case snd_soc_dapm_supply:
			case snd_soc_dapm_regulator_supply:
			case snd_soc_dapm_pinctrl:
			case snd_soc_dapm_clock_supply:
			case snd_soc_dapm_micbias:
				if (d->target_bias_level < SND_SOC_BIAS_STANDBY)
					d->target_bias_level = SND_SOC_BIAS_STANDBY;
				break;
			default:
				d->target_bias_level = SND_SOC_BIAS_ON;
				break;
			}
```

This is the one place the deprecated [`snd_soc_dapm_micbias`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L434) is grouped with the real supplies, for bias-level purposes only; its power decision still comes from the generic audio check.

```
    target_bias_level a powered widget raises its context to
    ────────────────────────────────────────────────────────

    ┌────────────────────────────────────┬─────────────────────┐
    │ widget id (when new_power == 1)    │ raises context to   │
    ├────────────────────────────────────┼─────────────────────┤
    │ snd_soc_dapm_siggen                │ (no raise)          │
    │ snd_soc_dapm_vmid                  │ (no raise)          │
    ├────────────────────────────────────┼─────────────────────┤
    │ snd_soc_dapm_supply                │                     │
    │ snd_soc_dapm_regulator_supply      │ SND_SOC_BIAS_       │
    │ snd_soc_dapm_pinctrl               │ STANDBY             │
    │ snd_soc_dapm_clock_supply          │ (floor only)        │
    │ snd_soc_dapm_micbias               │                     │
    ├────────────────────────────────────┼─────────────────────┤
    │ default (any audio widget)         │ SND_SOC_BIAS_ON     │
    └────────────────────────────────────┴─────────────────────┘
```

### Regulator, clock, and pinctrl handlers do the actual enable

For the resource-backed kinds the macro wires a built-in handler with [`SND_SOC_DAPM_PRE_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) and [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) flags, so it runs just before the supply powers up and just after it powers down. [`snd_soc_dapm_regulator_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1642) maps the edge to the regulator framework, enabling on the up edge and deferring the disable by the delay in [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529):

```c
/* sound/soc/soc-dapm.c:1642 */
int snd_soc_dapm_regulator_event(struct snd_soc_dapm_widget *w,
				 struct snd_kcontrol *kcontrol, int event)
{
	struct device *dev = snd_soc_dapm_to_dev(w->dapm);
	int ret;

	dapm_async_complete(w->dapm);

	if (SND_SOC_DAPM_EVENT_ON(event)) {
		if (w->on_val & SND_SOC_DAPM_REGULATOR_BYPASS) {
			ret = regulator_allow_bypass(w->regulator, false);
			if (ret != 0)
				dev_warn(dev,
					 "ASoC: Failed to unbypass %s: %d\n",
					 w->name, ret);
		}

		return regulator_enable(w->regulator);
	} else {
		if (w->on_val & SND_SOC_DAPM_REGULATOR_BYPASS) {
			ret = regulator_allow_bypass(w->regulator, true);
			if (ret != 0)
				dev_warn(dev,
					 "ASoC: Failed to bypass %s: %d\n",
					 w->name, ret);
		}

		return regulator_disable_deferred(w->regulator, w->shift);
	}
}
```

[`SND_SOC_DAPM_EVENT_ON()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L398) tests for a power-up edge. The [`SND_SOC_DAPM_REGULATOR_BYPASS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L402) flag in [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531) makes the handler unbypass the rail before enabling and re-bypass after disabling. [`snd_soc_dapm_clock_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1702) is the same shape against the clock framework:

```c
/* sound/soc/soc-dapm.c:1702 */
int snd_soc_dapm_clock_event(struct snd_soc_dapm_widget *w,
			     struct snd_kcontrol *kcontrol, int event)
{
	if (!w->clk)
		return -EIO;

	dapm_async_complete(w->dapm);

	if (SND_SOC_DAPM_EVENT_ON(event)) {
		return clk_prepare_enable(w->clk);
	} else {
		clk_disable_unprepare(w->clk);
		return 0;
	}

	return 0;
}
```

[`snd_soc_dapm_pinctrl_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1677) reads the two state names from the [`struct snd_soc_dapm_pinctrl_priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L595) in [`priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523), picks [`active_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L596) on the up edge and [`sleep_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L597) on the down edge, and applies it:

```c
/* sound/soc/soc-dapm.c:1677 */
int snd_soc_dapm_pinctrl_event(struct snd_soc_dapm_widget *w,
			       struct snd_kcontrol *kcontrol, int event)
{
	struct snd_soc_dapm_pinctrl_priv *priv = w->priv;
	struct pinctrl *p = w->pinctrl;
	struct pinctrl_state *s;

	if (!p || !priv)
		return -EIO;

	if (SND_SOC_DAPM_EVENT_ON(event))
		s = pinctrl_lookup_state(p, priv->active_state);
	else
		s = pinctrl_lookup_state(p, priv->sleep_state);

	if (IS_ERR(s))
		return PTR_ERR(s);

	return pinctrl_select_state(p, s);
}
```

In all three handlers the resource enabling happens once at the first power-up edge and the disable once at the last power-down edge, because [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) flips the supply's power state only at those two boundaries rather than once per dependent.

```
    Built-in event handler: action per power edge
    ─────────────────────────────────────────────

    ┌──────────────────────────┬──────────────────┬──────────────────┐
    │ handler                  │ power-up edge    │ power-down edge  │
    ├──────────────────────────┼──────────────────┼──────────────────┤
    │ regulator_event          │ regulator_enable │ regulator_       │
    │                          │                  │ disable_deferred │
    ├──────────────────────────┼──────────────────┼──────────────────┤
    │ clock_event              │ clk_prepare_     │ clk_disable_     │
    │                          │ enable           │ unprepare        │
    ├──────────────────────────┼──────────────────┼──────────────────┤
    │ pinctrl_event            │ select           │ select           │
    │                          │ active_state     │ sleep_state      │
    └──────────────────────────┴──────────────────┴──────────────────┘

    SND_SOC_DAPM_EVENT_ON(event) selects the up branch in each handler
```

### New widgets settle their initial power once

After a codec has created its widgets and routes, [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) finalizes them. It walks the card's widget list, allocates kcontrols and builds the mixer, mux, or pga state for the kinds that need it, reads each widget's initial power from its register, marks every widget dirty, and then runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) a single time so the whole graph settles to a consistent power state:

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
		switch(w->id) {
		...
		default:
			break;
		}

		/* Read the initial power state from the device */
		if (w->reg >= 0) {
			val = dapm_read(w->dapm, w->reg);
			val = val >> w->shift;
			val &= w->mask;
			if (val == w->on_val)
				w->power = 1;
		}

		w->new = 1;

		dapm_mark_dirty(w, "new widget");
		dapm_debugfs_add_widget(w);
	}

	dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, NULL);
	snd_soc_dapm_mutex_unlock(card);
	return 0;
}
```

The supply kinds skip the initial register read, because a supply created from one of the resource-backed macros, or the rt722-sdca PDE supplies created with [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), has [`w->reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) below zero and no on-state bit to sample. The single [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) call at the end is what drives every supply's [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) for the first time, so a supply with no active dependent is left off until a stream pulls one up.

### Worked example: rt722-sdca PDE supply widgets

The Realtek RT722 models its power islands as SDCA Power Domain Entities. Its widget array declares four [`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) widgets, one per PDE, each with [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) for its register because the power state is written by a custom event handler over the SoundWire control bus:

```c
/* sound/soc/codecs/rt722-sdca.c:1005 */
	SND_SOC_DAPM_SUPPLY("PDE 23", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde23_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_SUPPLY("PDE 47", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde47_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_SUPPLY("PDE 11", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde11_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_SUPPLY("PDE 12", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde12_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
```

The route table wires each PDE to its dependents with no control name, marking them supply edges. The headphone "HP" depends on "PDE 47" and the function unit "FU 42", and the speaker "SPK" depends on "PDE 23" and "FU 21":

```c
/* sound/soc/codecs/rt722-sdca.c:1054 */
	{"FU 36", NULL, "PDE 12"},
	{"FU 36", NULL, "ADC 22 Mux"},
	{"FU 113", NULL, "PDE 11"},
	...
	{"HP", NULL, "PDE 47"},
	{"HP", NULL, "FU 42"},
	{"SPK", NULL, "PDE 23"},
	{"SPK", NULL, "FU 21"},
```

So [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) for "PDE 47" returns 1 while the headphone path is up and returns 0 only after it stops. The custom handler [`rt722_sdca_pde47_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L896) runs at those boundaries, writing the SDCA requested-power-state control to power state 0 (full on) when the supply comes up and power state 3 (off) when it goes down:

```c
/* sound/soc/codecs/rt722-sdca.c:896 */
static int rt722_sdca_pde47_event(struct snd_soc_dapm_widget *w,
	struct snd_kcontrol *kcontrol, int event)
{
	struct snd_soc_component *component =
		snd_soc_dapm_to_component(w->dapm);
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	unsigned char ps0 = 0x0, ps3 = 0x3;

	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps0);
		rt722_pde_transition_delay(rt722, FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40, ps0);
		break;
	case SND_SOC_DAPM_PRE_PMD:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps3);
		rt722_pde_transition_delay(rt722, FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40, ps3);
		break;
	}
	return 0;
}
```

This widget carries [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) flags rather than the pre-up and post-down flags the regulator and clock macros use, so the SDCA power-state write lands after the rest of the up sequence has prepared the path and before the down sequence tears it apart. The whole array becomes live when [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) finalizes the codec and runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once, after which each PDE supply settles to off until the first playback or capture stream pulls its dependents up.

### One supply gating many dependents

A supply [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) with [`is_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L541) set feeds several dependents over control-less sink paths, and its [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) holds the resource on while any one dependent needs power and releases it on the last dependent's power-down.

```
    One supply, many dependents (fan-out)
    ─────────────────────────────────────

                  ┌──────────────────────────┐
                  │   supply widget          │
                  │   id = snd_soc_dapm_*    │
                  │   is_supply = 1          │
                  │   power_check =          │
                  │   dapm_supply_check_power│
                  └────────────┬─────────────┘
                               │ sink paths (control == NULL)
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌───────────┐    ┌───────────┐     ┌───────────┐
        │ dependent │    │ dependent │     │ dependent │
        │   DAC     │    │   ADC     │     │   PGA     │
        └───────────┘    └───────────┘     └───────────┘

    supply powered  ⟺  any one dependent's power_check() returns 1
    last dependent down  ▶  supply event fires PMD, resource released
```
