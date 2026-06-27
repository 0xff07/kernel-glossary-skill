# PCM transitions

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Each move of a PCM substream between [`SNDRV_PCM_STATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) values is one named [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instance (start, stop, pause, suspend, resume, reset, prepare, drain), and a public entry point in [`sound/core/pcm_native.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c) runs it through the pre/do/undo/post protocol. The running-path transitions issue one [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) command to the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op in their do-step and commit the new state in their post-step, so [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) sends START and reaches RUNNING, [`snd_pcm_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569) sends STOP and reaches a caller-chosen state, [`snd_pcm_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1670) sends PAUSE_PUSH or PAUSE_RELEASE, and [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) and [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852) send SUSPEND and RESUME around the saved [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365). The configuration transitions [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) and [`snd_pcm_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1940) reach the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op or the internal reset rather than a trigger command, and [`snd_pcm_drain()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2105) and an underrun through [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168) are expressed in terms of the start and stop helpers. A userspace client drives all of them through the [`SNDRV_PCM_IOCTL_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) commands dispatched by [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363).

```
    Running-path transitions of one substream
    ──────────────────────────────────────────

      PREPARED ──START──▶ RUNNING ──PAUSE_PUSH──▶ PAUSED
         ▲                 │  ▲                     │
         │ PREPARE         │  └────PAUSE_RELEASE────┘
         │ (recover)       │
         │              XRUN│  DRAIN (playback)
      ┌──┴───┐    ┌─────────┼──────────┐
      │ XRUN │◀───┘         ▼          ▼
      └──────┘         ┌──────────┐  ┌────────┐
                       │ DRAINING │──│ SETUP  │  (buffer empty / DROP)
                       └──────────┘  └────────┘
                            buffer drained ─▶ drain_done ─▶ SETUP

      SUSPEND from RUNNING/PREPARED/PAUSED/DRAINING/XRUN ─▶ SUSPENDED
      RESUME ─▶ restores the saved suspended_state
```

## SUMMARY

The transitions are the named [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instances [`snd_pcm_action_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1490), [`snd_pcm_action_stop`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1554), [`snd_pcm_action_pause`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1670), [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739), [`snd_pcm_action_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1845), [`snd_pcm_action_reset`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1934), [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984), and [`snd_pcm_action_drain_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2092), each a set of pre/do/undo/post functions. The public entry points map one to one onto them. [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) runs the start action to RUNNING, [`snd_pcm_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569) runs the stop action to a caller-chosen state, [`snd_pcm_stop_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1599) stops to XRUN through [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168), and [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753), [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852), [`snd_pcm_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1940), [`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997), [`snd_pcm_drain()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2105), and [`snd_pcm_drop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2233) run the rest.

The do-step of each running-path action calls the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op with the matching command and the post-step commits the new state, while the start, pause, and resume actions also carry an undo-step that reverses the trigger when a linked-group peer fails. The prepare action calls the driver [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op and resets the ring pointers, the reset action rewinds the pointers without changing the state, and the drain action moves a playback stream to DRAINING and lets the hardware-pointer path call [`snd_pcm_drain_done()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1584) to SETUP when the buffer empties. An underrun is not a separate action; [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168) reuses the stop action with XRUN as the destination state. On an ASoC link the per-command [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) entries these actions call are [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198), [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979), and [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054), so each ALSA transition runs the matching ASoC fan-out across the link's components and DAIs.

## SPECIFICATIONS

The PCM transitions are a Linux kernel software construct and have no standalone hardware specification. The state set, the legal transitions, the [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) commands, and the [`SNDRV_PCM_IOCTL_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) numbers that drive them are defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). On x86-64 the underlying controllers (Intel High Definition Audio, USB Audio Class, SoundWire codecs) define what their [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op does at each command while leaving the transition model to the kernel.

## LINUX KERNEL

### Transition action_ops instances (pcm_native.c)

- [`'snd_pcm_action_start':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1490): [`snd_pcm_pre_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1438) / [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) / [`snd_pcm_undo_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1466) / [`snd_pcm_post_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1475); sets RUNNING (or XRUN on `-EPIPE`)
- [`'snd_pcm_action_stop':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1554): [`snd_pcm_pre_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1520) / [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530) / [`snd_pcm_post_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1541); sets the state passed by the caller
- [`'snd_pcm_action_pause':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1670): [`snd_pcm_pre_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1613) / [`snd_pcm_do_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1628) / [`snd_pcm_undo_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1644) / [`snd_pcm_post_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1654); sets PAUSED (push) or RUNNING (release)
- [`'snd_pcm_action_suspend':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739): [`snd_pcm_pre_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1696) / [`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) / [`snd_pcm_post_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1726); saves the old state and sets SUSPENDED
- [`'snd_pcm_action_resume':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1845): [`snd_pcm_pre_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1802) / [`snd_pcm_do_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814) / [`snd_pcm_undo_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1828) / [`snd_pcm_post_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1836); restores [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365)
- [`'snd_pcm_action_reset':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1934): [`snd_pcm_pre_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1892) / [`snd_pcm_do_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1907) / [`snd_pcm_post_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1923); zeroes pointers, leaves the state unchanged
- [`'snd_pcm_action_prepare':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984): [`snd_pcm_pre_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1950) / [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) / [`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976); sets PREPARED
- [`'snd_pcm_action_drain_init':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2092): [`snd_pcm_pre_drain_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2028) / [`snd_pcm_do_drain_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2042) / [`snd_pcm_post_drain_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2087); sets DRAINING or SETUP

### Public entry points (pcm_native.c, pcm_lib.c)

- [`'\<snd_pcm_start\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504): start all linked streams to RUNNING (caller holds the stream lock); [`snd_pcm_start_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1511) takes the lock first
- [`'\<snd_pcm_stop\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569): stop the running streams and set them to the given state
- [`'\<snd_pcm_stop_xrun\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1599): stop a running stream as XRUN, taking the lock itself, via [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168)
- [`'\<snd_pcm_drain_done\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1584): stop only the given stream to SETUP at end of drain via [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306)
- [`'\<snd_pcm_suspend\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) / [`'\<snd_pcm_suspend_all\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768): suspend one substream, or every substream of a PCM
- [`'\<snd_pcm_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852): resume the linked streams (returns `-ENOSYS` without `CONFIG_PM`)
- [`'\<snd_pcm_reset\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1940): reset the ring-buffer pointers without a state change
- [`'\<snd_pcm_prepare\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997): undo a pause or suspend, then run the prepare action to PREPARED
- [`'\<snd_pcm_drain\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2105): move playback to DRAINING and wait for the buffer to empty
- [`'\<snd_pcm_drop\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2233): stop immediately to SETUP, discarding queued samples
- [`'\<__snd_pcm_xrun\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168): timestamp and stop a stream to XRUN, reached from the hw-pointer update and from [`snd_pcm_stop_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1599)

### Userspace ioctl surface (pcm_native.c, asound.h)

- [`'\<snd_pcm_common_ioctl\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363): the per-stream dispatcher routing `SNDRV_PCM_IOCTL_*` numbers to the transition helpers
- [`'SNDRV_PCM_IOCTL_PREPARE':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692): the PREPARE, RESET, START, DROP, DRAIN, PAUSE, RESUME, and XRUN command numbers
- [`'\<snd_pcm_sync_ptr\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118): copy [`runtime->status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) out for [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689)
- [`'\<snd_pcm_status64\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1031): fill the status block for [`SNDRV_PCM_IOCTL_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L684), reading [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM chapter describing the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback, the [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) commands, and the move to XRUN on underrun
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): the trigger timestamp each transition latches
- [`Documentation/sound/designs/powersave.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/powersave.rst): the runtime-PM context in which suspend and resume run

## OTHER SOURCES

- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [alsa-lib snd_pcm_state and the PCM state diagram](https://www.alsa-project.org/alsa-doc/alsa-lib/group___p_c_m.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The table maps each transition to its [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instance, the [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) command its do-step issues to the driver, and the resulting [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364).

| transition | action_ops | do_action trigger command | resulting state |
|------------|------------|---------------------------|-----------------|
| prepare | [`snd_pcm_action_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1984) | (none; calls [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op) | [`SNDRV_PCM_STATE_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L309) |
| start | [`snd_pcm_action_start`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1490) | [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) (XRUN on `-EPIPE`) |
| stop | [`snd_pcm_action_stop`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1554) | [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) | caller-chosen (SETUP or XRUN) |
| pause push | [`snd_pcm_action_pause`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1670) | [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) | [`SNDRV_PCM_STATE_PAUSED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L313) |
| pause release | [`snd_pcm_action_pause`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1670) | [`SNDRV_PCM_TRIGGER_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L101) | [`SNDRV_PCM_STATE_RUNNING`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L310) |
| suspend | [`snd_pcm_action_suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1739) | [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) | [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) |
| resume | [`snd_pcm_action_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1845) | [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) | restored [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) |
| reset | [`snd_pcm_action_reset`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1934) | (none; resets pointers) | unchanged |
| drain init | [`snd_pcm_action_drain_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2092) | [`SNDRV_PCM_TRIGGER_DRAIN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L104) (when supported) | DRAINING or SETUP |

The seven trigger commands are the only values the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op receives:

```c
/* include/sound/pcm.h:98 */
#define SNDRV_PCM_TRIGGER_STOP		0
#define SNDRV_PCM_TRIGGER_START		1
#define SNDRV_PCM_TRIGGER_PAUSE_PUSH	2
#define SNDRV_PCM_TRIGGER_PAUSE_RELEASE	3
#define SNDRV_PCM_TRIGGER_SUSPEND	4
#define SNDRV_PCM_TRIGGER_RESUME	5
#define SNDRV_PCM_TRIGGER_DRAIN		6
```

## DETAILS

### Prepare sets PREPARED

[`snd_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1997) first unwinds a pause or suspend back to a triggerable state, then runs the prepare action non-atomically. The do-step [`snd_pcm_do_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1965) synchronises any in-flight stop, calls the driver [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, and resets the ring-buffer pointers through [`snd_pcm_do_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1907):

```c
/* sound/core/pcm_native.c:1965 */
static int snd_pcm_do_prepare(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	int err;
	snd_pcm_sync_stop(substream, true);
	err = substream->ops->prepare(substream);
	if (err < 0)
		return err;
	return snd_pcm_do_reset(substream, state);
}
```

The post-step [`snd_pcm_post_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1976) commits PREPARED with the locked [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621). [`snd_pcm_pre_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1950) admits the prepare from any state but OPEN and DISCONNECTED, so a stream in XRUN can recover by re-preparing.

### Start sets RUNNING, or XRUN on -EPIPE

[`snd_pcm_pre_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1438) admits the start only from PREPARED, rejects a playback stream with no data queued, and elects the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366):

```c
/* sound/core/pcm_native.c:1438 */
static int snd_pcm_pre_start(struct snd_pcm_substream *substream,
			     snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->state != SNDRV_PCM_STATE_PREPARED)
		return -EBADFD;
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK &&
	    !snd_pcm_playback_data(substream))
		return -EPIPE;
	runtime->trigger_tstamp_latched = false;
	runtime->trigger_master = substream;
	return 0;
}
```

[`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) issues [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) to the driver op. According to the comment "XRUN happened during the start", a `-EPIPE` return sets XRUN directly rather than letting the post-step set RUNNING:

```c
/* sound/core/pcm_native.c:1452 */
static int snd_pcm_do_start(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state)
{
	int err;

	if (substream->runtime->trigger_master != substream)
		return 0;
	err = substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_START);
	/* XRUN happened during the start */
	if (err == -EPIPE)
		__snd_pcm_set_state(substream->runtime, SNDRV_PCM_STATE_XRUN);
	return err;
}
```

On the success path [`snd_pcm_post_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1475) sets the requested state (RUNNING, passed by [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504)) and primes the hardware-pointer jiffies accounting. If a later group member fails its do-step, [`snd_pcm_undo_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1466) issues [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) to the members that already started. [`snd_pcm_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1504) is the public entry, running the start action to RUNNING with the stream lock already held:

```c
/* sound/core/pcm_native.c:1504 */
int snd_pcm_start(struct snd_pcm_substream *substream)
{
	return snd_pcm_action(&snd_pcm_action_start, substream,
			      SNDRV_PCM_STATE_RUNNING);
}
```

That entry runs the action whose one START command lands the stream in RUNNING on success or in XRUN when the trigger returns -EPIPE:

```
    Start action: one command, two landing states
    ───────────────────────────────────────────────

    pre_start: state == PREPARED ?  ──no──▶ -EBADFD (rejected)
         │ yes, trigger_master elected
         ▼
    do_start: trigger(SNDRV_PCM_TRIGGER_START)
         │
         ├── returns -EPIPE ──▶ do_start sets XRUN itself
         │
         └── returns 0      ──▶ post_start sets RUNNING

    group rollback: undo_start issues SNDRV_PCM_TRIGGER_STOP
    to peers that already started when a later member fails.
```

### Stop sets the caller-chosen state

[`snd_pcm_pre_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1520) rejects only the OPEN state and elects the master. [`snd_pcm_do_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1530) issues [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) only when the stream is actually running, and according to its comment returns 0 "unconditionally stop all substreams" so even a non-running member of a group advances:

```c
/* sound/core/pcm_native.c:1530 */
static int snd_pcm_do_stop(struct snd_pcm_substream *substream,
			   snd_pcm_state_t state)
{
	if (substream->runtime->trigger_master == substream &&
	    snd_pcm_running(substream)) {
		substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_STOP);
		substream->runtime->stop_operating = true;
	}
	return 0; /* unconditionally stop all substreams */
}
```

[`snd_pcm_post_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1541) sets whatever state the caller passed (skipping the write when the stream is already in that state) and wakes the drain and transfer waiters:

```c
/* sound/core/pcm_native.c:1541 */
static void snd_pcm_post_stop(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->state != state) {
		snd_pcm_trigger_tstamp(substream);
		__snd_pcm_set_state(runtime, state);
		snd_pcm_timer_notify(substream, SNDRV_TIMER_EVENT_MSTOP);
	}
	wake_up(&runtime->sleep);
	wake_up(&runtime->tsleep);
}
```

[`snd_pcm_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569) takes the destination state as an argument, which lets the same action serve a clean stop to SETUP, an underrun to XRUN, and a drop. [`snd_pcm_drop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2233) calls it with SETUP after first releasing any pause:

```c
/* sound/core/pcm_native.c:2233 */
static int snd_pcm_drop(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime;
	int result = 0;
	...
	guard(pcm_stream_lock_irq)(substream);
	/* resume pause */
	if (runtime->state == SNDRV_PCM_STATE_PAUSED)
		snd_pcm_pause(substream, false);

	snd_pcm_stop(substream, SNDRV_PCM_STATE_SETUP);

	return result;
}
```

The drop is one of three callers that hand the stop action a destination, SETUP for a clean stop or a finished drain and XRUN for an underrun, which the post step then commits:

```
    Stop action: the resulting state is a caller argument
    ──────────────────────────────────────────────────────

    caller                         state passed to stop
    ──────────────────────────────────────────────────────
    snd_pcm_drop()         ──▶     SNDRV_PCM_STATE_SETUP
    snd_pcm_drain_done()   ──▶     SNDRV_PCM_STATE_SETUP
    __snd_pcm_xrun()       ──▶     SNDRV_PCM_STATE_XRUN
                                 │
                                 ▼
              ┌───────────────────────────────────────┐
              │ do_stop: trigger(TRIGGER_STOP) when   │
              │   trigger_master and running          │
              │ post_stop: __snd_pcm_set_state(state) │
              └───────────────────────────────────────┘

    one action serves every stop; do_stop returns 0 so even a
    non-running group member advances to the passed state.
```

### Pause sets PAUSED or RUNNING

The pause action carries a boolean push/release in its state argument, decoded by the [`pause_pushed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1611) macro. [`snd_pcm_do_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1628) issues [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100) or [`SNDRV_PCM_TRIGGER_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L101) by that flag:

```c
/* sound/core/pcm_native.c:1628 */
static int snd_pcm_do_pause(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state)
{
	if (substream->runtime->trigger_master != substream)
		return 0;
	...
	substream->runtime->hw_ptr_jiffies = jiffies - HZ * 1000;
	return substream->ops->trigger(substream,
				       pause_pushed(state) ?
				       SNDRV_PCM_TRIGGER_PAUSE_PUSH :
				       SNDRV_PCM_TRIGGER_PAUSE_RELEASE);
}
```

[`snd_pcm_post_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1654) sets PAUSED on a push and RUNNING on a release, and [`snd_pcm_undo_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1644) issues the opposite trigger on a group rollback:

```c
/* sound/core/pcm_native.c:1654 */
static void snd_pcm_post_pause(struct snd_pcm_substream *substream,
			       snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_trigger_tstamp(substream);
	if (pause_pushed(state)) {
		__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_PAUSED);
		snd_pcm_timer_notify(substream, SNDRV_TIMER_EVENT_MPAUSE);
		wake_up(&runtime->sleep);
		wake_up(&runtime->tsleep);
	} else {
		__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_RUNNING);
		snd_pcm_timer_notify(substream, SNDRV_TIMER_EVENT_MCONTINUE);
	}
}
```

[`snd_pcm_pre_pause()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1613) demands RUNNING for a push and PAUSED for a release, and rejects a device that does not advertise [`SNDRV_PCM_INFO_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L287).

### Suspend saves the state and resume restores it

[`snd_pcm_do_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1713) issues [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) when the stream is running and returns 0 to suspend the rest unconditionally. [`snd_pcm_post_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1726) records the pre-suspend state into [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) (and its mmap copy) before setting SUSPENDED:

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

[`snd_pcm_do_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814) issues [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) only when the saved state was RUNNING (or DRAINING for a playback stream), and [`snd_pcm_post_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1836) writes the saved state straight back:

```c
/* sound/core/pcm_native.c:1836 */
static void snd_pcm_post_resume(struct snd_pcm_substream *substream,
				snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_trigger_tstamp(substream);
	__snd_pcm_set_state(runtime, runtime->suspended_state);
	snd_pcm_timer_notify(substream, SNDRV_TIMER_EVENT_MRESUME);
}
```

[`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) is the per-substream entry that drives the SUSPENDED transition, taking the stream lock itself and running the suspend action with [`ACTION_ARG_IGNORE`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1303) because the post-step computes the saved state rather than taking one from the caller:

```c
/* sound/core/pcm_native.c:1753 */
static int snd_pcm_suspend(struct snd_pcm_substream *substream)
{
	guard(pcm_stream_lock_irqsave)(substream);
	return snd_pcm_action(&snd_pcm_action_suspend, substream,
			      ACTION_ARG_IGNORE);
}
```

[`snd_pcm_suspend_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1768) drives the suspend across a whole card from the driver suspend handler, calling [`snd_pcm_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1753) on each substream that has a [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L353) and an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L351), and tolerating the `-EBUSY` that [`snd_pcm_pre_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1696) returns for an unresumable state such as OPEN or SETUP:

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

Each stream that handler suspends makes the same round-trip, the prior state saved into suspended_state, SUSPENDED committed, and that saved value written back on resume:

```
    Suspend and resume: the saved-state round-trip
    ───────────────────────────────────────────────

    ┌─────────────────────────────────────────────┐
    │ runtime->state  =  RUNNING / PREPARED /     │
    │                    PAUSED / DRAINING / XRUN │
    └─────────────────────────────────────────────┘
            │ post_suspend saves the prior state into
            ▼
    ┌────────────────────────────────────────┐
    │ suspended_state   (plus its mmap copy) │
    └────────────────────────────────────────┘
            │ post_suspend then commits
            ▼
    ┌──────────────────────────────┐
    │ runtime->state  =  SUSPENDED │
    └──────────────────────────────┘
            │ post_resume reads suspended_state back
            ▼
    ┌────────────────────────────────────────────┐
    │ runtime->state  =  suspended_state         │
    │ (do_resume sends TRIGGER_RESUME first when │
    │  the saved state was RUNNING or DRAINING)  │
    └────────────────────────────────────────────┘
```

### Reset rewinds the pointers without changing the state

[`snd_pcm_pre_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1892) admits the reset from RUNNING, PREPARED, PAUSED, or SUSPENDED only. The do-step [`snd_pcm_do_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1907) runs the internal [`SNDRV_PCM_IOCTL1_RESET`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1907) op and rebases the hardware pointer, and the matching [`snd_pcm_action_reset`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1934) has no post-step that calls [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725), so the lifecycle value is left where it was:

```c
/* sound/core/pcm_native.c:1907 */
static int snd_pcm_do_reset(struct snd_pcm_substream *substream,
			    snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	int err = snd_pcm_ops_ioctl(substream, SNDRV_PCM_IOCTL1_RESET, NULL);
	if (err < 0)
		return err;
	guard(pcm_stream_lock_irq)(substream);
	runtime->hw_ptr_base = 0;
	runtime->hw_ptr_interrupt = runtime->status->hw_ptr -
		runtime->status->hw_ptr % runtime->period_size;
	runtime->silence_start = runtime->status->hw_ptr;
	runtime->silence_filled = 0;
	return 0;
}
```

### Drain moves playback to DRAINING then SETUP

The drain action is the one transition whose do-step itself calls the lower-level start and stop helpers. [`snd_pcm_do_drain_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2042) moves a running playback stream to DRAINING, starts a prepared one that has data, demotes an empty or XRUN stream straight to SETUP, and for capture stops the stream to SETUP or DRAINING by how much is buffered:

```c
/* sound/core/pcm_native.c:2042 */
static int snd_pcm_do_drain_init(struct snd_pcm_substream *substream,
				 snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		switch (runtime->state) {
		case SNDRV_PCM_STATE_PREPARED:
			/* start playback stream if possible */
			if (! snd_pcm_playback_empty(substream)) {
				snd_pcm_do_start(substream, SNDRV_PCM_STATE_DRAINING);
				snd_pcm_post_start(substream, SNDRV_PCM_STATE_DRAINING);
			} else {
				__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_SETUP);
			}
			break;
		case SNDRV_PCM_STATE_RUNNING:
			__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_DRAINING);
			break;
		case SNDRV_PCM_STATE_XRUN:
			__snd_pcm_set_state(runtime, SNDRV_PCM_STATE_SETUP);
			break;
		default:
			break;
		}
	} else {
		/* stop running stream */
		if (runtime->state == SNDRV_PCM_STATE_RUNNING) {
			snd_pcm_state_t new_state;

			new_state = snd_pcm_capture_avail(runtime) > 0 ?
				SNDRV_PCM_STATE_DRAINING : SNDRV_PCM_STATE_SETUP;
			snd_pcm_do_stop(substream, new_state);
			snd_pcm_post_stop(substream, new_state);
		}
	}

	if (runtime->state == SNDRV_PCM_STATE_DRAINING &&
	    runtime->trigger_master == substream &&
	    (runtime->hw.info & SNDRV_PCM_INFO_DRAIN_TRIGGER))
		return substream->ops->trigger(substream,
					       SNDRV_PCM_TRIGGER_DRAIN);

	return 0;
}
```

After the action sets DRAINING, [`snd_pcm_drain()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2105) sleeps until each draining playback stream empties. When the buffer drains the hardware-pointer path calls [`snd_pcm_drain_done()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1584), which completes the drain by running the stop action through [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) on that one stream to SETUP, ending the wait without disturbing any linked-group peer:

```c
/* sound/core/pcm_native.c:1584 */
int snd_pcm_drain_done(struct snd_pcm_substream *substream)
{
	return snd_pcm_action_single(&snd_pcm_action_stop, substream,
				     SNDRV_PCM_STATE_SETUP);
}
```

A drain timeout instead calls [`snd_pcm_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569) to SETUP and returns `-EIO`.

```
    do_drain_init: destination depends on direction and state
    ──────────────────────────────────────────────────────────

    PLAYBACK, state is            outcome
    ──────────────────────────────────────────────────────────
    PREPARED and has data    ──▶  do_start ──▶ DRAINING
    PREPARED and empty       ──▶  SETUP (nothing to play out)
    RUNNING                  ──▶  DRAINING
    XRUN                     ──▶  SETUP

    CAPTURE, state is             outcome
    ──────────────────────────────────────────────────────────
    RUNNING and avail > 0    ──▶  do_stop ──▶ DRAINING
    RUNNING and empty        ──▶  do_stop ──▶ SETUP

    then, while DRAINING, the hw-pointer path calls
    snd_pcm_drain_done() ──▶ stop action ──▶ SETUP (per stream)
```

### XRUN is a stop to the XRUN state

An underrun or overrun is not a separate action. [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168) timestamps the event and calls [`snd_pcm_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1569) with XRUN as the destination, so the stop action does the work and [`snd_pcm_post_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1541) commits the state:

```c
/* sound/core/pcm_lib.c:168 */
void __snd_pcm_xrun(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime = substream->runtime;

	trace_xrun(substream);
	if (runtime->tstamp_mode == SNDRV_PCM_TSTAMP_ENABLE) {
		struct timespec64 tstamp;

		snd_pcm_gettime(runtime, &tstamp);
		runtime->status->tstamp.tv_sec = tstamp.tv_sec;
		runtime->status->tstamp.tv_nsec = tstamp.tv_nsec;
	}
	snd_pcm_stop(substream, SNDRV_PCM_STATE_XRUN);
	...
}
```

[`snd_pcm_stop_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1599) is the variant a driver calls from outside the stream lock; it takes the lock itself and reaches [`__snd_pcm_xrun()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L168) only when [`snd_pcm_running()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1437) is still true, so it forces the XRUN transition from the running path and is otherwise a no-op:

```c
/* sound/core/pcm_native.c:1599 */
int snd_pcm_stop_xrun(struct snd_pcm_substream *substream)
{
	guard(pcm_stream_lock_irqsave)(substream);
	if (substream->runtime && snd_pcm_running(substream))
		__snd_pcm_xrun(substream);
	return 0;
}
```

A stream then leaves XRUN only through a recovery prepare.

### Userspace drives the transitions through snd_pcm_common_ioctl

A userspace client, or alsa-lib on its behalf, never names an action. It issues an ioctl on the PCM character device, and [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) rejects a disconnected stream, waits for the card to power up, then switches the [`SNDRV_PCM_IOCTL_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) number onto the transition helper:

```c
/* sound/core/pcm_native.c:3363 */
static int snd_pcm_common_ioctl(struct file *file,
				 struct snd_pcm_substream *substream,
				 unsigned int cmd, void __user *arg)
{
	struct snd_pcm_file *pcm_file = file->private_data;
	int res;

	if (PCM_RUNTIME_CHECK(substream))
		return -ENXIO;

	if (substream->runtime->state == SNDRV_PCM_STATE_DISCONNECTED)
		return -EBADFD;

	res = snd_power_wait(substream->pcm->card);
	if (res < 0)
		return res;

	switch (cmd) {
	...
```

The transition arms of that switch dispatch to the entry points named above:

```c
/* sound/core/pcm_native.c:3412 */
	case SNDRV_PCM_IOCTL_PREPARE:
		return snd_pcm_prepare(substream, file);
	case SNDRV_PCM_IOCTL_RESET:
		return snd_pcm_reset(substream);
	case SNDRV_PCM_IOCTL_START:
		return snd_pcm_start_lock_irq(substream);
	...
	case SNDRV_PCM_IOCTL_RESUME:
		return snd_pcm_resume(substream);
	case SNDRV_PCM_IOCTL_XRUN:
		return snd_pcm_xrun(substream);
	...
	case SNDRV_PCM_IOCTL_DRAIN:
		return snd_pcm_drain(substream, file);
	case SNDRV_PCM_IOCTL_DROP:
		return snd_pcm_drop(substream);
	case SNDRV_PCM_IOCTL_PAUSE:
		return snd_pcm_pause_lock_irq(substream, (unsigned long)arg);
```

So [`SNDRV_PCM_IOCTL_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) drives the prepare action to PREPARED, [`SNDRV_PCM_IOCTL_START`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L694) the start action to RUNNING, [`SNDRV_PCM_IOCTL_DROP`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L695) the stop action to SETUP, [`SNDRV_PCM_IOCTL_DRAIN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L696) the drain action through DRAINING to SETUP, [`SNDRV_PCM_IOCTL_PAUSE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L697) the pause action to PAUSED or RUNNING, [`SNDRV_PCM_IOCTL_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L693) the reset action with no state change, [`SNDRV_PCM_IOCTL_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L699) the resume action back to the saved state, and [`SNDRV_PCM_IOCTL_XRUN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L700) forces a running stream to XRUN. A player such as `aplay` opens the device (OPEN), sets parameters and calls prepare (PREPARED), writes the first periods and starts the stream (RUNNING), relies on the kernel demoting to XRUN on an underrun and re-preparing to recover, and at end of stream calls drain so the final partial buffer plays out (DRAINING then SETUP) rather than being dropped.

```
    snd_pcm_common_ioctl: command number to transition
    ───────────────────────────────────────────────────

    SNDRV_PCM_IOCTL_*    entry point             resulting state
    ──────────────────────────────────────────────────────────────
    PREPARE          ──▶ snd_pcm_prepare()        PREPARED
    RESET            ──▶ snd_pcm_reset()          unchanged
    START            ──▶ snd_pcm_start_lock_irq() RUNNING
    DROP             ──▶ snd_pcm_drop()           SETUP
    DRAIN            ──▶ snd_pcm_drain()          DRAINING ──▶ SETUP
    PAUSE            ──▶ snd_pcm_pause_lock_irq()  PAUSED / RUNNING
    RESUME           ──▶ snd_pcm_resume()         saved state
    XRUN             ──▶ snd_pcm_xrun()           XRUN

    a disconnected stream is rejected -EBADFD before the switch;
    snd_power_wait() blocks until the card has powered up.
```

### Userspace reads the current state through status and sync_ptr

The same ioctl surface lets a client read back the state these transitions reach without driving one. [`snd_pcm_status64()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1031) fills the status block for [`SNDRV_PCM_IOCTL_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L684) under the stream lock, copying the live [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) and returning early for OPEN, so a poller sees exactly which transition the substream last completed:

```c
/* sound/core/pcm_native.c:1054 */
	status->state = runtime->state;
	status->suspended_state = runtime->suspended_state;
	if (status->state == SNDRV_PCM_STATE_OPEN)
		return 0;
```

[`snd_pcm_sync_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3118) backs [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689), the fast pointer-exchange path that mmap clients use every period; it samples the same [`status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) from the mmap-shared [`snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L630) under the lock and hands it back beside the hardware pointer, which is how a running client notices a kernel-side demotion to XRUN or SUSPENDED:

```c
/* sound/core/pcm_native.c:3150 */
		sstatus.state = status->state;
		sstatus.hw_ptr = status->hw_ptr;
		sstatus.tstamp = status->tstamp;
		sstatus.suspended_state = status->suspended_state;
		sstatus.audio_tstamp = status->audio_tstamp;
```

### The ASoC layer implements the per-command ops

For a non-DPCM ASoC link the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) entries [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) installs are ASoC functions, wired up in [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2911) when the link is built:

```c
/* sound/soc/soc-pcm.c:2959 */
		rtd->ops.open		= soc_pcm_open;
		rtd->ops.hw_params	= soc_pcm_hw_params;
		rtd->ops.prepare	= soc_pcm_prepare;
		rtd->ops.trigger	= soc_pcm_trigger;
		rtd->ops.hw_free	= soc_pcm_hw_free;
		rtd->ops.close		= soc_pcm_close;
		rtd->ops.pointer	= soc_pcm_pointer;
```

Each ALSA transition that reaches one of these ops runs the matching ASoC fan-out across the link. The start, stop, pause, suspend, and resume actions reach [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198), which translates the one [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) command into an ordered sweep of the link, its DAIs, and its components, rolling a failed START back with the mirror STOP command:

```c
/* sound/soc/soc-pcm.c:1198 */
static int soc_pcm_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int ret = 0, r = 0, i;
	int rollback = 0;
	int start = 0, stop = 0;
	...
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for (i = 0; i < TRIGGER_MAX; i++) {
			r = trigger[start][i](substream, cmd, 0);
			if (r < 0)
				break;
		}
	}
	...
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		for (i = TRIGGER_MAX; i > 0; i--) {
			r = trigger[stop][i - 1](substream, cmd, rollback);
			if (r < 0)
				ret = r;
		}
	}

	return ret;
}
```

The other configuration ops follow the same shape off their own transitions. The [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) runs the link prepare on the prepare action, the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) configures every DAI on the SETUP move, and the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) tears that configuration back down on the HW_FREE move, so the per-command transitions documented above each drive an ASoC sweep across the link's components and DAIs rather than a single chip register write.

```
    Each ALSA transition reaches one snd_pcm_ops entry
    ───────────────────────────────────────────────────

    ALSA transition          snd_pcm_ops entry (ASoC)
    ──────────────────────────────────────────────────────
    start stop pause     ──▶ soc_pcm_trigger    (TRIGGER_*)
    suspend resume       ──▶ soc_pcm_trigger    (TRIGGER_*)
    prepare              ──▶ soc_pcm_prepare
    hw_params (SETUP)    ──▶ soc_pcm_hw_params
    hw_free  (HW_FREE)   ──▶ soc_pcm_hw_free

    each entry fans out across the link, its DAIs, and its
    components instead of writing one chip register.
```
