# DAPM power sequencing

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

DAPM power sequencing is the execution stage that turns the two sorted widget lists the power engine builds into the smallest set of register writes that realise them, firing each widget's event callback at the fixed moments around its write. [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) hands a down list and an up list to [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939), which walks each list in the order fixed by [`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) and [`dapm_down_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115), coalesces adjacent widgets that share a register through [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880), and fires the per-widget events through [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824). Each list is kept sorted as widgets are added by [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809) using [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775), which orders by widget type, then by the [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) tie-breaker, then by register. The same machinery seeds a freshly bound card from [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322). The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec is the worked example.

```
    dapm_seq_run coalesces a sorted list into minimal register writes
    ────────────────────────────────────────────────────────────────

    sorted up_list (order from dapm_seq_compare)

      widget   sort   reg
    ┌────────┬─────┬──────┐
    │  w0    │  2  │  A   │──┐
    ├────────┼─────┼──────┤  ├──▶ one write to reg A   (w0, w1 merged)
    │  w1    │  2  │  A   │──┘
    ├────────┼─────┼──────┤
    │  w2    │  3  │  B   │─────▶ one write to reg B
    ├────────┼─────┼──────┤
    │  w3    │  8  │  C   │──┐
    ├────────┼─────┼──────┤  ├──▶ one write to reg C   (w3, w4 merged)
    │  w4    │  8  │  C   │──┘
    ├────────┼─────┼──────┤
    │  w5    │ 10  │ NOPM │─────▶ no register, events only
    └────────┴─────┴──────┘

    A group ends when sort[id], reg, dapm, or subseq changes.
    Per group: PRE_PMx events ▶ dapm_update_bits(reg, mask, value) ▶ POST_PMx events.
    value |= on_val<<shift (up) or off_val<<shift (down);  mask |= mask<<shift.
    reg < 0 (SND_SOC_NOPM) skips the write; only the event callbacks run.
```

## SUMMARY

The sequencer receives two lists that the power engine has already filled and sorted, a down list of widgets whose power is dropping to 0 and an up list of widgets whose power is rising to 1. [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) runs the down list first and the up list second so a block being switched off goes quiet before a newly powered block can drive it, and between the two it applies any deferred kcontrol write through [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040). [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) walks one list and accumulates a run of adjacent widgets that share the same sort index, register, context, and [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) into a pending group, flushing the group through [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) when any of those keys changes.

Each group becomes one read-modify-write. [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) folds every member's [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531) or [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) into one value and one mask shifted by each widget's [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529), fires [`SND_SOC_DAPM_PRE_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) on each member, applies the single write with [`dapm_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L990), then fires [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389). A widget whose [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) is [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) takes the same path but skips the write, so the hardware change is carried entirely by its event callback, which is the common arrangement for a SoundWire codec that reaches its hardware over a regmap inside the callback rather than through a DAPM register field.

[`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) gates each event twice. It fires only when the event direction matches the widget's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) (an up event for a widget going on, a down event for one going off) and only when the widget's [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) opts into that flag. The same sequencer runs at card bring-up, where [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) finishes each new widget, reads its power-on state from its register so software matches hardware, marks every widget dirty, and runs one [`SND_SOC_DAPM_STREAM_NOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377) pass.

## SPECIFICATIONS

DAPM power sequencing is a Linux kernel software construct and has no standalone hardware specification. The register a coalesced write targets and the order constraints between supplies, clocks, and signal blocks are set by each codec's datasheet. On an SDCA codec reached over SoundWire the widgets commonly carry [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) and program their power-state controls from the event callbacks through SDCA control addressing.

## LINUX KERNEL

### The ordering tables (soc-dapm.c)

- [`'dapm_up_seq':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74): the power-up sort index per [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423); supplies, clocks, and pinctrl take low indices so they come up before the blocks they feed
- [`'dapm_down_seq':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115): the power-down sort index; signal blocks take low indices and supplies take high ones so the supplies drop last
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget type that indexes both tables; the [`BUILD_BUG_ON`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1781) in [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775) asserts both arrays hold one entry per type

### Sorted insertion (soc-dapm.c)

- [`'\<dapm_seq_insert\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809): insert one widget into a power list at the first position where [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775) returns a negative order, else append
- [`'\<dapm_seq_compare\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775): total order over (sort index, [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544), [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L521)); the subseq direction flips for the down list

### The run loop and coalescing (soc-dapm.c)

- [`'\<dapm_seq_run\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939): walk one sorted list, run the [`snd_soc_dapm_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L441) and [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) widgets inline, queue every other widget into a pending group, and flush the group when its sort key changes
- [`'\<dapm_seq_run_coalesced\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880): merge a group of same-register widgets into one value and mask, fire the PRE events, apply one [`dapm_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L990), fire the POST events
- [`'\<dapm_update_bits\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L990): the single masked register write, routed to [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L777)
- [`'\<dapm_widget_update\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040): apply the trigger kcontrol's own register write between the down and up sequences, bracketed by [`SND_SOC_DAPM_PRE_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L390) and [`SND_SOC_DAPM_POST_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L391)
- [`'\<snd_soc_component_seq_notifier\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L116): tell a component that a sort index finished, dispatched to the optional [`seq_notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op of its [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)

### Event dispatch (soc-dapm.c)

- [`'\<dapm_seq_check_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824): fire one event when the widget's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) matches the event direction and the widget's [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) selects it
- [`'\<SND_SOC_DAPM_WILL_PMU\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L392) / [`'\<SND_SOC_DAPM_WILL_PMD\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L393): the start-of-pass notifications fired over the up list and the down list before any register write
- [`'\<SND_SOC_DAPM_PRE_PMU\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) / [`'\<SND_SOC_DAPM_POST_PMU\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387): the before and after power-up events fired by [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880)
- [`'\<SND_SOC_DAPM_PRE_PMD\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) / [`'\<SND_SOC_DAPM_POST_PMD\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389): the before and after power-down events

### Widget fields the sequencer reads (soc-dapm.h)

- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): carries the [`power_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L563) node the lists thread through, the [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529), [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L530), [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531), and [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) the write uses, the [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) tie-breaker, and the [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback with its [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549)
- [`'\<SND_SOC_DAPM_PGA_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L205) / [`'\<SND_SOC_DAPM_SUPPLY_S\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L212): the widget constructors that set [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) so a driver can order widgets of one type

### Seeding at bring-up (soc-dapm.c)

- [`'\<snd_soc_dapm_new_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322): finish each new widget, build its kcontrols, read its initial [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533) from the register, mark all dirty, run one pass
- [`'\<dapm_mark_dirty\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220): the single point that adds a widget to the card dirty list before a pass

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM concept, widget types, and the power-management goal the sequencer implements
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the power-up and power-down ordering the down-before-up sequencing and the per-type tables satisfy

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The sequencer is a small set of static helpers in [`sound/soc/soc-dapm.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c) that operate on the [`power_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L563) thread of each widget. [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) builds the two lists, calls [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809) to keep them sorted, and then drives them through [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939); a caller never invokes these directly.

| primitive | role | register effect |
|-----------|------|-----------------|
| [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809) | place one widget into a power list in sorted order | none |
| [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775) | order two widgets by type, [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544), [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), context | none |
| [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) | walk one list and group adjacent same-register widgets | drives the writes below |
| [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) | apply one group as a single masked write with events | one [`dapm_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L990) per group |
| [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) | fire one event if direction and [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) match | none (the callback may write) |
| [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040) | apply the trigger kcontrol's deferred write | one or two writes |
| [`snd_soc_component_seq_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L116) | notify the component that a sort index finished | component-defined |

## DETAILS

### The two ordering tables fix the per-type order

[`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) and [`dapm_down_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115) are two arrays of small integers indexed by [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423). The up array gives a regulator, pinctrl, or clock supply index 2 and a plain supply index 3, then microphone bias 4, the DAI and stream widgets 5, the converters and gains in the middle, and the [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) marker last at 15, so a power-up walk reaches a supply before any block that depends on it:

```c
/* sound/soc/soc-dapm.c:74 */
static int dapm_up_seq[] = {
	[snd_soc_dapm_pre] = 1,
	[snd_soc_dapm_regulator_supply] = 2,
	[snd_soc_dapm_pinctrl] = 2,
	[snd_soc_dapm_clock_supply] = 2,
	[snd_soc_dapm_supply] = 3,
	[snd_soc_dapm_dai_link] = 3,
	[snd_soc_dapm_micbias] = 4,
	...
	[snd_soc_dapm_dac] = 8,
	[snd_soc_dapm_pga] = 10,
	[snd_soc_dapm_adc] = 11,
	[snd_soc_dapm_kcontrol] = 14,
	[snd_soc_dapm_post] = 15,
};
```

The down array is close to the reverse. It gives the ADC index 3, the speaker and headphone drivers 4 and 5, the converters 8, microphone bias 10, a plain supply 14, and the regulator, pinctrl, and clock supplies 15, so a power-down walk drops the signal path before the supplies that fed it:

```c
/* sound/soc/soc-dapm.c:115 */
static int dapm_down_seq[] = {
	[snd_soc_dapm_pre] = 1,
	[snd_soc_dapm_kcontrol] = 2,
	[snd_soc_dapm_adc] = 3,
	...
	[snd_soc_dapm_dac] = 8,
	[snd_soc_dapm_micbias] = 10,
	[snd_soc_dapm_supply] = 14,
	[snd_soc_dapm_clock_supply] = 15,
	[snd_soc_dapm_pinctrl] = 15,
	[snd_soc_dapm_regulator_supply] = 15,
	[snd_soc_dapm_post] = 16,
};
```

The comment above the tables reads "dapm power sequences - make this per codec in the future", so the order is one global policy for every card rather than a per-device table.

```
    dapm_up_seq vs dapm_down_seq: supplies first up, last down
    ──────────────────────────────────────────────────────────

       power UP (dapm_up_seq)        power DOWN (dapm_down_seq)
       ┌──────────────────────┐      ┌──────────────────────┐
       │  2  regulator/clk/   │      │  2  kcontrol         │
       │     pinctrl          │      │  3  adc              │
       │  3  supply / dai     │      │  8  dac              │
       │  4  micbias          │      │ 10  micbias          │
       │  8  dac              │      │ 14  supply           │
       │ 10  pga              │      │ 15  clk / pinctrl /  │
       │ 11  adc              │      │     regulator        │
       │ 14  kcontrol         │      │ 16  post             │
       │ 15  post             │      │                      │
       └──────────────────────┘      └──────────────────────┘
         low index runs first          low index runs first
         supplies on top               supplies near bottom

      A supply powers up before the dac/pga/adc blocks it feeds and
      powers down after them, so up_seq and down_seq run in reverse.
```

### Sorted insertion places each widget by type, subseq, then register

[`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) calls [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809) for each widget it decides, so the lists are sorted on the way in rather than sorted afterwards. The insert walks the list and stops at the first existing widget the new one sorts before:

```c
/* sound/soc/soc-dapm.c:1809 */
static void dapm_seq_insert(struct snd_soc_dapm_widget *new_widget,
			    struct list_head *list,
			    bool power_up)
{
	struct snd_soc_dapm_widget *w;

	list_for_each_entry(w, list, power_list)
		if (dapm_seq_compare(new_widget, w, power_up) < 0) {
			list_add_tail(&new_widget->power_list, &w->power_list);
			return;
		}

	list_add_tail(&new_widget->power_list, list);
}
```

[`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775) selects the up or down table by the `power_up` flag, then compares first on the per-type sort index, then on [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544), then on [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) so same-register widgets end up adjacent for coalescing, and finally on the context pointer. The [`BUILD_BUG_ON`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1781) lines assert each table has exactly one slot per widget type:

```c
/* sound/soc/soc-dapm.c:1775 */
static int dapm_seq_compare(struct snd_soc_dapm_widget *a,
			    struct snd_soc_dapm_widget *b,
			    bool power_up)
{
	int *sort;

	BUILD_BUG_ON(ARRAY_SIZE(dapm_up_seq) != SND_SOC_DAPM_TYPE_COUNT);
	BUILD_BUG_ON(ARRAY_SIZE(dapm_down_seq) != SND_SOC_DAPM_TYPE_COUNT);

	if (power_up)
		sort = dapm_up_seq;
	else
		sort = dapm_down_seq;
	...
	if (sort[a->id] != sort[b->id])
		return sort[a->id] - sort[b->id];
	if (a->subseq != b->subseq) {
		if (power_up)
			return a->subseq - b->subseq;
		else
			return b->subseq - a->subseq;
	}
	if (a->reg != b->reg)
		return a->reg - b->reg;
	if (a->dapm != b->dapm)
		return (unsigned long)a->dapm - (unsigned long)b->dapm;

	return 0;
}
```

### The subseq tie-breaker orders widgets of one type

Two widgets of the same type tie on the table index, so [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775) falls through to [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544). A driver sets [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) with the `_S` widget constructors, which carry an extra sub-sequence argument that the plain constructors leave at 0:

```c
/* include/sound/soc-dapm.h:205 */
#define SND_SOC_DAPM_PGA_S(wname, wsubseq, wreg, wshift, winvert, \
	wevent, wflags) \
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_pga, .name = wname, \
	SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.event = wevent, .event_flags = wflags, \
	.subseq = wsubseq}
```

The comparison applies [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) ascending on the up list and descending on the down list, so a pair of PGAs that must power up in one order power down in the opposite order without a second table. When [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) finishes a sort index it calls [`snd_soc_component_seq_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L116), which forwards to the optional [`seq_notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op so a codec can act once every widget of a type has been written:

```c
/* sound/soc/soc-component.c:116 */
void snd_soc_component_seq_notifier(struct snd_soc_component *component,
				    enum snd_soc_dapm_type type, int subseq)
{
	if (component->driver->seq_notifier)
		component->driver->seq_notifier(component, type, subseq);
}
```

### dapm_seq_run walks the list and coalesces same-register writes

[`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) picks the up or down table, then walks the sorted list keeping a running key of the current sort index, register, context, and [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544). When the next widget breaks that key it flushes the accumulated group through [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) and notifies the component for the finished index:

```c
/* sound/soc/soc-dapm.c:1939 */
	list_for_each_entry_safe(w, n, list, power_list) {
		int ret = 0;

		/* Do we need to apply any queued changes? */
		if (sort[w->id] != cur_sort || w->reg != cur_reg ||
		    w->dapm != cur_dapm || w->subseq != cur_subseq) {
			if (!list_empty(&pending))
				dapm_seq_run_coalesced(card, &pending);

			if (cur_dapm && cur_dapm->component) {
				for (i = 0; i < ARRAY_SIZE(dapm_up_seq); i++)
					if (sort[i] == cur_sort)
						snd_soc_component_seq_notifier(
							cur_dapm->component,
							i, cur_subseq);
			}
			...
		}
```

The [`snd_soc_dapm_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L441) and [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) marker widgets are handled inline because they own no register; they fire their event directly with the direction taken from the pass event, while every other widget is moved onto the pending group:

```c
/* sound/soc/soc-dapm.c:1985 */
		switch (w->id) {
		case snd_soc_dapm_pre:
			if (!w->event)
				continue;

			if (event == SND_SOC_DAPM_STREAM_START)
				ret = w->event(w,
					       NULL, SND_SOC_DAPM_PRE_PMU);
			else if (event == SND_SOC_DAPM_STREAM_STOP)
				ret = w->event(w,
					       NULL, SND_SOC_DAPM_PRE_PMD);
			break;
		...
		default:
			/* Queue it up for application */
			cur_sort = sort[w->id];
			cur_subseq = w->subseq;
			cur_reg = w->reg;
			cur_dapm = w->dapm;
			list_move(&w->power_list, &pending);
			break;
		}
```

After the loop the function flushes the final pending group and runs [`dapm_async_complete()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L196) on each context, so any event callback that scheduled asynchronous work is joined before the pass returns.

### dapm_seq_run_coalesced builds one masked write and brackets it with events

A group reaching [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) shares one register. The function commits each member's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) into its [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533), accumulates one `value` and one `mask` by shifting each widget's [`on_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L531) or [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) by its [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L529), and fires the PRE events on every member before the write:

```c
/* sound/soc/soc-dapm.c:1880 */
	list_for_each_entry(w, pending, power_list) {
		WARN_ON(reg != w->reg || dapm != w->dapm);
		w->power = w->new_power;

		mask |= w->mask << w->shift;
		if (w->power)
			value |= w->on_val << w->shift;
		else
			value |= w->off_val << w->shift;
		...
		/* Check for events */
		dapm_seq_check_event(card, w, SND_SOC_DAPM_PRE_PMU);
		dapm_seq_check_event(card, w, SND_SOC_DAPM_PRE_PMD);
	}
```

The single write happens only when the shared register is real; a group of widgets carrying [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) (a negative [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528)) skips the write and exists only to carry events. The POST events fire on every member after the write:

```c
/* sound/soc/soc-dapm.c:1913 */
	if (reg >= 0) {
		...
		dapm_pop_wait(card->pop_time);
		dapm_update_bits(dapm, reg, mask, value);
	}

	list_for_each_entry(w, pending, power_list) {
		dapm_seq_check_event(card, w, SND_SOC_DAPM_POST_PMU);
		dapm_seq_check_event(card, w, SND_SOC_DAPM_POST_PMD);
	}
```

[`dapm_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L990) forwards to [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L777), so the whole group of widgets sharing the register collapses into one regmap read-modify-write rather than one write per widget.

```
    dapm_seq_run_coalesced: one masked write folds the whole group
    ─────────────────────────────────────────────────────────────

      group members share one reg; each contributes a shifted field
        w_a   value += on_or_off_val << shift_a   mask += mask << shift_a
        w_b   value += on_or_off_val << shift_b   mask += mask << shift_b
            │ fold every member into one value and one mask
            ▼
      ┌──────────────────────────────────────────────────┐
      │  one accumulated value and mask for the reg      │
      └──────────────────────────────────────────────────┘
            │ reg >= 0
            ▼
      PRE_PMU/PRE_PMD ▶ dapm_update_bits(reg, mask, value) ▶ POST events

      reg < 0 (SND_SOC_NOPM): skip the write, fire events only.
```

### dapm_seq_check_event fires an event only when the direction matches

Each of the six PRE/POST/WILL calls in the run passes one flag to [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824). The function maps the flag to a power direction (1 for the up events, 0 for the down events), returns when the widget's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) does not match that direction, and otherwise calls the widget's [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) only when its [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) opt into that flag:

```c
/* sound/soc/soc-dapm.c:1824 */
	case SND_SOC_DAPM_POST_PMU:
		ev_name = "POST_PMU";
		power = 1;
		break;
	...
	case SND_SOC_DAPM_PRE_PMD:
		ev_name = "PRE_PMD";
		power = 0;
		break;
	...
	if (w->new_power != power)
		return;

	if (w->event && (w->event_flags & event)) {
		int ret;
		...
		ret = w->event(w, NULL, event);
		...
	}
```

Because the same coalesced group fires all four PRE and POST flags over each member, the direction test is what keeps a widget powering up from receiving a PMD event and a widget powering down from receiving a PMU event, even though both pairs of calls run unconditionally.

```
    dapm_seq_check_event: direction gate before the event_flags gate
    ───────────────────────────────────────────────────────────────

    ┌────────────────┬───────────────┬──────────────────────────┐
    │ event flag     │ needs new_pow │ fires when               │
    ├────────────────┼───────────────┼──────────────────────────┤
    │ WILL_PMU       │       1       │ event_flags has the flag │
    │ PRE_PMU        │       1       │ and new_power == 1       │
    │ POST_PMU       │       1       │ (widget powering up)     │
    ├────────────────┼───────────────┼──────────────────────────┤
    │ WILL_PMD       │       0       │ event_flags has the flag │
    │ PRE_PMD        │       0       │ and new_power == 0       │
    │ POST_PMD       │       0       │ (widget powering down)   │
    └────────────────┴───────────────┴──────────────────────────┘
      new_power != needed direction ──▶ return, no event fired.
```

### A deferred kcontrol write lands between the two sequences

When the trigger is a mixer or mux change, the kcontrol's own register write is deferred so it happens after the down sequence and before the up sequence. [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) calls [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040) at that point, which fires [`SND_SOC_DAPM_PRE_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L390) on each widget bound to the kcontrol, applies the bits, and fires [`SND_SOC_DAPM_POST_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L391):

```c
/* sound/soc/soc-dapm.c:2040 */
	for_each_dapm_widgets(wlist, wi, w) {
		if (w->event && (w->event_flags & SND_SOC_DAPM_PRE_REG)) {
			ret = w->event(w, update->kcontrol, SND_SOC_DAPM_PRE_REG);
			...
		}
	}

	if (!w)
		return;

	ret = dapm_update_bits(w->dapm, update->reg, update->mask,
		update->val);
```

Ordering the connection write between the two sequences means the path is torn down before the routing bit changes and rebuilt after, so a mux switch does not briefly route a live source into a block that is about to be powered down.

```
    The kcontrol write is deferred between the down and up sequences
    ───────────────────────────────────────────────────────────────

      dapm_seq_run(down_list)      tear the old path down first
        │
        ▼
      dapm_widget_update           PRE_REG ▶ dapm_update_bits(reg,
        │                          mask, val) ▶ POST_REG  (mux switch)
        ▼
      dapm_seq_run(up_list)        build the new path up after

      The routing bit changes only after the source is silenced and
      before the new block powers, so no live source drives a dying one.
```

### snd_soc_dapm_new_widgets seeds the graph through one sequence

The same sequencer runs once at the end of card binding. [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) walks every widget that is not yet finished, allocates its kcontrol array, dispatches by [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) to the per-type constructor, reads the widget's power-on state from its register so the software [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533) matches the hardware, then marks it dirty:

```c
/* sound/soc/soc-dapm.c:3322 */
	for_each_card_widgets(card, w)
	{
		if (w->new)
			continue;
		...
		switch(w->id) {
		case snd_soc_dapm_switch:
		case snd_soc_dapm_mixer:
		case snd_soc_dapm_mixer_named_ctl:
			dapm_new_mixer(w);
			break;
		case snd_soc_dapm_mux:
		case snd_soc_dapm_demux:
			dapm_new_mux(w);
			break;
		...
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
```

The closing [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) call with [`SND_SOC_DAPM_STREAM_NOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377) runs one full down-then-up sequence so any widget that powered on at reset but has no complete path is turned back off before the card goes live.

### Worked example: an rt722-sdca path sequences as event-only NOPM widgets

The Realtek RT722 declares its analog graph in [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) and its routes in [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043). Its power-domain entity `PDE 47` is a [`snd_soc_dapm_supply`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423) widget and its DAC feature unit `FU 42` is a converter, so [`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) gives the supply index 3 and the DAC index 8 and the supply is written first on power up, while [`dapm_down_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115) gives the supply index 14 so it drops last on power down. Both widgets carry [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) for their [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), so [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) performs no register write for them and the hardware change is carried by the event callback [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) fires. The supply opts into [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388), and its [`rt722_sdca_pde47_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L896) writes the SDCA power-state control over the codec regmap:

```c
/* sound/soc/codecs/rt722-sdca.c:896 */
static int rt722_sdca_pde47_event(struct snd_soc_dapm_widget *w,
	struct snd_kcontrol *kcontrol, int event)
{
	...
	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps0);
		...
		break;
	case SND_SOC_DAPM_PRE_PMD:
		regmap_write(rt722->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_PDE40,
				RT722_SDCA_CTL_REQ_POWER_STATE, 0), ps3);
		...
		break;
	}
	return 0;
}
```

On a stream start the supply enters the up list at index 3 and fires its [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) after its (empty) write, so the power-state control reaches active before the DAC at index 8 produces signal. On a stream stop the four widgets enter the down list, the DAC at down index 8 is torn down before the supply at down index 14, and the supply fires [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) to write the off state last.

```
    rt722-sdca: PDE 47 supply brackets the FU 42 DAC (both NOPM)
    ───────────────────────────────────────────────────────────

      stream START (up_list)            stream STOP (down_list)
      ┌──────────────────────┐          ┌──────────────────────┐
      │ idx 3  PDE 47 supply │ first    │ idx 8  FU 42  dac    │ first
      │   POST_PMU ▶ ps0 on  │          │   (torn down)        │
      │ idx 8  FU 42  dac    │ then     │ idx 14 PDE 47 supply │ last
      │   (drives signal)    │          │   PRE_PMD ▶ ps3 off  │
      └──────────────────────┘          └──────────────────────┘

      No reg write for either (NOPM); the regmap access is entirely
      inside rt722_sdca_pde47_event at POST_PMU and PRE_PMD.
```

### Additional example: a tas2783 amplifier mutes from the same event moments

The TI TAS2783 SoundWire SDCA amplifier shows the same dispatch on a signal widget rather than a supply. It declares two DAC feature units `FU21` and `FU23` in [`tas_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L856), each built with [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) over [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) and opting into [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388). Because the widget is NOPM, the coalesced group writes nothing and the entire effect is in [`tas_fu21_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L812), which [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) calls with [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) once the DAC index is reached on the up list and with [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) before it on the down list:

```c
/* sound/soc/codecs/tas2783-sdw.c:812 */
static s32 tas_fu21_event(struct snd_soc_dapm_widget *w,
			  struct snd_kcontrol *k, s32 event)
{
	...
	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		mute = 0;
		break;

	case SND_SOC_DAPM_PRE_PMD:
		mute = 1;
		break;
	}

	return sdw_write_no_pm(tas_dev->sdw_peripheral,
			       SDW_SDCA_CTL(1, TAS2783_SDCA_ENT_FU21,
					    TAS2783_SDCA_CTL_FU_MUTE, 1), mute);
}
```

The unmute lands at [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) so the amplifier opens only after the DAC widget is on, and the mute lands at [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) so it closes before teardown, which are exactly the moments the down-then-up sequencing reaches each widget. The second DAC `FU23` repeats the pattern through [`tas_fu23_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L834).
