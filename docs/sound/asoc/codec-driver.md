# ASoC codec driver

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A codec driver describes an audio codec to ASoC as one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) plus an array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and the generic component this builds on adds register I/O through a [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35), a table of mixer [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71), a set of DAPM [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75), and an optional [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback for headset detection. The component driver is static and const, shared across every card that instantiates the codec, and [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) binds it to a device together with the DAI array. At card bind time [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) reads the [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71), and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) arrays out of the driver and instantiates each one onto the live [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207). The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec is the worked example, an SDCA part reached over SoundWire whose component driver [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) supplies all five of those fields and whose private state is a [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) reached from any component callback through [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356).

```
    component driver  (const, shared)
    soc_sdca_dev_rt722 : struct snd_soc_component_driver
    ┌────────────────────────────────────────────────────────┐
    │ controls       ─▶ rt722_sdca_controls[]  (mixers)      │
    │ dapm_widgets   ─▶ rt722_sdca_dapm_widgets[]            │
    │ dapm_routes    ─▶ rt722_sdca_audio_map[]               │
    │ set_jack       ─▶ rt722_sdca_set_jack_detect()         │
    │ endianness = 1                                         │
    └───────────────────────────┬────────────────────────────┘
                                │ devm_snd_soc_register_component()
            ┌───────────────────┼────────────────────┐
            ▼                   ▼                    ▼
       struct regmap     struct rt722_sdca_priv  snd_soc_dai_driver[]
       rt722_sdca_regmap   (drvdata)             rt722_sdca_dai
       reg 32 / val 16     regmap, slave, jack   aif1 / aif2 / aif3
       (rt722-sdca-sdw.c)  reached via drvdata   three SoundWire DAIs
```

## SUMMARY

A codec driver provides two static descriptors. One [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) describes the codec as a whole, and an array of [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) describes its audio interfaces. The generic component machinery handles probe ordering, the DAI list, suspend and resume, and PCM creation, and the codec specializes that generic component by filling the description fields the codec layer reads. The mixer controls are a [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) array of [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47); the DAPM graph is a [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) array of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) and a [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) array of [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473); and the headset hook is the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) function pointer. Register I/O is carried by a [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35) built from a [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) with one of the `devm_regmap_init_*` helpers, and the codec reads or writes its hardware registers through that map rather than touching the bus directly.

Registration runs through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), which calls [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) to allocate a [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), run [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) on it, point its [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221) field at the static descriptor, and register every DAI in the array. When a card binds, [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) instantiates the description into the live component. It calls [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) on the [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) array, runs the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), then calls [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) on the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) array and [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) on the [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) array. The codec stores its instance state in a private struct, hands the pointer to the core with [`snd_soc_component_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L350) (or the equivalent [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) before registration), and reads it back inside any control, DAPM, or jack callback through [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356).

The Realtek RT722 follows this shape exactly. Its [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) names a [`rt722_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697) mixer table, a [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996) widget array, a [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) route array, a [`rt722_sdca_probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1075) probe, and a [`rt722_sdca_set_jack_detect`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321) jack hook, and sets [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) to 1 because the SoundWire transport fixes the wire endian. The [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) array registered alongside it declares three SoundWire interfaces. The regmap is a separate [`rt722_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195) configuration built in [`rt722_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416) with [`devm_regmap_init_sdw_mbq_cfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1226) and stashed in the [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) field of the codec's [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) before the component is registered.

## SPECIFICATIONS

The [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) object is a Linux kernel software construct and has no standalone hardware specification. The RT722 it describes is an SDCA (SoundWire Device Class for Audio) part whose register access and audio streams travel over SoundWire, and its control ranges (volume, mute, boost) map onto SDCA function-unit controls addressed by the [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h) register-address macro in the kernel headers. The serial-audio transport and the device-class layout are handled in the kernel by the SoundWire core and the SDCA helper layer; this page describes only the kernel representation.

## LINUX KERNEL

### Generic component description (soc-component.h)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the static, const description a codec or platform driver registers; carries the control/DAPM/jack description and the component callbacks
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the runtime component allocated at registration; holds the back pointer to the driver, the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), the [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L226) pointer, and the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L237) context
- [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) / [`num_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L72): the mixer control table and its length, added to the component after [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs
- [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) / [`num_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L74): the DAPM widget array and its length, instantiated before [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) / [`num_dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L76): the DAPM route array and its length, connected after [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the headset-detection callback the machine layer drives through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190)
- [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191): a one-bit field set when the component does not care about PCM endian, so the core registers both LE and BE variants of each format

### drvdata accessors (soc-component.h, soc-component.c)

- [`'\<snd_soc_component_get_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356): read the codec's private pointer back from the component device; wraps [`dev_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h)
- [`'\<snd_soc_component_set_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L350): store the codec's private pointer on the component device; wraps [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h)
- [`'\<snd_soc_component_init_regmap\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L367): late-bind a [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35) onto the component when it was not ready at registration

### Registration and probe (soc-core.c, soc-devres.c)

- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): device-managed registration of a component driver plus its DAI array; auto-unregisters at device teardown
- [`'\<snd_soc_register_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932): allocate the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), bind the driver, and register the DAIs
- [`'\<snd_soc_component_initialize\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850): set up the component's DAPM context, list heads, and IO mutex, and point [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221) at the static descriptor
- [`'\<soc_probe_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602): at card bind, create the widgets, run the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), then add the controls and routes onto the live component

### Control and DAPM instantiation (soc-core.c, soc-dapm.c)

- [`'\<snd_soc_add_component_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501): register an array of [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) against a component so userspace sees them as ALSA mixer elements
- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932): create one [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) per template in the array, building the power-management graph nodes
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): connect widget pairs named by each [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) into the graph edges
- [`'\<snd_soc_component_set_jack\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190): invoke the component's [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op, returning `-ENOTSUPP` when the codec supplies none

### Description types

- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): one mixer control template (name, access, [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)/[`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callbacks, TLV, and a packed [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47))
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): one DAPM graph node (a DAC, ADC, mux, supply, or audio-interface endpoint) with its power state and event callback
- [`'\<struct snd_soc_dapm_route\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473): one directed edge from [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) to [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), optionally gated by a named [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473)
- [`'\<struct snd_soc_jack\>':'include/sound/soc-jack.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80): the jack object whose [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask the codec updates when headset insertion or buttons change
- [`'\<struct regmap_config\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408): the register-map geometry (register/value widths, volatile and readable predicates, defaults, cache type)

### rt722-sdca worked example (codecs/rt722-sdca.c, rt722-sdca-sdw.c)

- [`'soc_sdca_dev_rt722':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090): the codec's [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), supplying controls, widgets, routes, probe, and jack hook
- [`'rt722_sdca_controls':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697): the mixer table of volume, mute, and boost controls over SDCA function units
- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the widget array (HP/SPK outputs, mic and DMIC inputs, FU function-unit DAC/ADC nodes, PDE supplies, AIF endpoints)
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the route array wiring the DAPM endpoints to the function units and pins
- [`'\<rt722_sdca_probe\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1075): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67); records the component pointer and resumes the device
- [`'\<rt722_sdca_set_jack_detect\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L321): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op; stores the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) and arms detection via [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293)
- [`'\<rt722_sdca_set_gain_get\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419) / [`'\<rt722_sdca_set_gain_put\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L348): the get/put callbacks shared by the volume controls; read and write the SDCA gain register through the codec regmap
- [`'rt722_sdca_dai':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries registered with the component (`aif1`, `aif2`, `aif3`)
- [`'\<rt722_sdca_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299): allocate the [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18), store it as drvdata, and call [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'rt722_sdca_regmap':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L195): the [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit register, 16-bit value, MAPLE cache) for the SoundWire register space
- [`'\<rt722_sdca_sdw_probe\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416): the SoundWire slave probe; builds the regmap and hands it to [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299)
- [`'\<struct rt722_sdca_priv\>':'sound/soc/codecs/rt722-sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18): the codec's private state (regmap, SoundWire slave, jack, mute flags) reached through drvdata

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC codec class driver guide covering the component, its controls, DAPM, and DAI
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget and route model the codec's [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) build
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack abstraction the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback drives
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA control API behind [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and the info/get/put callbacks
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the rt722-sdca DAIs join

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A codec specializes the generic component by populating the description fields of [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). Each field is optional, and the core skips an empty one. The RT722 fills the controls, widgets, routes, probe, jack, and endianness fields and leaves the rest at their defaults.

| component-driver field | type | rt722-sdca value |
|------------------------|------|------------------|
| `controls` / `num_controls` | `const struct snd_kcontrol_new *` | rt722_sdca_controls |
| `dapm_widgets` / `num_dapm_widgets` | `const struct snd_soc_dapm_widget *` | rt722_sdca_dapm_widgets |
| `dapm_routes` / `num_dapm_routes` | `const struct snd_soc_dapm_route *` | rt722_sdca_audio_map |
| `probe` | `int (*)(struct snd_soc_component *)` | rt722_sdca_probe |
| `set_jack` | `int (*)(struct snd_soc_component *, struct snd_soc_jack *, void *)` | rt722_sdca_set_jack_detect |
| `endianness` | `unsigned int :1` | 1 |

### controls and num_controls

[`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) points at an array of [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`num_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L72) gives its length. According to the comment on the field, the controls are added after [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs, so the codec can finish any hardware setup the control callbacks depend on before userspace can touch them. [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) passes the array to [`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501), which registers each entry as an ALSA mixer element on the card.

### dapm_widgets and num_dapm_widgets

[`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) is an array of [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) templates, usually built with the `SND_SOC_DAPM_*` constructor macros. Each entry becomes one node in the codec's power-management graph, whether a DAC, an ADC, a mux, a supply, or an audio-interface endpoint. [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) instantiates them through [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) before the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs.

### dapm_routes and num_dapm_routes

[`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) is an array of [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), each naming a [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), an optional [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and a [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) by widget name. [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) connects them with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) after the controls are added, so every widget a route references already exists in the graph.

### set_jack and get_jack_type

[`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is the entry point through which a machine driver registers a [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) with the codec, and the core reaches it through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190), which returns `-ENOTSUPP` when the codec leaves the field NULL. The codec stores the jack pointer and arms its insertion-detection logic so a later interrupt can report status changes through the jack object.

### probe and endianness

[`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs once from [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) after the widgets are created but before the controls and routes are added, so the codec can resume the device and finish setup. [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) is a one-bit field. According to the comment on the field, a component sets it when it sits behind a bus that abstracts away PCM endian (I2S, SLIMbus, SoundWire) or for which endian has no meaning, and the core then ensures both LE and BE variants of each used format are present.

## DETAILS

### The component driver gathers the codec description

A codec writes one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). The leading fields are the description the codec layer reads, and the trailing fields are the callbacks the PCM and power paths invoke. The header groups the description first:

```c
/* include/sound/soc-component.h:67 */
struct snd_soc_component_driver {
	const char *name;

	/* Default control and setup, added after probe() is run */
	const struct snd_kcontrol_new *controls;
	unsigned int num_controls;
	const struct snd_soc_dapm_widget *dapm_widgets;
	unsigned int num_dapm_widgets;
	const struct snd_soc_dapm_route *dapm_routes;
	unsigned int num_dapm_routes;

	int (*probe)(struct snd_soc_component *component);
	void (*remove)(struct snd_soc_component *component);
	int (*suspend)(struct snd_soc_component *component);
	int (*resume)(struct snd_soc_component *component);
	...
	int (*set_jack)(struct snd_soc_component *component,
			struct snd_soc_jack *jack,  void *data);
	int (*get_jack_type)(struct snd_soc_component *component);
	...
	unsigned int endianness:1;
	unsigned int legacy_dai_naming:1;
	...
};
```

The RT722 fills exactly the six fields the page tracks and leaves everything else at its zero default, so a codec driver stays mostly description and very little code:

```c
/* sound/soc/codecs/rt722-sdca.c:1090 */
static const struct snd_soc_component_driver soc_sdca_dev_rt722 = {
	.probe = rt722_sdca_probe,
	.controls = rt722_sdca_controls,
	.num_controls = ARRAY_SIZE(rt722_sdca_controls),
	.dapm_widgets = rt722_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt722_sdca_dapm_widgets),
	.dapm_routes = rt722_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt722_sdca_audio_map),
	.set_jack = rt722_sdca_set_jack_detect,
	.endianness = 1,
};
```

The runtime counterpart is [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), allocated at registration. It points back at the static driver, holds the codec's [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L226), owns the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and carries the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L237) graph context the widgets attach to:

```c
/* include/sound/soc-component.h:207 */
struct snd_soc_component {
	const char *name;
	const char *name_prefix;
	struct device *dev;
	struct snd_soc_card *card;

	unsigned int active;

	unsigned int suspended:1; /* is in suspend PM state */

	struct list_head list;
	struct list_head card_aux_list; /* for auxiliary bound components */
	struct list_head card_list;

	const struct snd_soc_component_driver *driver;

	struct list_head dai_list;
	int num_dai;

	struct regmap *regmap;
	int val_bytes;

	struct mutex io_mutex;

	/* attached dynamic objects */
	struct list_head dobj_list;
	...
	struct snd_soc_dapm_context *dapm;
	...
};
```

The two structs sit one above the other with the runtime component's driver field pointing back up at the const descriptor, whose description fields carry their after-probe() and before-probe() timing:

```
    snd_soc_component_driver layout: fields then callbacks
    ──────────────────────────────────────────────────────
    struct snd_soc_component_driver   (const, shared)
    ┌──────────────────────────────────────────────┐
    │ name                                         │
    │ controls      num_controls    after probe()  │
    │ dapm_widgets  num_dapm_widgets before probe()│
    │ dapm_routes   num_dapm_routes  after probe() │
    │ probe remove suspend resume   callbacks      │
    │ set_jack  get_jack_type        callbacks     │
    │ endianness:1  legacy_dai_naming:1            │
    └──────────────────────┬───────────────────────┘
                           │ component->driver back pointer
                           ▼
    struct snd_soc_component   (runtime, per registration)
    ┌──────────────────────────────────────────────┐
    │ dev   card   active   suspended:1            │
    │ driver  ─────▶ the const descriptor above    │
    │ dai_list   num_dai                           │
    │ regmap     val_bytes                         │
    │ dapm  ─────▶ graph the widgets attach to     │
    └──────────────────────────────────────────────┘
```

### Registration binds the driver and the private data

The codec's bus probe allocates the private struct, stores it on the device, and registers the component. [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) does this for the RT722. It calls [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) for the [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18), stashes the SoundWire slave and the regmap into it, hands the pointer to the device with [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h), and finally registers the component and DAIs:

```c
/* sound/soc/codecs/rt722-sdca.c:1299 */
int rt722_sdca_init(struct device *dev, struct regmap *regmap, struct sdw_slave *slave)
{
	struct rt722_sdca_priv *rt722;

	rt722 = devm_kzalloc(dev, sizeof(*rt722), GFP_KERNEL);
	if (!rt722)
		return -ENOMEM;

	dev_set_drvdata(dev, rt722);
	rt722->slave = slave;
	rt722->regmap = regmap;

	regcache_cache_only(rt722->regmap, true);
	...
	return devm_snd_soc_register_component(dev,
			&soc_sdca_dev_rt722, rt722_sdca_dai, ARRAY_SIZE(rt722_sdca_dai));
}
```

[`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) wraps the bare [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) in a devres action so the component is unregistered automatically when the device goes away. Inside the registration path, [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) allocates the DAPM context, initialises the list heads and the IO mutex, and records the [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221) pointer that every later lookup of the description goes through:

```c
/* sound/soc/soc-core.c:2850 */
int snd_soc_component_initialize(struct snd_soc_component *component,
				 const struct snd_soc_component_driver *driver,
				 struct device *dev)
{
	component->dapm = snd_soc_dapm_alloc(dev);
	if (!component->dapm)
		return -ENOMEM;

	INIT_LIST_HEAD(&component->dai_list);
	INIT_LIST_HEAD(&component->dobj_list);
	INIT_LIST_HEAD(&component->card_list);
	INIT_LIST_HEAD(&component->list);
	INIT_LIST_HEAD(&component->card_aux_list);
	mutex_init(&component->io_mutex);
	...
	component->dev		= dev;
	component->driver	= driver;
	...
	return 0;
}
```

### soc_probe_component instantiates the description

Registration links the component to the card, but the description in the driver becomes live only when the card binds and [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) runs. The ordering is fixed and matches the comment on the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71) field. The widgets are created first, then the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) runs, then the controls and routes are added:

```c
/* sound/soc/soc-core.c:1602 */
	snd_soc_dapm_init(dapm, card, component);

	ret = snd_soc_dapm_new_controls(dapm,
					component->driver->dapm_widgets,
					component->driver->num_dapm_widgets);
	...
	ret = snd_soc_component_probe(component);
	if (ret < 0)
		goto err_probe;
	...
	ret = snd_soc_add_component_controls(component,
					     component->driver->controls,
					     component->driver->num_controls);
	if (ret < 0)
		goto err_probe;

	ret = snd_soc_dapm_add_routes(dapm,
				      component->driver->dapm_routes,
				      component->driver->num_dapm_routes);
	if (ret < 0)
		goto err_probe;
```

[`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) walks the widget array and builds one graph node per template under the DAPM mutex:

```c
/* sound/soc/soc-dapm.c:3932 */
int snd_soc_dapm_new_controls(struct snd_soc_dapm_context *dapm,
	const struct snd_soc_dapm_widget *widget,
	unsigned int num)
{
	int i;
	int ret = 0;

	snd_soc_dapm_mutex_lock_root(dapm);
	for (i = 0; i < num; i++) {
		struct snd_soc_dapm_widget *w = snd_soc_dapm_new_control_unlocked(dapm, widget);
		if (IS_ERR(w)) {
			ret = PTR_ERR(w);
			break;
		}
		widget++;
	}
	snd_soc_dapm_mutex_unlock(dapm);
	return ret;
}
```

[`snd_soc_add_component_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2501) registers the mixer table against the card so each [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) entry becomes a userspace-visible control:

```c
/* sound/soc/soc-core.c:2501 */
int snd_soc_add_component_controls(struct snd_soc_component *component,
	const struct snd_kcontrol_new *controls, unsigned int num_controls)
{
	struct snd_card *card = component->card->snd_card;

	return snd_soc_add_controls(card, component->dev, controls,
			num_controls, component->name_prefix, component);
}
```

[`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) then iterates the route array, adding one edge per [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) and accumulating any per-route error.

```
    soc_probe_component(): fixed instantiation order
    ────────────────────────────────────────────────
    ┌────────────────────────────────────────────────────────────┐
    │ 1  snd_soc_dapm_init             DAPM context              │
    ├────────────────────────────────────────────────────────────┤
    │ 2  snd_soc_dapm_new_controls  ◀── dapm_widgets             │
    ├────────────────────────────────────────────────────────────┤
    │ 3  snd_soc_component_probe        codec probe()            │
    ├────────────────────────────────────────────────────────────┤
    │ 4  snd_soc_add_component_controls ◀── controls             │
    ├────────────────────────────────────────────────────────────┤
    │ 5  snd_soc_dapm_add_routes     ◀── dapm_routes             │
    └────────────────────────────────────────────────────────────┘
```

### The DAPM widgets and routes describe the audio graph

The widget array is built from constructor macros. The RT722 array mixes pin endpoints ([`SND_SOC_DAPM_OUTPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L64), [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60)), power-supply nodes ([`SND_SOC_DAPM_SUPPLY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L308) for the SDCA PDE function units), DAC and ADC nodes with event callbacks ([`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279), [`SND_SOC_DAPM_ADC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290) for the FU function units), input muxes, and the audio-interface endpoints that bind to the DAI stream names:

```c
/* sound/soc/codecs/rt722-sdca.c:996 */
static const struct snd_soc_dapm_widget rt722_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("MIC2"),
	SND_SOC_DAPM_INPUT("LINE1"),
	SND_SOC_DAPM_INPUT("LINE2"),
	SND_SOC_DAPM_INPUT("DMIC1_2"),
	SND_SOC_DAPM_INPUT("DMIC3_4"),

	SND_SOC_DAPM_SUPPLY("PDE 23", SND_SOC_NOPM, 0, 0,
		rt722_sdca_pde23_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	...
	SND_SOC_DAPM_DAC_E("FU 21", NULL, SND_SOC_NOPM, 0, 0,
		rt722_sdca_fu21_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_DAC_E("FU 42", NULL, SND_SOC_NOPM, 0, 0,
		rt722_sdca_fu42_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_ADC_E("FU 36", NULL, SND_SOC_NOPM, 0, 0,
		rt722_sdca_fu36_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	...
	SND_SOC_DAPM_AIF_IN("DP1RX", "DP1 Headphone Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP2TX", "DP2 Headset Capture", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_IN("DP3RX", "DP3 Speaker Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP6TX", "DP6 DMic Capture", 0, SND_SOC_NOPM, 0, 0),
};
```

The route array names source/sink pairs by widget name. Each [`struct snd_soc_dapm_route`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) is a `{sink, control, source}` triple, and a NULL control means an unconditional edge. The RT722 map wires the playback DAC chain from the AIF endpoint out to the HP and SPK pins, and the capture chain from the mic and DMIC pins through the ADC muxes to the capture AIF endpoints:

```c
/* sound/soc/codecs/rt722-sdca.c:1043 */
static const struct snd_soc_dapm_route rt722_sdca_audio_map[] = {
	{"FU 42", NULL, "DP1RX"},
	{"FU 21", NULL, "DP3RX"},

	{"ADC 22 Mux", "MIC2", "MIC2"},
	{"ADC 22 Mux", "LINE1", "LINE1"},
	{"ADC 22 Mux", "LINE2", "LINE2"},
	{"ADC 24 Mux", "DMIC1", "DMIC1_2"},
	{"ADC 24 Mux", "DMIC2", "DMIC3_4"},
	...
	{"DP2TX", NULL, "FU 36"},
	{"DP6TX", NULL, "FU 113"},

	{"HP", NULL, "PDE 47"},
	{"HP", NULL, "FU 42"},
	{"SPK", NULL, "PDE 23"},
	{"SPK", NULL, "FU 21"},
};
```

The structure of one route entry is the type definition itself, where [`sink`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473), and [`source`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L473) are the three names the brace-initialiser fills:

```c
/* include/sound/soc-dapm.h:473 */
struct snd_soc_dapm_route {
	const char *sink;
	const char *control;
	const char *source;

	/* Note: currently only supported for links where source is a supply */
	int (*connected)(struct snd_soc_dapm_widget *source,
			 struct snd_soc_dapm_widget *sink);

	struct snd_soc_dobj dobj;
};
```

Each row below is one such triple assembled into the graph, playback running from a DP receive endpoint through a function unit out to the HP and SPK pins and capture running the mic and DMIC pins back through a mux to a DP transmit endpoint:

```
    rt722 DAPM graph: AIF endpoints fan out to pins
    ─────────────────────────────────────────────────
    playback  (AIF in)        function unit        pin
      DP1RX  ───────────────▶  FU 42  ───────────▶  HP
      DP3RX  ───────────────▶  FU 21  ───────────▶  SPK

    capture   pin / mux           function unit   AIF out
      MIC2  ─┐
      LINE1 ─┼▶ ADC 22 Mux ──▶  FU 36  ──────────▶  DP2TX
      LINE2 ─┘
      DMIC1_2 ─┐
      DMIC3_4 ─┴▶ ADC 24 Mux ─▶  FU 113 ──────────▶  DP6TX

    each row is one snd_soc_dapm_route {sink, ctl, source}
    the AIF names equal the DAI stream_name strings
```

### A control reaches the codec through drvdata and regmap

Each mixer control is a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47). Its [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) packs the register address and range, and its [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callbacks read and write the hardware. The RT722 control table builds these entries with the ASoC mixer macros. The headphone volume uses `SOC_DOUBLE_R_EXT_TLV`, which encodes the left and right SDCA volume register addresses, the range, and the shared [`rt722_sdca_set_gain_get`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419)/[`rt722_sdca_set_gain_put`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L348) callbacks:

```c
/* sound/soc/codecs/rt722-sdca.c:697 */
static const struct snd_kcontrol_new rt722_sdca_controls[] = {
	/* Headphone playback settings */
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_R), 0, 0x57, 0,
		rt722_sdca_set_gain_get, rt722_sdca_set_gain_put, out_vol_tlv),
	/* Headset mic capture settings */
	SOC_DOUBLE_EXT("FU0F Capture Switch", SND_SOC_NOPM, 0, 1, 1, 0,
		rt722_sdca_fu0f_capture_get, rt722_sdca_fu0f_capture_put),
	...
};
```

The get callback shows how a control reaches the codec hardware. It resolves the component from the kcontrol with [`snd_kcontrol_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14), then reads the codec's [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) back with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), and reads the left and right gain registers through the private [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) with [`regmap_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c):

```c
/* sound/soc/codecs/rt722-sdca.c:419 */
static int rt722_sdca_set_gain_get(struct snd_kcontrol *kcontrol,
		struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int read_l, read_r, ctl_l = 0, ctl_r = 0;
	unsigned int adc_vol_flag = 0;
	const unsigned int interval_offset = 0xc0;
	const unsigned int tendB = 0xa00;
	...
	regmap_read(rt722->regmap, mc->reg, &read_l);
	regmap_read(rt722->regmap, mc->rreg, &read_r);
	...
	ucontrol->value.integer.value[0] = ctl_l;
	ucontrol->value.integer.value[1] = ctl_r;

	return 0;
}
```

The two accessors that connect the control to its private data are [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356) and [`snd_soc_component_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L350), thin wrappers over the device drvdata:

```c
/* include/sound/soc-component.h:350 */
static inline void snd_soc_component_set_drvdata(struct snd_soc_component *c,
						 void *data)
{
	dev_set_drvdata(c->dev, data);
}

static inline void *snd_soc_component_get_drvdata(struct snd_soc_component *c)
{
	return dev_get_drvdata(c->dev);
}
```

The RT722 calls [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h) directly in [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299) before the component exists, and every later callback reads it back with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), which is why the codec never needs a separate pointer from the component to its state.

```
    A control get/put resolves to the codec register
    ─────────────────────────────────────────────────
    struct snd_kcontrol
    ┌─────────────────────────┐
    │ private_value ──────────┼──▶ struct soc_mixer_control
    │ chip  (snd_kcontrol_chip)│      reg   rreg  (L / R addr)
    └────────────┬────────────┘
                 ▼ snd_kcontrol_chip()
    struct snd_soc_component
    ┌─────────────────────────┐
    │ dev ────────────────────┼──▶ get_drvdata(dev)
    └────────────┬────────────┘
                 ▼ snd_soc_component_get_drvdata()
    struct rt722_sdca_priv
    ┌─────────────────────────┐
    │ regmap ─────────────────┼──▶ regmap_read(regmap,
    │ slave  hs_jack  mutes   │      mc->reg / mc->rreg)
    └─────────────────────────┘
```

### The private data struct holds the codec instance state

The [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) is the single object every component, control, DAPM, and jack callback dereferences. It holds the [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) used for register I/O, the SoundWire [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) the DAI hw_params op adds to a stream, the [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) pointer set by the jack hook, and the per-function-unit mute flags the DAPM and control callbacks toggle:

```c
/* sound/soc/codecs/rt722-sdca.h:18 */
struct  rt722_sdca_priv {
	struct regmap *regmap;
	struct snd_soc_component *component;
	struct sdw_slave *slave;
	struct sdw_bus_params params;
	bool hw_init;
	bool first_hw_init;
	struct mutex calibrate_mutex;
	struct mutex disable_irq_lock;
	bool disable_irq;
	/* For Headset jack & Headphone */
	unsigned int scp_sdca_stat1;
	unsigned int scp_sdca_stat2;
	struct snd_soc_jack *hs_jack;
	struct delayed_work jack_detect_work;
	struct delayed_work jack_btn_check_work;
	int jack_type;
	int jd_src;
	bool fu0f_dapm_mute;
	bool fu0f_mixer_l_mute;
	bool fu0f_mixer_r_mute;
	/* For DMIC */
	bool fu1e_dapm_mute;
	bool fu1e_mixer_mute[4];
	int hw_vid;
};
```

The same fields regroup into four bands by what they serve, register I/O and the SoundWire slave, bring-up state and locks, the jack and its detection work, and the per-function-unit mute flags:

```
    struct rt722_sdca_priv: grouped instance state
    ─────────────────────────────────────────────────
    ┌────────────────────────────────────────────────────────┐
    ├─ I/O and transport ────────────────────────────────────┤
    │ regmap        register access map                      │
    │ component      back pointer to the runtime component   │
    │ slave  params  SoundWire device and bus params         │
    ├─ bring-up and locks ───────────────────────────────────┤
    │ hw_init  first_hw_init  hw_vid                         │
    │ calibrate_mutex  disable_irq_lock  disable_irq         │
    ├─ jack and detection ───────────────────────────────────┤
    │ hs_jack        the snd_soc_jack set by set_jack        │
    │ jack_type  jd_src  scp_sdca_stat1 / stat2              │
    │ jack_detect_work  jack_btn_check_work                  │
    ├─ mute flags ───────────────────────────────────────────┤
    │ fu0f_dapm_mute  fu0f_mixer_l_mute  _r_mute             │
    │ fu1e_dapm_mute  fu1e_mixer_mute[4]                     │
    └────────────────────────────────────────────────────────┘
```

### The jack hook stores the jack and arms detection

[`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is reached from the machine layer through [`snd_soc_component_set_jack()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L190), which only forwards to the codec op when the field is set. The RT722 op reads its private data through [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), stores the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) pointer in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18), resumes the device, and arms the detection logic in [`rt722_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L293):

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

The jack object itself is small. [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) holds the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) bitmask the codec updates and the underlying [`struct snd_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/jack.h#L61) that reports input events to userspace:

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

### The regmap carries register I/O for the codec

A codec does register access through a [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35) rather than the bus directly. The map is built from a [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) that fixes the register and value widths and the cache behavior. The RT722 config declares a 32-bit register and 16-bit value space with a MAPLE-tree cache, the layout of the SoundWire register address built by [`SDW_SDCA_CTL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:195 */
static const struct regmap_config rt722_sdca_regmap = {
	.reg_bits = 32,
	.val_bits = 16,
	.readable_reg = rt722_sdca_readable_register,
	.volatile_reg = rt722_sdca_volatile_register,
	.max_register = 0x44ffffff,
	.reg_defaults = rt722_sdca_reg_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt722_sdca_reg_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};
```

The SoundWire slave probe is where the regmap is created and handed to the codec. [`rt722_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416) calls [`devm_regmap_init_sdw_mbq_cfg()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1226) with the config above, then passes the resulting map into [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299), which stores it in the private struct before registering the component:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:416 */
static int rt722_sdca_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap;

	/* Regmap Initialization */
	regmap = devm_regmap_init_sdw_mbq_cfg(&slave->dev, slave,
					      &rt722_sdca_regmap,
					      &rt722_mbq_config);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt722_sdca_init(&slave->dev, regmap, slave);
}
```

Because the RT722 builds its regmap in the bus probe and stores it on the device before [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) runs, the component is already able to do register I/O when its callbacks first fire, and the codec never needs the deferred [`snd_soc_component_init_regmap()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L367) path that a codec with a late-arriving map would use.

### The DAI array completes the codec

The component description and the DAI array are registered together. The RT722 declares three SoundWire interfaces in [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253), each a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and all three share one function pointer struct. The DAI [`stream_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) strings (`DP1 Headphone Playback`, `DP2 Headset Capture`, and so on) are the same names the [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255)/[`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265) widgets carry, which is how the DAI side of the codec and the DAPM graph join at the audio-interface endpoints. The component supplies the controls, widgets, routes, jack hook, and regmap; the DAI array supplies the streaming endpoints; and the private [`struct rt722_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) reached through drvdata ties every callback on both sides to the same instance state.

```
    DAI side and DAPM side join on the stream_name string
    ──────────────────────────────────────────────────────
    ┌────────────────────────┬───────────────────────┐
    │ snd_soc_dai_driver     │ AIF widget            │
    │ .stream_name           │ SND_SOC_DAPM_AIF_*    │
    ├────────────────────────┼───────────────────────┤
    │ DP1 Headphone Playback │ DP1RX   AIF_IN        │
    │ DP2 Headset Capture    │ DP2TX   AIF_OUT       │
    │ DP3 Speaker Playback   │ DP3RX   AIF_IN        │
    │ DP6 DMic Capture       │ DP6TX   AIF_OUT       │
    └────────────────────────┴───────────────────────┘
    aif1 / aif2 / aif3 share one snd_soc_dai_ops struct
```
