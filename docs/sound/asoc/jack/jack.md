# ASoC jack (snd_soc_jack)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A jack is the physical headphone, headset, or microphone socket on a machine, and ASoC represents one with [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), a passive object the machine driver creates and a detection method updates. The object holds a [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask of [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) values, a [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) list of [`struct snd_soc_jack_pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) records that each name a DAPM endpoint, a [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) of type [`struct blocking_notifier_head`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L65), a [`jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) list of voltage ranges, and the underlying ALSA [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L61) that surfaces the state to user space. A detection method calls [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with a new status and a mask of the bits it owns, and that one call folds the bits into [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) under the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), enables or disables each DAPM pin whose [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) intersects the new status, fires the blocking notifier chain, runs [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005), and pushes the state to ALSA through [`snd_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L87). The detection methods that drive that report (voltage zones, a GPIO line, codec-integrated detection) are documented separately.

```
    struct snd_soc_jack
    ┌─────────────────────────────────────────────────────────────┐
    │  mutex                                                      │
    │  jack ─────▶ struct snd_jack  (ALSA, user-space view)       │
    │  card ─────▶ struct snd_soc_card                            │
    │  status   (bitmask of enum snd_jack_types)                  │
    │  pins ──────────┐   jack_zones ─────┐   notifier ───────┐   │
    └─────────────────┼───────────────────┼───────────────────┼───┘
                      │                   │                   │
                      ▼                   ▼                   ▼
       struct snd_soc_jack_pin   snd_soc_jack_zone   blocking_notifier_head
       ┌────────────────────┐    ┌──────────────┐    ┌──────────────────┐
       │ pin   (DAPM name)  │    │ min_mv       │    │ notifier_block 0 │
       │ mask  (jack bits)  │    │ max_mv       │    │ notifier_block 1 │
       │ invert             │    │ jack_type    │    │ ...              │
       └─────────┬──────────┘    └──────────────┘    └──────────────────┘
                 │ snd_soc_jack_report() enables/disables by mask
                 ▼
       DAPM pin (endpoint widget) ──▶ snd_soc_dapm_sync()

    snd_soc_jack_report(jack, status, mask):
      status &= ~mask; status |= new & mask;  then for each pin,
      enable = pin->mask & status (inverted if pin->invert);
      enable ? dapm_enable_pin : dapm_disable_pin;
      blocking_notifier_call_chain(); dapm_sync(); snd_jack_report()
```

## SUMMARY

ASoC layers jack detection on top of the ALSA jack API. The machine driver, or a codec acting on the machine driver's behalf, creates one [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) with [`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L82), passing a bitmask of [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) the jack can report and an array of [`struct snd_soc_jack_pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) records, each naming a DAPM endpoint and the status bits that drive it. The older [`snd_soc_card_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L59) creates the same object without pins, and [`snd_soc_jack_add_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136) attaches them afterward. Both paths run [`jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L32), which initializes the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), the two lists, and the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain before calling [`snd_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L80) to build the ALSA [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L61).

A detection method monitors hardware and calls [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with the bits it observed and a mask of the bits it controls, leaving the rest of [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) untouched so several methods can share one jack. The masking step is the contract. The line `jack->status &= ~mask` clears only the bits the caller owns, and `jack->status |= status & mask` sets exactly those, so a GPIO method reporting [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) never disturbs a microphone bit another method set. A consumer that needs to observe state changes without owning detection registers a [`struct notifier_block`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L52) with [`snd_soc_jack_notifier_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L180), and every [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) fires that chain before the DAPM sync.

## SPECIFICATIONS

The [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) object is a Linux kernel software construct and has no standalone hardware specification. The four-pole headset electrical convention (the CTIA and OMTP pinouts, mic-bias voltage thresholds) is set by the connector conventions the analog codecs follow, and the user-visible state is the ALSA jack ABI in [`include/sound/jack.h`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h).

## LINUX KERNEL

### Jack and pin types (soc-jack.h, jack.h)

- [`'\<struct snd_soc_jack\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80): the jack object; holds the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), the ALSA [`jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) pointer, the [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), the [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and [`jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) lists, the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask, and the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain
- [`'\<struct snd_soc_jack_pin\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19): a DAPM endpoint to update; carries the [`pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) name, the [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) of jack-status bits that drive it, and the [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) flag
- [`'\<enum snd_jack_types\>':'include/sound/jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38): the bit values for [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39), [`SND_JACK_MICROPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L40), [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41), and [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50) through [`SND_JACK_BTN_5`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L55)
- [`'\<struct snd_jack\>':'include/sound/jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L61): the ALSA jack the ASoC object wraps; the user-space-visible side updated by [`snd_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L87)

### Jack creation (soc-card.c)

- [`'\<snd_soc_card_jack_new\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L59): create a jack with no pins; thin wrapper over [`jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L32) with `initial_kctl` true
- [`'\<snd_soc_card_jack_new_pins\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L82): create a jack and attach an array of [`struct snd_soc_jack_pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) in one call
- [`'\<jack_new\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L32): the shared initializer; sets up the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), the two lists, and the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) head, then calls [`snd_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L80)

### Pin association and reporting (soc-jack.c)

- [`'\<snd_soc_jack_add_pins\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136): link each [`struct snd_soc_jack_pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) onto [`jack->pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), add an ALSA kcontrol for each, then call [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with mask 0 to sync the initial state
- [`'\<snd_soc_jack_report\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33): fold `status & mask` into [`jack->status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), drive every pin, fire the notifier, sync DAPM, and report to ALSA, all under [`jack->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80)
- [`'\<snd_soc_jack_notifier_register\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L180): register a [`struct notifier_block`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L52) on [`jack->notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) via [`blocking_notifier_chain_register()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L148)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack model, splitting a jack into the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), its pins, and the detection methods
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the pin and route machinery a jack report drives
- [`Documentation/sound/designs/jack-controls.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/jack-controls.rst): the ALSA jack kcontrol layer that [`snd_soc_jack_add_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136) feeds through [`snd_jack_add_new_kctl()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L82)

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A jack reaches its working state in two steps. The machine driver creates the object and declares the pins, and a detection method then drives [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) over the jack's lifetime. The status mask is the contract between them, a method passes only the bits it owns, so several detection families can update one user-visible jack without clobbering one another.

| Jack status bit | Value | Meaning |
|-----------------|-------|---------|
| `SND_JACK_HEADPHONE` | 0x0001 | headphone present |
| `SND_JACK_MICROPHONE` | 0x0002 | microphone present |
| `SND_JACK_HEADSET` | 0x0003 | headphone bit OR microphone bit |
| `SND_JACK_LINEOUT` | 0x0004 | line out present |
| `SND_JACK_MECHANICAL` | 0x0008 | mechanical switch closed |
| `SND_JACK_BTN_0` | 0x4000 | button 0 (media/play) pressed |
| `SND_JACK_BTN_1` | 0x2000 | button 1 (volume up) pressed |
| `SND_JACK_BTN_2` | 0x1000 | button 2 (volume down) pressed |
| `SND_JACK_BTN_3` | 0x0800 | button 3 pressed |

### snd_soc_card_jack_new and snd_soc_card_jack_new_pins

[`snd_soc_card_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L59) creates a bare jack, and [`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L82) creates one and attaches its DAPM pins in the same call. Both take a `type` bitmask of [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) values declaring every bit the jack will ever report, which is what [`snd_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L80) uses to size the ALSA kcontrol and input device.

### snd_soc_jack_add_pins

[`snd_soc_jack_add_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136) associates an array of [`struct snd_soc_jack_pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) with the jack. Each entry names a DAPM endpoint in [`pin`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) and a [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) of jack-status bits, and the function rejects an entry with no name or no mask. After linking the pins it calls [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with status and mask both 0 so a jack whose state was set before pins existed gets synced to the new pins.

### snd_soc_jack_report

[`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) is the single update entry point every method calls. It takes the jack, the observed `status`, and a `mask` of the bits the caller owns, and it must run in a context that can sleep because it takes [`jack->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and synchronizes DAPM.

### snd_soc_jack_notifier_register

[`snd_soc_jack_notifier_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L180) adds a [`struct notifier_block`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L52) to the jack's blocking chain. According to the function comment, the callback cannot report further jack events; it exists so a consumer such as a second detection stage can react to the first stage's result.

## DETAILS

### The jack object and the pin records

[`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) is a passive container. The machine driver creates it, a detection method updates it, and it carries no detection logic of its own:

```c
/* include/sound/soc-jack.h:80 */
struct snd_soc_jack {
	struct mutex mutex;
	struct snd_jack *jack;
	struct snd_soc_card *card;
	struct list_head pins;
	int status;
	struct blocking_notifier_head notifier;
	struct list_head jack_zones;
};
```

The [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) field is the live bitmask of [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) values, [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and [`jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) are the two association lists, and [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) is the blocking chain consumers register on. Each pin record names one DAPM endpoint and the status bits that govern it:

```c
/* include/sound/soc-jack.h:19 */
/**
 * struct snd_soc_jack_pin - Describes a pin to update based on jack detection
 *
 * @pin:    name of the pin to update
 * @mask:   bits to check for in reported jack status
 * @invert: if non-zero then pin is enabled when status is not reported
 * @list:   internal list entry
 */
struct snd_soc_jack_pin {
	struct list_head list;
	const char *pin;
	int mask;
	bool invert;
};
```

The [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) flag covers the case where an endpoint should be on when the jack bit is absent, for instance a built-in microphone that is enabled only while no external microphone is plugged. The jack-type bit values are defined in [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38), where [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) is the bitwise OR of the headphone and microphone bits and the button bits sit in a separate high range:

```c
/* include/sound/jack.h:38 */
enum snd_jack_types {
	SND_JACK_HEADPHONE	= 0x0001,
	SND_JACK_MICROPHONE	= 0x0002,
	SND_JACK_HEADSET	= SND_JACK_HEADPHONE | SND_JACK_MICROPHONE,
	SND_JACK_LINEOUT	= 0x0004,
	SND_JACK_MECHANICAL	= 0x0008, /* If detected separately */
	SND_JACK_VIDEOOUT	= 0x0010,
	SND_JACK_AVOUT		= SND_JACK_LINEOUT | SND_JACK_VIDEOOUT,
	SND_JACK_LINEIN		= 0x0020,
	SND_JACK_USB		= 0x0040,

	/* Kept separate from switches to facilitate implementation */
	SND_JACK_BTN_0		= 0x4000,
	SND_JACK_BTN_1		= 0x2000,
	SND_JACK_BTN_2		= 0x1000,
	SND_JACK_BTN_3		= 0x0800,
	SND_JACK_BTN_4		= 0x0400,
	SND_JACK_BTN_5		= 0x0200,
};
```

The same constants land in this 16-bit field, the accessory bits filling the low byte from HP at bit 0 and the buttons occupying the high range from 0x4000 down to 0x0200:

```
    enum snd_jack_types as a 16-bit report mask
    ────────────────────────────────────────────
    bit  15  14  13  12  11  10   9   8   7   6   5   4   3   2   1   0
        ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
        │ . │B0 │B1 │B2 │B3 │B4 │B5 │ . │ . │USB│LI │VO │ME │LO │MI │HP │
        └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
         button range 0x4000 .. 0x0200      accessory range 0x40 .. 0x01

    HP  SND_JACK_HEADPHONE  0x0001    B0  SND_JACK_BTN_0  0x4000
    MI  SND_JACK_MICROPHONE 0x0002    B1  SND_JACK_BTN_1  0x2000
    LO  SND_JACK_LINEOUT    0x0004    B2  SND_JACK_BTN_2  0x1000
    ME  SND_JACK_MECHANICAL 0x0008    B3  SND_JACK_BTN_3  0x0800
    VO  SND_JACK_VIDEOOUT   0x0010    B4  SND_JACK_BTN_4  0x0400
    LI  SND_JACK_LINEIN     0x0020    B5  SND_JACK_BTN_5  0x0200
    USB SND_JACK_USB        0x0040
    SND_JACK_HEADSET = HEADPHONE OR MICROPHONE = 0x0003  (bits 1 and 0)
```

### Creation initializes the lists, the mutex, and the notifier

Both creation entry points call the static [`jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L32), which initializes the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), empties the two lists, primes the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) head with [`BLOCKING_INIT_NOTIFIER_HEAD`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L85), and then builds the ALSA [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L61) with [`snd_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L80):

```c
/* sound/soc/soc-card.c:32 */
static int jack_new(struct snd_soc_card *card, const char *id, int type,
		    struct snd_soc_jack *jack, bool initial_kctl)
{
	mutex_init(&jack->mutex);
	jack->card = card;
	INIT_LIST_HEAD(&jack->pins);
	INIT_LIST_HEAD(&jack->jack_zones);
	BLOCKING_INIT_NOTIFIER_HEAD(&jack->notifier);

	return snd_jack_new(card->snd_card, id, type, &jack->jack, initial_kctl, false);
}
```

[`snd_soc_card_jack_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L59) is the no-pin form. It passes `true` for `initial_kctl` so the ALSA control is created immediately, and wraps the result through [`soc_card_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L14) for error annotation:

```c
/* sound/soc/soc-card.c:59 */
int snd_soc_card_jack_new(struct snd_soc_card *card, const char *id, int type,
			  struct snd_soc_jack *jack)
{
	return soc_card_ret(card, jack_new(card, id, type, jack, true));
}
```

[`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L82) is the form a modern machine driver uses. It creates the jack with `initial_kctl` false (the kcontrols come from the pins instead) and, when `num_pins` is non-zero, hands the array straight to [`snd_soc_jack_add_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136):

```c
/* sound/soc/soc-card.c:82 */
int snd_soc_card_jack_new_pins(struct snd_soc_card *card, const char *id,
			       int type, struct snd_soc_jack *jack,
			       struct snd_soc_jack_pin *pins,
			       unsigned int num_pins)
{
	int ret;

	ret = jack_new(card, id, type, jack, false);
	if (ret)
		goto end;

	if (num_pins)
		ret = snd_soc_jack_add_pins(jack, num_pins, pins);
end:
	return soc_card_ret(card, ret);
}
```

[`snd_soc_jack_add_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L136) validates each entry, links it onto [`jack->pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), and registers an ALSA kcontrol named after the pin with [`snd_jack_add_new_kctl()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L82). The trailing [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with both arguments 0 changes no status bit but runs the pin-update loop once against the existing state:

```c
/* sound/soc/soc-jack.c:136 */
int snd_soc_jack_add_pins(struct snd_soc_jack *jack, int count,
			  struct snd_soc_jack_pin *pins)
{
	int i;

	for (i = 0; i < count; i++) {
		if (!pins[i].pin) {
			dev_err(jack->card->dev, "ASoC: No name for pin %d\n",
				i);
			return -EINVAL;
		}
		if (!pins[i].mask) {
			dev_err(jack->card->dev, "ASoC: No mask for pin %d"
				" (%s)\n", i, pins[i].pin);
			return -EINVAL;
		}

		INIT_LIST_HEAD(&pins[i].list);
		list_add(&(pins[i].list), &jack->pins);
		snd_jack_add_new_kctl(jack->jack, pins[i].pin, pins[i].mask);
	}

	/* Update to reflect the last reported status; canned jack
	 * implementations are likely to set their state before the
	 * card has an opportunity to associate pins.
	 */
	snd_soc_jack_report(jack, 0, 0);

	return 0;
}
```

According to the comment, a canned codec implementation may set the jack state before the card associates pins, so the report re-derives the pin states from whatever [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) already holds.

### snd_soc_jack_report drives pins, the notifier, and ALSA

[`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) is the heart of the subsystem. It updates [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) using the supplied mask, walks the pin list to enable or disable each DAPM endpoint, fires the blocking notifier, synchronizes DAPM, and finally pushes the new state to ALSA, all inside [`jack->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80):

```c
/* sound/soc/soc-jack.c:33 */
void snd_soc_jack_report(struct snd_soc_jack *jack, int status, int mask)
{
	struct snd_soc_dapm_context *dapm;
	struct snd_soc_jack_pin *pin;
	unsigned int sync = 0;

	if (!jack || !jack->jack)
		return;
	trace_snd_soc_jack_report(jack, mask, status);

	dapm = snd_soc_card_to_dapm(jack->card);

	mutex_lock(&jack->mutex);

	jack->status &= ~mask;
	jack->status |= status & mask;

	trace_snd_soc_jack_notify(jack, status);

	list_for_each_entry(pin, &jack->pins, list) {
		int enable = pin->mask & jack->status;

		if (pin->invert)
			enable = !enable;

		if (enable)
			snd_soc_dapm_enable_pin(dapm, pin->pin);
		else
			snd_soc_dapm_disable_pin(dapm, pin->pin);

		/* we need to sync for this case only */
		sync = 1;
	}

	/* Report before the DAPM sync to help users updating micbias status */
	blocking_notifier_call_chain(&jack->notifier, jack->status, jack);

	if (sync)
		snd_soc_dapm_sync(dapm);

	snd_jack_report(jack->jack, jack->status);

	mutex_unlock(&jack->mutex);
}
```

The masking step allows several detection methods to share one jack. The line `jack->status &= ~mask` clears only the bits the caller owns, and `jack->status |= status & mask` sets the new values of exactly those bits, so a GPIO method reporting [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) never disturbs a microphone bit another method set. For each pin, `enable` is the intersection of the pin's [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) with the updated status, flipped when [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L19) is set, and the pin's named DAPM endpoint is driven by [`snd_soc_dapm_enable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4684) or [`snd_soc_dapm_disable_pin()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4800). According to the comment, the notifier fires before the DAPM sync so a listener can adjust mic-bias before the power changes propagate. Both pin calls only mark the pin, and the single [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) afterward is what actually walks the routes and switches widget power. The closing [`snd_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L87) hands the merged [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) to the ALSA jack, which updates the kcontrols and, when an input device is built, emits the switch and key events user space reads.

```
    snd_soc_jack_report: masked read-modify-write of status
    ───────────────────────────────────────────────────────
    each caller owns a mask; the merge touches only those bits,
    so several detection methods share one jack without collision

       status &= ~mask;             AND-clear the owned bits
       status  =  status OR (arg AND mask)   set their new values

    example: a GPIO method reports SND_JACK_HEADPHONE (bit 0)
    while a mic method already set SND_JACK_MICROPHONE (bit 1)

                       bit 1      bit 0
                       MIC        HP
    old status          1          0
    caller mask         0          1     owns only HP
    caller arg          0          1     HP now present
    ───────────────    ───        ───
    after AND-clear     1          0     MIC bit untouched
    after OR-in         1          1     HP folded in

    then per pin:  enable = (pin->mask AND status), negated if invert
       enable ─▶ snd_soc_dapm_enable_pin   else  dapm_disable_pin
    then notifier ─▶ dapm_sync ─▶ snd_jack_report (all under mutex)
```

### The mutex and the notifier chain

The [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) serializes every [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) so the read-modify-write of [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and the DAPM sync are atomic against a second method reporting concurrently. According to the comment on the function, it uses mutexes and must be called from a sleepable context, which is why the GPIO and codec methods both report from a workqueue rather than directly from their interrupt handlers. The [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) is a [`struct blocking_notifier_head`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L65), so the chain runs in process context and its callbacks may sleep. [`snd_soc_jack_notifier_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L180) is a thin wrapper that adds a block to that chain:

```c
/* sound/soc/soc-jack.c:180 */
void snd_soc_jack_notifier_register(struct snd_soc_jack *jack,
				    struct notifier_block *nb)
{
	blocking_notifier_chain_register(&jack->notifier, nb);
}
```

In [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) the chain is fired with [`blocking_notifier_call_chain()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/notifier.h#L171), passing the merged [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) as the action and the jack itself as the data, so each registered callback sees the full post-merge bitmask. According to the comment on [`snd_soc_jack_notifier_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L180), the callback cannot report further jack events; the chain supports a two-stage detector where a mechanical detection enables electrical detection, the callback reacting to the first stage by arming the next stage rather than issuing its own report.
