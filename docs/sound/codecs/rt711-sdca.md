# RT711 SDCA codec

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Realtek RT711 SDCA is a SoundWire headset codec whose ASoC component driver [`soc_sdca_dev_rt711`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1300) registers the [`rt711_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435) headphone-playback and mic-capture DAIs with [`rt711_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1428) (whose [`rt711_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1326) joins each stream), points [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) at [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522) which arms detection through [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451), and binds to the SoundWire bus with [`rt711_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L345) whose [`rt711_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245) and [`rt711_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L141) drive the jack work over the byte [`rt711_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L114) and the multi-byte-quantity [`rt711_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L127) into the machine driver's [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) via [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33).

```
    RT711 SDCA jack/headset codec
    ─────────────────────────────

       struct snd_soc_component_driver
       soc_sdca_dev_rt711
       ┌──────────────────────────────────────────────────────────┐
       │  controls / dapm_widgets / dapm_routes                   │
       │  set_jack ─▶ rt711_sdca_set_jack_detect()                │
       │  endianness = 1                                          │
       └──────────────────────────────┬───────────────────────────┘
                                      │ devm_snd_soc_register_component()
              ┌───────────────────────┴────────────────┐
              ▼                                        ▼
       struct snd_soc_dai_driver[]            struct snd_soc_jack
       rt711_sdca_dai                         ┌──────────────────┐
       ┌──────────────────────────┐          │ status (bitmask)  │
       │ aif1: DP3 HP Playback    │          │ pins, notifier   │
       │       DP2 Mic Capture    │          └────────▲─────────┘
       │ aif2: DP4 Capture        │                   │ snd_soc_jack_report()
       │ ops ─▶ hw_params/hw_free │                   │  status &= ~mask
       └───────────┬──────────────┘                   │  status |= new & mask
                   │ sdw_stream_add_slave()  ┌────────┴───────────┐
                   ▼                         │ jack_detect_work   │
            SoundWire data ports             │ headset_detect +   │
            (DP3 = playback, DP2/4 = cap)    │ button_detect      │
                                             └─────────▲──────────┘
       struct sdw_slave_ops                            │ mod_delayed_work
       rt711_sdca_slave_ops                            │
       ┌───────────────────────────────────────┐      │
       │ update_status (ATTACHED / UNATTACHED) │      │
       │ interrupt_callback ───────────────────┼──────┘
       │ read_prop                             │  on SDW_DP0_SDCA_CASCADE
       └───────────────────────────────────────┘
```

## SUMMARY

The RT711 SDCA registers one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), from [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469). The component [`soc_sdca_dev_rt711`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1300) sets [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) to 1 because the SoundWire transport fixes the wire endian, and its [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op stores the machine driver's [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and arms the codec's detection logic. Each DAI in [`rt711_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435) declares a [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capability for the headphone path and a [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capability for the microphone, and the shared [`rt711_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1428) fills [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) to receive the SoundWire stream handle, [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) to add the codec to that stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) to remove it with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228).

Register access goes through two regmaps built over the SoundWire transport. [`rt711_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L114) is the 8-bit-value map built with [`devm_regmap_init_sdw()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196), and [`rt711_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L127) is the 16-bit multi-byte-quantity map built with [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210), and the codec selects between them by which register space a control addresses. On the bus side [`rt711_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L345) supplies a [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) whose [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op runs per-device initialization when the peripheral reaches [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) and whose [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op runs in thread context on an in-band interrupt. The interrupt handler reads and clears the SDCA status registers and, on an [`SDW_DP0_SDCA_CASCADE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L42) event, schedules [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26), whose handler does the slower register reads that classify the jack and the pressed button and then calls [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33).

The generic ASoC jack model is what [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) implements. It updates [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) under the jack mutex, masking in only the bits the caller owns, toggles the DAPM pins bound to the jack, calls the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain, and reports the new state to the input layer through the underlying [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80). The RT711 owns the fixed mask [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) plus the four button bits [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50) through [`SND_JACK_BTN_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L53), and decodes the plug type from the SDCA Ground-Engine detected-mode register and the button from the SDCA HID report.

## SPECIFICATIONS

- SoundWire (the MIPI DisCo for SoundWire and the SoundWire 1.x bus specification) defines the in-band interrupt mechanism, the peripheral attach state machine that drives [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and the data-port model the codec joins from [`rt711_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1326); the bus registers are represented in the kernel by the macros in [`sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h)
- SDCA (the MIPI SoundWire Device Class for Audio) defines the function and entity model RT711 addresses through [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h) control addresses, and the SDCA cascade interrupt bit [`SDW_DP0_SDCA_CASCADE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L42) (`BIT(3)`) in [`SDW_DP0_INT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L32) (0x0) that the codec polls in its interrupt callback; the jack-detect path uses the per-function SDCA interrupt bits [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137) and [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147). The MIPI documents are membership-gated, so the entity numbers and control addresses are described here from the kernel source
- The jack and button reporting model is a Linux software construct in [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and [`enum snd_jack_types`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L38) rather than a hardware register layout

## LINUX KERNEL

### Generic component, DAI, and jack types (soc-component.h, soc-dai.h, soc-jack.h)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the per-codec descriptor carrying controls, DAPM widgets and routes, the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78) op, the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) callback, and the [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) bit
- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): one DAI's static description, with its [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capability records and its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointer
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the DAI function pointer struct; a SoundWire codec fills [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)
- [`'\<struct snd_soc_jack\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80): the jack object with a [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask, a list of DAPM [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), a [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain, and the underlying [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80)
- [`'\<snd_soc_jack_report\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33): apply a masked status change to the jack, toggle its DAPM pins, run the notifier, and report to the input layer
- [`'\<snd_soc_component_set_jack\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190): the machine-driver entry that invokes the codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op, returning `-ENOTSUPP` when the op is absent

### Generic SoundWire bus and stream surface (sdw.h, regmap.h, sdw.h, stream.c)

- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the peripheral driver callbacks ([`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`bus_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616))
- [`'\<struct sdw_slave_intr_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528): the per-interrupt status passed to [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), carrying [`control_port`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) and [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528)
- [`'\<enum sdw_slave_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94): the attach state, [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) (0) and [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) (1)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): register the component and its DAI array, freeing both at device teardown
- [`'\<snd_soc_component_get_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356): fetch the codec's [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18) from the component
- [`'\<snd_soc_dai_dma_data_set\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506): store the SoundWire stream handle in the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) slot
- [`'\<snd_sdw_params_to_config\>':'include/sound/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdw.h#L32): translate [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) into a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893)
- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): allocate and bind the peripheral runtime to a stream
- [`'\<sdw_stream_remove_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228): free the peripheral's port and runtime from the stream
- [`'\<snd_soc_card_jack_new_pins\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L35): the machine-driver call that creates the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and attaches its DAPM pins before the codec receives it

### RT711 component and DAIs (codecs/rt711-sdca.c)

- [`'soc_sdca_dev_rt711':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1300): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) with [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) set to [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522)
- [`'\<rt711_sdca_probe\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1282): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78) op recording the component pointer and resuming the device
- [`'rt711_sdca_dai':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435): the two DAIs, `rt711-sdca-aif1` (DP3 Playback + DP2 Capture) and `rt711-sdca-aif2` (DP4 Capture)
- [`'rt711_sdca_ops':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1428): the four-callback [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) shared by both DAIs
- [`'\<rt711_sdca_pcm_hw_params\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1326): build the stream config, pick the data port by direction and DAI id, add the peripheral, and program the SDCA clock-source sample rate
- [`'\<rt711_sdca_pcm_hw_free\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1408): remove the peripheral from the stream
- [`'\<rt711_sdca_set_sdw_stream\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1312): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op storing the stream handle
- [`'\<rt711_sdca_init\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469): allocate the [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18), init the work items, and register the component
- [`'rt711_sdca_snd_controls':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L866) / [`'rt711_sdca_dapm_widgets':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1206) / [`'rt711_sdca_audio_map':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1250): the mixer, widget, and route tables the component names

### RT711 jack detection (codecs/rt711-sdca.c)

- [`'\<rt711_sdca_set_jack_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op storing the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25) and calling [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451)
- [`'\<rt711_sdca_jack_init\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451): program the HID and Ground-Engine event control bits, select the jack-detect source [`jd_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31), and unmask [`SDW_SCP_SDCA_INTMASK_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L177) and [`SDW_SCP_SDCA_INTMASK_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L187)
- [`'\<rt711_sdca_jack_detect_handler\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309): the [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26) worker that runs headset detect on [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137) and button detect on [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147), then reports
- [`'\<rt711_sdca_btn_check_handler\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L360): the [`jack_btn_check_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L27) worker that re-reads the detected mode and the HID buffer to model the button release
- [`'\<rt711_sdca_headset_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L264): read the SDCA Ground-Engine detected-mode register and set [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31) to [`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39) or [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41)
- [`'\<rt711_sdca_button_detect\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L186): read the SDCA HID UMP buffer and map it to a `SND_JACK_BTN_*` bit, then return ownership of the buffer to the device
- [`'\<rt711_sdca_ge_force_jack_type\>':'sound/soc/codecs/rt711-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L84): override the Ground-Engine selected mode from the [`ge_mode_override`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L36) device-property value before detection
- [`'\<struct rt711_sdca_priv\>':'sound/soc/codecs/rt711-sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18): the codec's private state (both regmaps, SoundWire slave, jack, the two work items, the cached SDCA status, and the mute flags) reached through drvdata

### RT711 SoundWire bind (codecs/rt711-sdca-sdw.c)

- [`'rt711_sdca_slave_ops':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L345): the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) filling [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<rt711_sdca_sdw_probe\>':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L351): the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) op building both regmaps and calling [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469)
- [`'\<rt711_sdca_read_prop\>':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L175): the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op publishing the [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) (0x14) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) (0x8) bitmaps and the [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372)
- [`'\<rt711_sdca_update_status\>':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L141): the [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op re-asserting the interrupt mask and running [`rt711_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1588) on attach
- [`'\<rt711_sdca_interrupt_callback\>':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245): the [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op reading and clearing the SDCA status, then scheduling [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26) on a cascade
- [`'rt711_sdca_regmap':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L114): the byte [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit register, 8-bit value, MAPLE cache) for the plain SoundWire register space
- [`'rt711_sdca_mbq_regmap':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L127): the multi-byte-quantity [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit register, 16-bit value, MAPLE cache) named `sdw-mbq`
- [`'rt711_sdca_id':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L383): the one-entry match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x711, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717)
- [`'rt711_sdca_sdw_driver':'sound/soc/codecs/rt711-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L480): the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) registered by [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack reporting model that [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) implements
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component and DAI driver structure the RT711 follows
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families and the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) callback contract
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle [`rt711_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1326) joins through [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus and peripheral model the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) plugs into
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): the bus-clash and parity errors the RT711 unmasks in its [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [ALSA SoundWire wiki](https://github.com/thesofproject/linux/wiki)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The RT711 specializes the generic component, DAI, and SoundWire-peripheral objects by populating the description fields and callback sets each one reads. The component driver and DAI array are static and shared; the regmaps are built once at SoundWire probe and stored on the device; the jack is created and owned by the machine driver and handed to the codec, which keeps the pointer for the life of the bind.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`soc_sdca_dev_rt711`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1300) | static, registered by [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469) | the module |
| [`rt711_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435) array | static, registered alongside the component | the module |
| [`rt711_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L345) | static, pointed to by [`drv->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) | the module |
| [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18) | [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) in [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469) | the device |
| [`rt711_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L114) / [`rt711_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L127) | [`rt711_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L351) | the device |
| [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) | the machine driver via [`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L35) | the card |
| [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26) / [`jack_btn_check_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L27) | [`INIT_DELAYED_WORK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h) in [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469) | the device |

### set_jack

[`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) receives the machine driver's [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and a driver-private pointer, and the core reaches it through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190). The RT711 op [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522) stores the pointer in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25) and runs [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451) to arm the SDCA interrupts, so a later in-band interrupt can report into that jack.

### set_stream, hw_params, and hw_free

[`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) hands the codec the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) the machine layer allocated, which [`rt711_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1312) keeps with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506). [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) reads that handle back, fills a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) with [`snd_sdw_params_to_config()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdw.h#L32), and calls [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) with the data-port number for the direction and DAI. [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) reverses that with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228).

### update_status and interrupt_callback

[`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) runs at every transition of [`enum sdw_slave_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94). On [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) the RT711 re-asserts its SDCA interrupt mask and runs I/O init, and on [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) it clears [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L23). [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) runs in thread context on an in-band interrupt; it reads and clears the SDCA status registers and, when [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) is set, queues the jack work.

## DETAILS

### The component driver and the headset DAI pair

The RT711 registers an ASoC component with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) from [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469), passing the [`soc_sdca_dev_rt711`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1300) descriptor and the two-entry [`rt711_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1435) array. The component driver wires the controls, the DAPM graph, the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) callback, and sets [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) to 1 because the data crosses a SoundWire link that fixes the transmission endian:

```c
/* sound/soc/codecs/rt711-sdca.c:1300 */
static const struct snd_soc_component_driver soc_sdca_dev_rt711 = {
	.probe = rt711_sdca_probe,
	.controls = rt711_sdca_snd_controls,
	.num_controls = ARRAY_SIZE(rt711_sdca_snd_controls),
	.dapm_widgets = rt711_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt711_sdca_dapm_widgets),
	.dapm_routes = rt711_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt711_sdca_audio_map),
	.set_jack = rt711_sdca_set_jack_detect,
	.endianness = 1,
};
```

The [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) field is one of the function pointers in the generic [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), grouped with the other component-level codec hooks:

```c
/* include/sound/soc-component.h:99 */
	int (*set_jack)(struct snd_soc_component *component,
			struct snd_soc_jack *jack,  void *data);
	int (*get_jack_type)(struct snd_soc_component *component);
```

The two DAIs follow the headset shape. The `rt711-sdca-aif1` entry declares a stereo headphone [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) on the SoundWire DP3 data port and a stereo [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) for the headset microphone on DP2, and `rt711-sdca-aif2` adds a second capture for the on-board analog microphone on DP4. Both name [`rt711_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1428) as their [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403):

```c
/* sound/soc/codecs/rt711-sdca.c:1435 */
static struct snd_soc_dai_driver rt711_sdca_dai[] = {
	{
		.name = "rt711-sdca-aif1",
		.id = RT711_AIF1,
		.playback = {
			.stream_name = "DP3 Playback",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT711_STEREO_RATES,
			.formats = RT711_FORMATS,
		},
		.capture = {
			.stream_name = "DP2 Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT711_STEREO_RATES,
			.formats = RT711_FORMATS,
		},
		.ops = &rt711_sdca_ops,
	},
	{
		.name = "rt711-sdca-aif2",
		.id = RT711_AIF2,
		.capture = {
			.stream_name = "DP4 Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT711_STEREO_RATES,
			.formats = RT711_FORMATS,
		},
		.ops = &rt711_sdca_ops,
	}
};
```

[`rt711_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1428) fills only the four SoundWire callbacks, leaving every other op NULL behind the ASoC wrapper guards:

```c
/* sound/soc/codecs/rt711-sdca.c:1428 */
static const struct snd_soc_dai_ops rt711_sdca_ops = {
	.hw_params	= rt711_sdca_pcm_hw_params,
	.hw_free	= rt711_sdca_pcm_hw_free,
	.set_stream	= rt711_sdca_set_sdw_stream,
	.shutdown	= rt711_sdca_shutdown,
};
```

Both DAIs hang those ops off the same struct, aif1 carrying a DP3 playback and a DP2 capture and aif2 a single DP4 capture, so the two fan out across three data ports:

```
    rt711_sdca_dai[]: two DAIs fan out to three SoundWire data ports
    ─────────────────────────────────────────────────────────────────

    rt711-sdca-aif1  (id RT711_AIF1)        rt711-sdca-aif2 (RT711_AIF2)
    ┌──────────────────────────────┐        ┌──────────────────────────┐
    │ playback "DP3 Playback"      │        │ capture "DP4 Capture"    │
    │ capture  "DP2 Capture"       │        │                          │
    └───────┬───────────────┬──────┘        └────────────┬─────────────┘
            │ playback      │ capture                    │ capture
            ▼               ▼                            ▼
        ┌───────┐       ┌───────┐                    ┌───────┐
        │  DP3  │       │  DP2  │                    │  DP4  │
        │ sink  │       │ source│                    │ source│
        └───────┘       └───────┘                    └───────┘
       headphone        headset mic                  analog mic

    sink_ports = 0x8 (DP3)      source_ports = 0x14 (DP2, DP4)
```

### set_stream stores the handle, hw_params joins the stream

The [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op stores the opaque SoundWire stream handle in the DAI's per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) slot with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506), and the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op clears it again:

```c
/* sound/soc/codecs/rt711-sdca.c:1312 */
static int rt711_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}

static void rt711_sdca_shutdown(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	snd_soc_dai_set_dma_data(dai, substream, NULL);
}
```

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op [`rt711_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1326) reads the [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18) back with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), recovers the stream handle, runs [`snd_sdw_params_to_config()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdw.h#L32) to fill the stream and port config, and selects the data port from the substream direction and the DAI [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403). Playback always uses port 3, capture uses port 2 for `aif1` and port 4 for `aif2`:

```c
/* sound/soc/codecs/rt711-sdca.c:1326 */
static int rt711_sdca_pcm_hw_params(struct snd_pcm_substream *substream,
				struct snd_pcm_hw_params *params,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt711_sdca_priv *rt711 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_config stream_config = {0};
	struct sdw_port_config port_config = {0};
	struct sdw_stream_runtime *sdw_stream;
	int retval;
	unsigned int sampling_rate;

	dev_dbg(dai->dev, "%s %s", __func__, dai->name);
	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);

	if (!sdw_stream)
		return -EINVAL;

	if (!rt711->slave)
		return -EINVAL;

	/* SoundWire specific configuration */
	snd_sdw_params_to_config(substream, params, &stream_config, &port_config);

	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		port_config.num = 3;
	} else {
		if (dai->id == RT711_AIF1)
			port_config.num = 2;
		else if (dai->id == RT711_AIF2)
			port_config.num = 4;
		else
			return -EINVAL;
	}

	retval = sdw_stream_add_slave(rt711->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
	...
```

After the peripheral joins the stream, the tail of the op maps the PCM rate to an SDCA rate constant and writes the sample-frequency-index control of three SDCA clock-source entities through the byte [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408):

```c
/* sound/soc/codecs/rt711-sdca.c:1374 */
	/* sampling rate configuration */
	switch (params_rate(params)) {
	case 44100:
		sampling_rate = RT711_SDCA_RATE_44100HZ;
		break;
	case 48000:
		sampling_rate = RT711_SDCA_RATE_48000HZ;
		break;
	case 96000:
		sampling_rate = RT711_SDCA_RATE_96000HZ;
		break;
	case 192000:
		sampling_rate = RT711_SDCA_RATE_192000HZ;
		break;
	default:
		dev_err(component->dev, "%s: Rate %d is not supported\n",
			__func__, params_rate(params));
		return -EINVAL;
	}

	/* set sampling frequency */
	regmap_write(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_CS01, RT711_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);
	regmap_write(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_CS11, RT711_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);
	regmap_write(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT711_SDCA_ENT_CS1F, RT711_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);

	return 0;
}
```

[`rt711_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1408) reverses the add by removing the peripheral from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228):

```c
/* sound/soc/codecs/rt711-sdca.c:1408 */
static int rt711_sdca_pcm_hw_free(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt711_sdca_priv *rt711 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_runtime *sdw_stream =
		snd_soc_dai_get_dma_data(dai, substream);

	if (!rt711->slave)
		return -EINVAL;

	sdw_stream_remove_slave(rt711->slave, sdw_stream);
	return 0;
}
```

The setup side reads the substream direction and DAI id together, playback taking port 3 while a capture takes port 2 on aif1 and port 4 on aif2 before the add:

```
    rt711_sdca_pcm_hw_params(): direction x DAI id selects port_config.num
    ──────────────────────────────────────────────────────────────────────

    substream->stream      dai->id            port_config.num
    ┌────────────────────┬────────────────┬───────────────────┐
    │ PLAYBACK           │ any            │  3                │
    ├────────────────────┼────────────────┼───────────────────┤
    │ CAPTURE            │ RT711_AIF1     │  2                │
    │ CAPTURE            │ RT711_AIF2     │  4                │
    │ CAPTURE            │ other          │  -EINVAL          │
    └────────────────────┴────────────────┴───────────────────┘

    then sdw_stream_add_slave(slave, &stream_config, &port_config, 1, ...)
```

### The private data struct holds the codec instance state

The [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18) is the single object every component, DAI, and jack callback dereferences. It holds the byte [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L19) and the [`mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L19) for register I/O, the SoundWire [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L21), the [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25) pointer set by the jack hook, the two delayed-work items the interrupt schedules, the cached SDCA status words [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32), and the jack-detect source [`jd_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31):

```c
/* sound/soc/codecs/rt711-sdca.h:18 */
struct  rt711_sdca_priv {
	struct regmap *regmap, *mbq_regmap;
	struct snd_soc_component *component;
	struct sdw_slave *slave;
	struct sdw_bus_params params;
	bool hw_init;
	bool first_hw_init;
	struct snd_soc_jack *hs_jack;
	struct delayed_work jack_detect_work;
	struct delayed_work jack_btn_check_work;
	struct mutex calibrate_mutex; /* for headset calibration */
	struct mutex disable_irq_lock; /* SDCA irq lock protection */
	bool disable_irq;
	int jack_type, jd_src;
	unsigned int scp_sdca_stat1, scp_sdca_stat2;
	int hw_ver;
	bool fu0f_dapm_mute, fu0f_mixer_l_mute, fu0f_mixer_r_mute;
	bool fu1e_dapm_mute, fu1e_mixer_l_mute, fu1e_mixer_r_mute;
	unsigned int ge_mode_override;
};
```

[`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469) allocates the struct, stores it on the device with [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h), stashes both regmaps in cache-only mode, binds the two work items to their handlers, defaults [`jd_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31) to JD2, and registers the component:

```c
/* sound/soc/codecs/rt711-sdca.c:1469 */
int rt711_sdca_init(struct device *dev, struct regmap *regmap,
			struct regmap *mbq_regmap, struct sdw_slave *slave)
{
	struct rt711_sdca_priv *rt711;
	int ret;

	rt711 = devm_kzalloc(dev, sizeof(*rt711), GFP_KERNEL);
	if (!rt711)
		return -ENOMEM;

	dev_set_drvdata(dev, rt711);
	rt711->slave = slave;
	rt711->regmap = regmap;
	rt711->mbq_regmap = mbq_regmap;

	regcache_cache_only(rt711->regmap, true);
	regcache_cache_only(rt711->mbq_regmap, true);

	mutex_init(&rt711->calibrate_mutex);
	mutex_init(&rt711->disable_irq_lock);

	INIT_DELAYED_WORK(&rt711->jack_detect_work, rt711_sdca_jack_detect_handler);
	INIT_DELAYED_WORK(&rt711->jack_btn_check_work, rt711_sdca_btn_check_handler);
	...
	/* JD source uses JD2 in default */
	rt711->jd_src = RT711_JD2;

	ret =  devm_snd_soc_register_component(dev,
			&soc_sdca_dev_rt711,
			rt711_sdca_dai,
			ARRAY_SIZE(rt711_sdca_dai));
	...
}
```

That init fills the one drvdata struct whose fields the figure groups by owner, the two regmaps for register I/O, the slave for the bus binding, the jack hook, and the two IRQ-scheduled work items:

```
    struct rt711_sdca_priv: fields grouped by the path that owns them
    ─────────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────┐
    │ struct rt711_sdca_priv  (drvdata, one per device)            │
    ├──────────────────────────────────────────────────────────────┤
    │ register I/O   regmap, mbq_regmap                            │
    │ bus binding    slave, params, hw_init, first_hw_init         │
    │ ASoC           component                                     │
    │ jack hook      hs_jack, jd_src, jack_type                    │
    │ IRQ-scheduled  jack_detect_work, jack_btn_check_work         │
    │ cached IRQ     scp_sdca_stat1, scp_sdca_stat2                │
    │ locks          calibrate_mutex, disable_irq_lock, disable_irq│
    │ mute state     fu0f_*_mute, fu1e_*_mute, ge_mode_override    │
    └──────────────────────────────────────────────────────────────┘
```

### The generic jack model: snd_soc_jack and snd_soc_jack_report

The codec never touches the input layer directly. It updates a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) that the machine driver created, and the only mutation path is [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33). The jack object is small, holding the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask, the DAPM [`pins`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) list, the [`notifier`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) chain, and the underlying [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80):

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

[`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) takes the jack mutex, clears the masked bits out of [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), ORs in the reported bits under the same mask, toggles each DAPM pin that the new status drives, runs the notifier chain, and finally reports the merged status to the input layer through [`snd_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/jack.c). The kernel-doc warns it sleeps:

```c
/* sound/soc/soc-jack.c:33 */
/*
 * Note: This function uses mutexes and should be called from a
 * context which can sleep (such as a workqueue).
 */

void snd_soc_jack_report(struct snd_soc_jack *jack, int status, int mask)
{
	struct snd_soc_dapm_context *dapm;
	struct snd_soc_jack_pin *pin;
	unsigned int sync = 0;

	if (!jack || !jack->jack)
		return;
	...
	mutex_lock(&jack->mutex);

	jack->status &= ~mask;
	jack->status |= status & mask;
	...
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

Because [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) is only ever changed under the supplied mask, a caller that owns a subset of the bits (a GPIO line, an analog zone, or this codec's headset-plus-button mask) updates that subset without disturbing bits another method owns. The RT711 always passes the same mask, the fixed set [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) OR [`SND_JACK_BTN_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L50) through [`SND_JACK_BTN_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L53).

### The jack hook stores the jack and arms detection

The codec's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op is reached from the machine layer through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190), which forwards to the codec op only when the field is set. [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522) reads its private data, stores the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) pointer in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L25), and arms the detection logic in [`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451). It returns early when the device was never initialized so the jack is wired only once the hardware is present:

```c
/* sound/soc/codecs/rt711-sdca.c:522 */
static int rt711_sdca_set_jack_detect(struct snd_soc_component *component,
	struct snd_soc_jack *hs_jack, void *data)
{
	struct rt711_sdca_priv *rt711 = snd_soc_component_get_drvdata(component);
	int ret;

	rt711->hs_jack = hs_jack;

	/* we can only resume if the device was initialized at least once */
	if (!rt711->first_hw_init)
		return 0;

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

	rt711_sdca_jack_init(rt711);

	pm_runtime_put_autosuspend(component->dev);

	return 0;
}
```

The jack handed in is created and owned by the machine driver. The SoundWire generic helper [`asoc_sdw_rt_sdca_jack_rtd_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c#L93) builds it with [`snd_soc_card_jack_new_pins()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L35), passing the type mask of [`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) plus the four button bits and a pin table for the headphone and microphone, then attaches button-to-key mappings and hands the jack to the codec through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190):

```c
/* sound/soc/sdw_utils/soc_sdw_rt_sdca_jack_common.c:146 */
	ret = snd_soc_card_jack_new_pins(rtd->card, "Headset Jack",
					 SND_JACK_HEADSET | SND_JACK_BTN_0 |
					 SND_JACK_BTN_1 | SND_JACK_BTN_2 |
					 SND_JACK_BTN_3,
					 &ctx->sdw_headset,
					 rt_sdca_jack_pins,
					 ARRAY_SIZE(rt_sdca_jack_pins));
	...
	jack = &ctx->sdw_headset;

	snd_jack_set_key(jack->jack, SND_JACK_BTN_0, KEY_PLAYPAUSE);
	snd_jack_set_key(jack->jack, SND_JACK_BTN_1, KEY_VOICECOMMAND);
	snd_jack_set_key(jack->jack, SND_JACK_BTN_2, KEY_VOLUMEUP);
	snd_jack_set_key(jack->jack, SND_JACK_BTN_3, KEY_VOLUMEDOWN);

	ret = snd_soc_component_set_jack(component, jack, NULL);
```

[`rt711_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L451) programs the HID and Ground-Engine event-enable bits, applies the per-source decode settings selected by [`jd_src`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31), and finally unmasks the two SDCA interrupt sources that feed jack and button detection by writing [`SDW_SCP_SDCA_INTMASK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L176) and [`SDW_SCP_SDCA_INTMASK2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L186) with [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h):

```c
/* sound/soc/codecs/rt711-sdca.c:451 */
static void rt711_sdca_jack_init(struct rt711_sdca_priv *rt711)
{
	mutex_lock(&rt711->calibrate_mutex);

	if (rt711->hs_jack) {
		/* Enable HID1 event & set button RTC mode */
		rt711_sdca_index_update_bits(rt711, RT711_VENDOR_HDA_CTL,
			RT711_PUSH_BTN_INT_CTL6, 0x80f0, 0x8000);
		...
		/* GE_mode_change_event_en & Hid1_push_button_event_en */
		rt711_sdca_index_update_bits(rt711, RT711_VENDOR_HDA_CTL,
			RT711_GE_MODE_RELATED_CTL, 0x0c00, 0x0c00);

		switch (rt711->jd_src) {
		case RT711_JD1:
			/* default settings was already for JD1 */
			break;
		case RT711_JD2:
			...
			break;
		...
		}

		/* set SCP_SDCA_IntMask1[0]=1 */
		sdw_write_no_pm(rt711->slave, SDW_SCP_SDCA_INTMASK1, SDW_SCP_SDCA_INTMASK_SDCA_0);
		/* set SCP_SDCA_IntMask2[0]=1 */
		sdw_write_no_pm(rt711->slave, SDW_SCP_SDCA_INTMASK2, SDW_SCP_SDCA_INTMASK_SDCA_8);
		dev_dbg(&rt711->slave->dev, "in %s enable\n", __func__);
	} else {
		/* disable HID 1/2 event */
		rt711_sdca_index_update_bits(rt711, RT711_VENDOR_HDA_CTL,
			RT711_GE_MODE_RELATED_CTL, 0x0c00, 0x0000);

		dev_dbg(&rt711->slave->dev, "in %s disable\n", __func__);
	}

	mutex_unlock(&rt711->calibrate_mutex);
}
```

This function is reached from two callers, [`rt711_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L522) at jack-registration time and [`rt711_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1588) on the first hardware init, so a peripheral that attaches after the machine driver already registered the jack still arms detection. Because the SDCA interrupt mask is cleared by any device reset, [`rt711_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L141) re-writes the same two mask bits on every re-attach.

### The detection worker classifies the jack and the button

A SoundWire cascade interrupt schedules [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26), whose handler runs in process context where it may sleep and call into DAPM. [`rt711_sdca_jack_detect_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309) recovers the [`struct rt711_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L18) from the work item, runs headset detection when the cached [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) carries [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137) and button detection when [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) carries [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147), then makes one [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33) carrying both the headset type and the button bit:

```c
/* sound/soc/codecs/rt711-sdca.c:309 */
static void rt711_sdca_jack_detect_handler(struct work_struct *work)
{
	struct rt711_sdca_priv *rt711 =
		container_of(work, struct rt711_sdca_priv, jack_detect_work.work);
	int btn_type = 0, ret;

	if (!rt711->hs_jack)
		return;

	if (!snd_soc_card_is_instantiated(rt711->component->card))
		return;

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
	snd_soc_jack_report(rt711->hs_jack, rt711->jack_type | btn_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);

	if (btn_type) {
		/* button released */
		snd_soc_jack_report(rt711->hs_jack, rt711->jack_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);

		mod_delayed_work(system_power_efficient_wq,
			&rt711->jack_btn_check_work, msecs_to_jiffies(200));
	}
}
```

The first report posts the current state, and when a button was seen the handler immediately posts a second report with [`btn_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309) cleared, modeling a press followed by a release, then schedules [`jack_btn_check_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L27) 200 ms out to poll for the physical release. When [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31) is 0 the handler forces [`btn_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L309) to 0, so a button is never reported on an unplugged jack.

[`rt711_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L264) drives the impedance and microphone classification. It first applies any forced Ground-Engine override through [`rt711_sdca_ge_force_jack_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L84), then reads the SDCA Ground-Engine 49 detected-mode register and maps it to a jack type. Mode 0x03 is a three-pole plug ([`SND_JACK_HEADPHONE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L39), no microphone) and mode 0x05 is a four-pole plug ([`SND_JACK_HEADSET`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L41) with microphone); the detected mode is then written back as the selected mode so the analog path matches the impedance the hardware found:

```c
/* sound/soc/codecs/rt711-sdca.c:264 */
static int rt711_sdca_headset_detect(struct rt711_sdca_priv *rt711)
{
	unsigned int det_mode;
	int ret;

	rt711_sdca_ge_force_jack_type(rt711, rt711->ge_mode_override);

	/* get detected_mode */
	ret = regmap_read(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_GE49, RT711_SDCA_CTL_DETECTED_MODE, 0),
		&det_mode);
	if (ret < 0)
		goto io_error;

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

	/* write selected_mode */
	if (det_mode) {
		ret = regmap_write(rt711->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT711_SDCA_ENT_GE49, RT711_SDCA_CTL_SELECTED_MODE, 0),
			det_mode);
		if (ret < 0)
			goto io_error;
	}
	...
io_error:
	pr_err_ratelimited("IO error in %s, ret %d\n", __func__, ret);
	return ret;
}
```

[`rt711_sdca_button_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L186) reads the SDCA HID01 entity's UMP message. It checks the current message owner first and returns 0 when the device still owns the buffer, reads the message offset, copies three bytes from the HID buffer through the byte [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L19), and decodes the button nibble into a `SND_JACK_BTN_*` bit before handing ownership of the buffer back to the device:

```c
/* sound/soc/codecs/rt711-sdca.c:186 */
static unsigned int rt711_sdca_button_detect(struct rt711_sdca_priv *rt711)
{
	unsigned int btn_type = 0, offset, idx, val, owner;
	int ret;
	unsigned char buf[3];

	/* get current UMP message owner */
	ret = regmap_read(rt711->regmap,
		SDW_SDCA_CTL(FUNC_NUM_HID, RT711_SDCA_ENT_HID01, RT711_SDCA_CTL_HIDTX_CURRENT_OWNER, 0),
		&owner);
	if (ret < 0)
		return 0;

	/* if owner is device then there is no button event from device */
	if (owner == 1)
		return 0;
	...
	if (buf[0] == 0x11) {
		switch (buf[1] & 0xf0) {
		case 0x10:
			btn_type |= SND_JACK_BTN_2;
			break;
		case 0x20:
			btn_type |= SND_JACK_BTN_3;
			break;
		case 0x40:
			btn_type |= SND_JACK_BTN_0;
			break;
		case 0x80:
			btn_type |= SND_JACK_BTN_1;
			break;
		}
		...
	}

_end_btn_det_:
	/* Host is owner, so set back to device */
	if (owner == 0)
		/* set owner to device */
		regmap_write(rt711->regmap,
			SDW_SDCA_CTL(FUNC_NUM_HID, RT711_SDCA_ENT_HID01,
				RT711_SDCA_CTL_HIDTX_SET_OWNER_TO_DEVICE, 0), 0x01);

	return btn_type;
}
```

[`rt711_sdca_btn_check_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L360) is the follow-up poll. It re-reads the Ground-Engine detected mode, and if the pin is still attached re-reads the HID buffer and re-reports the held button; if the pin has detached it sets [`jack_type`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L31) back to 0. While a button stays pressed it re-arms itself every 200 ms, so a long press is reported as a continuous key event rather than a single edge.

```
    Jack/button states from GE49 detected_mode and the HID report
    ───────────────────────────────────────────────────────────────

       ┌─────────────────────────────────────────┐
       │ UNPLUGGED    jack_type = 0              │ ◀─ pin detached
       └──────────┬──────────────────┬───────────┘
        det_mode  │ 0x03        0x05 │
                  ▼                  ▼
       ┌───────────────────┐  ┌───────────────────┐
       │ HEADPHONE         │  │ HEADSET           │
       │ SND_JACK_HEADPHONE│  │ SND_JACK_HEADSET  │
       └───────────────────┘  └─────────┬─────────┘
                                        │ HID buf[1] & 0xf0
                                        ▼
       ┌──────────────────────────────────────────┐
       │ BUTTON  report jack_type + BTN_0..3      │
       │ then re-report jack_type (press, release)│
       └──────────────────┬───────────────────────┘
                          ▼  jack_btn_check_work +200ms, re-poll

```

### The SoundWire bind drives the interrupt and attach paths

The RT711 binds to the SoundWire bus through [`rt711_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L345), which fills three of the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callbacks:

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:345 */
static const struct sdw_slave_ops rt711_sdca_slave_ops = {
	.read_prop = rt711_sdca_read_prop,
	.interrupt_callback = rt711_sdca_interrupt_callback,
	.update_status = rt711_sdca_update_status,
};
```

[`rt711_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L141) is invoked for every attach state change. It clears [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L23) on [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95), re-writes the SDCA interrupt mask on [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) when a jack is registered, and runs [`rt711_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1588) the first time the peripheral attaches:

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:141 */
static int rt711_sdca_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt711_sdca_priv *rt711 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt711->hw_init = false;

	if (status == SDW_SLAVE_ATTACHED) {
		if (rt711->hs_jack) {
			/*
			 * Due to the SCP_SDCA_INTMASK will be cleared by any reset, and then
			 * if the device attached again, we will need to set the setting back.
			 * It could avoid losing the jack detection interrupt.
			 * This also could sync with the cache value as the rt711_sdca_jack_init set.
			 */
			sdw_write_no_pm(rt711->slave, SDW_SCP_SDCA_INTMASK1,
				SDW_SCP_SDCA_INTMASK_SDCA_0);
			sdw_write_no_pm(rt711->slave, SDW_SCP_SDCA_INTMASK2,
				SDW_SCP_SDCA_INTMASK_SDCA_8);
		}
	}

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt711->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt711_sdca_io_init(&slave->dev, slave);
}
```

[`rt711_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L245) runs in thread context on an in-band interrupt. It cancels any pending jack work, takes [`disable_irq_lock`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L29) so a concurrent system suspend cannot disable the interrupt mid-handling, reads the two SDCA status registers into the cached [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L32), and loops clearing the status bits until they read clear or a retry budget is exhausted:

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:245 */
static int rt711_sdca_interrupt_callback(struct sdw_slave *slave,
					struct sdw_slave_intr_status *status)
{
	struct rt711_sdca_priv *rt711 = dev_get_drvdata(&slave->dev);
	int ret, stat;
	int count = 0, retry = 3;
	unsigned int sdca_cascade, scp_sdca_stat1, scp_sdca_stat2 = 0;
	...
	if (cancel_delayed_work_sync(&rt711->jack_detect_work)) {
		dev_warn(&slave->dev, "%s the pending delayed_work was cancelled", __func__);
		/* avoid the HID owner doesn't change to device */
		if (rt711->scp_sdca_stat2)
			scp_sdca_stat2 = rt711->scp_sdca_stat2;
	}
	...
	mutex_lock(&rt711->disable_irq_lock);

	ret = sdw_read_no_pm(rt711->slave, SDW_SCP_SDCA_INT1);
	if (ret < 0)
		goto io_error;
	rt711->scp_sdca_stat1 = ret;
	ret = sdw_read_no_pm(rt711->slave, SDW_SCP_SDCA_INT2);
	if (ret < 0)
		goto io_error;
	rt711->scp_sdca_stat2 = ret;
	...
	do {
		/* clear flag */
		ret = sdw_read_no_pm(rt711->slave, SDW_SCP_SDCA_INT1);
		...
		/* check if flag clear or not */
		ret = sdw_read_no_pm(rt711->slave, SDW_DP0_INT);
		if (ret < 0)
			goto io_error;
		sdca_cascade = ret & SDW_DP0_SDCA_CASCADE;
		...
		stat = scp_sdca_stat1 || scp_sdca_stat2 || sdca_cascade;

		count++;
	} while (stat != 0 && count < retry);
	...
	if (status->sdca_cascade && !rt711->disable_irq)
		mod_delayed_work(system_power_efficient_wq,
			&rt711->jack_detect_work, msecs_to_jiffies(30));

	mutex_unlock(&rt711->disable_irq_lock);

	return 0;

io_error:
	mutex_unlock(&rt711->disable_irq_lock);
	pr_err_ratelimited("IO error in %s, ret %d\n", __func__, ret);
	return ret;
}
```

The decision to do jack work is gated on the [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) flag of the [`struct sdw_slave_intr_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) the bus passes in. When the SDCA cascade bit is set and the codec is not being suspended, the handler schedules [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.h#L26) 30 ms out so the slow per-entity reads run in process context rather than in the interrupt thread. The interrupt struct is small, carrying the cascade flag, the control-port status, and the per-port array:

```c
/* include/linux/soundwire/sdw.h:528 */
struct sdw_slave_intr_status {
	bool sdca_cascade;
	u8 control_port;
	u8 port[15];
};
```

### Two regmaps over one SoundWire transport

The RT711 builds two register maps in its SoundWire probe, because the SDCA register space mixes plain byte registers with multi-byte-quantity registers that the SoundWire MBQ access mode pages in word-at-a-time. [`rt711_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L114) is the 8-bit-value map, and [`rt711_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L127) is the 16-bit map named `sdw-mbq`, both with a 32-bit register address and a MAPLE-tree cache:

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:114 */
static const struct regmap_config rt711_sdca_regmap = {
	.reg_bits = 32,
	.val_bits = 8,
	.readable_reg = rt711_sdca_readable_register,
	.volatile_reg = rt711_sdca_volatile_register,
	.max_register = 0x44ffffff,
	.reg_defaults = rt711_sdca_reg_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt711_sdca_reg_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};

static const struct regmap_config rt711_sdca_mbq_regmap = {
	.name = "sdw-mbq",
	.reg_bits = 32,
	.val_bits = 16,
	.readable_reg = rt711_sdca_mbq_readable_register,
	.volatile_reg = rt711_sdca_mbq_volatile_register,
	.max_register = 0x40800f12,
	.reg_defaults = rt711_sdca_mbq_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt711_sdca_mbq_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};
```

[`rt711_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L351) creates both maps and hands them to [`rt711_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca.c#L1469). The MBQ map is built with [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) and the byte map with [`devm_regmap_init_sdw()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196):

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:351 */
static int rt711_sdca_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap, *mbq_regmap;

	/* Regmap Initialization */
	mbq_regmap = devm_regmap_init_sdw_mbq(slave, &rt711_sdca_mbq_regmap);
	if (IS_ERR(mbq_regmap))
		return PTR_ERR(mbq_regmap);

	regmap = devm_regmap_init_sdw(slave, &rt711_sdca_regmap);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt711_sdca_init(&slave->dev, regmap, mbq_regmap, slave);
}
```

The [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op [`rt711_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L175) runs once at probe to publish the peripheral's data-port bitmaps and the error-interrupt mask. It declares source ports 0x14 (DP2 and DP4, the two capture ports) and sink port 0x8 (DP3, the playback port), sets [`paging_support`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), and enables the bus-clash and parity error interrupts in [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372):

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:175 */
static int rt711_sdca_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	int nval;
	int i, j;
	u32 bit;
	unsigned long addr;
	struct sdw_dpn_prop *dpn;

	prop->scp_int1_mask = SDW_SCP_INT1_BUS_CLASH | SDW_SCP_INT1_PARITY;
	prop->quirks = SDW_SLAVE_QUIRKS_INVALID_INITIAL_PARITY;

	prop->paging_support = true;

	/* first we need to allocate memory for set bits in port lists */
	prop->source_ports = 0x14; /* BITMAP: 00010100 */
	prop->sink_ports = 0x8; /* BITMAP:  00001000 */
	...
	/* wake-up event */
	prop->wake_capable = 1;

	return 0;
}
```

The whole driver is registered by [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) over [`rt711_sdca_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L480), whose one-entry match table [`rt711_sdca_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt711-sdca-sdw.c#L383) carries the MIPI id of the part. On an Intel MTL or LNL x86-64 ACPI platform the peripheral is enumerated from its `_ADR` integer and bound when its manufacturer id 0x025d and part id 0x711 match this row:

```c
/* sound/soc/codecs/rt711-sdca-sdw.c:383 */
static const struct sdw_device_id rt711_sdca_id[] = {
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x711, 0x3, 0x1, 0),
	{},
};
MODULE_DEVICE_TABLE(sdw, rt711_sdca_id);
```

The bound peripheral reaches its registers over one control link split into two maps, an 8-bit value map for the plain SDCA controls and a 16-bit MBQ map for the feature-unit volumes and channel gains:

```
    One SoundWire transport, two regmaps split by value width
    ──────────────────────────────────────────────────────────

                       SoundWire control link (slave)
                                   │
                  ┌────────────────┴─────────────────┐
                  ▼                                   ▼
       devm_regmap_init_sdw          devm_regmap_init_sdw_mbq
       ┌──────────────────────┐      ┌──────────────────────────┐
       │ rt711_sdca_regmap    │      │ rt711_sdca_mbq_regmap    │
       │ val_bits = 8         │      │ name "sdw-mbq"           │
       │ reg_bits = 32        │      │ val_bits = 16            │
       │ max_register         │      │ reg_bits = 32            │
       │   0x44ffffff         │      │ max_register 0x40800f12  │
       │ REGCACHE_MAPLE       │      │ REGCACHE_MAPLE           │
       └──────────┬───────────┘      └────────────┬─────────────┘
                  ▼                                ▼
       plain 1-byte SDCA controls       2-byte feature-unit
       (mute, owner, freq index)        volumes and channel gains
```

### SoundWire headset/jack codec structure

A generic SDCA headset codec registers one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) (controls, DAPM widgets, and a [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op) alongside its [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array and a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), while its [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) ([`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)) drives a detection worker on the SDCA cascade interrupt.

```
    SoundWire headset/jack codec (SDCA)
    ───────────────────────────────────

       struct snd_soc_component_driver
       ┌──────────────────────────────────────────────────────────┐
       │  controls / dapm_widgets / dapm_routes                   │
       │  set_jack ───────────────────┐                           │
       └──────────────────────────────┼───────────────────────────┘
                                      │ registers DAIs + jack
              ┌───────────────────────┴────────────────┐
              ▼                                        ▼
       struct snd_soc_dai_driver[]            struct snd_soc_jack
       ┌──────────────────────────┐           ┌──────────────────┐
       │ aif: HP Playback (DAC)   │           │ status (bitmask) │
       │      Mic  Capture (ADC)  │           │ pins, notifier   │
       │ ops ─▶ hw_params/set_str │           └────────▲─────────┘
       └───────────┬──────────────┘                    │ report
                   │ sdw_stream_add_slave              │
                   ▼                          ┌────────┴─────────┐
            SoundWire data ports              │ detection worker │
            (RX = playback, TX = capture)     └────────▲─────────┘
                                                       │ schedule
       struct sdw_slave_ops                            │
       ┌───────────────────────────────────────┐       │
       │ update_status  (ATTACHED / UNATTACHED)│       │
       │ interrupt_callback ───────────────────┼───────┘
       │ read_prop                             │  on SDCA cascade IRQ
       └───────────────────────────────────────┘
```
