# ASoC PCM trigger and teardown (soc-pcm)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

After the setup operations have prepared a substream, the runtime half of the ASoC PCM operation set drives the transfer and tears it down: [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) starts and stops the data flow, [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) reports the ring position, and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) and `close` release what setup claimed. [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) is the one operation whose layer order is configurable, because some hardware starts the DAI before the platform DMA and some the other way around; it indexes a static table of three layer-trigger functions by an [`enum snd_soc_trigger_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601) and runs the start commands forward through it and the stop commands backward. The teardown handlers [`soc_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) and [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) share their bodies with the error-unwind path through a `rollback` flag, and the per-substream marks that the setup wrappers recorded decide which DAIs and components actually get unwound. [`soc_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1280) reads the hardware position from the platform component and folds the DAI and component latencies into [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1549).

```
    soc_pcm_trigger layer order
    ───────────────────────────

    start cmd: walk table[start] forward (i = 0 → 2)
    stop  cmd: walk table[stop]  reverse (i = 2 → 0)

                        i = 0      i = 1        i = 2
    ORDER_DEFAULT     ┌────────┬────────────┬────────────┐
       start ▼        │  Link  │ Component  │    DAI     │
       stop  ▲        └────────┴────────────┴────────────┘
    ORDER_LDC         ┌────────┬────────────┬────────────┐
       start ▼        │  Link  │    DAI     │ Component  │
       stop  ▲        └────────┴────────────┴────────────┘

    a START that fails at layer k becomes the matching STOP/SUSPEND/
    PAUSE_PUSH, and the stop pass (rollback = 1) unwinds only the
    layers whose mark shows they had started.
```

## SUMMARY

[`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) first picks a start order and a stop order, defaulting each to whatever a component or the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) requested through its [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) fields, then runs the start group forward and the stop group backward through the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1185) table. Each table cell is one of [`snd_soc_link_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142), [`snd_soc_pcm_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1135), and [`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618), and each applies a forward-start, marked-stop discipline so a rollback stops only the layers that started. Trigger runs in the ALSA PCM stream lock and can be atomic, so it takes no [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001). A failing start translates the command into its matching stop ([`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99) into [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98), and the resume and pause variants likewise) and runs the stop pass with `rollback = 1`.

The teardown handlers free in the reverse direction from setup. [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) runs [`soc_pcm_hw_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1008), which clears the per-DAI parameter record, mutes the DAIs, runs [`snd_soc_dapm_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4630), and frees the link, component, and DAI hardware resources. [`soc_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) runs [`soc_pcm_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L755), which deactivates the runtime with [`snd_soc_runtime_deactivate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L491), shuts the DAIs down in reverse order through [`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456), shuts the link down, and closes the components through [`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266). Both bodies take a `rollback` argument and are reached with `rollback = 1` from a failed open or hw_params, where each teardown wrapper checks the matching setup mark and skips a layer whose setup op never ran. [`soc_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1280) reads the ring offset with [`snd_soc_pcm_component_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884) and adds the maximum DAI and component delays from [`snd_soc_pcm_dai_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) and [`snd_soc_pcm_component_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L912).

## SPECIFICATIONS

The soc-pcm trigger and teardown layer is a Linux kernel software construct and has no standalone hardware specification. The operations it implements ([`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), `hw_free`, `close`, [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55)) and the trigger command set are defined by the ALSA PCM userspace interface.

## LINUX KERNEL

### Trigger (soc-pcm.c, soc.h)

- [`'\<soc_pcm_trigger\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198): select the start and stop orders and drive the three layers forward then backward
- [`'\<enum snd_soc_trigger_order\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601): [`SND_SOC_TRIGGER_ORDER_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601) (Link, Component, DAI) and [`SND_SOC_TRIGGER_ORDER_LDC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L604) (Link, DAI, Component)

### Layer trigger wrappers (soc-link.c, soc-component.c, soc-dai.c)

- [`'\<snd_soc_link_trigger\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142): run the machine link trigger op with the start/stop mark
- [`'\<snd_soc_pcm_component_trigger\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1135): run every component trigger op, forward on start and marked-only on rollback stop
- [`'\<snd_soc_pcm_dai_trigger\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618): run every DAI trigger op, applying the trigger-time mute and the mark

### Teardown handlers and shared bodies (soc-pcm.c)

- [`'\<soc_pcm_close\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) / [`'\<__soc_pcm_close\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L795): close the substream through [`soc_pcm_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L755)
- [`'\<soc_pcm_hw_free\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) / [`'\<__soc_pcm_hw_free\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1047): release hw_params resources through [`soc_pcm_hw_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1008)
- [`'\<soc_pcm_clean\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L755): the shared close body, run with `rollback = 0` on close and `rollback = 1` on open failure
- [`'\<soc_pcm_hw_clean\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1008): the shared hw_free body, run with `rollback = 0` on hw_free and `rollback = 1` on hw_params failure
- [`'\<soc_pcm_components_close\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L737): close each component and drop the per-open module reference

### Teardown fan-out wrappers (soc-dai.c, soc-component.c, soc-link.c)

- [`'\<snd_soc_dai_shutdown\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456): run a DAI shutdown op, honoring the startup mark on rollback
- [`'\<snd_soc_component_close\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266): run a component close op, honoring the open mark on rollback
- [`'\<snd_soc_link_shutdown\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70) and [`'\<snd_soc_link_hw_free\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L115): run the machine link shutdown and hw_free ops
- [`'\<snd_soc_pcm_component_hw_free\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1101): free each component's hardware resources, honoring the hw_params mark

### DAPM, mute, and activation (soc-dapm.c, soc-dai.c, soc.h)

- [`'\<snd_soc_dapm_stream_stop\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4630): power the path down, immediately for capture and after the pmdown delay for playback
- [`'\<snd_soc_dai_digital_mute\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386): mute a DAI as part of hw_free or a trigger stop
- [`'\<snd_soc_runtime_deactivate\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L491): drop the runtime and DAI usage counts at close

### Pointer and delay (soc-pcm.c, soc-component.c, soc-dai.c)

- [`'\<soc_pcm_pointer\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1280): read the ring offset and sum the path latency into [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1549)
- [`'\<snd_soc_pcm_component_pointer\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884): return the first component's [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) result
- [`'\<snd_soc_pcm_dai_delay\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) and [`'\<snd_soc_pcm_component_delay\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L912): take the maximum delay across the transmit and receive DAIs and components

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the pmdown delayed power-down that [`snd_soc_dapm_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4630) schedules for playback
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component whose trigger and pointer ops the wrappers reach
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families the per-DAI trigger and delay ops drive

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The runtime phase uses four of the seven [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) fields. Trigger and pointer have no inner double-underscore worker, because trigger runs without the card mutex and pointer is read-only; hw_free and close wrap an inner worker the same way the setup handlers do.

| Operation | soc-pcm handler | DAI wrapper | component wrapper | link wrapper |
|-----------|-----------------|-------------|-------------------|--------------|
| `SNDRV_PCM_IOCTL_START` / `_DROP` | [`soc_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) | [`snd_soc_pcm_dai_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) | [`snd_soc_pcm_component_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1135) | [`snd_soc_link_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142) |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`soc_pcm_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) | [`snd_soc_dai_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) | [`snd_soc_pcm_component_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1101) | [`snd_soc_link_hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L115) |
| `close()` | [`soc_pcm_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) | [`snd_soc_dai_shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) | [`snd_soc_component_close`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266) | [`snd_soc_link_shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L70) |
| read pointer | [`soc_pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1280) | [`snd_soc_pcm_dai_delay`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) | [`snd_soc_pcm_component_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884) | (none) |

The trigger command arrives as one of [`SNDRV_PCM_TRIGGER_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L99), [`SNDRV_PCM_TRIGGER_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L98), [`SNDRV_PCM_TRIGGER_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L100), [`SNDRV_PCM_TRIGGER_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L101), [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102), or [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103). The three commands in the start group walk the table forward, the three in the stop group walk it backward.

## DETAILS

### The trigger table and the order selection

The configurable order is held in a two-row table of function pointers indexed by [`enum snd_soc_trigger_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L601). Each row lists the three layer-trigger functions in the order they run on a start:

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

The enum names the two orders and its comment records the start and stop sequence each produces, with stop being the reverse of start:

```c
/* include/sound/soc.h:601 */
enum snd_soc_trigger_order {
					/* start			stop		     */
	SND_SOC_TRIGGER_ORDER_DEFAULT	= 0,	/* Link->Component->DAI		DAI->Component->Link */
	SND_SOC_TRIGGER_ORDER_LDC,		/* Link->DAI->Component		Component->DAI->Link */

	SND_SOC_TRIGGER_ORDER_MAX,
};
```

[`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) chooses the start index and the stop index independently. A [`trigger_start`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) or [`trigger_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) set on any component sets the order, and the same field on the [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) overrides that, so a machine driver has the final say:

```c
/* sound/soc/soc-pcm.c:1198 */
	/*
	 * select START/STOP sequence
	 */
	for_each_rtd_components(rtd, i, component) {
		if (component->driver->trigger_start)
			start = component->driver->trigger_start;
		if (component->driver->trigger_stop)
			stop = component->driver->trigger_stop;
	}
	if (rtd->dai_link->trigger_start)
		start = rtd->dai_link->trigger_start;
	if (rtd->dai_link->trigger_stop)
		stop  = rtd->dai_link->trigger_stop;

	if (start < 0 || start >= SND_SOC_TRIGGER_ORDER_MAX ||
	    stop  < 0 || stop  >= SND_SOC_TRIGGER_ORDER_MAX)
		return -EINVAL;
```

The whole of [`soc_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1198) is the order select followed by the forward start pass and the backward stop pass, with the rollback rewrite between them. It takes only the substream and the command and carries no inner double-underscore worker, because it runs inside the ALSA PCM stream lock and never reaches for [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001):

```c
/* sound/soc/soc-pcm.c:1198 */
static int soc_pcm_trigger(struct snd_pcm_substream *substream, int cmd)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int ret = 0, r = 0, i;
	int rollback = 0;
	int start = 0, stop = 0;

	/*
	 * select START/STOP sequence
	 */
	for_each_rtd_components(rtd, i, component) {
		if (component->driver->trigger_start)
			start = component->driver->trigger_start;
		if (component->driver->trigger_stop)
			stop = component->driver->trigger_stop;
	}
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

The handler resolves the start and stop indices down two parallel columns, each component allowed to set its value and the dai_link given the final say:

```
    start and stop indices are resolved independently, dai_link wins
    ───────────────────────────────────────────────────────────────

          start index                  stop index
    ┌───────────────────────┐    ┌───────────────────────┐
    │ = 0 (ORDER_DEFAULT)   │    │ = 0 (ORDER_DEFAULT)   │
    └───────────┬───────────┘    └───────────┬───────────┘
                ▼ each component             ▼ each component
    ┌───────────────────────┐    ┌───────────────────────┐
    │ component->driver     │    │ component->driver     │
    │   ->trigger_start     │    │   ->trigger_stop      │
    │   (if set, override)  │    │   (if set, override)  │
    └───────────┬───────────┘    └───────────┬───────────┘
                ▼ dai_link last              ▼ dai_link last
    ┌───────────────────────┐    ┌───────────────────────┐
    │ rtd->dai_link         │    │ rtd->dai_link         │
    │   ->trigger_start     │    │   ->trigger_stop      │
    │   (final say)         │    │   (final say)         │
    └───────────┬───────────┘    └───────────┬───────────┘
                ▼                            ▼
      index into trigger[start][]  index into trigger[stop][]
      (must be < SND_SOC_TRIGGER_ORDER_MAX, else -EINVAL)
```

### Start forward, roll back to stop on failure

The start group walks the chosen row from index 0 to 2, breaking on the first error:

```c
/* sound/soc/soc-pcm.c:1227 */
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
```

When a start fails, the handler sets `rollback = 1` and rewrites the command into its matching stop so the stop pass that follows tears down only what started:

```c
/* sound/soc/soc-pcm.c:1242 */
	if (r < 0) {
		rollback = 1;
		ret = r;
		switch (cmd) {
		case SNDRV_PCM_TRIGGER_START:
			cmd = SNDRV_PCM_TRIGGER_STOP;
			break;
		case SNDRV_PCM_TRIGGER_RESUME:
			cmd = SNDRV_PCM_TRIGGER_SUSPEND;
			break;
		case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
			cmd = SNDRV_PCM_TRIGGER_PAUSE_PUSH;
			break;
		}
	}

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

A clean stop arrives directly in the stop group and runs with `rollback = 0`, so the same backward walk handles both a genuine stop request and the unwind of a failed start.

```
    A failed start rewrites the command into its matching stop
    ──────────────────────────────────────────────────────────

    START group (walk table forward, i = 0 ▶ 2, break on first error)
      ┌───────────────────────┬───────────────────────────────┐
      │ command               │ on failure rewrites to        │
      ├───────────────────────┼───────────────────────────────┤
      │ TRIGGER_START         │ TRIGGER_STOP                  │
      │ TRIGGER_RESUME        │ TRIGGER_SUSPEND               │
      │ TRIGGER_PAUSE_RELEASE │ TRIGGER_PAUSE_PUSH            │
      └───────────────────────┴───────────────────────────────┘

    STOP group (walk table reverse, i = 2 ▶ 0); rollback set by path
      ┌───────────────────────────────┬───────────────────────┐
      │ how the stop group is reached │ rollback              │
      ├───────────────────────────────┼───────────────────────┤
      │ rewritten from a failed start │ 1 (unwind started)    │
      │ a genuine STOP/SUSPEND/PAUSE  │ 0 (tear all down)     │
      └───────────────────────────────┴───────────────────────┘
      same reverse walk serves both a real stop and a start unwind
```

### Each layer trigger marks on start and matches on stop

[`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) shows the discipline every layer follows. On a start command it triggers each DAI, unmutes the DAIs whose mute is deferred to trigger, and pushes a [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) record; on a stop command under rollback it skips any DAI whose mark does not match, so an unwind touches only the DAIs that actually started:

```c
/* sound/soc/soc-dai.c:618 */
int snd_soc_pcm_dai_trigger(struct snd_pcm_substream *substream,
			    int cmd, int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int i, r, ret = 0;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for_each_rtd_dais(rtd, i, dai) {
			ret = soc_dai_trigger(dai, substream, cmd);
			if (ret < 0)
				break;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 0, substream->stream);

			soc_dai_mark_push(dai, substream, trigger);
		}
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		for_each_rtd_dais(rtd, i, dai) {
			if (rollback && !soc_dai_mark_match(dai, substream, trigger))
				continue;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 1, substream->stream);

			r = soc_dai_trigger(dai, substream, cmd);
			if (r < 0)
				ret = r; /* use last ret */
			soc_dai_mark_pop(dai, trigger);
		}
	}

	return ret;
}
```

[`snd_soc_pcm_component_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1135) applies the same forward-start, marked-stop pattern over the components, and [`snd_soc_link_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L142) over the single machine link op:

```c
/* sound/soc/soc-component.c:1135 */
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		for_each_rtd_components(rtd, i, component) {
			if (rollback && !soc_component_mark_match(component, substream, trigger))
				continue;

			r = soc_component_trigger(component, substream, cmd);
			if (r < 0)
				ret = r; /* use last ret */
			soc_component_mark_pop(component, trigger);
		}
	}
```

Each layer pushes a mark on the way in and matches it on the way out, so a rollback stop walks past any item whose start never recorded one:

```
    Per-item (DAI / component) trigger mark lifecycle
    ─────────────────────────────────────────────────

    START path (forward over each item, break on first error)
    ┌───────────────────────────────────────────────────────────┐
    │ soc_*_trigger(cmd)                                        │
    │ if mute-at-trigger: unmute                                │
    │ mark_push(trigger)        ◀── records "this item ran"     │
    └───────────────────────────────────────────────────────────┘
                              │  the mark gates the unwind
                              ▼
    STOP path (reverse over each item)
    ┌───────────────────────────────────────────────────────────┐
    │ if rollback && mark not matched ─▶ skip this item         │
    │ if mute-at-trigger: mute                                  │
    │ soc_*_trigger(cmd)                                        │
    │ mark_pop(trigger)                                         │
    └───────────────────────────────────────────────────────────┘

    only items whose mark is present are torn down on a rollback stop
```

### The close and hw_free ops wrap an inner worker under the card mutex

The ALSA-facing close and hw_free ops are thin. Each grabs the card mutex with [`snd_soc_dpcm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1548), calls an inner double-underscore worker, and drops the mutex, the same split the setup handlers use, so the shared body never has to know whether it was reached from the op or from a sibling DPCM walk. [`soc_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) is the [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op registered for non-DPCM streams, and [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) is the matching hw_free op:

```c
/* sound/soc/soc-pcm.c:802 */
/* PCM close ops for non-DPCM streams */
static int soc_pcm_close(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);

	snd_soc_dpcm_mutex_lock(rtd);
	__soc_pcm_close(rtd, substream);
	snd_soc_dpcm_mutex_unlock(rtd);
	return 0;
}
```

```c
/* sound/soc/soc-pcm.c:1054 */
/* hw_free PCM ops for non-DPCM streams */
static int soc_pcm_hw_free(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret;

	snd_soc_dpcm_mutex_lock(rtd);
	ret = __soc_pcm_hw_free(rtd, substream);
	snd_soc_dpcm_mutex_unlock(rtd);
	return ret;
}
```

The inner workers hold the mutex on entry and fix the `rollback` argument at 0, because a real close or hw_free always tears the whole layer down. [`__soc_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L795) forwards into [`soc_pcm_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L755) and [`__soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1047) into [`soc_pcm_hw_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1008), and the open and hw_params error paths are the callers that reach the same bodies with `rollback = 1`, separately from these wrappers:

```c
/* sound/soc/soc-pcm.c:795 */
static int __soc_pcm_close(struct snd_soc_pcm_runtime *rtd,
			   struct snd_pcm_substream *substream)
{
	return soc_pcm_clean(rtd, substream, 0);
}
```

```c
/* sound/soc/soc-pcm.c:1047 */
static int __soc_pcm_hw_free(struct snd_soc_pcm_runtime *rtd,
			     struct snd_pcm_substream *substream)
{
	return soc_pcm_hw_clean(rtd, substream, 0);
}
```

### hw_free reverses hw_params

[`soc_pcm_hw_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1008) is the body behind both [`soc_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1054) and the hw_params error path. It clears each DAI's stored parameters as the DAI goes inactive, mutes the DAIs that mute outside trigger, runs the DAPM stop event, and frees the link, component, and DAI hardware in that order:

```c
/* sound/soc/soc-pcm.c:1008 */
static int soc_pcm_hw_clean(struct snd_soc_pcm_runtime *rtd,
			    struct snd_pcm_substream *substream, int rollback)
{
	struct snd_soc_dai *dai;
	int i;

	snd_soc_dpcm_mutex_assert_held(rtd);

	/* clear the corresponding DAIs parameters when going to be inactive */
	for_each_rtd_dais(rtd, i, dai) {
		if (snd_soc_dai_active(dai) == 1)
			soc_pcm_set_dai_params(dai, NULL);

		if (snd_soc_dai_stream_active(dai, substream->stream) == 1) {
			if (!snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 1, substream->stream);
		}
	}

	/* run the stream event */
	snd_soc_dapm_stream_stop(rtd, substream->stream);

	/* free any machine hw params */
	snd_soc_link_hw_free(substream, rollback);

	/* free any component resources */
	snd_soc_pcm_component_hw_free(substream, rollback);

	/* now free hw params for the DAIs  */
	for_each_rtd_dais(rtd, i, dai)
		if (snd_soc_dai_stream_valid(dai, substream->stream))
			snd_soc_dai_hw_free(dai, substream, rollback);

	return 0;
}
```

The DAPM stop is not always immediate. [`snd_soc_dapm_stream_stop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4630) powers a capture path down at once, but for a playback path it queues the power-down on a delayed work after `pmdown_time` unless the runtime opts out, which is the anti-pop behavior that keeps a short gap between tracks from cycling the amplifier:

```c
/* sound/soc/soc-dapm.c:4630 */
void snd_soc_dapm_stream_stop(struct snd_soc_pcm_runtime *rtd, int stream)
{
	if (stream == SNDRV_PCM_STREAM_PLAYBACK) {
		if (snd_soc_runtime_ignore_pmdown_time(rtd)) {
			/* powered down playback stream now */
			snd_soc_dapm_stream_event(rtd,
						  SNDRV_PCM_STREAM_PLAYBACK,
						  SND_SOC_DAPM_STREAM_STOP);
		} else {
			/* start delayed pop wq here for playback streams */
			rtd->pop_wait = 1;
			queue_delayed_work(system_power_efficient_wq,
					   &rtd->delayed_work,
					   msecs_to_jiffies(rtd->pmdown_time));
		}
	} else {
		/* capture streams can be powered down now */
		snd_soc_dapm_stream_event(rtd, SNDRV_PCM_STREAM_CAPTURE,
					  SND_SOC_DAPM_STREAM_STOP);
	}
}
```

The DAPM stop above sits between clearing each DAI's stored parameters and freeing the link, the components, and the DAIs in turn:

```
    soc_pcm_hw_clean sweep (frees in reverse of hw_params) — time ▼
    ──────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ 1. for each DAI: clear stored params if going inactive   │
    │    mute DAIs whose mute is outside trigger               │
    ├──────────────────────────────────────────────────────────┤
    │ 2. snd_soc_dapm_stream_stop(rtd, stream)  (branch below) │
    ├──────────────────────────────────────────────────────────┤
    │ 3. snd_soc_link_hw_free            (machine link)        │
    │ 4. snd_soc_pcm_component_hw_free   (components)          │
    │ 5. snd_soc_dai_hw_free per DAI     (DAIs)                │
    └──────────────────────────────────────────────────────────┘
       each free wrapper honors the hw_params mark on rollback

    snd_soc_dapm_stream_stop branch:
      ┌──────────────────────────┬───────────────────────────────┐
      │ stream / condition       │ power-down                    │
      ├──────────────────────────┼───────────────────────────────┤
      │ CAPTURE                  │ immediate STREAM_STOP event   │
      │ PLAYBACK, ignore pmdown  │ immediate STREAM_STOP event   │
      │ PLAYBACK, otherwise      │ pop_wait = 1, queue delayed   │
      │                          │   work after pmdown_time      │
      └──────────────────────────┴───────────────────────────────┘
```

### close reverses open

[`soc_pcm_clean()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L755) is the body behind [`soc_pcm_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L802) and the open error path. On a real close (not a rollback) it deactivates the runtime first and clears the parameters of any DAI that became inactive, then shuts down the DAIs in reverse order, shuts the link down, closes the components, and drops the runtime power references:

```c
/* sound/soc/soc-pcm.c:755 */
static int soc_pcm_clean(struct snd_soc_pcm_runtime *rtd,
			 struct snd_pcm_substream *substream, int rollback)
{
	struct snd_soc_component *component;
	struct snd_soc_dai *dai;
	int i;

	snd_soc_dpcm_mutex_assert_held(rtd);

	if (!rollback) {
		snd_soc_runtime_deactivate(rtd, substream->stream);

		/* Make sure DAI parameters cleared if the DAI becomes inactive */
		for_each_rtd_dais(rtd, i, dai) {
			if (snd_soc_dai_active(dai) == 0)
				soc_pcm_set_dai_params(dai, NULL);
		}
	}

	for_each_rtd_dais_reverse(rtd, i, dai)
		snd_soc_dai_shutdown(dai, substream, rollback);

	snd_soc_link_shutdown(substream, rollback);

	soc_pcm_components_close(substream, rollback);

	snd_soc_pcm_component_pm_runtime_put(rtd, substream, rollback);

	for_each_rtd_components(rtd, i, component)
		if (!snd_soc_component_active(component))
			pinctrl_pm_select_sleep_state(component->dev);

	return 0;
}
```

The `rollback` flag is where the per-substream marks earn their place. [`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) returns early when a rollback finds no matching startup mark, so a failed open that started only the first two DAIs shuts down only those two:

```c
/* sound/soc/soc-dai.c:456 */
void snd_soc_dai_shutdown(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  int rollback)
{
	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return;

	if (rollback && !soc_dai_mark_match(dai, substream, startup))
		return;

	if (dai->driver->ops &&
	    dai->driver->ops->shutdown)
		dai->driver->ops->shutdown(substream, dai);

	/* remove marked substream */
	soc_dai_mark_pop(dai, startup);
}
```

[`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266) does the same against the open mark, returning early on a rollback that finds no matching open mark and otherwise calling the component's [`close`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op before popping the mark:

```c
/* sound/soc/soc-component.c:266 */
int snd_soc_component_close(struct snd_soc_component *component,
			    struct snd_pcm_substream *substream,
			    int rollback)
{
	int ret = 0;

	if (rollback && !soc_component_mark_match(component, substream, open))
		return 0;

	if (component->driver->close)
		ret = component->driver->close(component, substream);

	/* remove marked substream */
	soc_component_mark_pop(component, open);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_pcm_component_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1101) checks the hw_params mark the same way, so every teardown wrapper is safe to call on a layer whose setup op never ran.

### pointer reports position plus path delay

[`soc_pcm_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1280) reads the ring buffer offset from the component and then adds the latency of the full audio path into [`runtime->delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1549), so a userspace client computing the true playback position accounts for the DAI and component pipelines:

```c
/* sound/soc/soc-pcm.c:1280 */
static snd_pcm_uframes_t soc_pcm_pointer(struct snd_pcm_substream *substream)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	snd_pcm_uframes_t offset = 0;
	snd_pcm_sframes_t codec_delay = 0;
	snd_pcm_sframes_t cpu_delay = 0;

	offset = snd_soc_pcm_component_pointer(substream);

	/* should be called *after* snd_soc_pcm_component_pointer() */
	snd_soc_pcm_dai_delay(substream, &cpu_delay, &codec_delay);
	snd_soc_pcm_component_delay(substream, &cpu_delay, &codec_delay);

	runtime->delay = cpu_delay + codec_delay;

	return offset;
}
```

[`snd_soc_pcm_component_pointer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L884) returns the first component that provides a [`pointer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, which on x86 is the platform component reporting where the DSP host DMA stands. [`snd_soc_pcm_dai_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L660) and [`snd_soc_pcm_component_delay()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L912) take the maximum transmit delay and the maximum receive delay separately, because the playback latency and the capture latency travel different DAIs:

```c
/* sound/soc/soc-dai.c:660 */
void snd_soc_pcm_dai_delay(struct snd_pcm_substream *substream,
			   snd_pcm_sframes_t *cpu_delay,
			   snd_pcm_sframes_t *codec_delay)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int i;
	...
	/* for CPU */
	for_each_rtd_cpu_dais(rtd, i, dai)
		if (dai->driver->ops &&
		    dai->driver->ops->delay)
			*cpu_delay = max(*cpu_delay, dai->driver->ops->delay(substream, dai));

	/* for Codec */
	for_each_rtd_codec_dais(rtd, i, dai)
		if (dai->driver->ops &&
		    dai->driver->ops->delay)
			*codec_delay = max(*codec_delay, dai->driver->ops->delay(substream, dai));
}
```

### Worked example: SOF trigger on x86 ACPI

On an x86-64 ACPI machine the component layer of the trigger reaches the Sound Open Firmware [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op [`sof_pcm_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385), which orders the firmware IPC against the platform DMA by command so the DSP pipeline and the host DMA start and stop in the right sequence. Because the firmware path can sleep, SOF marks its PCMs nonatomic, and the soc-pcm trigger runs from process context rather than the atomic stream lock for those streams. The teardown side reaches [`sof_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L287) through [`snd_soc_pcm_component_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1101), which tears down the firmware widgets the matching [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) set up. The soc-pcm layer itself only sequences the three layers and applies the marks; the SOF component decides what each trigger command means to the DSP.
