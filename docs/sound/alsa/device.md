# ALSA device object (snd_device)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ALSA card is a container of typed sub-objects (a control, one or more PCMs, a timer, raw MIDI), and the kernel wraps each one in a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) so the card can build, register, disconnect, and free them from one place in a fixed order. The wrapper holds five things, the list node linking it into the card's [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) list, a back pointer to the owning [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), a lifecycle [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) drawn from [`enum snd_device_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), a [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) drawn from [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38), and a [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer to the real object plus its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) function pointer struct. A sub-object joins the card by calling [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29), which allocates the wrapper, sets its state to [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), and inserts it into the [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) list sorted by [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), so [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189) and [`snd_device_free_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L222) later walk the list in the order the enum spells out, low-level hardware first and the control device last on register, the reverse on free.

```
    card->devices, sorted by enum snd_device_type
    ─────────────────────────────────────────────

      LOWLEVEL ─▶ INFO ─▶ ... ─▶ PCM ─▶ ... ─▶ CONTROL
      (head)                                   (tail)

      register_all:  walk head ─▶ tail   (LOWLEVEL before CONTROL)
      free_all:      walk tail ─▶ head   (CONTROL before LOWLEVEL)
```

## SUMMARY

Every object an ALSA card owns is registered as a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), and the card never touches the object directly. It walks its [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) list and dispatches through the [`struct snd_device_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) function pointer struct each wrapper carries. The three callbacks in that struct are [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), and [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), and all three are optional. A sub-object creates its wrapper with [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29), passing its [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38), a unique [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer that doubles as the lookup key, and a pointer to a static ops struct.

The [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) drives the ordering. [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29) keeps the [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) list sorted by the numeric value of [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38), whose first value is [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) and whose last value is [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50). [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189), reached from [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870), walks the list forward and runs [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) on each, so the low-level hardware device registers before the control device that exposes the card to userspace. Teardown reverses the order. [`snd_device_disconnect_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L208) from [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) and [`snd_device_free_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L222) from [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580) walk the list in reverse, so the control device is disconnected and freed before the hardware it depends on. The single-object entry points [`snd_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L171), [`snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L106), and [`snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L130) find one wrapper by its [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer through [`look_for_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L82) and drive that one through the same callbacks. On an x86-64 ACPI machine the ASoC layer populates this list indirectly, where its [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) creates a [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) wrapper through [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) and its mixer controls reach the single [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) device through [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501).

## SPECIFICATIONS

The [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) abstraction is a Linux kernel software construct internal to the ALSA core and has no standalone hardware specification. The character devices the registered objects surface under /dev/snd (controlC0, pcmC0D0p, timer) are an ALSA interface rather than a device-class register layout.

## LINUX KERNEL

### The wrapper and its enums (include/sound/core.h)

- [`'\<struct snd_device\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67): the per-object wrapper holding the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) node, the owning [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67), the [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer, and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer
- [`'\<enum snd_device_type\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38): the type tag from [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) through [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50); its numeric order is the registration and free order
- [`'\<enum snd_device_state\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53): the three lifecycle states [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), and [`SNDRV_DEV_DISCONNECTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L56)
- [`'\<struct snd_device_ops\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61): the function pointer struct with [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), and [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61)
- [`'\<struct snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80): the card; its [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) field is the sorted list every wrapper joins

### Per-object lifecycle (sound/core/device.c)

- [`'\<snd_device_new\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29): allocate a wrapper, set its state to [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), and insert it into [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) sorted by [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67)
- [`'\<snd_device_register\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L171): register one already-built object found by its [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer
- [`'\<snd_device_disconnect\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L106): move one object into the disconnected state, running [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) when it was registered
- [`'\<snd_device_free\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L130): unlink one object and run [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) then [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) according to its state
- [`'\<look_for_dev\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L82): scan [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) for the wrapper whose [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) matches the supplied pointer

### Internal state-machine helpers (sound/core/device.c)

- [`'\<__snd_device_register\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L145): run [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) when the state is [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) and advance to [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53)
- [`'\<__snd_device_disconnect\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59): run [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) when the state is [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) and advance to [`SNDRV_DEV_DISCONNECTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L56)
- [`'\<__snd_device_free\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L69): [`list_del`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L235) the wrapper, call [`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59), run [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), and free the wrapper

### Whole-card sweeps (sound/core/device.c)

- [`'\<snd_device_register_all\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189): walk [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) forward and register each object
- [`'\<snd_device_disconnect_all\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L208): walk the list in reverse and disconnect each object
- [`'\<snd_device_free_all\>':'sound/core/device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L222): free the list in reverse, deferring [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) and [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) to a second pass

### Card-level callers and userspace registration

- [`'\<snd_card_register\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870): the public card-bring-up entry that calls [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189)
- [`'\<snd_card_disconnect\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491): the card-removal entry that calls [`snd_device_disconnect_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L208)
- [`'\<snd_card_do_free\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580): the card release path that calls [`snd_device_free_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L222)
- [`'\<snd_register_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249): allocate a minor number and add the character device that surfaces in /dev/snd; called from inside the [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callbacks
- [`'\<snd_device_alloc\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L127): allocate the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) the object later passes to [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249)

### Object constructors that register a wrapper

- [`'\<snd_ctl_create\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2355): build the control object with [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50), the last type in the list
- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2295): the control object's [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback, which calls [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249)
- [`'\<_snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697): build a PCM object with [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43), earlier in the list than the control
- [`'\<snd_pcm_dev_register\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044): the PCM object's [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback, which registers the playback and capture nodes through [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the "Management of Cards and Components" chapter covering [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29) and the constructor/destructor pattern
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated reference for the ALSA core API, including the device-management functions
- [`Documentation/sound/designs/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/index.rst): the ALSA design notes covering the card and component model

## OTHER SOURCES

- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) exposes no kernel-internal call interface of its own beyond the three callbacks in its [`struct snd_device_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61). Each callback receives the wrapper pointer and reaches the real object through [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67). The core runs them on the state transitions the table records, and an object may leave any of the three NULL, in which case the matching transition still advances the state while performing no object-specific work.

| Callback | Run by | Runs when state is | New state |
|----------|--------|--------------------|-----------|
| [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) | [`__snd_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L145) | [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) | [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) |
| [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) | [`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59) | [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) | [`SNDRV_DEV_DISCONNECTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L56) |
| [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) | [`__snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L69) | any (after disconnect) | (wrapper freed) |

[`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) creates the userspace-visible part of the object, typically the /dev/snd character device, and runs once when the card is registered or when the object is added after registration. [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) detaches that visible part so further userspace opens fail, and runs at card removal before any memory is released. [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) releases the object itself, and the core runs it only after a disconnect because [`__snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L69) calls [`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59) first.

## DETAILS

### The wrapper and its two enums

A [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) is the card's handle on one sub-object. It carries the list node threading it onto the card, the back pointer to the card, the current state, the type tag, the pointer to the wrapped object, and the callbacks:

```c
/* include/sound/core.h:67 */
struct snd_device {
	struct list_head list;		/* list of registered devices */
	struct snd_card *card;		/* card which holds this device */
	enum snd_device_state state;	/* state of the device */
	enum snd_device_type type;	/* device type */
	void *device_data;		/* device structure */
	const struct snd_device_ops *ops;	/* operations */
};
```

The [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) field is the ordering key. [`enum snd_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) lists the object kinds from [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) (the hardware low-level driver) up to [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50), and the comment above the enum states the order of the values is itself the calling order. According to the comment on [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50), "this must be the last one", so the control device, the mixer interface userspace opens first to discover the card, is always registered after every hardware object it describes:

```c
/* include/sound/core.h:38 */
/* device allocation stuff */
/* type of the object used in snd_device_*()
 * this also defines the calling order
 */
enum snd_device_type {
	SNDRV_DEV_LOWLEVEL,
	SNDRV_DEV_INFO,
	SNDRV_DEV_BUS,
	SNDRV_DEV_CODEC,
	SNDRV_DEV_PCM,
	SNDRV_DEV_COMPRESS,
	SNDRV_DEV_RAWMIDI,
	SNDRV_DEV_TIMER,
	SNDRV_DEV_SEQUENCER,
	SNDRV_DEV_HWDEP,
	SNDRV_DEV_JACK,
	SNDRV_DEV_CONTROL,	/* NOTE: this must be the last one */
};
```

The [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) field tracks where the object sits in its lifecycle. [`enum snd_device_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) has exactly three values, and each callback fires on one transition:

```c
/* include/sound/core.h:53 */
enum snd_device_state {
	SNDRV_DEV_BUILD,
	SNDRV_DEV_REGISTERED,
	SNDRV_DEV_DISCONNECTED,
};
```

The callbacks are three optional function pointers:

```c
/* include/sound/core.h:61 */
struct snd_device_ops {
	int (*dev_free)(struct snd_device *dev);
	int (*dev_register)(struct snd_device *dev);
	int (*dev_disconnect)(struct snd_device *dev);
};
```

That ops pointer is the last of the wrapper's fields, the type sorting it onto the card's list and device_data keying lookups while the three callbacks fire on the state moves:

```
    struct snd_device: a typed handle on one sub-object
    ───────────────────────────────────────────────────

    ┌────────────────────────────────────────────┐
    │ list         node on card->devices         │
    │ card         owning struct snd_card        │
    │ state        SNDRV_DEV_BUILD / REGISTERED  │
    │ type         enum snd_device_type, sort key│
    │ device_data  ─▶ the real object, lookup key│
    │ ops          ─▶ struct snd_device_ops      │
    └────────────────────────────────────────────┘

    ops holds three optional callbacks:
    ┌───────────────────────────────────────────┐
    │ dev_register    BUILD      to REGISTERED  │
    │ dev_disconnect  REGISTERED to DISCONNECTED│
    │ dev_free        any, after disconnect     │
    └───────────────────────────────────────────┘
```

### snd_device_new inserts sorted by type

[`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29) allocates the wrapper, fills in the type, the [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) starting state, the object pointer, and the ops, then inserts the wrapper into the card's [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) list at the position that keeps the list sorted by ascending [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67). It walks the list backward with [`list_for_each_prev()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L726) until it finds an entry whose type is less than or equal to the new one, and inserts after it:

```c
/* sound/core/device.c:29 */
int snd_device_new(struct snd_card *card, enum snd_device_type type,
		   void *device_data, const struct snd_device_ops *ops)
{
	struct snd_device *dev;
	struct list_head *p;

	if (snd_BUG_ON(!card || !device_data || !ops))
		return -ENXIO;
	dev = kzalloc_obj(*dev);
	if (!dev)
		return -ENOMEM;
	INIT_LIST_HEAD(&dev->list);
	dev->card = card;
	dev->type = type;
	dev->state = SNDRV_DEV_BUILD;
	dev->device_data = device_data;
	dev->ops = ops;

	/* insert the entry in an incrementally sorted list */
	list_for_each_prev(p, &card->devices) {
		struct snd_device *pdev = list_entry(p, struct snd_device, list);
		if ((unsigned int)pdev->type <= (unsigned int)type)
			break;
	}

	list_add(&dev->list, p);
	return 0;
}
```

Sorting at insertion time leaves the later whole-card sweeps with nothing to sort. A forward walk visits objects in ascending type order, and a reverse walk visits them in descending order. The [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer is the object identity, and the doc comment requires the pointer address to be unique and unchanged, because [`look_for_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L82) later matches on exactly that pointer.

### The state machine is gated, so each transition runs at most once

The three internal helpers each guard on the current state, so calling a transition twice is a no-op the second time. [`__snd_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L145) runs [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) only from [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), and on success advances to [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53):

```c
/* sound/core/device.c:145 */
static int __snd_device_register(struct snd_device *dev)
{
	if (dev->state == SNDRV_DEV_BUILD) {
		if (dev->ops->dev_register) {
			int err = dev->ops->dev_register(dev);
			if (err < 0)
				return err;
		}
		dev->state = SNDRV_DEV_REGISTERED;
	}
	return 0;
}
```

[`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59) runs [`dev_disconnect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) only from [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53), so an object that was built but never registered, or one already disconnected, is skipped:

```c
/* sound/core/device.c:59 */
static void __snd_device_disconnect(struct snd_device *dev)
{
	if (dev->state == SNDRV_DEV_REGISTERED) {
		if (dev->ops->dev_disconnect &&
		    dev->ops->dev_disconnect(dev))
			dev_err(dev->card->dev, "device disconnect failure\n");
		dev->state = SNDRV_DEV_DISCONNECTED;
	}
}
```

[`__snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L69) unlinks the wrapper from the list, calls [`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59) so a still-registered object is disconnected first, runs [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), and frees the wrapper:

```c
/* sound/core/device.c:69 */
static void __snd_device_free(struct snd_device *dev)
{
	/* unlink */
	list_del(&dev->list);

	__snd_device_disconnect(dev);
	if (dev->ops->dev_free) {
		if (dev->ops->dev_free(dev))
			dev_err(dev->card->dev, "device free failure\n");
	}
	kfree(dev);
}
```

The full path through the three states is [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) at [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29), then [`SNDRV_DEV_REGISTERED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53) once [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) succeeds, then [`SNDRV_DEV_DISCONNECTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L56) at teardown, then freed:

```
    snd_device state transitions
    ────────────────────────────

      snd_device_new()
            │
            ▼
      ┌──────────────────┐  dev_register   ┌──────────────────────┐
      │ SNDRV_DEV_BUILD  │────────────────▶│ SNDRV_DEV_REGISTERED │
      └──────────────────┘                 └──────────┬───────────┘
            │                                         │ dev_disconnect
            │ dev_free (no node yet)                  ▼
            │                              ┌────────────────────────┐
            │                              │ SNDRV_DEV_DISCONNECTED │
            │                              └───────────┬────────────┘
            │                                          │ dev_free
            ▼                                          ▼
                            (wrapper unlinked and freed)
```

### The single-object entry points find the wrapper by pointer

The public per-object calls take the card and the object's [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer rather than the wrapper, so they first translate the pointer to a wrapper with [`look_for_dev()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L82), a linear scan of the card's list:

```c
/* sound/core/device.c:82 */
static struct snd_device *look_for_dev(struct snd_card *card, void *device_data)
{
	struct snd_device *dev;

	list_for_each_entry(dev, &card->devices, list)
		if (dev->device_data == device_data)
			return dev;

	return NULL;
}
```

[`snd_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L171) is the path a driver uses to register one object after the card is already up, for example a jack created on the fly. It looks the object up and dispatches to the same [`__snd_device_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L145) the whole-card sweep uses:

```c
/* sound/core/device.c:171 */
int snd_device_register(struct snd_card *card, void *device_data)
{
	struct snd_device *dev;

	if (snd_BUG_ON(!card || !device_data))
		return -ENXIO;
	dev = look_for_dev(card, device_data);
	if (dev)
		return __snd_device_register(dev);
	snd_BUG();
	return -ENXIO;
}
```

[`snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L130) and [`snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L106) follow the same shape, resolving the pointer and calling [`__snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L69) or [`__snd_device_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L59). [`snd_device_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L130) is the destructor an object constructor calls in its own error-unwind path when a later step fails:

```c
/* sound/core/device.c:130 */
void snd_device_free(struct snd_card *card, void *device_data)
{
	struct snd_device *dev;
	
	if (snd_BUG_ON(!card || !device_data))
		return;
	dev = look_for_dev(card, device_data);
	if (dev)
		__snd_device_free(dev);
	else
		dev_dbg(card->dev, "device free %p (from %pS), not found\n",
			device_data, __builtin_return_address(0));
}
```

All three public calls share that shape, the list scan turning the device_data pointer into its wrapper before the matching internal helper runs:

```
    The single-object calls resolve device_data to a wrapper
    ────────────────────────────────────────────────────────

    snd_device_register(card, device_data)
    snd_device_disconnect(card, device_data)
    snd_device_free(card, device_data)
                    │ device_data pointer
                    ▼
    ┌────────────────────────────────────────┐
    │ look_for_dev(card, device_data)        │
    │ scan card->devices for the wrapper     │
    │ whose device_data == the pointer       │
    └────────────────────────────────────────┘
                    │ the matching snd_device
                    ▼
    ┌──────────────────────────────────────────┐
    │ __snd_device_register   (if BUILD)       │
    │ __snd_device_disconnect (if REGISTERED)  │
    │ __snd_device_free       (unlink + free)  │
    └──────────────────────────────────────────┘
```

### The whole-card sweeps walk the sorted list in opposite directions

[`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L189) is the forward sweep. [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) calls it once the card is ready, and it walks [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97) from head to tail, registering each object. Because the list is sorted by ascending type, the [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) hardware driver registers before the [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) device, which registers before the [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) mixer:

```c
/* sound/core/device.c:189 */
int snd_device_register_all(struct snd_card *card)
{
	struct snd_device *dev;
	int err;
	
	if (snd_BUG_ON(!card))
		return -ENXIO;
	list_for_each_entry(dev, &card->devices, list) {
		err = __snd_device_register(dev);
		if (err < 0)
			return err;
	}
	return 0;
}
```

[`snd_device_disconnect_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L208), called from [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491), walks the same list with [`list_for_each_entry_reverse()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L792), so the control device disconnects first and the low-level hardware last:

```c
/* sound/core/device.c:208 */
void snd_device_disconnect_all(struct snd_card *card)
{
	struct snd_device *dev;

	if (snd_BUG_ON(!card))
		return;
	list_for_each_entry_reverse(dev, &card->devices, list)
		__snd_device_disconnect(dev);
}
```

[`snd_device_free_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L222), called from [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580), frees in reverse as well, in two passes. The first reverse pass skips [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) and [`SNDRV_DEV_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L38) so the mixer interface and the hardware driver outlive the PCM and other objects that depend on them, and the second reverse pass frees everything remaining. According to the comment, "exception: free ctl and lowlevel stuff later":

```c
/* sound/core/device.c:222 */
void snd_device_free_all(struct snd_card *card)
{
	struct snd_device *dev, *next;

	if (snd_BUG_ON(!card))
		return;
	list_for_each_entry_safe_reverse(dev, next, &card->devices, list) {
		/* exception: free ctl and lowlevel stuff later */
		if (dev->type == SNDRV_DEV_CONTROL ||
		    dev->type == SNDRV_DEV_LOWLEVEL)
			continue;
		__snd_device_free(dev);
	}

	/* free all */
	list_for_each_entry_safe_reverse(dev, next, &card->devices, list)
		__snd_device_free(dev);
}
```

The two reverse loops fall out as two passes, the first freeing PCM and the other middle objects while it skips CONTROL and LOWLEVEL, the second coming back for those two:

```
    snd_device_free_all frees in reverse, in two passes
    ───────────────────────────────────────────────────

    list sorted by type (head -> tail):
      LOWLEVEL .. PCM .. RAWMIDI .. JACK .. CONTROL

    pass 1  reverse walk, free everything EXCEPT
    ┌─────────────────────────────────┐
    │ skip SNDRV_DEV_CONTROL          │
    │ skip SNDRV_DEV_LOWLEVEL         │
    │ free PCM, RAWMIDI, JACK, ... now│
    └─────────────────────────────────┘
                    │ dependents gone first
                    ▼
    pass 2  reverse walk again, free the rest
    ┌────────────────────────┐
    │ free SNDRV_DEV_CONTROL │
    │ free SNDRV_DEV_LOWLEVEL│
    └────────────────────────┘
    ctl and lowlevel outlive the objects depending on them
```

### A PCM object and the control object take adjacent type slots

A PCM is created through [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697), which builds two static [`struct snd_device_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) instances and registers the PCM as a [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) object. A normal PCM gets all three callbacks, while an internal PCM gets only [`dev_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61), so it is freed with the card while surfacing no /dev/snd node:

```c
/* sound/core/pcm.c:697 */
static int _snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, bool internal,
		struct snd_pcm **rpcm)
{
	struct snd_pcm *pcm;
	int err;
	static const struct snd_device_ops ops = {
		.dev_free = snd_pcm_dev_free,
		.dev_register =	snd_pcm_dev_register,
		.dev_disconnect = snd_pcm_dev_disconnect,
	};
	static const struct snd_device_ops internal_ops = {
		.dev_free = snd_pcm_dev_free,
	};
	...
	err = snd_device_new(card, SNDRV_DEV_PCM, pcm,
			     internal ? &internal_ops : &ops);
	if (err < 0)
		goto free_pcm;

	if (rpcm)
		*rpcm = pcm;
	return 0;

free_pcm:
	snd_pcm_free(pcm);
	return err;
}
```

The control object is created by [`snd_ctl_create()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2355) as a [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) object, the last type, with the card itself as the [`device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) pointer:

```c
/* sound/core/control.c:2355 */
int snd_ctl_create(struct snd_card *card)
{
	static const struct snd_device_ops ops = {
		.dev_free = snd_ctl_dev_free,
		.dev_register =	snd_ctl_dev_register,
		.dev_disconnect = snd_ctl_dev_disconnect,
	};
	int err;
	...
	err = snd_device_alloc(&card->ctl_dev, card);
	if (err < 0)
		return err;
	dev_set_name(card->ctl_dev, "controlC%d", card->number);

	err = snd_device_new(card, SNDRV_DEV_CONTROL, card, &ops);
	if (err < 0)
		put_device(card->ctl_dev);
	return err;
}
```

Both objects were inserted into the same list by [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29). Since [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) sorts before [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50), the forward register sweep brings up the PCM's playback and capture nodes before the control node, and the reverse free sweep tears the control node down first.

```
    Which snd_device_ops callbacks each object sets
    ───────────────────────────────────────────────

    ┌──────────────┬───────────────────┬──────────────────────────────┐
    │ object       │ type              │ ops set                      │
    ├──────────────┼───────────────────┼──────────────────────────────┤
    │ normal PCM   │ SNDRV_DEV_PCM     │ free + register + disconnect │
    │ internal PCM │ SNDRV_DEV_PCM     │ free only (no /dev node)     │
    │ control      │ SNDRV_DEV_CONTROL │ free + register + disconnect │
    └──────────────┴───────────────────┴──────────────────────────────┘
    a NULL callback still advances the state, doing no work
```

### A registered object has no node of its own until dev_register runs

A [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) is a bookkeeping wrapper. It owns no /dev/snd entry by itself, and nothing about the wrapper appears under /dev. The userspace-visible character device is created indirectly, inside the object's [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback, by a call to [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249), which allocates a minor number and adds the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L719) the udev layer turns into a node. The control object's callback [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2295) shows the indirection, registering the controlC%d node as its wrapper transitions out of [`SNDRV_DEV_BUILD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L53):

```c
/* sound/core/control.c:2295 */
static int snd_ctl_dev_register(struct snd_device *device)
{
	struct snd_card *card = device->device_data;
	int err;

	err = snd_register_device(SNDRV_DEVICE_TYPE_CONTROL, card, -1,
				  &snd_ctl_f_ops, card, card->ctl_dev);
	if (err < 0)
		return err;
	call_snd_ctl_lops(card, lregister);
	return 0;
}
```

[`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) is the function that surfaces the node. It allocates a free minor for the requested device type, stores the file operations and the private pointer in the global minor table, sets the device number, and adds the device to the driver model with [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572):

```c
/* sound/core/sound.c:249 */
int snd_register_device(int type, struct snd_card *card, int dev,
			const struct file_operations *f_ops,
			void *private_data, struct device *device)
{
	int minor;
	int err = 0;
	struct snd_minor *preg;

	if (snd_BUG_ON(!device))
		return -EINVAL;

	preg = kmalloc_obj(*preg);
	if (preg == NULL)
		return -ENOMEM;
	preg->type = type;
	preg->card = card ? card->number : -1;
	preg->device = dev;
	preg->f_ops = f_ops;
	preg->private_data = private_data;
	preg->card_ptr = card;
	guard(mutex)(&sound_mutex);
	minor = snd_find_free_minor(type, card, dev);
	if (minor < 0) {
		err = minor;
		goto error;
	}

	preg->dev = device;
	device->devt = MKDEV(major, minor);
	err = device_add(device);
	if (err < 0)
		goto error;

	snd_minors[minor] = preg;
 error:
	if (err < 0)
		kfree(preg);
	return err;
}
```

The PCM object reaches the same function from [`snd_pcm_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L1044), calling [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) once per active direction to create the pcmC%dD%dp and pcmC%dD%dc nodes. The relationship between the [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) wrapper and /dev/snd is therefore indirect, where the wrapper orders and gates the lifecycle and the object's own [`dev_register`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L61) callback registers the character device through [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249).

```
    The /dev/snd node is registered below the wrapper
    ─────────────────────────────────────────────────

    ┌───────────────────────────┐
    │ struct snd_device wrapper │
    │ orders and gates lifecycle│
    │ owns NO /dev/snd entry    │
    └───────────────────────────┘
                  │ dev_register callback (e.g.
                  │ snd_ctl_dev_register) calls
                  ▼
    ┌──────────────────────────┐
    │ snd_register_device()    │
    │ picks a free minor       │
    │ sets struct device devt  │
    │ device_add(struct device)│
    └──────────────────────────┘
                  │ populates
                  ▼
    ┌───────────────────────────┐
    │ snd_minors[minor]         │
    │ holds f_ops + private_data│
    │ struct device -> udev node│
    │ controlC%d, pcmC%dD%dp/c  │
    └───────────────────────────┘
```

### ASoC populates the list through ordinary PCM and control objects

On an x86-64 ACPI machine the ASoC layer never builds a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) directly. Its [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) creates an ordinary PCM, so the [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) wrapper appears because [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) forwards to [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697), which calls [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29):

```c
/* sound/core/pcm.c:767 */
int snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, struct snd_pcm **rpcm)
{
	return _snd_pcm_new(card, id, device, playback_count, capture_count,
			false, rpcm);
}
```

That is the same [`_snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L697) shown above whose [`snd_device_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c#L29) call inserts the [`SNDRV_DEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L43) wrapper into [`card->devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97). An ASoC mixer control reaches the card's single [`SNDRV_DEV_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L50) device the same indirect way, where [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) hands each control to [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) on the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) rather than registering a new wrapper. The ASoC card is therefore an ordinary collection of typed objects that each become a [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) through the same constructors any ALSA driver uses.
