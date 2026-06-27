# DAPM power engine

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

DAPM (Dynamic Audio Power Management) decides which audio widgets carry signal and powers exactly those, and the routine that performs the decision is [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): one pass over the card's dirty list that recomputes each widget's power, builds an ordered down sequence and up sequence, runs them, fires the per-widget events, and moves the bias level. A trigger marks widgets dirty before the pass runs. A stream start or stop reaches the engine through [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620), a mixer or mux change through [`snd_soc_dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2727), and a machine-driver pin change through [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005). Each path marks the affected widget dirty with [`dapm_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220) so it lands on [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073), then calls [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) under [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998). Per widget the decision is made by a [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) function pointer, one of [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737), [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749), or [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770), assigned by widget type at creation.

```
    Power change ordering for one dapm_power_widgets() pass
    ───────────────────────────────────────────────────────

    trigger ▶ dapm_mark_dirty ▶ card->dapm_dirty ▶ dapm_power_widgets

      reset                target_bias_level per context (STANDBY or OFF)
        │
        ▼
      decide               dapm_power_one_widget per dirty widget
        │                  power_check ▶ up_list (1) or down_list (0)
        ▼
      pre-bias             dapm_pre_sequence_async: OFF▶STANDBY, then ▶PREPARE
        │
        ▼
      WILL events          down_list: WILL_PMD     up_list: WILL_PMU
        │
        ▼
      down sequence        dapm_seq_run(down_list)   power-OFF path widgets first
        │                    PRE_PMD ▶ register write ▶ POST_PMD
        ▼
      kcontrol write       dapm_widget_update (PRE_REG ▶ reg ▶ POST_REG)
        │
        ▼
      up sequence          dapm_seq_run(up_list)     power-ON path widgets next
        │                    PRE_PMU ▶ register write ▶ POST_PMU
        ▼
      post-bias            dapm_post_sequence_async: PREPARE▶ON or ▶STANDBY▶OFF

      bias ladder:  OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON   (up)
                    ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF   (down)
```

## SUMMARY

The power engine [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) runs once per trigger and produces two effects. The per-widget register writes turn audio blocks on and off, and the per-context bias-level moves bring the analog supplies up and down. It assumes the caller holds [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) and asserts so with [`snd_soc_dapm_mutex_assert_held()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1511). The unlocked entry [`snd_soc_dapm_sync_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2983) calls it with [`SND_SOC_DAPM_STREAM_NOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377), and [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) takes the mutex around it. After a card adds widgets, [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) reads each new widget's initial power from its register, marks it dirty, and runs one pass so the hardware matches the graph.

The pass has four stages. It first sets every context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) or [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) and clears the per-widget power state in [`dapm_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L969). It then calls [`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176) for every dirty widget, which evaluates it through [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) and inserts it into an up list or a down list with [`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809), raising [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) for any context with a powered signal widget. It runs the bias pre-sequence [`dapm_pre_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093), fires the WILL events, runs the down sequence then the up sequence through [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939), and applies any pending kcontrol write with [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040) between them. It ends with the bias post-sequence [`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126). The down sequence runs before the up sequence so a block being switched off is silenced before a newly powered block can drive it, which the comment in [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) states as "Power down widgets first; try to avoid amplifying pops."

Within each sequence the widgets are kept in a fixed type order so supplies and clocks come up before the blocks they feed and come down after, and [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) coalesces adjacent widgets sharing a register into one write. The order is encoded in [`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) and [`dapm_down_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115), indexed by [`enum snd_soc_dapm_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423). Per widget the events fire from [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) and from the [`snd_soc_dapm_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L441) and [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) cases inside [`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939), giving the [`SND_SOC_DAPM_PRE_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386), [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387), [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388), and [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) callbacks a codec uses to talk to its hardware around each power change.

## SPECIFICATIONS

DAPM and its power engine are a Linux kernel software construct with no standalone hardware specification. The register fields the engine writes and the analog supply transitions the bias level drives are defined by each codec's datasheet. On an SDCA codec reached over SoundWire the power-state writes target power-domain entities, which the codec's event callbacks program through SDCA control addressing.

## LINUX KERNEL

### The engine and its entry points (soc-dapm.c)

- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): the top-level pass; resets bias targets, builds the up/down lists, runs both sequences, drives the bias ladder
- [`'\<snd_soc_dapm_sync_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2983): scan and power paths with the lock held; suppresses runs before the card is instantiated, then calls the engine with [`SND_SOC_DAPM_STREAM_NOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377)
- [`'\<snd_soc_dapm_sync\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005): the locked wrapper that takes [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998)
- [`'\<snd_soc_dapm_new_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322): finish newly added widgets, read each one's initial power, mark all dirty, then run one pass
- [`'\<dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598): mark each runtime DAI widget dirty for a stream event, then run the engine
- [`'\<dapm_mixer_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680): connect or disconnect the kcontrol's paths, then run the engine passing the kcontrol [`struct snd_soc_dapm_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572)

### Per-widget power decision (soc-dapm.c)

- [`'\<dapm_widget_power_check\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721): memoised wrapper that returns the cached result or invokes the widget's [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546)
- [`'\<dapm_generic_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737): power a normal widget when it has both a connected input endpoint and a connected output endpoint
- [`'\<dapm_supply_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749): power a supply when any of its sink widgets needs power
- [`'\<dapm_always_on_check_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770): power an endpoint or siggen whenever its pin is [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535)
- [`'\<dapm_power_one_widget\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176): decide one widget, mark changed neighbours dirty, and insert it into the up or down list
- [`'\<dapm_widget_set_peer_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2161): mark a connected neighbour dirty when this widget's power crosses its state
- [`'\<snd_soc_dapm_new_control_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757): create a widget and assign its [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) by [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517)

### The dirty list and reset (soc-dapm.c, soc.h)

- [`'\<dapm_mark_dirty\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220): add a widget to [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073) if it is not already on it
- [`'\<dapm_dirty_widget\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L215): test whether a widget's [`dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L563) node is already linked
- [`'\<dapm_reset\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L969): zero the per-pass stats and reset every widget's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) and [`power_checked`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L540)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the widget; carries [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533), [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539), [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546), [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550), [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549), and the [`power_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L562) and [`dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L563) nodes
- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): holds [`dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073), [`widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070), [`dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998), and the root [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1079) context

### Sequencing (soc-dapm.c)

- [`'\<dapm_seq_insert\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809): insert a widget into a power list in sorted order using [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775)
- [`'\<dapm_seq_compare\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775): order two widgets by sequence index, then [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544), then [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528), then context
- [`'\<dapm_seq_run\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939): walk one sorted list, fire pre/post widget events, and coalesce same-register writes
- [`'\<dapm_seq_run_coalesced\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880): apply one group of same-register widgets in a single write, with PRE/POST events around it
- [`'\<dapm_seq_check_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824): fire one event on a widget when its [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) matches the event direction and its [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) select it
- [`'\<dapm_widget_update\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040): apply a deferred kcontrol register write, firing [`SND_SOC_DAPM_PRE_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L390) before and [`SND_SOC_DAPM_POST_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L391) after
- [`'dapm_up_seq':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) / [`'dapm_down_seq':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115): the per-type sort order, supplies and clocks first on the way up and last on the way down

### Bias level (soc-dapm.c, soc-dapm.h)

- [`'\<enum snd_soc_bias_level\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415): the four power states [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416), [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417), [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418), [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419)
- [`'\<dapm_pre_sequence_async\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093): bring a context from [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) up to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and into [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) before the register writes
- [`'\<dapm_post_sequence_async\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126): settle a context to its final [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419), [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417), or [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) after the register writes
- [`'\<snd_soc_dapm_set_bias_level\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093): drive one context to a level through the card and component bias hooks, then record it
- [`'\<struct snd_soc_dapm_context\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44): one power domain; holds [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) and [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53)

### Trigger entry points (soc-dapm.c)

- [`'\<snd_soc_dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620): take the mutex and run [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598) for a stream start/stop/suspend/resume
- [`'\<dapm_dai_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530): mark a DAI widget dirty and set its [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) and endpoint role from the stream event
- [`'\<snd_soc_dapm_put_volsw\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453): the DAPM volsw control put handler that calls [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680)
- [`'\<__dapm_set_pin\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932): set a pin's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) state and mark its widget dirty; reached from [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684)

### Locking (soc.h)

- [`'\<snd_soc_dapm_mutex_lock\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505) / [`'\<snd_soc_dapm_mutex_lock_root\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1502): take [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) at the runtime or root nesting class
- [`'\<snd_soc_dapm_mutex_assert_held\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1511): the lockdep assertion the engine runs at entry

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM concept, widget types, routes, and the power-management goal the engine implements
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the power-up and power-down ordering the down-before-up sequencing satisfies
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): how DAPM sits among the codec, platform, and machine layers
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle an SDCA codec's power events run alongside

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The per-widget power decision is a [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) function pointer assigned once at creation, and the per-widget hardware actions around a power change are an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) pointer filtered by an [`event_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L549) mask. The decision callback is selected by widget [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) inside [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757); the event callback is supplied by the codec.

| Widget id | power_check assigned | when it returns power |
|-----------|----------------------|-----------------------|
| `snd_soc_dapm_dac`, `snd_soc_dapm_adc`, `snd_soc_dapm_pga`, `snd_soc_dapm_mixer`, `snd_soc_dapm_mux`, `snd_soc_dapm_aif_in`, `snd_soc_dapm_aif_out` | [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) | input endpoint and output endpoint both connected |
| `snd_soc_dapm_supply`, `snd_soc_dapm_regulator_supply`, `snd_soc_dapm_clock_supply`, `snd_soc_dapm_pinctrl`, `snd_soc_dapm_kcontrol` | [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) | any sink widget needs power |
| `snd_soc_dapm_vmid`, `snd_soc_dapm_siggen`, `snd_soc_dapm_sink`, default | [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770) | the pin is [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) |

The event callback fires at up to six distinct moments per pass.

| Moment | Event flag | Fired from |
|--------|------------|------------|
| start of the pass, before powering up | [`SND_SOC_DAPM_WILL_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L392) | [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) over the up list |
| start of the pass, before powering down | [`SND_SOC_DAPM_WILL_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L393) | [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824) over the down list |
| before a widget's register write turns it on | [`SND_SOC_DAPM_PRE_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L386) | [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) |
| after a widget's register write turned it on | [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) | [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) |
| before a widget's register write turns it off | [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) | [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) |
| after a widget's register write turned it off | [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) | [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) |
| around a deferred kcontrol register write | [`SND_SOC_DAPM_PRE_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L390) / [`SND_SOC_DAPM_POST_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L391) | [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040) |

### power_check is chosen by widget id

[`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) assigns the decision callback in a switch on the widget [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), so the same engine treats a DAC, a supply, and a hard-wired endpoint differently without any per-type code inside the pass:

```c
/* sound/soc/soc-dapm.c:3830 */
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

## DETAILS

### A trigger marks widgets dirty, then runs the engine

Three kinds of event reach the engine, and each one marks the affected widgets dirty and then calls [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) under the lock. A stream start arrives through [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620), which runs [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598) to mark each runtime DAI widget dirty and then call the engine:

```c
/* sound/soc/soc-dapm.c:4598 */
static void dapm_stream_event(struct snd_soc_pcm_runtime *rtd, int stream, int event)
{
	struct snd_soc_dai *dai;
	int i;

	for_each_rtd_dais(rtd, i, dai)
		dapm_dai_stream_event(dai, stream, event);

	dapm_power_widgets(rtd->card, event, NULL);
}
```

A control change arrives through [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) for a mixer or switch, which calls [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) to connect or disconnect the kcontrol's paths and, only if a path changed, run the engine with the kcontrol's [`struct snd_soc_dapm_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572). A machine-driver pin change arrives through [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) or [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800), whose inner [`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932) marks the widget dirty but does not run the engine, which is why the contract requires a following [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005). [`dapm_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220) is the single accounting point, adding the widget to [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073) only when it is not already linked:

```c
/* sound/soc/soc-dapm.c:220 */
static void dapm_mark_dirty(struct snd_soc_dapm_widget *w, const char *reason)
{
	struct device *dev = snd_soc_dapm_to_dev(w->dapm);

	dapm_assert_locked(w->dapm);

	if (!dapm_dirty_widget(w)) {
		dev_vdbg(dev, "Marking %s dirty due to %s\n",
			 w->name, reason);
		list_add_tail(&w->dirty, &w->dapm->card->dapm_dirty);
	}
}
```

The three trigger kinds all reach this same dirty-mark and then a single power pass, the stream and control paths running it at once and the pin path leaving the run for a later sync:

```
    Three triggers fan in through dapm_mark_dirty to one pass
    ─────────────────────────────────────────────────────────

      stream start/stop      mixer/mux change       pin enable/disable
    snd_soc_dapm_stream_   snd_soc_dapm_put_       snd_soc_dapm_enable_
          event()               volsw()                  pin()
           │                      │                        │
           ▼                      ▼                        ▼
    dapm_dai_stream_       dapm_mixer_update_       __dapm_set_pin()
        event()               power()              (no run; sync later)
           │                      │                        │
           └──────────────┬───────┴────────────────────────┘
                          ▼
                  dapm_mark_dirty()
                          │
                          ▼
                   card->dapm_dirty
                          │
                          ▼
                 dapm_power_widgets()   (under card->dapm_mutex)
```

### The stream-event trigger locks the card and runs the engine

[`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) is the exported entry the PCM layer calls on every stream start, stop, suspend, and resume. It takes [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) through [`snd_soc_dapm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505), runs [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598) to mark the runtime DAI widgets dirty and call the engine, then drops the lock, so the dirty-mark and the [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) pass happen atomically against any concurrent control or pin change:

```c
/* sound/soc/soc-dapm.c:4620 */
void snd_soc_dapm_stream_event(struct snd_soc_pcm_runtime *rtd, int stream,
			      int event)
{
	struct snd_soc_card *card = rtd->card;

	snd_soc_dapm_mutex_lock(card);
	dapm_stream_event(rtd, stream, event);
	snd_soc_dapm_mutex_unlock(card);
}
```

### The mixer trigger connects paths through put_volsw and mixer_update_power

A DAPM mixer or switch kcontrol routes its put callback to [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453), which decodes the new value, takes the lock, and when the stored value or the register bits change fills a [`struct snd_soc_dapm_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572) describing the deferred write and hands it to [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680):

```c
/* sound/soc/soc-dapm.c:3507 */
	if (change || reg_change) {
		if (reg_change) {
			if (snd_soc_volsw_is_stereo(mc)) {
				update.has_second_set = true;
				update.reg2 = mc->rreg;
				update.mask2 = mask << mc->rshift;
				update.val2 = rval;
			}
			update.kcontrol = kcontrol;
			update.reg = reg;
			update.mask = mask << shift;
			update.val = val;
			pupdate = &update;
		}
		ret = dapm_mixer_update_power(card, kcontrol, pupdate, connect, rconnect);
	}
```

[`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) connects or disconnects each path the kcontrol owns with [`dapm_connect_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L546), which marks the affected widgets dirty, and runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) only when a path actually moved, passing the [`update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572) so the kcontrol register write lands between the down and up sequences:

```c
/* sound/soc/soc-dapm.c:2721 */
	if (found)
		dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, update);

	return found;
}
```

### The pin trigger marks a widget dirty but defers the run to sync

A machine driver enabling or disabling a pin reaches [`__dapm_set_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2932), which only updates the pin widget's [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag and marks it dirty with [`dapm_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220); it returns 1 to say a change is pending but does not run the engine, which is why a pin edit must be followed by [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005):

```c
/* sound/soc/soc-dapm.c:2946 */
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

### Sync flushes the dirty list outside any stream event

[`snd_soc_dapm_sync_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2983) is the engine-only entry that callers reach when they have already accumulated dirty widgets, for example after a batch of pin changes. It suppresses runs before the card is instantiated, then calls [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) with [`SND_SOC_DAPM_STREAM_NOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377) so no stream PRE/POST events fire, only the power decision:

```c
/* sound/soc/soc-dapm.c:2983 */
int snd_soc_dapm_sync_unlocked(struct snd_soc_dapm_context *dapm)
{
	/*
	 * Suppress early reports (eg, jacks syncing their state) to avoid
	 * silly DAPM runs during card startup.
	 */
	if (!snd_soc_card_is_instantiated(dapm->card))
		return 0;

	return dapm_power_widgets(dapm->card, SND_SOC_DAPM_STREAM_NOP, NULL);
}
```

[`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) is the locked wrapper machine drivers call after a pin change, taking [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) through [`snd_soc_dapm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505) around the unlocked call so the assertion [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) makes at entry holds:

```c
/* sound/soc/soc-dapm.c:3005 */
int snd_soc_dapm_sync(struct snd_soc_dapm_context *dapm)
{
	int ret;

	snd_soc_dapm_mutex_lock(dapm);
	ret = snd_soc_dapm_sync_unlocked(dapm);
	snd_soc_dapm_mutex_unlock(dapm);
	return ret;
}
```

The lock both entries reach is the [`_Generic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505) macro [`snd_soc_dapm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1505), which dispatches on whether the caller passes a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) or a [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) and locks the one [`card->dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998) either way:

```c
/* include/sound/soc.h:1505 */
#define snd_soc_dapm_mutex_lock(x) _Generic((x),			\
	struct snd_soc_card * :		_snd_soc_dapm_mutex_lock_c,	\
	struct snd_soc_dapm_context * :	_snd_soc_dapm_mutex_lock_d)(x)
```

### The four bias levels the engine drives a context through

[`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415) names the analog power states a [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) moves through, and the engine raises [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) toward one of them per pass. The values are ordered so a numeric comparison expresses the ladder: [`dapm_pre_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093) climbs from [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) up to [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) before the register writes and [`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126) settles to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) or back down to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) after:

```c
/* include/sound/soc-dapm.h:415 */
enum snd_soc_bias_level {
	SND_SOC_BIAS_OFF = 0,
	SND_SOC_BIAS_STANDBY = 1,
	SND_SOC_BIAS_PREPARE = 2,
	SND_SOC_BIAS_ON = 3,
};
```

### Widget creation assigns the power_check the engine later calls

[`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) copies a template into a live [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) with [`dapm_cnew_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L433), then in the switch shown under CALLBACKS binds the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) the pass will invoke. It finishes by linking the widget onto [`card->widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1070) and setting [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535), leaving the new widget for [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) to mark dirty and power:

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
	...
	w->dapm = dapm;
	INIT_LIST_HEAD(&w->list);
	INIT_LIST_HEAD(&w->dirty);
	/* see for_each_card_widgets */
	list_add_tail(&w->list, &dapm->card->widgets);
	...
	/* machine layer sets up unconnected pins and insertions */
	w->connected = 1;
	return w;
	...
}
```

### The pass resets bias targets and decides each dirty widget

[`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) opens by setting every context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) to its idle floor, then calls [`dapm_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L969), which seeds each widget's [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) from its current [`power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L533) and clears [`power_checked`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L540):

```c
/* sound/soc/soc-dapm.c:969 */
static void dapm_reset(struct snd_soc_card *card)
{
	struct snd_soc_dapm_widget *w;

	snd_soc_dapm_mutex_assert_held(card);

	memset(&card->dapm_stats, 0, sizeof(card->dapm_stats));

	for_each_card_widgets(card, w) {
		w->new_power = w->power;
		w->power_checked = false;
	}
}
```

The decision loop walks [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073) and calls [`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176) on each entry; deciding one widget can mark a neighbour dirty, so widgets may be appended while the loop iterates. A later walk raises [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53), where a powered supply lifts its context only to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and a powered signal widget lifts it to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419):

```c
/* sound/soc/soc-dapm.c:2252 */
		if (w->new_power) {
			d = w->dapm;
			...
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
		}
```

Each powered widget lifts its context to a level set by its id, a signal widget to ON, a supply to at least STANDBY, and siggen or vmid leaving it where it is:

```
    A powered widget's id sets its context target_bias_level
    ─────────────────────────────────────────────────────────

      powered widget id              target_bias_level becomes
    ┌────────────────────────┐     ┌─────────────────────────────┐
    │ siggen, vmid           │ ──▶ │ unchanged (no floor raised) │
    ├────────────────────────┤     ├─────────────────────────────┤
    │ supply, regulator,     │ ──▶ │ at least STANDBY            │
    │ pinctrl, clock, micbias│     │                             │
    ├────────────────────────┤     ├─────────────────────────────┤
    │ any other (signal)     │ ──▶ │ ON                          │
    └────────────────────────┘     └─────────────────────────────┘
```

### dapm_power_one_widget decides one widget and propagates to neighbours

[`dapm_power_one_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2176) treats [`snd_soc_dapm_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L441) as power 0 and [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) as power 1 so they bracket the sequences. For every other widget it calls [`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721), returns early if power did not change, and otherwise propagates to connected neighbours by marking them dirty so a single edit ripples outward:

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
	...
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

[`dapm_widget_power_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1721) is the memoised gate in front of the [`power_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L546) pointer; it returns the cached [`new_power`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L539) when the widget was already evaluated this pass, forces power on when [`force`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L537) is set, and otherwise calls the type-specific callback:

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

A normal widget is powered when [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) confirms both a connected input endpoint and a connected output endpoint, a supply when [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749) finds any sink it feeds needs power, and a hard-wired source or sink when [`dapm_always_on_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1770) reads its [`connected`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L535) flag:

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

The propagation step uses [`dapm_widget_set_peer_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2161), which marks a neighbour dirty only when an actual connection exists and the neighbour is not already in the state being moved to, so the ripple terminates instead of looping:

```c
/* sound/soc/soc-dapm.c:2161 */
static void dapm_widget_set_peer_power(struct snd_soc_dapm_widget *peer,
				       bool power, bool connect)
{
	/* If a connection is being made or broken then that update
	 * will have marked the peer dirty, otherwise the widgets are
	 * not connected and this update has no impact. */
	if (!connect)
		return;

	/* If the peer is already in the state we're moving to then we
	 * won't have an impact on it. */
	if (power != peer->power)
		dapm_mark_dirty(peer, "peer state change");
}
```

Each decided widget marks its connected input and output peers dirty and lands on the up list or the down list by its new power, so one edit ripples outward until no peer changes:

```
    dapm_power_one_widget: a power change ripples to connected peers
    ──────────────────────────────────────────────────────────────────

        source peer            W               sink peer
       (W's input)          (decided)         (W's output)
      ┌──────────┐      ┌──────────────┐      ┌──────────┐
      │  marked  │ ◀─── │ power_check  │ ───▶ │  marked  │
      │  dirty   │      │   → 0 or 1   │      │  dirty   │
      └──────────┘      └──────┬───────┘      └──────────┘
                               │
                   power 1 ─▶ up_list ;  0 ─▶ down_list

      W marks a peer dirty only when connected and the peer's power
      differs; a supply marks only its source/input peers.
      Each dirtied peer is then decided, so one edit ripples across
      the graph until no peer's power changes.
```

### Insertion keeps each list in the up and down type order

[`dapm_seq_insert()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1809) places each widget into its list in sorted position using [`dapm_seq_compare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1775), which orders first by the per-type sequence number from [`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) or [`dapm_down_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L115), then by [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544), then by [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) so same-register widgets sit adjacent for coalescing:

```c
/* sound/soc/soc-dapm.c:1775 */
static int dapm_seq_compare(struct snd_soc_dapm_widget *a,
			    struct snd_soc_dapm_widget *b,
			    bool power_up)
{
	int *sort;
	...
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

The up array puts supplies and clocks at a low index so they precede the blocks they feed; the down array puts them last so they drop only after the signal blocks go quiet:

```c
/* sound/soc/soc-dapm.c:74 */
static int dapm_up_seq[] = {
	[snd_soc_dapm_pre] = 1,
	[snd_soc_dapm_regulator_supply] = 2,
	[snd_soc_dapm_pinctrl] = 2,
	[snd_soc_dapm_clock_supply] = 2,
	[snd_soc_dapm_supply] = 3,
	[snd_soc_dapm_dai_link] = 3,
	...
	[snd_soc_dapm_dac] = 8,
	[snd_soc_dapm_pga] = 10,
	[snd_soc_dapm_adc] = 11,
	[snd_soc_dapm_kcontrol] = 14,
	[snd_soc_dapm_post] = 15,
};
```

```c
/* sound/soc/soc-dapm.c:115 */
static int dapm_down_seq[] = {
	[snd_soc_dapm_pre] = 1,
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

The two arrays read in opposite directions, a supply or clock taking a low index up so it powers before the dac, pga, and adc blocks and a high index down so it drops after them:

```
    Power sequencing: supplies first up, last down (avoids pops)
    ───────────────────────────────────────────────────────────────
    (each list is sorted by a per-type index; low index applied first,
     so the top of each box runs first and the bottom runs last)

       power UP (dapm_up_seq)         power DOWN (dapm_down_seq)
       ┌──────────────────────┐       ┌──────────────────────┐
       │  2  regulator / clk  │       │  3  adc              │
       │  3  supply           │       │  8  dac              │
       │  8  dac              │       │ 10  micbias          │
       │ 10  pga              │       │ 14  supply           │
       │ 11  adc              │       │ 15  clk / pinctrl /  │
       │ 14  kcontrol         │       │     regulator        │
       └──────────────────────┘       └──────────────────────┘
         supplies on top                supplies on bottom
         (powered first)                (dropped last)

      A supply powers up before the dac/pga/adc blocks it feeds and
      powers down after them, so up_seq and down_seq run in reverse.
```

### The pass runs the bias pre-sequence, the WILL events, then the register sequences

With both lists built, [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) runs the card context's bias pre-sequence inline, schedules the other contexts' pre-sequences through the async domain, fires the WILL events, then runs the down sequence, the deferred kcontrol write, and the up sequence in that order:

```c
/* sound/soc/soc-dapm.c:2252 */
	/* Run card bias changes at first */
	dapm_pre_sequence_async(dapm, 0);
	/* Run other bias changes in parallel */
	for_each_card_dapms(card, d) {
		if (d != dapm && d->bias_level != d->target_bias_level)
			async_schedule_domain(dapm_pre_sequence_async, d,
						&async_domain);
	}
	async_synchronize_full_domain(&async_domain);

	list_for_each_entry(w, &down_list, power_list) {
		dapm_seq_check_event(card, w, SND_SOC_DAPM_WILL_PMD);
	}

	list_for_each_entry(w, &up_list, power_list) {
		dapm_seq_check_event(card, w, SND_SOC_DAPM_WILL_PMU);
	}

	/* Power down widgets first; try to avoid amplifying pops. */
	dapm_seq_run(card, &down_list, event, false);

	dapm_widget_update(card, update);

	/* Now power up. */
	dapm_seq_run(card, &up_list, event, true);
```

[`dapm_seq_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1939) walks the sorted list and coalesces adjacent widgets that share a register into one write, flushing a pending group through [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) when the sort key, register, context, or [`subseq`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L544) changes:

```c
/* sound/soc/soc-dapm.c:1939 */
	list_for_each_entry_safe(w, n, list, power_list) {
		int ret = 0;

		/* Do we need to apply any queued changes? */
		if (sort[w->id] != cur_sort || w->reg != cur_reg ||
		    w->dapm != cur_dapm || w->subseq != cur_subseq) {
			if (!list_empty(&pending))
				dapm_seq_run_coalesced(card, &pending);
			...
		}
```

The [`snd_soc_dapm_pre`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L441) and [`snd_soc_dapm_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L442) widgets fire their events directly from the run, taking the direction from the pass event so a stream start fires the PMU pair and a stream stop the PMD pair, while every other widget is queued for coalescing:

```c
/* sound/soc/soc-dapm.c:1939 */
		switch (w->id) {
		case snd_soc_dapm_pre:
			if (!w->event)
				continue;

			if (event == SND_SOC_DAPM_STREAM_START)
				ret = w->event(w, NULL, SND_SOC_DAPM_PRE_PMU);
			else if (event == SND_SOC_DAPM_STREAM_STOP)
				ret = w->event(w, NULL, SND_SOC_DAPM_PRE_PMD);
			break;
		case snd_soc_dapm_post:
			if (!w->event)
				continue;

			if (event == SND_SOC_DAPM_STREAM_START)
				ret = w->event(w, NULL, SND_SOC_DAPM_POST_PMU);
			else if (event == SND_SOC_DAPM_STREAM_STOP)
				ret = w->event(w, NULL, SND_SOC_DAPM_POST_PMD);
			break;
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

The per-widget PRE and POST events for regular widgets are fired by [`dapm_seq_run_coalesced()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1880) around the register write through [`dapm_seq_check_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1824). When the trigger is a kcontrol change, the deferred register write happens between the two sequences in [`dapm_widget_update()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2040), which fires [`SND_SOC_DAPM_PRE_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L390) on each bound widget, applies the bits, and fires [`SND_SOC_DAPM_POST_REG`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L391) after.

### The bias ladder is driven before and after the register sequences

[`dapm_pre_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093) runs before any register writes and takes a context up to the working level, from [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and into [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) when the target crosses into or out of [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419):

```c
/* sound/soc/soc-dapm.c:2093 */
static void dapm_pre_sequence_async(void *data, async_cookie_t cookie)
{
	struct snd_soc_dapm_context *dapm = data;
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	int ret;

	/* If we're off and we're not supposed to go into STANDBY */
	if (dapm->bias_level == SND_SOC_BIAS_OFF &&
	    dapm->target_bias_level != SND_SOC_BIAS_OFF) {
		if (dev && cookie)
			pm_runtime_get_sync(dev);

		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_STANDBY);
		...
	}

	/* Prepare for a transition to ON or away from ON */
	if ((dapm->target_bias_level == SND_SOC_BIAS_ON &&
	     dapm->bias_level != SND_SOC_BIAS_ON) ||
	    (dapm->target_bias_level != SND_SOC_BIAS_ON &&
	     dapm->bias_level == SND_SOC_BIAS_ON)) {
		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_PREPARE);
		...
	}
}
```

The settling routine is itself an async callback, mirroring [`dapm_pre_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093), so the engine can settle every context in parallel through the same async domain it used on the way up:

```c
/* sound/soc/soc-dapm.c:2126 */
static void dapm_post_sequence_async(void *data, async_cookie_t cookie)
{
	struct snd_soc_dapm_context *dapm = data;
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	int ret;
	...
}
```

[`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126) runs after the register writes and settles a context to its final level, dropping from [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and on to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) (releasing the runtime) when nothing is left on, or rising to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419):

```c
/* sound/soc/soc-dapm.c:2126 */
	/* If we just powered the last thing off drop to standby bias */
	if (dapm->bias_level == SND_SOC_BIAS_PREPARE &&
	    (dapm->target_bias_level == SND_SOC_BIAS_STANDBY ||
	     dapm->target_bias_level == SND_SOC_BIAS_OFF)) {
		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_STANDBY);
		...
	}
	...
	/* If we just powered up then move to active bias */
	if (dapm->bias_level == SND_SOC_BIAS_PREPARE &&
	    dapm->target_bias_level == SND_SOC_BIAS_ON) {
		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_ON);
		...
	}
```

Each step goes through [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093), which calls the card-level and component-level bias hooks and records the new level on success.

### snd_soc_dapm_new_widgets seeds the graph and runs one pass

When a card finishes binding, [`snd_soc_dapm_new_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3322) finishes every not-yet-new widget, reads each one's power-on state from its register so the software state matches the hardware, marks every widget dirty, and runs one pass:

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

### Worked example: an rt722-sdca stream start re-powers the path

The Realtek RT722 describes its analog graph with [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) and [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043). The headphone playback path declares an AIF input port `DP1RX`, a DAC feature unit `FU 42`, the output pin `HP`, and the power-domain supply `PDE 47`, with the supply and DAC carrying event callbacks that opt into [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388), and the route `{"HP", NULL, "PDE 47"}` makes the supply a dependent of the output. When userspace prepares the headphone PCM, the prepare path calls [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) with [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378). [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) sets `DP1RX` active and marks it a source endpoint, then [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) runs. Because `DP1RX` now has a complete path to `HP`, [`dapm_generic_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1737) powers `DP1RX`, `FU 42`, and `HP`, the change ripples to `PDE 47` through [`dapm_supply_check_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1749), and all four enter the up list.

`PDE 47` sorts at index 3 in [`dapm_up_seq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L74) and `FU 42` at index 8, so the supply powers first, and because each declared [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) its callback fires after its register write. The supply callback [`rt722_sdca_pde47_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L896) writes the SDCA power-state control to active on power up and to off on power down:

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

For this run the up list is non-empty and the down list empty, so the engine raises the codec context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) to [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) because `FU 42` is a powered signal widget, [`dapm_pre_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093) brings the context through [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418), the up sequence writes the four widgets and fires their POST_PMU events, and [`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126) lands the context at [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419). At stream stop the same pass runs in reverse. The four widgets enter the down list, the down sequence runs first so `FU 42` and the supply are torn down before any newly powered block could drive them, `PDE 47` fires [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) to write the off state, and the bias ladder returns to the idle floor.

```
    rt722-sdca headphone power-up: supply leads the signal block
    ────────────────────────────────────────────────────────────

      up_list sorted by dapm_up_seq index, low index written first

        idx 3   PDE 47    ─▶ write ─▶ POST_PMU: rt722_sdca_pde47_event
                                        writes power-state active
          │
          ▼
        idx 8   FU 42     ─▶ write ─▶ POST_PMU
          │
          ▼
                HP        ─▶ write   (output pin)

      stop runs in reverse. down_list tears FU 42 and PDE 47 down
      first, and PDE 47 fires PRE_PMD to write the off power-state.
```

### Additional example: a tas2783 amplifier mutes around the same power points

The TI TAS2783 SoundWire SDCA smart amplifier shows the same ordering on a signal widget rather than a supply. It declares two Function Unit DAC widgets `FU21` and `FU23` in [`tas_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L856), each built with [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) over [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) and opting into [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) and [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388). After `FU21` enters the up list the engine fires its [`tas_fu21_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L812) with [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) so the amplifier clears mute only once the widget is on, and at stop fires it with [`SND_SOC_DAPM_PRE_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L388) so it mutes first:

```c
/* sound/soc/codecs/tas2783-sdw.c:812 */
static s32 tas_fu21_event(struct snd_soc_dapm_widget *w,
			  struct snd_kcontrol *k, s32 event)
{
	struct snd_soc_component *component = snd_soc_dapm_to_component(w->dapm);
	struct tas2783_prv *tas_dev = snd_soc_component_get_drvdata(component);
	s32 mute;

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

The post-up unmute and pre-down mute land on exactly the moments the events table above describes, and the second DAC `FU23` repeats the pattern through [`tas_fu23_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L834).

```
    tas2783 FU21: unmute follows power-up, mute precedes power-down
    ──────────────────────────────────────────────────────────────

      sequence        event fired        tas_fu21_event writes
    ┌────────────┐   ┌─────────────┐   ┌────────────────────────┐
    │ up_list    │──▶│ POST_PMU    │──▶│ mute = 0  (unmute on)  │
    └────────────┘   └─────────────┘   └────────────────────────┘
    ┌────────────┐   ┌─────────────┐   ┌────────────────────────┐
    │ down_list  │──▶│ PRE_PMD     │──▶│ mute = 1  (mute first) │
    └────────────┘   └─────────────┘   └────────────────────────┘
```

### The four-stage ordering of one power pass

One [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) pass runs after a trigger marks widgets dirty through [`dapm_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L220) onto [`card->dapm_dirty`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1073), moving each context through the reset, decide, down-sequence, and up-sequence stages while climbing the bias ladder.

```
    Power change ordering for one dapm_power_widgets() pass
    ───────────────────────────────────────────────────────

    trigger ▶ dapm_mark_dirty ▶ card->dapm_dirty ▶ dapm_power_widgets

      reset                target_bias_level per context (STANDBY or OFF)
        │
        ▼
      decide               dapm_power_one_widget per dirty widget
        │                  power_check ▶ up_list (1) or down_list (0)
        ▼
      pre-bias             dapm_pre_sequence_async: OFF▶STANDBY, then ▶PREPARE
        │
        ▼
      WILL events          down_list: WILL_PMD     up_list: WILL_PMU
        │
        ▼
      down sequence        dapm_seq_run(down_list)   OFF path widgets first
        │                    PRE_PMD ▶ register write ▶ POST_PMD
        ▼
      kcontrol write       dapm_widget_update (PRE_REG ▶ reg ▶ POST_REG)
        │
        ▼
      up sequence          dapm_seq_run(up_list)     power ON path widgets next
        │                    PRE_PMU ▶ register write ▶ POST_PMU
        ▼
      post-bias            dapm_post_sequence_async: PREPARE▶ON or ▶STANDBY▶OFF

      bias ladder:  OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON   (up)
                    ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF   (down)
```
