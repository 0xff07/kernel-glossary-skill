# PCM state machine

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ALSA PCM substream carries one lifecycle value, [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), of type [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306), and every transition between its values runs through one dispatch model built on the [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) callback set. The PCM core never writes the state field from scattered code. Each transition is described by a four-function instance of [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) (a [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231) precondition check, a [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233) that calls the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op, an optional [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235) for rollback, and a [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) that commits the new state), and [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) runs the three or four functions in order. The state is committed by [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725), which writes [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the read-only mmap copy [`runtime->status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) together so a userspace client that mapped the status page sees the same value. The driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op receives one of the [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) commands at each running-path transition, and when substreams are linked with [`snd_pcm_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2279) the whole group transitions together under the group lock through [`snd_pcm_action_group()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246).

```
    PCM state-transition map (SNDRV_PCM_STATE_*)
    ────────────────────────────────────────────

          open()
            │
            ▼
        ┌────────┐  HW_PARAMS   ┌────────┐  PREPARE   ┌──────────┐
        │  OPEN  │─────────────▶│ SETUP  │───────────▶│ PREPARED │
        │        │◀─────────────│        │◀───────┐   │          │
        └────────┘   HW_FREE    └────────┘        │   └────┬─────┘
                                  ▲   ▲           │         │ START
                          DROP /  │   │ drain     │ PREPARE │
                          stop    │   │ done      │         ▼
                                  │   │      ┌────┴─────┐ ┌──────────┐
                         DRAIN    │   └──────│ DRAINING │ │ RUNNING  │
                       (playback) │          └──────────┘ │          │
                                  │               ▲       └──┬───┬───┘
                                  └───────────────┘  DRAIN   │   │
                                              (capture/PB)   │   │ XRUN
                              PAUSE_PUSH ┌──────────┐ START  │   ▼
                          ┌─────────────▶│  PAUSED  │────────┘ ┌──────┐
                          │              └────┬─────┘ PAUSE_   │ XRUN │
                          │  PAUSE_RELEASE    │       RELEASE  └──┬───┘
                       RUNNING ◀──────────────┘                   │ PREPARE
                          ▲    SUSPEND ┌───────────┐  RESUME      │
                          └────────────│ SUSPENDED │──────────────┘
                                       └───────────┘
    suspend reaches SUSPENDED from RUNNING/PREPARED/PAUSED/DRAINING/XRUN;
    resume restores the saved suspended_state.  DISCONNECTED is terminal.
```

## SUMMARY

The PCM lifecycle value is [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364), the first field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), typed [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306) and taking one of the nine [`SNDRV_PCM_STATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) values (OPEN, SETUP, PREPARED, RUNNING, XRUN, DRAINING, PAUSED, SUSPENDED, DISCONNECTED). [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) writes that field and mirrors it into the read-only [`runtime->status->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) of the mmapped [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531), and [`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) wraps it under the stream lock while skipping a stream already in DISCONNECTED.

Every transition that touches the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op is expressed as a [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instance and run by [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387), which selects [`snd_pcm_action_group()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246) for a linked stream group and [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) for a lone substream. The single-stream path calls [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230), then [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230), then [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) on success or [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) on failure. The named per-command instances (start, stop, pause, suspend, resume, reset, prepare, drain) plug into this machinery, and the atomic running-path transitions take the stream spinlock through [`snd_pcm_action_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1406) while the prepare, reset, and drain transitions that may sleep take the link rwsem and the buffer-access lock through [`snd_pcm_action_nonatomic()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416). A userspace client drives the transitions through the [`SNDRV_PCM_IOCTL_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L692) commands dispatched by [`snd_pcm_common_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L3363) and reads the resulting state back through the mmapped status page or [`SNDRV_PCM_IOCTL_SYNC_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L689). For an ASoC PCM the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op the do-action calls is [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198), which fans the START or STOP command out across every component and DAI of the link in a configured order.

## SPECIFICATIONS

The PCM state machine is a Linux kernel software construct and has no standalone hardware specification. The state set, the transition rules, and the ioctl numbers that drive them are defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h), where [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306) and the [`SNDRV_PCM_STATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307) constants are the normative interface, and the read-only [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) defines the shared-page contract. On x86-64 the underlying controllers (Intel High Definition Audio, USB Audio Class, SoundWire codecs) are specified by their own standards, which constrain what a driver's [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op does at each transition while leaving the state model to the kernel.

## LINUX KERNEL

### State value and its storage (include/sound/pcm.h, include/uapi/sound/asound.h)

- [`'\<snd_pcm_state_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306): the bitwise int that types the state field
- [`'SNDRV_PCM_STATE_OPEN':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L307): the nine `SNDRV_PCM_STATE_*` values, 0 (OPEN) through 8 (DISCONNECTED), with [`SNDRV_PCM_STATE_LAST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L316) aliasing DISCONNECTED
- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the runtime record whose first field [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) holds the lifecycle value and whose [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) remembers the state to restore on resume
- [`'\<struct snd_pcm_mmap_status\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531): the read-only page whose [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L532) field is the mmap copy userspace reads
- [`'\<__snd_pcm_set_state\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725): write [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the mmap copy in one inline call (call within the stream lock)
- [`'\<snd_pcm_set_state\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621): the stream-lock wrapper around [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) that skips a DISCONNECTED stream
- [`'\<snd_pcm_running\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L711): true when the state is RUNNING, or DRAINING for a playback stream

### Trigger commands (include/sound/pcm.h)

- [`'SNDRV_PCM_TRIGGER_STOP':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98): the seven `SNDRV_PCM_TRIGGER_*` commands (STOP, START, PAUSE_PUSH, PAUSE_RELEASE, SUSPEND, RESUME, DRAIN) the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op receives

### Dispatch model (pcm_native.c)

- [`'\<struct action_ops\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230): the four-function callback set ([`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231), [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233), [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235), [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237)) one per transition
- [`'\<snd_pcm_action_single\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306): run pre, do, then post (success) or undo (failure) on one substream
- [`'\<snd_pcm_action_group\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246): run pre across all group members, then do, then post, undoing the prefix that succeeded if a do fails
- [`'\<snd_pcm_action\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387): pick the group or single path via [`snd_pcm_stream_group_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1351) (call with the stream lock)
- [`'\<snd_pcm_action_lock_irq\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1406): take the stream lock, then run [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387)
- [`'\<snd_pcm_action_nonatomic\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416): take the link rwsem and buffer-access lock for the prepare, reset, and drain actions that may sleep
- [`'\<snd_pcm_stream_group_ref\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1351): reference and lock the link group, returning NULL when the substream is not linked

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM chapter describing the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) callback, the [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) commands, and the move to [`SNDRV_PCM_STATE_XRUN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L311) on underrun
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): the trigger timestamp each transition latches and the running-state position model
- [`Documentation/sound/designs/powersave.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/powersave.rst): the runtime-PM context in which the suspend and resume transitions run

## OTHER SOURCES

- [ALSA project library documentation (alsa-lib PCM)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [alsa-lib snd_pcm_state and the PCM state diagram](https://www.alsa-project.org/alsa-doc/alsa-lib/group___p_c_m.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Each transition is described by one [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230), a callback set of up to four function pointers that [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) and [`snd_pcm_action_group()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246) invoke in a fixed order. The four roles are the same for every transition.

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

### pre_action

[`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231) validates the precondition and records [`runtime->trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366); it returns a negative errno to reject the transition before any hardware is touched, so a start from a state other than PREPARED returns `-EBADFD` from [`snd_pcm_pre_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1438). Setting [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366) to the substream tells the do and undo steps which member of a linked group owns the hardware trigger.

### do_action

[`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233) performs the transition, which for the running-path actions means calling the driver [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) op with the matching [`SNDRV_PCM_TRIGGER_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98) command, guarded by a test that the substream is the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366) so a linked group issues the hardware trigger once. It may itself set a state, as [`snd_pcm_do_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1452) does when it demotes to XRUN on `-EPIPE`, and it returns a negative errno to send [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) down the undo branch instead of the post branch.

### undo_action

[`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235) is optional and present only on the start, pause, and resume instances, the transitions whose do-step has a hardware effect worth reversing. It runs when a later group member's do-step fails after this member already triggered, reversing the trigger (for example [`snd_pcm_undo_start()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1466) issues [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98)). For a lone substream it runs when that substream's own do-step returns an error.

### post_action

[`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) commits the transition. It latches the trigger timestamp with [`snd_pcm_trigger_tstamp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1213) and sets the new state with [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725) so both [`runtime->state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) and the mmap copy advance at once. Because it runs after every member's do-step succeeded, the group's states change together rather than partway through a failed bring-up.

## DETAILS

### The state value and the read-only mmap copy

The lifecycle value is the first field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), typed [`snd_pcm_state_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L306), and the [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365) next to it remembers where to return after a resume. The same record holds the [`trigger_master`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L366) the action callbacks set and the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) pointer to the mmapped page:

```c
/* include/sound/pcm.h:362 */
struct snd_pcm_runtime {
	/* -- Status -- */
	snd_pcm_state_t state;		/* stream state */
	snd_pcm_state_t suspended_state; /* suspended stream state */
	struct snd_pcm_substream *trigger_master;
	struct timespec64 trigger_tstamp;	/* trigger timestamp */
	...
	/* -- mmap -- */
	struct snd_pcm_mmap_status *status;
	struct snd_pcm_mmap_control *control;
	...
};
```

The [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L364) takes one of the nine values defined in the ABI header, numbered 0 through 8 with [`SNDRV_PCM_STATE_LAST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L316) aliasing the highest:

```c
/* include/uapi/sound/asound.h:306 */
typedef int __bitwise snd_pcm_state_t;
#define	SNDRV_PCM_STATE_OPEN		((__force snd_pcm_state_t) 0) /* stream is open */
#define	SNDRV_PCM_STATE_SETUP		((__force snd_pcm_state_t) 1) /* stream has a setup */
#define	SNDRV_PCM_STATE_PREPARED	((__force snd_pcm_state_t) 2) /* stream is ready to start */
#define	SNDRV_PCM_STATE_RUNNING		((__force snd_pcm_state_t) 3) /* stream is running */
#define	SNDRV_PCM_STATE_XRUN		((__force snd_pcm_state_t) 4) /* stream reached an xrun */
#define	SNDRV_PCM_STATE_DRAINING	((__force snd_pcm_state_t) 5) /* stream is draining */
#define	SNDRV_PCM_STATE_PAUSED		((__force snd_pcm_state_t) 6) /* stream is paused */
#define	SNDRV_PCM_STATE_SUSPENDED	((__force snd_pcm_state_t) 7) /* hardware is suspended */
#define	SNDRV_PCM_STATE_DISCONNECTED	((__force snd_pcm_state_t) 8) /* hardware is disconnected */
#define	SNDRV_PCM_STATE_LAST		SNDRV_PCM_STATE_DISCONNECTED
```

The single point that changes the state is [`__snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L725). It writes the in-kernel field and the mmap copy in the same call, and the comment marks the second store as the copy a userspace reader sees:

```c
/* include/sound/pcm.h:725 */
static inline void __snd_pcm_set_state(struct snd_pcm_runtime *runtime,
				       snd_pcm_state_t state)
{
	runtime->state = state;
	runtime->status->state = state; /* copy for mmap */
}
```

The [`runtime->status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L412) pointer addresses a [`struct snd_pcm_mmap_status`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L531) whose every field is marked read-only for userspace, so a client that mmaps the status page reads the state without an ioctl while the kernel stays the only writer through the copy above:

```c
/* include/uapi/sound/asound.h:531 */
struct __snd_pcm_mmap_status {
	snd_pcm_state_t state;		/* RO: state - SNDRV_PCM_STATE_XXXX */
	int pad1;			/* Needed for 64 bit alignment */
	snd_pcm_uframes_t hw_ptr;	/* RO: hw ptr (0...boundary-1) */
	struct __snd_timespec tstamp;	/* Timestamp */
	snd_pcm_state_t suspended_state; /* RO: suspended stream state */
	struct __snd_timespec audio_tstamp; /* from sample counter or wall clock */
};
```

[`snd_pcm_set_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L621) is the locked wrapper used by the configuration path. It holds the stream lock and skips the write entirely once a stream has reached DISCONNECTED, so a disconnect is terminal:

```c
/* sound/core/pcm_native.c:621 */
static void snd_pcm_set_state(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	guard(pcm_stream_lock_irq)(substream);
	if (substream->runtime->state != SNDRV_PCM_STATE_DISCONNECTED)
		__snd_pcm_set_state(substream->runtime, state);
}
```

Below that guard the inner setter writes both at once, the in-kernel field and the mmap copy the userspace reader picks up with no ioctl:

```
    __snd_pcm_set_state(): one write reaches two copies
    ────────────────────────────────────────────────────

          __snd_pcm_set_state(runtime, state)
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
    ┌───────────────────┐  ┌───────────────────────┐
    │ runtime->state    │  │ runtime->status->state│
    │ (in-kernel field) │  │ (RO mmap copy)        │
    └───────────────────┘  └───────────┬───────────┘
                                       │ mmap status page
                                       ▼
                              ┌───────────────────┐
                              │ userspace reader  │
                              │ (no ioctl needed) │
                              └───────────────────┘

    snd_pcm_set_state() wraps this under the stream lock and skips
    the write once state == SNDRV_PCM_STATE_DISCONNECTED.
```

### The pre/do/undo/post protocol on one substream

[`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) runs one transition on one substream. It calls [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231) first and returns its error without touching hardware; on success it runs [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233) and then either [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) (when the do-step returned 0) or [`undo_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1235) (when it failed and an undo exists):

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

The phases run top to bottom on one substream, the precondition check first and then the trigger, branching to commit on success or to the undo step on a failure:

```
    snd_pcm_action_single(): four phases, one substream
    ────────────────────────────────────────────────────

    pre_action   ──▶  check precondition, set trigger_master
         │              res < 0 ──▶ return, no hardware touched
         ▼
    do_action    ──▶  call driver trigger (SNDRV_PCM_TRIGGER_*)
         │
         ├──▶ res == 0 ──▶ post_action  ──▶ commit new state
         │                 (trigger_tstamp, __snd_pcm_set_state)
         │
         └──▶ res < 0  ──▶ undo_action  (only if one is defined)
                           reverse the trigger, return the error
```

### The group path runs the protocol in three passes

[`snd_pcm_action_group()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246) runs the same transition across every member of a linked group in three separate passes. It walks the group once calling [`pre_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1231) on each (taking each peer's lock as it goes), a second time calling [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233) on each, and a third time calling [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) on each. According to the comment, "the stream state might be changed also on failure", and the do-pass rolls back the prefix that already ran when one member fails:

```c
/* sound/core/pcm_native.c:1269 */
	snd_pcm_group_for_each_entry(s, substream) {
		res = ops->do_action(s, state);
		if (res < 0) {
			if (ops->undo_action) {
				snd_pcm_group_for_each_entry(s1, substream) {
					if (s1 == s) /* failed stream */
						break;
					ops->undo_action(s1, state);
				}
			}
			s = NULL; /* unlock all */
			goto _unlock;
		}
	}
	snd_pcm_group_for_each_entry(s, substream) {
		ops->post_action(s, state);
	}
```

Splitting the work into a pre pass, a do pass, and a post pass lets a linked group reach the new state atomically. No member commits its state in [`post_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1237) until every member's [`do_action`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1233) has succeeded, and a failure midway through the do pass reverses only the members that already triggered.

```
    snd_pcm_action_group(): three passes over linked members
    ────────────────────────────────────────────────────────

    member:        s0        s1        s2
                   │         │         │
    pass 1   ──▶ pre ──▶   pre ──▶   pre        (lock each peer)
                   │         │         │
    pass 2   ──▶  do ──▶    do ──▶  do FAILS
                   │         │         │
                   │         ▼         ▼
                   │    undo_action  (stop here)
                   ◀─────────┘  roll back the prefix that ran
                   │         │
    pass 3   ──▶ post ──▶  post              (only if all do ok)

    no member commits state in post until every do_action
    succeeded; a mid-pass failure undoes only members that ran.
```

### Choosing the group or single path and the locking

[`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387) is the chooser. It references the link group with [`snd_pcm_stream_group_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1351), which returns NULL when the substream is not linked, and dispatches to the group path or the single path accordingly:

```c
/* sound/core/pcm_native.c:1387 */
static int snd_pcm_action(const struct action_ops *ops,
			  struct snd_pcm_substream *substream,
			  snd_pcm_state_t state)
{
	struct snd_pcm_group *group;
	int res;

	group = snd_pcm_stream_group_ref(substream);
	if (group)
		res = snd_pcm_action_group(ops, substream, state, true);
	else
		res = snd_pcm_action_single(ops, substream, state);
	snd_pcm_group_unref(group, substream);
	return res;
}
```

[`snd_pcm_action_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1406) wraps [`snd_pcm_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1387) for callers that arrive without the stream lock, taking it for the duration. The atomic-context start, stop, pause, and resume entry points use this wrapper. The prepare, reset, and drain transitions can sleep, so they run through [`snd_pcm_action_nonatomic()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416) instead, which holds the link rwsem and the buffer-access lock rather than the stream spinlock and selects the group or single path by [`snd_pcm_stream_linked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416):

```c
/* sound/core/pcm_native.c:1416 */
static int snd_pcm_action_nonatomic(const struct action_ops *ops,
				    struct snd_pcm_substream *substream,
				    snd_pcm_state_t state)
{
	int res;

	/* Guarantee the group members won't change during non-atomic action */
	guard(rwsem_read)(&snd_pcm_link_rwsem);
	res = snd_pcm_buffer_access_lock(substream->runtime);
	if (res < 0)
		return res;
	if (snd_pcm_stream_linked(substream))
		res = snd_pcm_action_group(ops, substream, state, false);
	else
		res = snd_pcm_action_single(ops, substream, state);
	snd_pcm_buffer_access_unlock(substream->runtime);
	return res;
}
```

The two wrappers split by whether the action's do-step can sleep. The running-path triggers run in atomic context under the stream spinlock through [`snd_pcm_action_lock_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1406), while prepare, reset, and drain run under the sleeping locks through [`snd_pcm_action_nonatomic()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1416). Either way the inner [`snd_pcm_action_single()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1306) or [`snd_pcm_action_group()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1246) runs the same pre/do/undo/post protocol, and the per-command [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) instances supply the four functions for start, stop, pause, suspend, resume, reset, prepare, and drain.

```
    snd_pcm_action(): path and lock by context
    ───────────────────────────────────────────

                 snd_pcm_stream_group_ref()
                          │
              linked? ────┴──── not linked
                 │                   │
                 ▼                   ▼
         action_group()       action_single()
              (shared pre/do/undo/post protocol)

    caller wrapper            lock held            actions
    ──────────────────────────────────────────────────────────
    action_lock_irq()    stream spinlock      start stop
                         (atomic)             pause resume
    action_nonatomic()   link rwsem +         prepare reset
                         buffer-access lock   drain
```

### The ASoC layer plugs into the trigger step

The do-action of the running-path transitions calls [`substream->ops->trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and for a non-DPCM ASoC link that op is [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198). Rather than touch one chip, it fans the command out across the whole link through a two-row dispatch table indexed by the configured trigger order:

```c
/* sound/soc/soc-pcm.c:1184 */
#define TRIGGER_MAX 3
static int (* const trigger[][TRIGGER_MAX])(struct snd_pcm_substream *substream, int cmd, int rollback) = {
	[SND_SOC_TRIGGER_ORDER_DEFAULT] = {
		snd_soc_link_trigger,
		snd_soc_pcm_component_trigger,
		snd_soc_pcm_dai_trigger,
	},
	[SND_SOC_TRIGGER_ORDER_LDC] = {
		snd_soc_link_trigger,
		snd_soc_pcm_dai_trigger,
		snd_soc_pcm_component_trigger,
	},
};
```

[`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) reads the start and stop order from the link and its components, then runs the three table entries forward for a START, RESUME, or PAUSE_RELEASE and in reverse for a STOP, SUSPEND, or PAUSE_PUSH, so the link, its DAIs, and its components start in one order and stop in the mirror order:

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
	/*
	 * START
	 */
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
	/*
	 * STOP
	 */
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

The state machine never sees this fan-out. From the do-action's view a single [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) call returned, and [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) has translated that one command into an ordered sweep of [`snd_soc_link_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1187), [`snd_soc_pcm_component_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1188), and [`snd_soc_pcm_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1189) across the link, rolling the START sequence back with the matching STOP command when an entry fails.

```
    soc_pcm_trigger(): command selects sweep direction
    ───────────────────────────────────────────────────

    trigger command            order over the 3 table entries
    ──────────────────────────────────────────────────────────
    START                      forward  i = 0 ──▶ TRIGGER_MAX-1
    RESUME                     link ──▶ component ──▶ dai
    PAUSE_RELEASE              (DEFAULT order)
    ──────────────────────────────────────────────────────────
    STOP                       reverse  i = TRIGGER_MAX-1 ──▶ 0
    SUSPEND                    dai ──▶ component ──▶ link
    PAUSE_PUSH                 (mirror of START)

    the do_action sees one trigger() return; the fan-out across
    link, components, and DAIs stays below the state machine.
```
