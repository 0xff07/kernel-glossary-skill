# ASoC jack detection methods (zones, GPIO, codec-integrated)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) is passive, and a detection method is what drives its [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) over the jack's lifetime by calling [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33). Three method families exist. An analog mic-bias voltage is classified by zones added with [`snd_soc_jack_add_zones()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89) and read by [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112). A GPIO line is wired up with [`snd_soc_jack_add_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310), which installs [`gpio_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L232) on the line's IRQ and reports from a debounced work item. Codec-integrated detection runs in the codec's own interrupt path, and the machine layer hands the codec its jack through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190), which calls the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op. The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec, an SDCA part reached over SoundWire on x86 ACPI systems, is the worked example, detecting a headset in [`rt722_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L140) and buttons in [`rt722_sdca_button_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L94) from a SoundWire interrupt, then reporting both through [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33).

```
    detection method                      shared jack
    ────────────────                      ───────────
    voltage zones                         struct snd_soc_jack
      ADC read ─▶ snd_soc_jack_get_type ──┐
                                          │
    GPIO line                             ├─▶ snd_soc_jack_report(status, mask)
      IRQ ─▶ gpio_work ─▶ gpio_detect ────┤      status &= ~mask
                                          │      status |= new & mask
    codec-integrated (rt722-sdca)         │      drive pins, notifier, dapm_sync
      SDW IRQ ─▶ jack_detect_work ────────┘      snd_jack_report to user space
        headset_detect + button_detect

    each method passes only the bits it owns in `mask`,
    so they update one user-visible jack without collision
```

## SUMMARY

A detection method monitors hardware and calls [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with the bits it observed and a mask of the bits it controls. The three families differ in how they observe. The voltage-zone family suits an analog headset socket, where the codec measures the mic-bias voltage on its ADC, classifies it through zones added by [`snd_soc_jack_add_zones()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89), and reads the matching [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) with [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112). The GPIO family suits a board with a dedicated detect pin, where [`snd_soc_jack_add_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310) requests the descriptor and a shared edge IRQ, [`gpio_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L232) queues a debounced work item, and [`snd_soc_jack_gpio_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L210) reads the line and reports. The codec-integrated family suits a modern smart codec that decodes the plug and the buttons in hardware, where the machine layer hands the codec its jack with [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) and the codec reports from its own interrupt work.

Every family ends at the same [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33), which must run in a sleepable context because it takes [`jack->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and synchronizes DAPM, so the GPIO and codec methods both report from a workqueue rather than from the interrupt handler. The mask each method passes is exactly the set of bits it owns, the GPIO line's own [`report`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) mask or the codec's fixed headset-plus-button mask, so a board that mixes families updates one user-visible jack without collision.

## SPECIFICATIONS

The detection methods are Linux kernel software constructs and have no standalone hardware specification. The mic-bias voltage thresholds and the four-pole headset pinout (CTIA, OMTP) are set by the connector conventions the analog codecs follow. For an SDCA codec on SoundWire the headset and button signaling is decoded from the SDCA Ground-Engine (GE) and HID entities, represented in the kernel by the entity numbers and the [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) register-address macro in the SoundWire headers.

## LINUX KERNEL

### Voltage-zone method (soc-jack.c, soc-jack.h)

- [`'\<struct snd_soc_jack_zone\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36): one mic-bias voltage range ([`min_mv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36), [`max_mv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36)) mapped to a [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36)
- [`'\<snd_soc_jack_add_zones\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89): link each [`struct snd_soc_jack_zone`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) onto [`jack->jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80)
- [`'\<snd_soc_jack_get_type\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112): walk [`jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and return the [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) of the zone whose voltage range contains the measured mic-bias value

### GPIO method (soc-jack.c, soc-jack.h)

- [`'\<struct snd_soc_jack_gpio\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60): one GPIO detection line; carries the descriptor, the [`report`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) bits, a [`debounce_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60), a [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60), and an optional [`jack_status_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) callback
- [`'\<snd_soc_jack_add_gpios\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310): request each GPIO descriptor and IRQ, register a PM notifier, and schedule the initial read; on x86 ACPI the descriptor comes from a GPIO resource named in the codec's ACPI device
- [`'\<snd_soc_jack_free_gpios\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L432): release the IRQ, PM notifier, work item, and descriptor for each GPIO, through [`jack_free_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L278)
- [`'\<gpio_handler\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L232): the IRQ handler; queues [`gpio_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L249) on the debounce delay
- [`'\<snd_soc_jack_gpio_detect\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L210): read the GPIO level (or call [`jack_status_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60)) and forward the result to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33)
- [`'\<snd_soc_jack_pm_notifier\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L257): re-read the GPIO after resume so a plug event during sleep is not missed

### Codec-integrated method (soc-component.c, codecs/rt722-sdca.c)

- [`'\<snd_soc_component_set_jack\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190): hand a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) to a codec by invoking its [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, returning `-ENOTSUPP` when the op is absent
- [`'\<rt722_sdca_set_jack_detect\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321): the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; stores the jack and arms detection through [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293)
- [`'\<rt722_sdca_jack_detect_handler\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L183): the [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1316) handler; calls headset and button detect, then [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33)
- [`'\<rt722_sdca_headset_detect\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L140): read the SDCA detected-mode register and set [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L160) to [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) or [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41)
- [`'\<rt722_sdca_button_detect\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L94): read the SDCA HID button report and map it to a `SND_JACK_BTN_*` bit via [`rt722_sdca_btn_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L76)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack model and the detection-method split
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the pin and route machinery a jack report drives through [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005)
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire bus the rt722-sdca codec carries its interrupt and register access over

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

Each detection family registers through one entry point and ends at [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33). The machine driver picks the family that matches the hardware and supplies the bits that family owns.

| Family | Setup | Observation | Reports |
|--------|-------|-------------|---------|
| voltage zones | [`snd_soc_jack_add_zones()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89) | codec ADC + [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112) | the zone's [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) |
| GPIO line | [`snd_soc_jack_add_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310) | IRQ + debounced [`snd_soc_jack_gpio_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L210) | the line's [`report`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) mask |
| codec-integrated | [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) | codec interrupt work | headset + button bits |

### snd_soc_jack_add_zones and snd_soc_jack_get_type

[`snd_soc_jack_add_zones()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89) links voltage ranges onto the jack, and [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112) classifies a measured mic-bias voltage by finding the [`struct snd_soc_jack_zone`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) whose [`min_mv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) and [`max_mv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) bracket it and returning that zone's [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36). An analog codec reads its ADC, calls [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112), and passes the result to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33).

### snd_soc_jack_add_gpios

[`snd_soc_jack_add_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310) sets up the GPIO detection family. It requests a descriptor and a shared edge-triggered IRQ for each [`struct snd_soc_jack_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60), registers a PM notifier, and schedules the first read. On x86 ACPI the descriptor resolves from a GPIO resource named in the codec's ACPI `_CRS`.

### snd_soc_component_set_jack

[`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) is how the machine driver wires a jack to a codec that does its own detection. It calls the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, passing the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) the codec will report into.

## DETAILS

### The voltage-zone method

For an analog headset socket the codec measures the mic-bias voltage and classifies it. [`snd_soc_jack_add_zones()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L89) links each range onto the jack:

```c
/* sound/soc/soc-jack.c:89 */
int snd_soc_jack_add_zones(struct snd_soc_jack *jack, int count,
			  struct snd_soc_jack_zone *zones)
{
	int i;

	for (i = 0; i < count; i++) {
		INIT_LIST_HEAD(&zones[i].list);
		list_add(&(zones[i].list), &jack->jack_zones);
	}
	return 0;
}
```

The zone record maps a half-open voltage range to a jack type:

```c
/* include/sound/soc-jack.h:36 */
struct snd_soc_jack_zone {
	unsigned int min_mv;
	unsigned int max_mv;
	unsigned int jack_type;
	unsigned int debounce_time;
	struct list_head list;
};
```

[`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112) then walks [`jack_zones`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and returns the [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L36) of the first zone whose range contains the reading:

```c
/* sound/soc/soc-jack.c:112 */
int snd_soc_jack_get_type(struct snd_soc_jack *jack, int micbias_voltage)
{
	struct snd_soc_jack_zone *zone;

	list_for_each_entry(zone, &jack->jack_zones, list) {
		if (micbias_voltage >= zone->min_mv &&
			micbias_voltage < zone->max_mv)
				return zone->jack_type;
	}
	return 0;
}
```

The codec reads its ADC, calls [`snd_soc_jack_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L112), and forwards the returned bit to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33), so a voltage in the headset zone reports [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) while one in the headphone zone reports [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39).

```
    Voltage zones: a mic-bias reading classified to a jack type
    ────────────────────────────────────────────────────────────
    snd_soc_jack_get_type walks jack_zones in list order and
    returns the jack_type of the first zone whose half-open
    range  [min_mv, max_mv)  contains micbias_voltage.

    jack_zones (each entry: struct snd_soc_jack_zone)
    ┌──────────────┬──────────────┬───────────────────────────┐
    │ min_mv       │ max_mv       │ jack_type                 │
    ├──────────────┼──────────────┼───────────────────────────┤
    │ zone A min   │ zone A max   │ e.g. SND_JACK_HEADPHONE   │
    │ zone B min   │ zone B max   │ e.g. SND_JACK_HEADSET     │
    │ ...          │ ...          │ ...                       │
    └──────────────┴──────────────┴───────────────────────────┘
                           │  micbias_voltage in [min_mv, max_mv)
                           ▼
            return zone->jack_type  ─▶  snd_soc_jack_report
            (no zone matches ─▶ return 0)
```

### The GPIO method

[`snd_soc_jack_add_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L310) wires a hardware detection line to the jack. For each [`struct snd_soc_jack_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) it acquires a descriptor with [`gpiod_get_index()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/consumer.h), installs [`gpio_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L232) on the line's IRQ for both edges, registers a PM notifier, and schedules the initial read:

```c
/* sound/soc/soc-jack.c:310 */
int snd_soc_jack_add_gpios(struct snd_soc_jack *jack, int count,
			struct snd_soc_jack_gpio *gpios)
{
	int i, ret;
	struct jack_gpio_tbl *tbl;
	...
	for (i = 0; i < count; i++) {
		...
got_gpio:
		INIT_DELAYED_WORK(&gpios[i].work, gpio_work);
		gpios[i].jack = jack;

		ret = request_any_context_irq(gpiod_to_irq(gpios[i].desc),
					      gpio_handler,
					      IRQF_SHARED |
					      IRQF_TRIGGER_RISING |
					      IRQF_TRIGGER_FALLING,
					      gpios[i].name,
					      &gpios[i]);
		if (ret < 0)
			goto undo;

		if (gpios[i].wake) {
			ret = irq_set_irq_wake(gpiod_to_irq(gpios[i].desc), 1);
			...
		}

		/*
		 * Register PM notifier so we do not miss state transitions
		 * happening while system is asleep.
		 */
		gpios[i].pm_notifier.notifier_call = snd_soc_jack_pm_notifier;
		register_pm_notifier(&gpios[i].pm_notifier);
		...
		/* Update initial jack status */
		schedule_delayed_work(&gpios[i].work,
				      msecs_to_jiffies(gpios[i].debounce_time));
	}
	...
}
```

On x86 ACPI platforms the descriptor resolves from a GPIO resource declared in the codec's ACPI device. The IRQ does no work itself. [`gpio_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L232) only marks the device as a wake event and queues the debounced work, because the report path needs to sleep:

```c
/* sound/soc/soc-jack.c:232 */
static irqreturn_t gpio_handler(int irq, void *data)
{
	struct snd_soc_jack_gpio *gpio = data;
	struct device *dev = gpio->jack->card->dev;

	trace_snd_soc_jack_irq(gpio->name);

	if (device_may_wakeup(dev))
		pm_wakeup_event(dev, gpio->debounce_time + 50);

	queue_delayed_work(system_power_efficient_wq, &gpio->work,
			      msecs_to_jiffies(gpio->debounce_time));

	return IRQ_HANDLED;
}
```

[`gpio_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L249) recovers the [`struct snd_soc_jack_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) and calls [`snd_soc_jack_gpio_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L210), which reads the line, optionally overrides the result through the [`jack_status_check`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) callback, and reports with the line's own [`report`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60) mask:

```c
/* sound/soc/soc-jack.c:210 */
static void snd_soc_jack_gpio_detect(struct snd_soc_jack_gpio *gpio)
{
	struct snd_soc_jack *jack = gpio->jack;
	int enable;
	int report;

	enable = gpiod_get_value_cansleep(gpio->desc);
	if (gpio->invert)
		enable = !enable;

	if (enable)
		report = gpio->report;
	else
		report = 0;

	if (gpio->jack_status_check)
		report = gpio->jack_status_check(gpio->data);

	snd_soc_jack_report(jack, report, gpio->report);
}
```

The mask passed to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) is [`gpio->report`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L60), the exact set of bits this line owns, so a board with one GPIO for the headphone and another for the microphone updates each independently. [`snd_soc_jack_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L257) re-queues the same work after resume so a plug or unplug during suspend is reconciled, and [`snd_soc_jack_free_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L432) tears the whole set down through [`jack_free_gpios()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L278), releasing the IRQ, the PM notifier, the work item, and the descriptor.

```
    GPIO method: edge IRQ, then a debounced read in process context
    ────────────────────────────────────────────────────────────────
    The IRQ runs atomically while the report path must sleep, so the handler
    only schedules work delayed by debounce_time; the work reads the
    line and reports with the line's own mask, gpio->report.

    edge on line                 +debounce_time            process context
    ┌──────────────┐  schedule   ┌──────────────┐  fires   ┌──────────────┐
    │ gpio_handler │ ──────────▶ │ delayed_work │ ───────▶ │ gpio_work    │
    │ (hardirq)    │  queue_     │ (gpio->work) │          │ gpio_detect  │
    └──────────────┘  delayed_   └──────────────┘          └──────┬───────┘
       wake event     work                                        │
       only, no read                                              ▼
                                       enable = gpiod_get_value_cansleep(desc)
                                       invert ─▶ enable = not enable
                                       report = enable ? gpio->report : 0
                                       jack_status_check ─▶ may override report
                                              │
                                              ▼
                       snd_soc_jack_report(jack, report, gpio->report)
                       mask = gpio->report : only the bits this line owns
```

### The codec-integrated method: rt722-sdca

The Realtek RT722 is an SDCA codec reached over SoundWire, the standard headset path on recent Intel x86 ACPI laptops. It does its own detection in firmware-assisted hardware and reports through the ASoC jack. The machine layer connects the two by calling [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190), which dispatches to the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op. The RT722 op [`rt722_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321) stores the jack pointer in the codec's private state and arms the hardware detection through [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293):

```c
/* sound/soc/codecs/rt722-sdca.c:321 */
static int rt722_sdca_set_jack_detect(struct snd_soc_component *component,
	struct snd_soc_jack *hs_jack, void *data)
{
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	int ret;

	rt722->hs_jack = hs_jack;

	ret = pm_runtime_resume_and_get(component->dev);
	if (ret < 0) {
		if (ret != -EACCES) {
			dev_err(component->dev, "%s: failed to resume %d\n", __func__, ret);
			return ret;
		}
		/* pm_runtime not enabled yet */
		dev_dbg(component->dev,	"%s: skipping jack init for now\n", __func__);
		return 0;
	}

	rt722_sdca_jack_init(rt722);

	pm_runtime_put_autosuspend(component->dev);

	return 0;
}
```

A SoundWire interrupt routed to the SDCA jack and HID entities eventually queues the codec's [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1316), whose handler runs in process context where it may sleep and call into DAPM. [`rt722_sdca_jack_detect_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L183) reads the interrupt status, runs headset detection on one SDCA interrupt and button detection on another, then makes a single [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) carrying both the headset type and the button bit:

```c
/* sound/soc/codecs/rt722-sdca.c:183 */
static void rt722_sdca_jack_detect_handler(struct work_struct *work)
{
	struct rt722_sdca_priv *rt722 =
		container_of(work, struct rt722_sdca_priv, jack_detect_work.work);
	int btn_type = 0, ret;

	if (!rt722->hs_jack)
		return;

	if (!rt722->component->card || !rt722->component->card->instantiated)
		return;

	/* SDW_SCP_SDCA_INT_SDCA_0 is used for jack detection */
	if (rt722->scp_sdca_stat1 & SDW_SCP_SDCA_INT_SDCA_0) {
		ret = rt722_sdca_headset_detect(rt722);
		if (ret < 0)
			return;
	}

	/* SDW_SCP_SDCA_INT_SDCA_8 is used for button detection */
	if (rt722->scp_sdca_stat2 & SDW_SCP_SDCA_INT_SDCA_8)
		btn_type = rt722_sdca_button_detect(rt722);

	if (rt722->jack_type == 0)
		btn_type = 0;
	...
	snd_soc_jack_report(rt722->hs_jack, rt722->jack_type | btn_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);

	if (btn_type) {
		/* button released */
		snd_soc_jack_report(rt722->hs_jack, rt722->jack_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);

		mod_delayed_work(system_power_efficient_wq,
			&rt722->jack_btn_check_work, msecs_to_jiffies(200));
	}
}
```

The mask in both reports is the fixed set [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) OR the four button bits, which is every bit this codec owns. The first report posts the current state; when a button was seen the handler immediately posts a second report with [`btn_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L183) cleared, modeling a press followed by a release, and schedules [`jack_btn_check_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1317) to poll for the physical release. [`rt722_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L140) reads the SDCA Ground-Detect entity's detected-mode register and sets [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L160) accordingly:

```c
/* sound/soc/codecs/rt722-sdca.c:140 */
static int rt722_sdca_headset_detect(struct rt722_sdca_priv *rt722)
{
	unsigned int det_mode;
	int ret;

	/* get detected_mode */
	ret = regmap_read(rt722->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_GE49,
			RT722_SDCA_CTL_DETECTED_MODE, 0), &det_mode);
	if (ret < 0)
		goto io_error;

	switch (det_mode) {
	case 0x00:
		rt722->jack_type = 0;
		break;
	case 0x03:
		rt722->jack_type = SND_JACK_HEADPHONE;
		break;
	case 0x05:
		rt722->jack_type = SND_JACK_HEADSET;
		break;
	}
	...
}
```

Detected-mode 0x03 maps to [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) (a three-pole plug, no microphone) and 0x05 to [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) (a four-pole plug with microphone). [`rt722_sdca_button_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L94) reads the SDCA HID button report into a buffer and decodes it through [`rt722_sdca_btn_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L76), which returns one of the `SND_JACK_BTN_*` bits:

```c
/* sound/soc/codecs/rt722-sdca.c:76 */
static int rt722_sdca_btn_type(unsigned char *buffer)
{
	if ((*buffer & 0xf0) == 0x10 || (*buffer & 0x0f) == 0x01 || (*(buffer + 1) == 0x01) ||
		(*(buffer + 1) == 0x10))
		return SND_JACK_BTN_2;
	else if ((*buffer & 0xf0) == 0x20 || (*buffer & 0x0f) == 0x02 || (*(buffer + 1) == 0x02) ||
		(*(buffer + 1) == 0x20))
		return SND_JACK_BTN_3;
	else if ((*buffer & 0xf0) == 0x40 || (*buffer & 0x0f) == 0x04 || (*(buffer + 1) == 0x04) ||
		(*(buffer + 1) == 0x40))
		return SND_JACK_BTN_0;
	else if ((*buffer & 0xf0) == 0x80 || (*buffer & 0x0f) == 0x08 || (*(buffer + 1) == 0x08) ||
		(*(buffer + 1) == 0x80))
		return SND_JACK_BTN_1;

	return 0;
}
```

The jack the codec reports into is created and owned by the machine driver (the SoundWire generic [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) board), which calls [`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L82) to build it with a type mask of [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) plus the button bits, attaches the headphone and microphone DAPM pins, and then hands the jack to the codec through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190). From that point a plug event drives the full path. The SoundWire interrupt queues the codec work, the work decodes the SDCA state, [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) updates [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), enables the headphone pin, runs [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) to power the output route, and pushes the headset state to user space through the ALSA jack.

```
    rt722-sdca: SDCA registers decoded to jack and button bits
    ───────────────────────────────────────────────────────────
    One interrupt feeds two decoders; each maps a hardware value
    to a report bit that snd_soc_jack_report folds into status.

    SDW_SCP_SDCA_INT_SDCA_0 ─▶ rt722_sdca_headset_detect
      reads the GE49 DETECTED_MODE register:
    ┌──────────────┬────────────────────────────────────────────┐
    │ det_mode     │ jack_type                                  │
    ├──────────────┼────────────────────────────────────────────┤
    │ 0x00         │ 0  (unplugged)                             │
    │ 0x03         │ SND_JACK_HEADPHONE  (3-pole, no mic)       │
    │ 0x05         │ SND_JACK_HEADSET    (4-pole, with mic)     │
    └──────────────┴────────────────────────────────────────────┘

    SDW_SCP_SDCA_INT_SDCA_8 ─▶ rt722_sdca_button_detect
      decodes the HID report byte in rt722_sdca_btn_type:
    ┌────────────────────────────────┬─────────────────────────┐
    │ HID byte nibble matches        │ returns                 │
    ├────────────────────────────────┼─────────────────────────┤
    │ 0x10 / 0x01                    │ SND_JACK_BTN_2          │
    │ 0x20 / 0x02                    │ SND_JACK_BTN_3          │
    │ 0x40 / 0x04                    │ SND_JACK_BTN_0          │
    │ 0x80 / 0x08                    │ SND_JACK_BTN_1          │
    │ (no match)                     │ 0                       │
    └────────────────────────────────┴─────────────────────────┘

    report mask = SND_JACK_HEADSET + BTN_0..BTN_3 (every owned bit)
```
