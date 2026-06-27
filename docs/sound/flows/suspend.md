# System suspend flow (ASoC)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an Intel Meteor Lake laptop with a Sound Open Firmware DSP and SoundWire codecs, system-wide suspend reaches the audio stack first at the ASoC sound card, whose device carries a [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) named [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2410) with [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) as its [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) member, and that one callback mutes active DACs through [`soc_playback_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L619), drives every running PCM to [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) through [`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) and the [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739) pre/do/post stages, sends a [`SND_SOC_DAPM_STREAM_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380) event through [`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638) so [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) recomputes widget power, and walks each component forcing its DAPM bias toward [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) through [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) before the PM core descends into the SOF DSP power-down and the SoundWire master stop.

```
    ASoC suspend descent (Intel MTL SOF + SoundWire)
    ────────────────────────────────────────────────

    PM core (dpm_suspend, reverse-dependency device walk)
        │  dev->driver->pm->suspend(dev)
        ▼
    ASoC card device   dev_pm_ops snd_soc_pm_ops .suspend
    ┌────────────────────────────────────────────────────────┐
    │ snd_soc_suspend(dev)                                   │
    │   snd_power_change_state ─▶ SNDRV_CTL_POWER_D3hot      │
    │                                                        │
    │   soc_playback_digital_mute(card, 1)   mute DACs       │
    │     └─ snd_soc_dai_digital_mute(dai, 1, PLAYBACK)      │
    │                                                        │
    │   for_each_card_rtds:                                  │
    │     snd_pcm_suspend_all(rtd->pcm)                      │
    │       └─ snd_pcm_suspend ─▶ snd_pcm_action             │
    │            └─ snd_pcm_action_suspend (action_ops)      │
    │                 pre_action  snd_pcm_pre_suspend        │
    │                 do_action   snd_pcm_do_suspend ──┐     │
    │                 post_action snd_pcm_post_suspend │     │
    │                       PCM state ─▶ SUSPENDED     │     │
    │                                                  ▼     │
    │   soc_dapm_suspend_resume(STREAM_SUSPEND)  trigger     │
    │     └─ snd_soc_dapm_stream_event                       │
    │          └─ dapm_power_widgets   recompute power       │
    │               └─ dapm_post_sequence_async             │
    │                    snd_soc_dapm_set_bias_level OFF     │
    │                                                        │
    │   per component: snd_soc_dapm_get_bias_level           │
    │     BIAS_OFF/STANDBY ─▶ snd_soc_component_suspend      │
    └──────────────────────────────┬─────────────────────────┘
                                   ▼
    SOF DSP (PCI)  +  SoundWire master  +  HDA controller
    (next stage: snd_sof_suspend / intel_suspend power-down)
```

## SUMMARY

The page traces the ASoC half of one system-wide suspend on an Intel Meteor Lake platform whose audio is driven by Sound Open Firmware over the HDA controller, with SoundWire codecs such as the Realtek RT722. The kernel suspends devices in reverse dependency order, so the ASoC sound card suspends before the SOF DSP device that supplies its DAIs. The card device is bound to the soc-core platform driver whose [`pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2424) member is [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2410), and the PM core invokes its [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2411) entry [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) when it reaches the card in the dependency walk. The DSP power-down, the SoundWire master clock-stop, and the codec detach that run after this callback are the next stage and are described by the sibling SOF/SoundWire suspend page; this page ends where the card callback returns.

[`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) returns early when the card never finished instantiating, waits for any in-flight resume work through [`snd_power_wait()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1159), and moves the ALSA control device to [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116) so userspace blocks until resume completes. It then mutes every active playback DAI through [`soc_playback_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L619), which gates each [`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386) on [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529), and walks each PCM runtime calling [`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768). That call reaches [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753), which runs the [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739) instance of [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) through [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387): [`snd_pcm_pre_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1696) rejects an unresumable stream, [`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) fires a [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102), and [`snd_pcm_post_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1726) records [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) and sets the runtime to [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314).

After the PCMs are suspended the function sends a [`SND_SOC_DAPM_STREAM_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380) event through [`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638), which reaches [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620), marks each DAI widget through [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530), and recomputes the whole graph through [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252). The power walk computes a [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) per context and applies it through [`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126), which calls [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) and, through it, [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050) to drive an idle context to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416). The function then walks each component, reads its bias with [`snd_soc_dapm_get_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1128), and for a component left at [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) (or at [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) with idle-bias-off support) calls [`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284), leaving a component held [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) by an active path running.

## SPECIFICATIONS

The suspend descent is a Linux kernel software sequence and has no single hardware specification. The PCM state set the flow drives streams into ([`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) and the rest of the [`SNDRV_PCM_STATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) values) is defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h), where [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306) is the normative type. The DAPM bias model ([`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415)) and the stream events are ASoC constructs with no external standard. The per-device PM callback phases the flow is dispatched through are part of the Linux device PM model. On an x86-64 ACPI platform the target sleep state the later DSP stage maps onto follows the ACPI Specification system-state model, but the card-level descent on this page does not itself read an ACPI object. It acts the same for any sleep depth, since [`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) and the DAPM bias descent are unconditional once the card callback runs.

## LINUX KERNEL

### PM callback entry (soc-core.c, include/linux/pm.h)

- [`'\<struct dev_pm_ops\>':'include/linux/pm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288): the per-device function pointer struct the PM core dispatches through; its [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288), [`freeze`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288), and [`poweroff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) members are the system-sleep suspend entries
- [`'\<snd_soc_pm_ops\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2410): the ASoC card device PM table, attached to the soc-core platform driver at [`soc_driver.driver.pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2424); its [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2411) and [`freeze`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2413) members point at [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654)

### ASoC card suspend (soc-core.c)

- [`'\<snd_soc_suspend\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654): the card suspend callback; blocks userspace, mutes DACs, suspends all PCMs, sends the DAPM suspend event, and suspends components down to bias off
- [`'\<soc_playback_digital_mute\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L619): mute every active playback DAI through [`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386), gated by [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529)
- [`'\<soc_dapm_suspend_resume\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638): send a stream event to both directions of every non-ignored runtime through [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620)
- [`'\<snd_soc_dai_digital_mute\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386): call the DAI driver [`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L194) op, skipping a capture mute on a DAI with [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L194)
- [`'\<snd_soc_dai_stream_active\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529): read the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) count the mute walk consults

### PCM suspend (pcm_native.c)

- [`'\<snd_pcm_suspend_all\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768): suspend every substream of one PCM device that has a runtime and substream ops, then run [`snd_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639) on each
- [`'\<snd_pcm_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753): take the stream lock and run the suspend action through [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387) with [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739)
- [`'snd_pcm_action_suspend':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739): the [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instance for the suspend transition, filling the pre, do, and post stages
- [`'\<struct action_ops\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230): the four-stage function pointer struct ([`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231), [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233), [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235), [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237)) every PCM state transition runs through
- [`'\<snd_pcm_action\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387): pick the group or single path via [`snd_pcm_stream_group_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1352), then run [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) for a lone substream
- [`'\<snd_pcm_action_single\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306): run [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231), [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233), then [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) on success or [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235) on failure
- [`'\<snd_pcm_pre_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1696): reject an already-suspended or unresumable stream with `-EBUSY` and set [`runtime->trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366)
- [`'\<snd_pcm_do_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713): fire a [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) on a running stream and set [`runtime->stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L420)
- [`'\<snd_pcm_post_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1726): record [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) and set the runtime state to [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) through [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725)
- [`'\<snd_pcm_running\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L711): the test [`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) makes before firing the trigger; true for RUNNING, or DRAINING on a playback stream
- [`'\<__snd_pcm_set_state\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725): write [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the mmap copy [`runtime->status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) together

### DAPM suspend event and bias descent (soc-dapm.c, soc-dapm.h)

- [`'\<snd_soc_dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620): take the DAPM mutex and call [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598)
- [`'\<dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598): mark each DAI widget for the event and run [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252)
- [`'\<dapm_dai_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530): invalidate the widget's cached path power and mark it dirty; the [`SND_SOC_DAPM_STREAM_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380) case leaves the [`active`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4532) count untouched so the power walk recomputes the bias
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): scan dirty widgets for complete audio paths, compute each context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53), and run the pre and post bias sequences
- [`'\<dapm_pre_sequence_async\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2093): bring a context up to [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) before powering widgets, through [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093)
- [`'\<dapm_post_sequence_async\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126): step a context down from [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) to [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) and then to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) when its target is off
- [`'\<snd_soc_dapm_set_bias_level\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093): run the card-level pre and post bias callbacks and the context's own bias change through [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050)
- [`'\<snd_soc_dapm_force_bias_level\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050): call the component's [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L112) op and store the new [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45); the leaf that actually drives the codec to bias off
- [`'snd_soc_component_force_bias_level':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L729): macro form that applies [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050) to a component's own [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267) context
- [`'\<snd_soc_dapm_get_bias_level\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1128): read a context's current [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45), which the per-component suspend switch consults to skip components held on by active paths
- [`'\<snd_soc_dapm_get_idle_bias\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2222): report whether a context uses bias off when idle, refined by the codec's [`suspend_bias_off`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L180) flag while the card is at [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116)
- [`'\<enum snd_soc_bias_level\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415): the four ordered levels [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) (0) through [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) (3)
- [`'SND_SOC_DAPM_STREAM_SUSPEND':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380): the stream event the card suspend passes, one of the [`SND_SOC_DAPM_STREAM_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L377) flags

### Component suspend (soc-component.c)

- [`'\<snd_soc_component_suspend\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284): call the component driver [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L80) op and set [`component->suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215)
- [`'\<snd_soc_component_is_suspended\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L298): read [`component->suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) so the walk skips a component already suspended
- [`'\<snd_soc_component_to_dapm\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267): return the [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) a component owns, the context whose bias the suspend switch reads

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the Dynamic Audio Power Management bias levels and stream events the card suspend walk drives
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback and the [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) command [`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) issues
- [`Documentation/sound/designs/powersave.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/powersave.rst): the power-save context in which the PCM suspend and the DAPM bias descent run
- [`Documentation/driver-api/pm/devices.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/pm/devices.rst): the device PM model and the [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) callback phases the card suspend is dispatched through

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The card suspend runs as one ordered descent inside a single [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) callback. The table below lists the entry points in the order [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) invokes them and the state each leaves behind. The SOF DSP power-down and the SoundWire master stop are the next stage and are reached only after this callback returns 0.

| Order | Entry point | Owns / acts on | Resulting state |
|-------|-------------|----------------|-----------------|
| 0 | [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2410) `.suspend` ([`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654)) | the ASoC card device | the whole descent below |
| 1 | [`snd_power_change_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L158) | the ALSA control device | [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116) (userspace blocks) |
| 2 | [`soc_playback_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L619) | active playback DAIs | DAC digital mute asserted |
| 3 | [`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) | every running PCM substream | [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) |
| 4 | [`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638) | the DAPM graph | idle contexts driven to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) |
| 5 | [`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284) | each non-active component | [`component->suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) = 1 |
| next | (sibling page) | SOF DSP, SoundWire master, HDA | DSP D3, bus clock-stopped, codec unattached |

Steps 2 through 5 each iterate the card's runtimes through [`for_each_card_rtds`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1109) and skip any runtime whose link sets [`ignore_suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L784), so a DAI link marked to survive suspend (a microphone wake path, for example) is left untouched by the mute, the PCM suspend, and the DAPM event alike.

## DETAILS

### The card device PM table names snd_soc_suspend

The ASoC card device is bound to the soc-core platform driver, and that driver names [`snd_soc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2410) as its PM table. The PM core, walking devices in reverse dependency order during the suspend phase, calls the [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) member of that table when it reaches the card:

```c
/* sound/soc/soc-core.c:2410 */
const struct dev_pm_ops snd_soc_pm_ops = {
	.suspend = snd_soc_suspend,
	.resume = snd_soc_resume,
	.freeze = snd_soc_suspend,
	.thaw = snd_soc_resume,
	.poweroff = snd_soc_poweroff,
	.restore = snd_soc_resume,
};
EXPORT_SYMBOL_GPL(snd_soc_pm_ops);

/* ASoC platform driver */
static struct platform_driver soc_driver = {
	.driver		= {
		.name		= "soc-audio",
		.pm		= &snd_soc_pm_ops,
	},
	.probe		= soc_probe,
};
```

The [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2411) and [`freeze`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2413) members both point at [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654), so a plain system suspend and a hibernation freeze run the same descent. The card object reached through [`dev_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) is the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) a machine driver registered, the same object whose [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) the descent iterates.

### snd_soc_suspend blocks userspace and mutes active DACs

[`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) is the first audio callback the PM core runs. According to its comment it "powers down audio subsystem for suspend". It returns early when the card never finished instantiating, waits for any in-flight resume work, then moves the ALSA control device to [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116) so userspace blocks until resume completes, and mutes active DACs:

```c
/* sound/soc/soc-core.c:654 */
/* powers down audio subsystem for suspend */
int snd_soc_suspend(struct device *dev)
{
	struct snd_soc_card *card = dev_get_drvdata(dev);
	struct snd_soc_component *component;
	struct snd_soc_pcm_runtime *rtd;
	int i;

	/* If the card is not initialized yet there is nothing to do */
	if (!snd_soc_card_is_instantiated(card))
		return 0;

	/*
	 * Due to the resume being scheduled into a workqueue we could
	 * suspend before that's finished - wait for it to complete.
	 */
	snd_power_wait(card->snd_card);

	/* we're going to block userspace touching us until resume completes */
	snd_power_change_state(card->snd_card, SNDRV_CTL_POWER_D3hot);

	/* mute any active DACs */
	soc_playback_digital_mute(card, 1);

	/* suspend all pcms */
	for_each_card_rtds(card, rtd) {
		if (rtd->dai_link->ignore_suspend)
			continue;

		snd_pcm_suspend_all(rtd->pcm);
	}
	...
```

The [`snd_soc_card_is_instantiated()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132) guard skips a card that was only ever parked on the deferred-probe list and never bound. [`snd_power_change_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L158) raises the control device to [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116), and a concurrent ioctl then waits through [`snd_power_wait()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1159) on the resume path instead of touching half-suspended hardware. That same [`D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116) reading is read back by [`snd_soc_dapm_get_idle_bias()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2222) further down to decide whether a codec that normally idles at standby should drop to bias off for suspend.

[`soc_playback_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L619) walks every runtime and every DAI, and mutes a DAI only when its playback direction is still active according to [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529), so the mute applies to the codec DAIs carrying audio at suspend time:

```c
/* sound/soc/soc-core.c:619 */
static void soc_playback_digital_mute(struct snd_soc_card *card, int mute)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_dai *dai;
	int playback = SNDRV_PCM_STREAM_PLAYBACK;
	int i;

	for_each_card_rtds(card, rtd) {

		if (rtd->dai_link->ignore_suspend)
			continue;

		for_each_rtd_dais(rtd, i, dai) {
			if (snd_soc_dai_stream_active(dai, playback))
				snd_soc_dai_digital_mute(dai, mute, playback);
		}
	}
}
```

[`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) reads the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) count the open and trigger paths maintain, and [`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386) dispatches to the DAI driver's [`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L194) op, declining a capture-direction mute on a DAI that set [`no_capture_mute`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L194):

```c
/* sound/soc/soc-dai.c:386 */
int snd_soc_dai_digital_mute(struct snd_soc_dai *dai, int mute,
			     int direction)
{
	int ret = -ENOTSUPP;

	/*
	 * ignore if direction was CAPTURE
	 * and it had .no_capture_mute flag
	 */
	if (dai->driver->ops &&
	    dai->driver->ops->mute_stream &&
	    (direction == SNDRV_PCM_STREAM_PLAYBACK ||
	     !dai->driver->ops->no_capture_mute))
		ret = dai->driver->ops->mute_stream(dai, mute, direction);

	return soc_dai_ret(dai, ret);
}
```

Muting runs before the PCMs stop so the codec output does not click as the data path comes down. The DAC is silenced while it still has clocks, and the stream is suspended afterward.

### Each active PCM lands at SNDRV_PCM_STATE_SUSPENDED

[`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) iterates the substreams of one PCM device and suspends each one that has a runtime and substream ops, skipping internal back-end links that never set ops, then quiesces each with [`snd_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639). According to its kerneldoc, "After this call, all streams are changed to SUSPENDED state":

```c
/* sound/core/pcm_native.c:1768 */
int snd_pcm_suspend_all(struct snd_pcm *pcm)
{
	struct snd_pcm_substream *substream;
	int stream, err = 0;

	if (! pcm)
		return 0;

	for_each_pcm_substream(pcm, stream, substream) {
		/* FIXME: the open/close code should lock this as well */
		if (!substream->runtime)
			continue;

		/*
		 * Skip BE dai link PCM's that are internal and may
		 * not have their substream ops set.
		 */
		if (!substream->ops)
			continue;

		err = snd_pcm_suspend(substream);
		if (err < 0 && err != -EBUSY)
			return err;
	}

	for_each_pcm_substream(pcm, stream, substream)
		snd_pcm_sync_stop(substream, false);

	return 0;
}
```

A `-EBUSY` from [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) is swallowed rather than propagated, because it means the stream was already suspended or in a state with nothing to suspend, so a partially-suspended card does not abort the whole walk. [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) takes the stream lock and runs the suspend transition through the generic [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387) machine with the [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739) action:

```c
/* sound/core/pcm_native.c:1753 */
static int snd_pcm_suspend(struct snd_pcm_substream *substream)
{
	guard(pcm_stream_lock_irqsave)(substream);
	return snd_pcm_action(&snd_pcm_action_suspend, substream,
			      ACTION_ARG_IGNORE);
}
```

Every PCM state change is expressed as a [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230), a four-stage function pointer struct, and the suspend instance fills the pre, do, and post stages (it has no undo stage, since a suspend has nothing to roll back):

```c
/* sound/core/pcm_native.c:1230 */
struct action_ops {
	int (*pre_action)(struct snd_pcm_substream *substream,
			  snd_pcm_state_t state);
	int (*do_action)(struct snd_pcm_substream *substream,
			 snd_pcm_state_t state);
	void (*undo_action)(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state);
	void (*post_action)(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state);
};
```

```c
/* sound/core/pcm_native.c:1739 */
static const struct action_ops snd_pcm_action_suspend = {
	.pre_action = snd_pcm_pre_suspend,
	.do_action = snd_pcm_do_suspend,
	.post_action = snd_pcm_post_suspend
};
```

[`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387) selects the single-stream path for a lone substream and the group path for a linked stream group, but in either case the inner [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) runs the three stages in order, returning the pre-stage error without touching hardware and choosing the post stage only when the do stage returned 0:

```c
/* sound/core/pcm_native.c:1306 */
static int snd_pcm_action_single(const struct action_ops *ops,
				 struct snd_pcm_substream *substream,
				 snd_pcm_state_t state)
{
	int res;
	
	res = ops->pre_action(substream, state);
	if (res < 0)
		return res;
	res = ops->do_action(substream, state);
	if (res == 0)
		ops->post_action(substream, state);
	else if (ops->undo_action)
		ops->undo_action(substream, state);
	return res;
}
```

[`snd_pcm_pre_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1696) is the stage that returns the `-EBUSY` that [`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) swallows. It refuses to suspend a stream that is already at [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) or in an unresumable state such as [`SNDRV_PCM_STATE_OPEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) or [`SNDRV_PCM_STATE_SETUP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L308), and otherwise claims the substream as [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366):

```c
/* sound/core/pcm_native.c:1696 */
/* suspend callback: state argument ignored */
static int snd_pcm_pre_suspend(struct snd_pcm_substream *substream,
			       snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	switch (runtime->state) {
	case SNDRV_PCM_STATE_SUSPENDED:
		return -EBUSY;
	/* unresumable PCM state; return -EBUSY for skipping suspend */
	case SNDRV_PCM_STATE_OPEN:
	case SNDRV_PCM_STATE_SETUP:
	case SNDRV_PCM_STATE_DISCONNECTED:
		return -EBUSY;
	}
	runtime->trigger_master = substream;
	return 0;
}
```

[`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) fires the suspend trigger on the running stream, which is what reaches the DAI trigger op and, on a SOF back-end, propagates toward the DSP and SoundWire path documented on the next page. It runs the trigger only on the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366) and only when [`snd_pcm_running()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L711) reports the stream actually running, then marks [`stop_operating`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L420) so the later [`snd_pcm_sync_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L639) knows a hardware stop is pending:

```c
/* sound/core/pcm_native.c:1713 */
static int snd_pcm_do_suspend(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->trigger_master != substream)
		return 0;
	if (! snd_pcm_running(substream))
		return 0;
	substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_SUSPEND);
	runtime->stop_operating = true;
	return 0; /* suspend unconditionally */
}
```

[`snd_pcm_post_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1726) is the stage that performs the state change. It snapshots the current runtime state into [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) so resume can restore it, then sets the state to [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) through [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) and wakes any waiter:

```c
/* sound/core/pcm_native.c:1726 */
static void snd_pcm_post_suspend(struct snd_pcm_substream *substream,
				 snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_trigger_tstamp(substream);
	runtime->suspended_state = runtime->state;
	runtime->status->suspended_state = runtime->suspended_state;
	__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_SUSPENDED);
	snd_pcm_timer_notify(substream, SNDRV_TIMER_EVENT_MSUSPEND);
	wake_up(&runtime->sleep);
	wake_up(&runtime->tsleep);
}
```

[`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) writes both the in-kernel [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the read-only mmap copy [`runtime->status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) in one call, so a userspace client that mapped the status page sees [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) without an ioctl:

```c
/* include/sound/pcm.h:725 */
static inline void __snd_pcm_set_state(struct snd_pcm_runtime *runtime,
				       snd_pcm_state_t state)
{
	runtime->state = state;
	runtime->status->state = state; /* copy for mmap */
}
```

Recording the pre-suspend value in [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) lets the matching resume return a stream that was RUNNING to RUNNING and one that was merely PREPARED to PREPARED, rather than collapsing every suspended stream to one state.

```
    PCM runtime state on suspend (snd_pcm_action_suspend stages)
    ─────────────────────────────────────────────────────────────

    prior runtime->state        pre_suspend verdict
    ────────────────────────     ───────────────────────────────
    SUSPENDED                    -EBUSY (already there)
    OPEN / SETUP / DISCONNECTED  -EBUSY (unresumable, skipped)
    RUNNING / DRAINING / other   accepted, claims trigger_master

              accepted stream
                    │
                    ▼  do_suspend: if snd_pcm_running
            SNDRV_PCM_TRIGGER_SUSPEND  +  stop_operating = true
                    │
                    ▼  post_suspend
            suspended_state = prior state   (saved for resume)
            __snd_pcm_set_state ─▶ SNDRV_PCM_STATE_SUSPENDED
                 (writes runtime->state and mmap status->state)
```

### The DAPM suspend event recomputes widget power

With the PCMs at [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314), [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) flushes delayed work, sends the DAPM suspend event, re-marks endpoints dirty, and syncs DAPM:

```c
/* sound/soc/soc-core.c:654 (DAPM event) */
	snd_soc_card_suspend_pre(card);

	/* close any waiting streams */
	snd_soc_flush_all_delayed_work(card);

	soc_dapm_suspend_resume(card, SND_SOC_DAPM_STREAM_SUSPEND);

	/* Recheck all endpoints too, their state is affected by suspend */
	snd_soc_dapm_mark_endpoints_dirty(card);
	snd_soc_dapm_sync(snd_soc_card_to_dapm(card));
```

[`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638) sends the same stream event to both directions of every non-ignored runtime:

```c
/* sound/soc/soc-core.c:638 */
static void soc_dapm_suspend_resume(struct snd_soc_card *card, int event)
{
	struct snd_soc_pcm_runtime *rtd;
	int stream;

	for_each_card_rtds(card, rtd) {

		if (rtd->dai_link->ignore_suspend)
			continue;

		for_each_pcm_streams(stream)
			snd_soc_dapm_stream_event(rtd, stream, event);
	}
}
```

The card suspend passes [`SND_SOC_DAPM_STREAM_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380) as the event, and [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) takes the DAPM mutex and forwards to [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598), which marks each DAI widget and recomputes widget power through [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252):

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

[`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) marks the DAI widget dirty and invalidates its cached input or output path power. For the suspend event it leaves the widget [`active`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4532) count unchanged, so the power walk re-derives each widget's power from the paths and brings idle paths down toward bias off without the widget itself being marked inactive:

```c
/* sound/soc/soc-dapm.c:4530 */
static void dapm_dai_stream_event(struct snd_soc_dai *dai, int stream, int event)
{
	struct snd_soc_dapm_widget *w;

	w = snd_soc_dai_get_widget(dai, stream);

	if (w) {
		unsigned int ep;

		dapm_mark_dirty(w, "stream event");

		if (w->id == snd_soc_dapm_dai_in) {
			ep = SND_SOC_DAPM_EP_SOURCE;
			dapm_widget_invalidate_input_paths(w);
		} else {
			ep = SND_SOC_DAPM_EP_SINK;
			dapm_widget_invalidate_output_paths(w);
		}

		switch (event) {
		case SND_SOC_DAPM_STREAM_START:
			w->active = 1;
			w->is_ep = ep;
			break;
		case SND_SOC_DAPM_STREAM_STOP:
			w->active = 0;
			w->is_ep = 0;
			break;
		case SND_SOC_DAPM_STREAM_SUSPEND:
		case SND_SOC_DAPM_STREAM_RESUME:
		case SND_SOC_DAPM_STREAM_PAUSE_PUSH:
		case SND_SOC_DAPM_STREAM_PAUSE_RELEASE:
			break;
		}
	}
}
```

### The bias descent runs in dapm_power_widgets

[`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) is where each DAPM context's bias is recomputed and applied. It first sets every context's [`target_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L53) to the floor (standby for an idle-bias context, off otherwise), then raises that target for any context that owns a powered widget, so a context with no live path keeps the off target:

```c
/* sound/soc/soc-dapm.c:2252 (target computation) */
	for_each_card_dapms(card, d) {
		if (snd_soc_dapm_get_idle_bias(d))
			d->target_bias_level = SND_SOC_BIAS_STANDBY;
		else
			d->target_bias_level = SND_SOC_BIAS_OFF;
	}

	dapm_reset(card);
	...
	list_for_each_entry(w, &card->dapm_dirty, dirty) {
		dapm_power_one_widget(w, &up_list, &down_list);
	}
```

After the widget power lists are built, the function powers widgets down before up and runs the per-context bias transitions through two async sequences. The pre sequence raises a context that needs to become active toward [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418), and the post sequence lowers a context whose target dropped:

```c
/* sound/soc/soc-dapm.c:2252 (sequences) */
	/* Run card bias changes at first */
	dapm_pre_sequence_async(dapm, 0);
	/* Run other bias changes in parallel */
	for_each_card_dapms(card, d) {
		if (d != dapm && d->bias_level != d->target_bias_level)
			async_schedule_domain(dapm_pre_sequence_async, d,
						&async_domain);
	}
	async_synchronize_full_domain(&async_domain);
	...
	/* Power down widgets first; try to avoid amplifying pops. */
	dapm_seq_run(card, &down_list, event, false);

	dapm_widget_update(card, update);

	/* Now power up. */
	dapm_seq_run(card, &up_list, event, true);

	/* Run all the bias changes in parallel */
	for_each_card_dapms(card, d) {
		if (d != dapm && d->bias_level != d->target_bias_level)
			async_schedule_domain(dapm_post_sequence_async, d,
						&async_domain);
	}
	async_synchronize_full_domain(&async_domain);
	/* Run card bias changes at last */
	dapm_post_sequence_async(dapm, 0);
```

[`dapm_post_sequence_async()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2126) is the step that walks a context down to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416). For a context that is at [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) with an off target (the state suspend leaves an idle codec in) it calls [`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) to reach off:

```c
/* sound/soc/soc-dapm.c:2126 */
static void dapm_post_sequence_async(void *data, async_cookie_t cookie)
{
	struct snd_soc_dapm_context *dapm = data;
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	int ret;

	/* If we just powered the last thing off drop to standby bias */
	if (dapm->bias_level == SND_SOC_BIAS_PREPARE &&
	    (dapm->target_bias_level == SND_SOC_BIAS_STANDBY ||
	     dapm->target_bias_level == SND_SOC_BIAS_OFF)) {
		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_STANDBY);
		if (ret != 0)
			dev_err(dev, "ASoC: Failed to apply standby bias: %d\n", ret);
	}

	/* If we're in standby and can support bias off then do that */
	if (dapm->bias_level == SND_SOC_BIAS_STANDBY &&
	    dapm->target_bias_level == SND_SOC_BIAS_OFF) {
		ret = snd_soc_dapm_set_bias_level(dapm, SND_SOC_BIAS_OFF);
		if (ret != 0)
			dev_err(dev, "ASoC: Failed to turn off bias: %d\n", ret);

		if (dev && cookie)
			pm_runtime_put(dev);
	}
	...
}
```

[`snd_soc_dapm_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1093) runs the card-level bias hooks and, for any context other than the card's own, applies the change through [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050):

```c
/* sound/soc/soc-dapm.c:1093 */
static int snd_soc_dapm_set_bias_level(struct snd_soc_dapm_context *dapm,
				       enum snd_soc_bias_level level)
{
	struct snd_soc_card *card = dapm->card;
	int ret = 0;

	trace_snd_soc_bias_level_start(dapm, level);

	ret = snd_soc_card_set_bias_level(card, dapm, level);
	if (ret != 0)
		goto out;

	if (dapm != card->dapm)
		ret = snd_soc_dapm_force_bias_level(dapm, level);

	if (ret != 0)
		goto out;

	ret = snd_soc_card_set_bias_level_post(card, dapm, level);
out:
	trace_snd_soc_bias_level_done(dapm, level);

	/* success */
	if (ret == 0)
		snd_soc_dapm_init_bias_level(dapm, level);

	return ret;
}
```

[`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050) is the leaf that drives the codec. It calls the component's [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L112) op through [`snd_soc_component_set_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L134) and records the new value in [`dapm->bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45):

```c
/* sound/soc/soc-dapm.c:1050 */
int snd_soc_dapm_force_bias_level(struct snd_soc_dapm_context *dapm,
	enum snd_soc_bias_level level)
{
	int ret = 0;

	if (dapm->component)
		ret = snd_soc_component_set_bias_level(dapm->component, level);

	if (ret == 0)
		dapm->bias_level = level;

	return ret;
}
```

The macro [`snd_soc_component_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L729) is the same leaf reached from a component handle rather than a DAPM context; it expands to [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050) on the component's own [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267) field and is what codec resume callbacks use to power a device back up before the DAPM core re-derives the graph:

```c
/* include/sound/soc-dapm.h:729 */
#define snd_soc_component_force_bias_level(c, l)	snd_soc_dapm_force_bias_level(&(c)->dapm, l)
```

The four bias values form an ordered enum, and the card suspend treats [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) (value 0) as the suspendable floor:

```c
/* include/sound/soc-dapm.h:415 */
enum snd_soc_bias_level {
	SND_SOC_BIAS_OFF = 0,
	SND_SOC_BIAS_STANDBY = 1,
	SND_SOC_BIAS_PREPARE = 2,
	SND_SOC_BIAS_ON = 3,
};
```

An idle context steps down these levels one at a time, PREPARE dropping to STANDBY and STANDBY dropping to OFF where it also releases the runtime PM reference:

```
    Bias descent for an idle context (dapm_post_sequence_async)
    ────────────────────────────────────────────────────────────
    enum order: OFF(0) ◀ STANDBY(1) ◀ PREPARE(2) ◀ ON(3)

       bias_level        target_bias_level     step taken
       ──────────        ─────────────────     ─────────────────────
       PREPARE           STANDBY or OFF    ─▶   set_bias_level STANDBY
       STANDBY           OFF               ─▶   set_bias_level OFF
                                                + pm_runtime_put(dev)

       ON ──▶ PREPARE ──▶ STANDBY ──▶ OFF      (suspend floor = OFF)
       reached step-by-step through snd_soc_dapm_set_bias_level,
       whose leaf snd_soc_dapm_force_bias_level calls the codec
       set_bias_level op and stores dapm->bias_level
```

### The per-component suspend reads the bias the walk left set

After the DAPM event has settled each context's bias, [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) walks each component and decides per component whether to suspend it. It reads the context bias with [`snd_soc_dapm_get_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1128) and switches on the result:

```c
/* sound/soc/soc-core.c:654 (component walk) */
	/* suspend all COMPONENTs */
	for_each_card_rtds(card, rtd) {

		if (rtd->dai_link->ignore_suspend)
			continue;

		for_each_rtd_components(rtd, i, component) {
			struct snd_soc_dapm_context *dapm = snd_soc_component_to_dapm(component);

			/*
			 * ignore if component was already suspended
			 */
			if (snd_soc_component_is_suspended(component))
				continue;

			/*
			 * If there are paths active then the COMPONENT will be
			 * held with bias _ON and should not be suspended.
			 */
			switch (snd_soc_dapm_get_bias_level(dapm)) {
			case SND_SOC_BIAS_STANDBY:
				/*
				 * If the COMPONENT is capable of idle
				 * bias off then being in STANDBY
				 * means it's doing something,
				 * otherwise fall through.
				 */
				if (!snd_soc_dapm_get_idle_bias(dapm)) {
					dev_dbg(component->dev,
						"ASoC: idle_bias_off CODEC on over suspend\n");
					break;
				}
				fallthrough;

			case SND_SOC_BIAS_OFF:
				snd_soc_component_suspend(component);
				if (component->regmap)
					regcache_mark_dirty(component->regmap);
				/* deactivate pins to sleep state */
				pinctrl_pm_select_sleep_state(component->dev);
				break;
			default:
				dev_dbg(component->dev,
					"ASoC: COMPONENT is on over suspend\n");
				break;
			}
		}
	}
```

[`snd_soc_dapm_get_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1128) is a one-line read of the [`bias_level`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L45) field that [`snd_soc_dapm_force_bias_level()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1050) stored during the power walk:

```c
/* sound/soc/soc-dapm.c:1128 */
enum snd_soc_bias_level snd_soc_dapm_get_bias_level(struct snd_soc_dapm_context *dapm)
{
	return dapm->bias_level;
}
```

A component left at [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) is suspended directly. A component at [`SND_SOC_BIAS_STANDBY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L417) is suspended only when [`snd_soc_dapm_get_idle_bias()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2222) reports the context uses bias off when idle, in which case standby means the device is doing something and the `fallthrough` carries it into the off case; a context that genuinely idles at standby reports false and the codec is left on. A component held at [`SND_SOC_BIAS_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L419) or [`SND_SOC_BIAS_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L418) by an active path falls into the default case and is not suspended. [`snd_soc_dapm_get_idle_bias()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2222) is the test the switch turns on, and it refines the context's [`idle_bias`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L47) flag with the codec's [`suspend_bias_off`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L180) capability while the card sits at [`SNDRV_CTL_POWER_D3hot`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1116):

```c
/* sound/soc/soc-dapm.c:2222 */
bool snd_soc_dapm_get_idle_bias(struct snd_soc_dapm_context *dapm)
{
	if (dapm->idle_bias) {
		struct snd_soc_component *component = snd_soc_dapm_to_component(dapm);
		unsigned int state = snd_power_get_state(dapm->card->snd_card);

		if ((state == SNDRV_CTL_POWER_D3hot || (state == SNDRV_CTL_POWER_D3cold)) &&
		    component)
			return !component->driver->suspend_bias_off;
	}

	return dapm->idle_bias;
}
```

[`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284) runs the component driver's optional [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L80) op and records the suspended flag, which [`snd_soc_component_is_suspended()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L298) reads at the top of the loop so a component shared across two runtimes is suspended once:

```c
/* sound/soc/soc-component.c:284 */
void snd_soc_component_suspend(struct snd_soc_component *component)
{
	if (component->driver->suspend)
		component->driver->suspend(component);
	component->suspended = 1;
}
```

```c
/* sound/soc/soc-component.c:298 */
int snd_soc_component_is_suspended(struct snd_soc_component *component)
{
	return component->suspended;
}
```

Marking the regmap cache dirty with [`regcache_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c) and selecting the pin sleep state with [`pinctrl_pm_select_sleep_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pinctrl/consumer.h) prepare the codec for the power loss the next stage causes. The dirty cache forces a full register restore on resume, and the sleep pin state lets the SoC drop pad power. With every suitable component suspended, [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) runs the card's [`suspend_post`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) hook through [`snd_soc_card_suspend_post()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L110) and returns 0, at which point the PM core descends into the SOF DSP device and the SoundWire master that the sibling SOF/SoundWire suspend page documents. The DSP firmware-context save, the bus clock-stop, and the codec move to the unattached state all happen there; from the card's point of view the audio data path is already silent, every PCM is at [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314), and every idle codec is at [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) with its register cache marked for restore.

```
    Per-component suspend decision from the bias the walk left
    ───────────────────────────────────────────────────────────
    snd_soc_dapm_get_bias_level(component dapm)  ▶  switch

       bias left set      idle_bias_off?     action
       ──────────────     ──────────────     ──────────────────────
       BIAS_OFF           —                  snd_soc_component_suspend
       BIAS_STANDBY       yes (fallthrough)  snd_soc_component_suspend
       BIAS_STANDBY       no                 leave on (doing work)
       BIAS_PREPARE / ON  —                  leave on (active path)

    suspend branch also: regcache_mark_dirty + pinctrl sleep state
    idle_bias_off = suspend_bias_off, read while card at D3hot/D3cold
```

### Full system suspend descent across all stages

The PM core walks the device hierarchy into the ASoC card's [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654), then the SOF PCI device's [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370) (running [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L238) and [`ctx_save`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L452)), then the SoundWire master's [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628) stopping the bus, and finally the HDA controller.

```
    System suspend descent (Intel MTL SOF + SoundWire)
    ──────────────────────────────────────────────────

    PM core (dpm_suspend, device hierarchy order)
        │
        ▼
    ASoC card device   dev_pm_ops snd_soc_pm_ops .suspend
    ┌──────────────────────────────────────────────────────┐
    │ snd_soc_suspend()                                    │
    │   soc_playback_digital_mute(card, 1)   mute DACs     │
    │   snd_pcm_suspend_all()   PCM ─▶ SUSPENDED           │
    │   soc_dapm_suspend_resume(STREAM_SUSPEND)            │
    │   snd_soc_component_suspend()   bias ─▶ BIAS_OFF     │
    └──────────────────────────────┬───────────────────────┘
                                   ▼
    SOF PCI device     dev_pm_ops sof_pci_pm system-sleep
    ┌──────────────────────────────────────────────────────┐
    │ snd_sof_suspend() ─▶ sof_suspend(dev, false)         │
    │   tear_down_all_pipelines (DSP was D0)               │
    │   snd_sof_dsp_hw_params_upon_resume()   arm replay   │
    │   pm_ops->ctx_save()   firmware context saved        │
    │   hda_dsp_suspend()  ─▶ DSP power ─▶ SOF_DSP_PM_D3   │
    └──────────────────────────────┬───────────────────────┘
                                   ▼
    SoundWire master aux device    dev_pm_ops intel_pm .suspend
    ┌──────────────────────────────────────────────────────┐
    │ intel_suspend() ─▶ sdw_intel_stop_bus()              │
    │   intel_stop_bus() ─▶ sdw_cdns_clock_stop()          │
    │   clock-stop / link power down                       │
    │   codec update_status ─▶ SDW_SLAVE_UNATTACHED        │
    └──────────────────────────────┬───────────────────────┘
                                   ▼
    HDA controller   reset, link reset, PCI D3
```
