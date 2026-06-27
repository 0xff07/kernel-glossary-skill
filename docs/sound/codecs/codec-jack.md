# Headset jack codecs

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A headset jack codec is the codec that drives a 3.5mm headphone jack. It pairs a headphone amplifier and a microphone-bias input behind a set of jack contacts with the accessory-detection hardware that reports what has been plugged in. The detection has three jobs that recur across every part. It senses insertion and removal, classifies the plug as a 3-pole headphone or a 4-pole headset, and decodes the media-key buttons on a headset. The codec runs that logic in its own interrupt handler and ends each decision at one call to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33), which posts the result into the machine driver's [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80). On x86 platforms the parts are the Cirrus Logic [`cs42l42`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c) and [`cs42l43`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l43.c) and the Realtek [`rt5682`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c), [`rt711-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c), and the combo `rt712`/`rt722` SDCA codecs; this page uses CS42L42 (analog detection over I2C or SoundWire) and RT711 SDCA (SoundWire SDCA detection) as the two worked examples. Texas Instruments ships only amplifiers on these platforms, so it contributes no jack codec here.

```
    A headset codec: an HP/MIC path with accessory detection
    ─────────────────────────────────────────────────────────

       ┌──────────────────────────────────────────────────┐
       │ codec                                            │
       │   host playback ──▶ HP amp  ──▶ TIP / RING (HP)  │
       │   host capture  ◀── mic bias ◀── MIC (RING2)     │
       │                                                  │
       │   accessory detect                               │
       │     tip-sense / plug      (insertion)            │
       │     type detect 3 vs 4    (headphone / headset)  │
       │     button DC-R or HID    (media keys)           │
       └───────────────────────┬──────────────────────────┘
                               │ snd_soc_jack_report(status, mask)
                               ▼
       struct snd_soc_jack ──▶ DAPM pins + input layer
         mask = SND_JACK_HEADSET | SND_JACK_BTN_0..3
```

## SUMMARY

The detection always ends at the generic jack model, so the codec-specific work is the front of the path and the shared mechanism is the tail. The codec receives a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) from the machine layer through its [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, stores the pointer, and arms its detection hardware. [`cs42l42_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L563) saves the jack and reports the current type, and [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522) saves it and runs [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451) to unmask the SDCA interrupts. From then on every plug, type, and button event flows to [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) with the fixed mask [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) ORed with [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50) through [`SND_JACK_BTN_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L53).

The detection runs in process context because it has to sleep over slow register reads and call into DAPM. The CS42L42 reports on its own hardware INT pin and decodes everything in the threaded handler [`cs42l42_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1662); the RT711 takes a SoundWire in-band interrupt in [`rt711_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245), which reads and clears the SDCA status and schedules [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26). Either way the slow classification happens in a workqueue or IRQ thread, while the interrupt itself stays short.

The two parts differ in how the hardware classifies a plug, which is the interesting half. The CS42L42 measures the accessory with analog tip-sense and headset-type detection and decodes media buttons from a DC-resistance sweep in [`cs42l42_handle_button_press()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1535). The RT711 reads the result from SDCA entities. [`rt711_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L264) reads the Ground-Engine 49 detected-mode Control and [`rt711_sdca_button_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L186) reads the SDCA HID report. The same shape appears on `cs42l43` and `rt5682`, and the combo `rt712`/`rt722` add a speaker amplifier alongside the same jack logic.

## SPECIFICATIONS

A headset jack codec is a hardware class with no single Linux specification; the contracts are the bus the part enumerates on and the jack model it reports into. The SoundWire parts follow the MIPI SoundWire and SDCA layouts, and on an SDCA part the accessory detection is exposed as SDCA entities (a Ground Engine for plug typing, a HID entity for buttons) addressed by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The CS42L42 on I2C is a plain register peripheral whose detection is Cirrus device hardware. The reporting target is the Linux software construct [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) with [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38), a software description distinct from any hardware register layout. The MIPI documents are membership-gated, so the layouts here are described from the kernel source.

- USB-C / 3.5mm accessory conventions: the 3-pole (TRS) and 4-pole (TRRS) contact assignments the type detection classifies

## LINUX KERNEL

### The generic jack model (soc-jack.h, jack.h, soc-jack.c, soc-component.c)

- [`'\<struct snd_soc_jack\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80): the jack object the codec reports into, with a [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask, the bound DAPM [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), and a [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain
- [`'\<enum snd_jack_types\>':'include/sound/jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38): the report bits, [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39), [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) (headphone plus microphone), and [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50) through [`SND_JACK_BTN_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L53)
- [`'\<snd_soc_jack_report\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33): the single reporting endpoint; updates [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) under the supplied mask, toggles the bound pins, runs the notifier, and reports to the input layer
- [`'\<snd_soc_component_set_jack\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190): the core path that forwards the machine driver's jack to the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op when one is set

### CS42L42 analog detection (codecs/cs42l42.c)

- [`'\<struct cs42l42_private\>':'sound/soc/codecs/cs42l42.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27): the core state, with the [`jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) pointer, the [`irq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) line, the [`plug_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) and [`hs_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27), and the four [`bias_thresholds`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) button levels
- [`'\<cs42l42_set_jack\>':'sound/soc/codecs/cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L563): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; stores the jack and reports the current [`hs_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27)
- [`'\<cs42l42_irq_thread\>':'sound/soc/codecs/cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1662): the threaded INT handler; reads the sticky status banks named in [`irq_params_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1635) and dispatches tip sense, type detect, and button detect
- [`'\<cs42l42_process_hs_type_detect\>':'sound/soc/codecs/cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1260): reads the auto-detect result into [`hs_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27), runs the manual fallback, and arms button detection on a headset
- [`'\<cs42l42_handle_button_press\>':'sound/soc/codecs/cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1535): sweeps the four [`bias_thresholds`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) DC-detect levels and returns the matching [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50)-family bit
- [`'\<cs42l42_handle_device_data\>':'sound/soc/codecs/cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1944): reads the `cirrus,bias-lvls` and the tip-sense and button debounce properties at [`cs42l42_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L2374), with [`threshold_defaults`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1937) as the fallback

### RT711 SDCA detection (codecs/rt711-sdca.c, rt711-sdca-sdw.c)

- [`'\<struct rt711_sdca_priv\>':'sound/soc/codecs/rt711-sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18): the core state, with the [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25) pointer, the two delayed-work items, the cached SDCA status words [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32), and the [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31)
- [`'\<rt711_sdca_set_jack_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; stores the jack in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25) and runs [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451)
- [`'\<rt711_sdca_interrupt_callback\>':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245): the in-band [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616); reads and clears the SDCA status and schedules [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26) on an [`SDW_DP0_SDCA_CASCADE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L42)
- [`'\<rt711_sdca_jack_detect_handler\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309): the workqueue handler; runs headset detect on [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137), button detect on [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147), then reports
- [`'\<rt711_sdca_headset_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L264): reads the SDCA Ground-Engine 49 detected-mode Control and sets [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31) to [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) or [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41)
- [`'\<rt711_sdca_button_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L186): reads the SDCA HID report buffer and maps it to a `SND_JACK_BTN_*` bit

### Shared machine-layer jack setup (sdw_utils)

- [`'soc_sdw_rt_sdca_jack_common.c':'sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c): the shared init that creates the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and calls [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190) for the Realtek SDCA jack codecs on x86 SOF boards
- [`'soc_sdw_cs42l42.c':'sound/soc/sdw_utils/soc_sdw_cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_cs42l42.c): the equivalent jack setup for the CS42L42 endpoint

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack reporting model the codec posts into through [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33)
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC component and DAI model both parts implement
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM pins a jack report toggles
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire bus and in-band interrupt the SDCA jack codec uses

## OTHER SOURCES

- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

A jack codec exposes its detection through device status and control registers that differ by part, so the representative registers come from the two examples. On the CS42L42 the threaded handler reads a set of sticky status banks (tip sense, type detect, and DC-detect) named in [`irq_params_table`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1635) and adjusts the button sensitivity through the level-detect field of the mic-detect control. On the RT711 the same information is in SDCA Controls addressed by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The Ground-Engine 49 detected-mode and selected-mode Controls carry the plug type, and the HID entity carries the button report. The reported result on both parts is a software bitmask, the [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) bits in the jack [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80).

## DETAILS

### The codec drives an HP/MIC path behind detectable jack contacts

A headset codec is a playback-and-capture codec whose analog endpoints are the contacts of a 3.5mm jack. The headphone amplifier drives the TIP and RING contacts, the microphone bias and ADC sit behind the second ring of a 4-pole plug, and the sleeve carries ground. The plug geometry is what the type detection reads. A 4-pole TRRS plug presents a microphone on the second ring, and a 3-pole TRS plug has only headphone and ground, so the codec sees a headphone with no microphone. The CS42L42 declares a 2-channel playback and capture DAI in [`cs42l42_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1134), and the RT711 declares a headphone-playback and mic-capture pair in [`rt711_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435). The contacts the detection classifies map to the codec path like this:

```
    The jack contacts and the codec's HP/MIC path
    ──────────────────────────────────────────────

    4-pole TRRS plug            codec
    ┌──────────────┐
    │ TIP   (HP L) │ ◀──────── HP amp   ◀── host playback
    │ RING  (HP R) │ ◀────────
    │ RING2 (MIC)  │ ────────▶ mic bias ──▶ host capture
    │ SLEEVE (GND) │
    └──────────────┘

    a 3-pole TRS plug has no RING2 contact, so the sleeve carries
    ground and the codec sees a headphone with no microphone
```

### Detection runs off an interrupt, in process context

A plug, type, or button event arrives as an interrupt, and the codec must read slow status registers and call into DAPM to settle it, so the work runs in a thread or workqueue where it can sleep. The CS42L42 reports on its own hardware INT pin and decodes the event in the threaded handler [`cs42l42_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1662) requested at probe. The RT711 takes a SoundWire in-band interrupt, whose [`rt711_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245) does the minimum at interrupt time, reading and clearing the SDCA status into [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) and scheduling the workqueue. [`rt711_sdca_jack_detect_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309) then does the slow classification and a single report:

```c
/* sound/soc/codecs/rt711-sdca.c:309 */
static void rt711_sdca_jack_detect_handler(struct work_struct *work)
{
	struct rt711_sdca_priv *rt711 =
		container_of(work, struct rt711_sdca_priv, jack_detect_work.work);
	int btn_type = 0, ret;

	if (!rt711->hs_jack)
		return;
	...
	/* SDW_SCP_SDCA_INT_SDCA_0 is used for jack detection */
	if (rt711->scp_sdca_stat1 & SDW_SCP_SDCA_INT_SDCA_0) {
		ret = rt711_sdca_headset_detect(rt711);
		if (ret < 0)
			return;
	}

	/* SDW_SCP_SDCA_INT_SDCA_8 is used for button detection */
	if (rt711->scp_sdca_stat2 & SDW_SCP_SDCA_INT_SDCA_8)
		btn_type = rt711_sdca_button_detect(rt711);

	if (rt711->jack_type == 0)
		btn_type = 0;
	...
}
```

The cached status words decide which classifier runs, the headset detect on one bit and the button detect on the other, and the handler folds both into one report. The interrupt half stays small and the classification moves to the thread:

```
    Detection runs off an interrupt, in process context
    ─────────────────────────────────────────────────────

    interrupt context (atomic)        process context (may sleep)
    ──────────────────────────        ────────────────────────────

    plug / type / button edge
         │
         ▼
    read + clear sticky status
         │  schedule work / wake thread
         └──────────────────────────▶  read slow registers, classify
                                          plug type and button
                                                │
                                                ▼
                                        snd_soc_jack_report(mask)
```

### Headphone versus headset typing

The first classification a plug edge triggers is the pole count, which decides whether the jack is a headphone or a headset. The CS42L42 measures it with analog tip-sense and headset-type detection in [`cs42l42_process_hs_type_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.c#L1260), recording the result in [`hs_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27). The RT711 reads the answer from an SDCA entity. [`rt711_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L264) reads the Ground-Engine 49 detected-mode Control and maps mode 0x03 to a 3-pole headphone and mode 0x05 to a 4-pole headset, then writes the same value back as the selected mode so the analog path matches:

```c
/* sound/soc/codecs/rt711-sdca.c:264 */
	/* get detected_mode */
	ret = regmap_read(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_GE49, RT711_SDCA_CTL_DETECTED_MODE, 0),
		&det_mode);
	...
	switch (det_mode) {
	case 0x00:
		rt711->jack_type = 0;
		break;
	case 0x03:
		rt711->jack_type = SND_JACK_HEADPHONE;
		break;
	case 0x05:
		rt711->jack_type = SND_JACK_HEADSET;
		break;
	}
```

The two methods reach the same two jack-type bits, an analog measurement on one part and a Ground-Engine mode read on the other. Each detected state maps to one [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) value:

```
    Plug typing: a detected state maps to a jack-type bit
    ──────────────────────────────────────────────────────

    detected state                          reported jack type
    ┌──────────────────────────┬───────────────────────────────┐
    │ 3-pole                   │ SND_JACK_HEADPHONE            │
    │  cs42l42 hs_type (no mic)│   (headphone, no microphone)  │
    │  rt711 GE49 mode 0x03    │                               │
    ├──────────────────────────┼───────────────────────────────┤
    │ 4-pole                   │ SND_JACK_HEADSET              │
    │  cs42l42 hs_type (+ mic) │   (headphone + microphone)    │
    │  rt711 GE49 mode 0x05    │                               │
    ├──────────────────────────┼───────────────────────────────┤
    │ unplugged (mode 0x00)    │ 0                             │
    └──────────────────────────┴───────────────────────────────┘
```

### Button decode: a DC-resistance ladder or an SDCA HID report

On a 4-pole headset the media keys short the microphone line through different resistors, so a button press is decoded by which resistance band the line falls into. The CS42L42 finds the band by sweeping the level-detect sensitivity through its four [`bias_thresholds`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/cs42l42.h#L27) entries until the headset-true bit stops asserting, then maps the level it stopped at to a button bit:

```c
/* sound/soc/codecs/cs42l42.c:1557 */
	/* Test all 4 level detect biases */
	bias_level = 1;
	do {
		/* Adjust button detect level sensitivity */
		regmap_update_bits(cs42l42->regmap, CS42L42_MIC_DET_CTL1,
			...
			(cs42l42->bias_thresholds[bias_level] <<
			CS42L42_HS_DET_LEVEL_SHIFT));

		regmap_read(cs42l42->regmap, CS42L42_DET_STATUS2, &detect_status);
	} while ((detect_status & CS42L42_HS_TRUE_MASK) &&
		(++bias_level < CS42L42_NUM_BIASES));

	switch (bias_level) {
	case 1: /* Function C button press */
		bias_level = SND_JACK_BTN_2;
		break;
	...
	}
```

The RT711 reads the same outcome from hardware. [`rt711_sdca_button_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L186) reads the SDCA HID report buffer the device fills and maps it to the matching bit. Either path lands on one of the four button bits, with the levels coming from device properties on the analog part. The level the sweep stops at decides which button is reported:

```
    Button decode: a level (or HID report) maps to a button bit
    ────────────────────────────────────────────────────────────
    cs42l42 sweeps bias_thresholds[1..4] until HS_TRUE drops;
    rt711 reads the SDCA HID report. Both land on one bit:

    ┌─────────────┬──────────────┬──────────────────┐
    │ level / key │ HS function  │ reported bit     │
    ├─────────────┼──────────────┼──────────────────┤
    │ 1           │ Function C   │ SND_JACK_BTN_2   │
    │ 2           │ Function B   │ SND_JACK_BTN_1   │
    │ 3           │ Function D   │ SND_JACK_BTN_3   │
    │ 4           │ Function A   │ SND_JACK_BTN_0   │
    │ none        │ (no match)   │ 0                │
    └─────────────┴──────────────┴──────────────────┘

    thresholds come from cirrus,bias-lvls (or threshold_defaults),
    read once at cs42l42_init
```

### Reporting into the generic snd_soc_jack

Every decision ends at [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33), the boundary where the codec-specific detection hands off to the generic ASoC jack framework. The codec passes the decoded status and a fixed mask naming the bits it owns, the headset type and the four button bits, and the framework updates only those bits of the jack [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), toggles the DAPM pins bound to the jack, runs the notifier chain, and reports the new state to the input layer. The RT711 handler shows the call, a press followed immediately by a release report:

```c
/* sound/soc/codecs/rt711-sdca.c:705 */
	snd_soc_jack_report(rt711->hs_jack, rt711->jack_type | btn_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);
```

Because the update is masked, the codec owns the headset and button bits while a separate method (a GPIO line, or an analog detection zone) can own other bits of the same jack without interference. The mask is what keeps the codec's report confined to its own bits:

```
    snd_soc_jack_report updates only the codec's owned bits
    ────────────────────────────────────────────────────────

    codec detect ──▶ snd_soc_jack_report(jack, report, mask)
                           │
                           ▼
    ┌──────────────────────────────────────────────────┐
    │ struct snd_soc_jack                              │
    │   status = (status & ~mask) | (report & mask)    │
    │   toggle the DAPM pins bound to the jack         │
    │   run the notifier chain                         │
    │   report the new state to the input layer        │
    └──────────────────────────────────────────────────┘

    the codec owns mask = SND_JACK_HEADSET | BTN_0..3;
    a GPIO or analog zone can own other bits of one jack
```
