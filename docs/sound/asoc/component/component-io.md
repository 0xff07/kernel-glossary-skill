# ASoC component register I/O and lifecycle state

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) abstracts its register bus behind a small set of wrappers in [`soc-component.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c). A driver that supplies a regmap leaves the [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callbacks NULL, and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) attaches that regmap instead. The wrappers [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671), [`snd_soc_component_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L706), and [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751) take the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) so a read-modify-write against a non-regmap codec is atomic with respect to other accesses. The same runtime instance carries the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) open-stream use count maintained by [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497), the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) PM bit toggled by [`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284), and the module reference taken by [`snd_soc_component_module_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L222).

```
    snd_soc_component_update_bits(reg, mask, val)
        │
        ├── component->regmap ?
        │      yes ─▶ regmap_update_bits_check()   (regmap locks internally)
        │      no  ─▶ snd_soc_component_update_bits_legacy()
        │                 mutex_lock(io_mutex)
        │                 old = read ; new = (old & ~mask) | (val & mask)
        │                 if change: write(new)
        │                 mutex_unlock(io_mutex)
        ▼
    one register field updated; io_mutex serializes the legacy RMW

    active use count                module reference
    ────────────────                ────────────────
    snd_soc_dai_action(+1/-1)       snd_soc_component_module_get(mark, upon_open)
      dai->stream[].active += a       try_module_get(owner) gated by
      dai->component->active += a       driver->module_get_upon_open
```

## SUMMARY

A component's register access flows through wrappers that hide whether the codec uses a regmap or a driver callback. [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671) takes the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) and runs [`soc_component_read_no_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L642), which dispatches to [`regmap_read()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) when a regmap is attached or to the driver [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback otherwise. [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751) hands the whole read-modify-write cycle to [`regmap_update_bits_check()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) when a regmap is present, otherwise it calls [`snd_soc_component_update_bits_legacy()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L719), which holds the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) across the read, the modify, and the conditional write so no other access sees the half-updated register.

The runtime instance carries three pieces of mutable lifecycle state. The [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) field counts open streams across the component. [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) adds the same signed delta to both a DAI's per-stream count and the parent component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213), and [`snd_soc_component_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L362) reads it. The [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) bit is set by [`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284) and cleared by [`snd_soc_component_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291) around the optional driver hooks, so the core records the PM state itself. The module reference is taken by [`snd_soc_component_module_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L222) and dropped by [`snd_soc_component_module_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L238), with the [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L176) flag selecting whether the reference is held from probe or only while a stream is open.

## SPECIFICATIONS

The register-I/O path is a Linux kernel software construct and has no standalone specification. The transport underneath a component's regmap is one of the hardware register buses (I2C, SPI, SoundWire, or memory-mapped registers), each defined by its own bus standard. The regmap abstraction itself is documented in-tree.

## LINUX KERNEL

### Register I/O wrappers (soc-component.c)

- [`'\<snd_soc_component_read\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671): read one register under [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), through regmap or the [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback
- [`'\<snd_soc_component_write\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L706): write one register under [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), through regmap or the [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback
- [`'\<snd_soc_component_update_bits\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751): read-modify-write a register field; uses [`regmap_update_bits_check()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) when a regmap is present, else [`snd_soc_component_update_bits_legacy()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L719) under [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229)
- [`'\<soc_component_read_no_lock\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L642): the inner read called with [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) already held
- [`'\<snd_soc_component_update_bits_legacy\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L719): the non-regmap RMW, holding the read, modify, and conditional write together under [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229)
- [`'\<snd_soc_component_read_field\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L814): read and shift a masked field down to bit 0

### Regmap attach (soc-core.c)

- [`'\<snd_soc_component_setup_regmap\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c): record the regmap value size on the component so the read/write wrappers can use it; called from [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) when the driver supplies no [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)/[`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)

### Module reference and use count (soc-component.c, soc-dai.c, soc-component.h)

- [`'\<snd_soc_component_module_get\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L222): take a module reference on the component's owner, gated by [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L176), recording the [`mark_module`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L246) mark
- [`'\<snd_soc_component_module_put\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L238): drop that reference, honoring the rollback mark
- [`'\<snd_soc_dai_action\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497): add a signed delta to both the DAI's per-stream count and the parent component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213)
- [`'\<snd_soc_component_active\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L362): read the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) open-stream use count

### Suspend, resume, and the PM bit (soc-component.c)

- [`'\<snd_soc_component_suspend\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284): run the [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback and set the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) bit
- [`'\<snd_soc_component_resume\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291): run the [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback and clear the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) bit
- [`'\<snd_soc_component_is_suspended\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L368): read the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) PM bit

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide covering the register-access model
- [`Documentation/driver-api/regmap.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/regmap.rst): the regmap register-access abstraction the component wrappers dispatch to
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the power-down delay the [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181) flag honors at stop

## OTHER SOURCES

- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The register-I/O surface is three wrappers plus an inner read, and the lifecycle state is three counters and bits. Every register wrapper resolves the regmap-versus-callback choice and serializes the legacy path on [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229).

| Operation | Function | Path |
|-----------|----------|------|
| read | [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671) | `io_mutex` then regmap or [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback |
| write | [`snd_soc_component_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L706) | `io_mutex` then regmap or [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback |
| update field | [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751) | regmap RMW, or legacy RMW under `io_mutex` |
| count streams | [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) | adjust [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) and the per-DAI count together |
| read use count | [`snd_soc_component_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L362) | return [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) |
| take module ref | [`snd_soc_component_module_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L222) | [`try_module_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h) gated by [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L176) |
| mark suspended | [`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284) | run [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), set [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) |

## DETAILS

### Register I/O serializes on io_mutex

The register wrappers take the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) so accesses to a codec that has no regmap cannot race. [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671) holds the mutex around the inner read:

```c
/* sound/soc/soc-component.c:671 */
unsigned int snd_soc_component_read(struct snd_soc_component *component,
				    unsigned int reg)
{
	unsigned int val;

	mutex_lock(&component->io_mutex);
	val = soc_component_read_no_lock(component, reg);
	mutex_unlock(&component->io_mutex);

	return val;
}
```

[`soc_component_read_no_lock()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L642) is the inner read, dispatching to regmap when one is attached or to the driver's [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback otherwise, and returning `-EIO` when the component has neither:

```c
/* sound/soc/soc-component.c:642 */
static unsigned int soc_component_read_no_lock(
	struct snd_soc_component *component,
	unsigned int reg)
{
	int ret;
	unsigned int val = 0;

	if (component->regmap)
		ret = regmap_read(component->regmap, reg, &val);
	else if (component->driver->read) {
		ret = 0;
		val = component->driver->read(component, reg);
	}
	else
		ret = -EIO;

	if (ret < 0)
		return soc_component_ret_reg_rw(component, ret, reg);

	return val;
}
```

[`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751) is the read-modify-write entry point. When a regmap is present it hands the whole cycle to [`regmap_update_bits_check()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h), which locks internally; otherwise it calls [`snd_soc_component_update_bits_legacy()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L719):

```c
/* sound/soc/soc-component.c:751 */
int snd_soc_component_update_bits(struct snd_soc_component *component,
				  unsigned int reg, unsigned int mask, unsigned int val)
{
	bool change;
	int ret;

	if (component->regmap)
		ret = regmap_update_bits_check(component->regmap, reg, mask,
					       val, &change);
	else
		ret = snd_soc_component_update_bits_legacy(component, reg,
							   mask, val, &change);

	if (ret < 0)
		return soc_component_ret_reg_rw(component, ret, reg);
	return change;
}
```

The legacy path is where the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) earns its place, holding the read, the modify, and the conditional write together so no other access sees the half-updated register:

```c
/* sound/soc/soc-component.c:719 */
static int snd_soc_component_update_bits_legacy(
	struct snd_soc_component *component, unsigned int reg,
	unsigned int mask, unsigned int val, bool *change)
{
	unsigned int old, new;
	int ret = 0;

	mutex_lock(&component->io_mutex);

	old = soc_component_read_no_lock(component, reg);

	new = (old & ~mask) | (val & mask);
	*change = old != new;
	if (*change)
		ret = soc_component_write_no_lock(component, reg, new);

	mutex_unlock(&component->io_mutex);

	return soc_component_ret_reg_rw(component, ret, reg);
}
```

A driver that supplies a regmap leaves the [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callbacks NULL, and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) fetches the device's regmap and records it on the component, so the wrappers take the regmap branch and the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) protects only the legacy callback path.

```
    Register I/O dispatch: each wrapper resolves regmap vs callback
    ─────────────────────────────────────────────────────────────
    (the legacy callback branch is what io_mutex serializes)

    wrapper            regmap attached      no regmap (callback)
    ─────────────────  ───────────────────  ────────────────────
    read               regmap_read          driver->read  (else -EIO)
    write              regmap_write         driver->write (else -EIO)
    update_bits        regmap_update_       update_bits_legacy:
                       bits_check           read, modify, write
                       (locks itself)       under io_mutex

    the regmap branch reaches the hardware register bus:

    ┌───────────────────────────────────────────────────────────┐
    │ component->regmap  ─▶  regmap core  ─▶  one of:           │
    │     I2C    SPI    SoundWire    memory-mapped (MMIO)       │
    └───────────────────────────────────────────────────────────┘
```

### Module reference and the open use count

[`snd_soc_component_module_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L222) takes a reference on the module that owns the component so it cannot be unloaded while in use. The [`module_get_upon_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L176) flag selects when the reference is taken, at probe for most components or at stream open for those that allow unbinding while idle, and the function records the [`mark_module`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L246) mark on success:

```c
/* sound/soc/soc-component.c:222 */
int snd_soc_component_module_get(struct snd_soc_component *component,
				 void *mark, int upon_open)
{
	int ret = 0;

	if (component->driver->module_get_upon_open == !!upon_open &&
	    !try_module_get(component->dev->driver->owner))
		ret = -ENODEV;

	/* mark module if succeeded */
	if (ret == 0)
		soc_component_mark_push(component, mark, module);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_component_module_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L238) drops the reference, returning early on a rollback whose mark does not match so a reference is never dropped twice:

```c
/* sound/soc/soc-component.c:238 */
void snd_soc_component_module_put(struct snd_soc_component *component,
				  void *mark, int upon_open, int rollback)
{
	if (rollback && !soc_component_mark_match(component, mark, module))
		return;

	if (component->driver->module_get_upon_open == !!upon_open)
		module_put(component->dev->driver->owner);

	/* remove the mark from module */
	soc_component_mark_pop(component, module);
}
```

The [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) field counts open streams across the component. It is maintained alongside the per-DAI count by [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497), which adds the same signed delta to both the DAI's stream count and the parent component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) field, so a single accounting point keeps them in sync:

```c
/* sound/soc/soc-dai.c:497 */
void snd_soc_dai_action(struct snd_soc_dai *dai,
			int stream, int action)
{
	/* see snd_soc_dai_stream_active() */
	dai->stream[stream].active	+= action;

	/* see snd_soc_component_active() */
	dai->component->active		+= action;
}
```

[`snd_soc_component_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L362) reads the count, which the suspend path and DAPM consult to decide whether the component is still carrying audio:

```c
/* include/sound/soc-component.h:362 */
static inline unsigned int
snd_soc_component_active(struct snd_soc_component *component)
{
	return component->active;
}
```

### Suspend marks the component's PM state

[`snd_soc_component_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L284) and [`snd_soc_component_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291) run the optional driver hooks and set the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) bit so the core records the PM state itself rather than asking the driver:

```c
/* sound/soc/soc-component.c:284 */
void snd_soc_component_suspend(struct snd_soc_component *component)
{
	if (component->driver->suspend)
		component->driver->suspend(component);
	component->suspended = 1;
}

void snd_soc_component_resume(struct snd_soc_component *component)
{
	if (component->driver->resume)
		component->driver->resume(component);
	component->suspended = 0;
}
```

When the descriptor's [`suspend_bias_off`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L180) flag is set, DAPM also drops the bias to [`SND_SOC_BIAS_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L416) across suspend, and the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) count tells the suspend path whether a stream is still running on the component before it powers anything down.
