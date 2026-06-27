# DAPM widget kcontrols

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAPM widget kcontrol is an ALSA control whose put handler does two things at once. It writes the codec register the control names, then re-runs the DAPM power engine so the audio graph edge the control gates is connected or disconnected and the widgets feeding it power up or down. It differs from a plain card mixer control built with [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), whose [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) handler only writes the register and reports a change. The DAPM variants are built with [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336), [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351), [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369), and their relatives, each of which substitutes a DAPM-aware get/put pair ([`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453), [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578), [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725)) into a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47). A codec attaches such a control to a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) through the widget's [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555) and [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553) fields, and the put handler reaches the [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) records the control gates through the per-control [`struct dapm_kcontrol_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383). The Realtek rt722-sdca codec on x86 SoundWire is the worked example, attaching a [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) mux such as [`rt722_sdca_adc22_mux`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L766) to its capture-path widgets, while an Intel SOF machine driver adds a [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) per jack pin at the card level.

```
    SOC_DAPM_SINGLE("HPL Switch", reg, shift, 1, 0)
       │  builds a snd_kcontrol_new with
       │  .get = snd_soc_dapm_get_volsw  .put = snd_soc_dapm_put_volsw
       ▼
    struct snd_soc_dapm_widget  (snd_soc_dapm_mixer)
    ┌──────────────────────────────────────────────────────┐
    │  kcontrol_news ─▶ snd_kcontrol_new[ ]                │
    │  num_kcontrols                                       │
    │  kcontrols    ─▶ snd_kcontrol[ ]                     │
    │                     │ private_data                   │
    │                     ▼                                │
    │                  dapm_kcontrol_data                  │
    │                  { value, widget, paths }            │
    └──────────────────────────────────────────────────────┘
                          │  paths
                          ▼
       snd_soc_dapm_path  (source ──▶ this widget)
                          ▲
       userspace amixer write
                          │
                          ▼
    snd_soc_dapm_put_volsw
       1. dapm_test_bits + regmap write   (update register)
       2. dapm_mixer_update_power         (re-power the graph)
            dapm_connect_path(path, connect)
            dapm_power_widgets(card, ...)
```

## SUMMARY

A DAPM widget kcontrol is built by one of the [`SOC_DAPM_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330) macros, each expanding to a standard [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) initializer whose only difference from a plain card control is the get/put pair. [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336), [`SOC_DAPM_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330), [`SOC_DAPM_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L333), [`SOC_DAPM_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L345), and [`SOC_DAPM_SINGLE_VIRT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L339) install [`snd_soc_dapm_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3395) and [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) over a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) private value; [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) and [`SOC_DAPM_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L354) install [`snd_soc_dapm_get_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3542) and [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) over a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273); and [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) installs the [`snd_soc_dapm_info_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3638), [`snd_soc_dapm_get_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3670), and [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725) trio over a pin-name string.

The put handlers are what set a widget kcontrol apart. After computing the register value, [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) and [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) call [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) or [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634), the internals behind the exported [`snd_soc_dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2727) and [`snd_soc_dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2663). Those walk the [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) list attached to the control, flip each path's [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit through [`dapm_connect_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621), and call [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) to recompute which widgets carry a complete route. The per-control [`struct dapm_kcontrol_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383) holds the cached value and the path list, and the autodisable variants ([`SOC_DAPM_SINGLE_AUTODISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L357), [`SOC_DAPM_SINGLE_TLV_AUTODISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L362)) add a hidden [`snd_soc_dapm_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L454) supply widget that holds the register at its off value whenever the control reads zero, so the path is muted in hardware when DAPM powers it down.

## SPECIFICATIONS

The [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) graph and the kcontrols bound to it are a Linux kernel software construct with no standalone hardware specification. The register a widget kcontrol writes is defined by the codec datasheet, and on a SoundWire codec the register address is an SDCA control encoded as a function/entity address.

## LINUX KERNEL

### DAPM control macros (include/sound/soc-dapm.h)

- [`'\<SOC_DAPM_SINGLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336): one-field mixer switch over a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231); wraps [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) with the DAPM volsw pair
- [`'\<SOC_DAPM_DOUBLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330) / [`'\<SOC_DAPM_DOUBLE_R\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L333): stereo switch in one register, or in two registers
- [`'\<SOC_DAPM_SINGLE_TLV\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L345): single field with a dB TLV scale, for a gated gain stage
- [`'\<SOC_DAPM_SINGLE_VIRT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L339): single switch with no register, `reg = SND_SOC_NOPM`; gates a path purely in the graph
- [`'\<SOC_DAPM_ENUM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351): mux selector over a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273); wraps [`SOC_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L314) with the DAPM enum pair
- [`'\<SOC_DAPM_ENUM_EXT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L354): mux selector with caller-supplied get/put, for a virtual mux
- [`'\<SOC_DAPM_PIN_SWITCH\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369): boolean pin enable named `"<pin> Switch"`, added at card level
- [`'\<SOC_DAPM_SINGLE_AUTODISABLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L357) / [`'\<SOC_DAPM_SINGLE_TLV_AUTODISABLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L362): switches whose private value sets the [`autodisable`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) bit so a hidden supply widget mutes the register when the control reads zero
- [`'\<SND_SOC_DAPM_MUX\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129): widget initializer that takes one [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) control as its [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555)
- [`'\<SND_SOC_NOPM\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26): the `-1` register sentinel a virtual control uses

### DAPM mixer/switch handlers (soc-dapm.c)

- [`'\<snd_soc_dapm_get_volsw\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3395): read a DAPM mixer control, from the register when the widget is powered or from the cached value when it is not
- [`'\<snd_soc_dapm_put_volsw\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453): write a DAPM mixer control and re-power the path via [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680)
- [`'\<snd_soc_dapm_get_enum_double\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3542) / [`'\<snd_soc_dapm_put_enum_double\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578): read and write a DAPM mux control, the put re-powering via [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634)
- [`'\<snd_soc_dapm_info_pin_switch\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3638): report a pin switch as a one-element boolean control
- [`'\<snd_soc_dapm_get_pin_switch\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3670) / [`'\<snd_soc_dapm_put_pin_switch\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725): read and set a card-level pin connect state, calling [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) on the write

### Power-engine entry points (soc-dapm.c)

- [`'\<snd_soc_dapm_mixer_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2727) / [`'\<snd_soc_dapm_mux_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2663): locked wrappers a codec event handler may call to connect/disconnect a path and re-power
- [`'\<dapm_mixer_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680): walk the control's path list, set each path's connect state, run [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252)
- [`'\<dapm_mux_update_power\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634): connect the one path whose name matches the selected enum item, disconnect the rest, then re-power
- [`'\<dapm_connect_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621): set a [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) connect bit and mark its endpoints dirty
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): recompute complete routes and sequence widget power up/down

### Per-control data and binding (soc-dapm.c)

- [`'\<struct dapm_kcontrol_data\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383): per-control state, the cached value, the optional autodisable widget, and the [`paths`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383) list the control gates
- [`'\<dapm_kcontrol_data_alloc\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L706): allocate the per-control data and, for an autodisable control, create the hidden [`snd_soc_dapm_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L454) supply widget
- [`'\<dapm_kcontrol_set_value\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L901): cache a new control value; returns whether it changed
- [`'\<dapm_kcontrol_is_powered\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L871): test whether the autodisable widget is powered, deciding whether the get path reads the register or the cache
- [`'\<dapm_kcontrol_for_each_path\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L889): iterate the [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) list bound to a kcontrol
- [`'\<snd_soc_dapm_kcontrol_to_dapm\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L949): recover the [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) from a kcontrol
- [`'\<snd_soc_dapm_new_control_unlocked\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757): build a widget from a template, the path by which the autodisable supply widget is created

### Types (soc-dapm.h, soc.h)

- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): a graph node carrying [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555), [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553), and the instantiated [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L556) array
- [`'\<struct snd_soc_dapm_path\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486): a directed edge with a [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit a widget kcontrol gates
- [`'\<struct snd_soc_dapm_update\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572): the deferred register write the power sequence applies at the moment the widget power changes
- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the gating widgets are [`snd_soc_dapm_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L439), [`snd_soc_dapm_mixer`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L428), [`snd_soc_dapm_mux`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L426), and the hidden [`snd_soc_dapm_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L454)
- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): the private values of a DAPM switch and a DAPM mux

### rt722-sdca and SOF machine worked examples (codecs, intel/boards)

- [`'rt722_adc22_enum':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L754): the [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) declared over the mux register
- [`'rt722_sdca_adc22_mux':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L766): the [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) control bound to the ADC 22 mux widget
- [`'sof_controls':'sound/soc/intel/boards/sof_cs42l42.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_cs42l42.c#L116): the card control array with [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) entries for the jack pins

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget types, the mixer/mux controls, and the path graph
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): codec component guide, where DAPM controls and routes are registered
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the `"<name> Switch"` naming convention a pin switch follows
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the rt722-sdca capture path joins once its mux is connected

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A widget kcontrol presents the same ALSA control interface as any element ([`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)), and the macro that builds it chooses the callbacks. The table maps each [`SOC_DAPM_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330) macro to the put handler it installs and the power-engine call that handler makes.

| control macro | private value type | put handler | re-power call |
|---------------|--------------------|-------------|---------------|
| [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |
| [`SOC_DAPM_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |
| [`SOC_DAPM_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L333) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |
| [`SOC_DAPM_SINGLE_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L345) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |
| [`SOC_DAPM_SINGLE_VIRT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L339) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (`reg = SND_SOC_NOPM`) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |
| [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) | [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) | [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) | [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) |
| [`SOC_DAPM_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L354) | [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) | caller-supplied | caller-supplied |
| [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) | pin-name string | [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725) | [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) |
| [`SOC_DAPM_SINGLE_AUTODISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L357) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (`autodisable = 1`) | [`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) | [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) |

### The volsw macro family

[`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336), [`SOC_DAPM_DOUBLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L330), and [`SOC_DAPM_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L333) are thin wrappers around [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) and its double variants that substitute the DAPM get/put pair, so a DAPM switch carries the same [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) private value a card control would:

```c
/* include/sound/soc-dapm.h:330 */
#define SOC_DAPM_DOUBLE(xname, reg, lshift, rshift, max, invert) \
	SOC_DOUBLE_EXT(xname, reg, lshift, rshift, max, invert, \
		       snd_soc_dapm_get_volsw, snd_soc_dapm_put_volsw)
#define SOC_DAPM_DOUBLE_R(xname, lreg, rreg, shift, max, invert) \
	SOC_DOUBLE_R_EXT(xname, lreg, rreg, shift, max, invert, \
			 snd_soc_dapm_get_volsw, snd_soc_dapm_put_volsw)
#define SOC_DAPM_SINGLE(xname, reg, shift, max, invert) \
	SOC_SINGLE_EXT(xname, reg, shift, max, invert, \
		       snd_soc_dapm_get_volsw, snd_soc_dapm_put_volsw)
#define SOC_DAPM_SINGLE_VIRT(xname, max) \
	SOC_DAPM_SINGLE(xname, SND_SOC_NOPM, 0, max, 0)
```

### The enum and pin-switch macros

[`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) wraps [`SOC_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L314) with the DAPM enum pair, [`SOC_DAPM_ENUM_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L354) leaves the get/put to the caller for a virtual mux, and [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) hard-codes its info/get/put trio and stores the pin name as the private value:

```c
/* include/sound/soc-dapm.h:351 */
#define SOC_DAPM_ENUM(xname, xenum) \
	SOC_ENUM_EXT(xname, xenum, snd_soc_dapm_get_enum_double, \
		     snd_soc_dapm_put_enum_double)
#define SOC_DAPM_ENUM_EXT(xname, xenum, xget, xput) \
	SOC_ENUM_EXT(xname, xenum, xget, xput)
```

```c
/* include/sound/soc-dapm.h:369 */
#define SOC_DAPM_PIN_SWITCH(xname) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname " Switch", \
	.info = snd_soc_dapm_info_pin_switch, \
	.get = snd_soc_dapm_get_pin_switch, \
	.put = snd_soc_dapm_put_pin_switch, \
	.private_value = (unsigned long)xname }
```

### The autodisable macros

[`SOC_DAPM_SINGLE_AUTODISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L357) spells out its initializer rather than wrapping [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234), because it passes 1 as the last argument of [`SOC_SINGLE_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L51) to set the [`autodisable`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) bit in the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231):

```c
/* include/sound/soc-dapm.h:357 */
#define SOC_DAPM_SINGLE_AUTODISABLE(xname, reg, shift, max, invert) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.info = snd_soc_info_volsw, \
	.get = snd_soc_dapm_get_volsw, .put = snd_soc_dapm_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(reg, shift, 0, max, invert, 1) }
```

## DETAILS

### The widget carries the controls

A [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) is a graph node, and the fields that bind kcontrols to it are [`kcontrol_news`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L555), the const array of [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) descriptors the driver supplies; [`num_kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L553), their count; and [`kcontrols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L556), the instantiated [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) array the core fills in:

```c
/* include/sound/soc-dapm.h:516 */
struct snd_soc_dapm_widget {
	enum snd_soc_dapm_type id;
	const char *name;			/* widget name */
	...
	/* dapm control */
	int reg;				/* negative reg = no direct dapm */
	unsigned char shift;			/* bits to shift */
	unsigned int mask;			/* non-shifted mask */
	unsigned int on_val;			/* on state value */
	unsigned int off_val;			/* off state value */
	unsigned char power:1;			/* block power status */
	...
	/* kcontrols that relate to this widget */
	int num_kcontrols;
	const struct snd_kcontrol_new *kcontrol_news;
	struct snd_kcontrol **kcontrols;
	struct snd_soc_dobj dobj;

	/* widget input and output edges */
	struct list_head edges[2];
	...
};
```

A mux widget such as [`SND_SOC_DAPM_MUX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L129) takes exactly one [`SOC_DAPM_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L351) control, and a mixer widget takes one [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) per input. The [`edges`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L559) lists hold the input and output [`struct snd_soc_dapm_path`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L486) edges, and it is the subset the control gates that the put handler connects and disconnects.

### The per-control data structure

The connection between a kcontrol and its paths is a [`struct dapm_kcontrol_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383) stored in the kcontrol's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70). It caches the control's [`value`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383) so the get path can answer without touching the register when the widget is unpowered, holds the optional autodisable [`widget`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383), and anchors the [`paths`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L383) list:

```c
/* sound/soc/soc-dapm.c:383 */
struct dapm_kcontrol_data {
	unsigned int value;
	struct snd_soc_dapm_widget *widget;
	struct list_head paths;
	struct snd_soc_dapm_widget_list *wlist;
};
```

[`dapm_kcontrol_data_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L706) allocates it when the kcontrol is created and decides, from the widget [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) and the [`autodisable`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) bit, whether to build the hidden supply widget:

```c
/* sound/soc/soc-dapm.c:706 */
	switch (widget->id) {
	case snd_soc_dapm_switch:
	case snd_soc_dapm_mixer:
	case snd_soc_dapm_mixer_named_ctl:
		mc = (struct soc_mixer_control *)kcontrol->private_value;

		if (mc->autodisable) {
			struct snd_soc_dapm_widget template;
			...
			template.off_val = mc->invert ? mc->max : 0;
			template.on_val = template.off_val;
			template.id = snd_soc_dapm_kcontrol;
			template.name = name;

			data->value = template.on_val;

			data->widget =
				snd_soc_dapm_new_control_unlocked(widget->dapm,
				&template);
			...
		}
		break;
```

The template's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517) is [`snd_soc_dapm_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L454), which [`snd_soc_dapm_new_control_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3757) treats as a supply widget. According to the comment beside the enum value it is the "Auto-disabled kcontrol" widget, and its [`off_val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L532) equals the muted register value, so whenever DAPM powers this hidden widget down it writes the off value into the real register and the gain or switch is silenced in hardware even though the userspace control still reads its set value.

```
    Autodisable: a hidden snd_soc_dapm_kcontrol supply mutes the reg
    ────────────────────────────────────────────────────────────────

    struct snd_kcontrol
    ┌──────────────────────┐
    │ private_data         │
    └──────────┬───────────┘
               ▼
    struct dapm_kcontrol_data
    ┌──────────────────────┐
    │ value   (cached)     │
    │ paths   (gated edges)│
    │ widget ───────────┐  │   only for autodisable switch /
    └───────────────────┼──┘   mixer / mixer_named_ctl controls
                        ▼
    struct snd_soc_dapm_widget  (id = snd_soc_dapm_kcontrol, a supply)
    ┌───────────────────────────────────────────────┐
    │ off_val = invert ? max : 0   (the muted code) │
    │ on_val  = off_val                             │
    └───────────────────────┬───────────────────────┘
                            ▼  DAPM powers this widget down
                  writes off_val into the real codec register
                  → path is silenced in hardware while the
                    userspace control still reads its set value
```

### put_volsw writes then re-powers

[`snd_soc_dapm_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3453) recovers the DAPM context with [`snd_soc_dapm_kcontrol_to_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L949), decodes the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), computes the connect state, caches the value with [`dapm_kcontrol_set_value()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L901), and tests whether the register needs changing with [`dapm_test_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L999):

```c
/* sound/soc/soc-dapm.c:3453 */
int snd_soc_dapm_put_volsw(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_dapm_context *dapm = snd_soc_dapm_kcontrol_to_dapm(kcontrol);
	...
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	int reg = mc->reg;
	unsigned int shift = mc->shift;
	...
	val = (ucontrol->value.integer.value[0] & mask);
	connect = !!val;
	...
	change = dapm_kcontrol_set_value(kcontrol, val | (rval << width));

	if (reg != SND_SOC_NOPM) {
		val = val << shift;
		rval = rval << mc->rshift;

		reg_change = dapm_test_bits(dapm, reg, mask << shift, val);
		...
	}

	if (change || reg_change) {
		if (reg_change) {
			...
			update.kcontrol = kcontrol;
			update.reg = reg;
			update.mask = mask << shift;
			update.val = val;
			pupdate = &update;
		}
		ret = dapm_mixer_update_power(card, kcontrol, pupdate, connect, rconnect);
	}

	snd_soc_dapm_mutex_unlock(card);
	...
	return change;
}
```

The register write is not issued here. The handler packages the register, mask, and value into a [`struct snd_soc_dapm_update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572) and hands it to [`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680), which performs the write at the precise point in the power sequence when the widget power transitions, so the register and the graph never disagree. A [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26) register, as a [`SOC_DAPM_SINGLE_VIRT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L339) control uses, skips the register half and updates only the graph. The handler returns `change`, the cached-value change flag, so userspace sees an event whenever the logical value moved even if no register bit did.

### dapm_mixer_update_power connects the paths

[`dapm_mixer_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2680) walks the control's gated edges, sets each edge's connect state with [`dapm_connect_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621), and runs [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once:

```c
/* sound/soc/soc-dapm.c:2680 */
static int dapm_mixer_update_power(struct snd_soc_card *card,
				   struct snd_kcontrol *kcontrol,
				   struct snd_soc_dapm_update *update,
				   int connect, int rconnect)
{
	struct snd_soc_dapm_path *path;
	int found = 0;

	snd_soc_dapm_mutex_assert_held(card);

	/* find dapm widget path assoc with kcontrol */
	dapm_kcontrol_for_each_path(path, kcontrol) {
		...
		if (found && rconnect >= 0)
			dapm_connect_path(path, rconnect, "mixer update");
		else
			dapm_connect_path(path, connect, "mixer update");
		found = 1;
	}

	if (found)
		dapm_power_widgets(card, SND_SOC_DAPM_STREAM_NOP, update);

	return found;
}
```

[`dapm_connect_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2621) only flips the [`connect`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L503) bit and marks both endpoint widgets dirty. [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) computes the consequence, rescanning the card for complete routes, building power-up and power-down lists, and running the sequences. The [`update`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L572) passed through is applied between powering widgets down and up, which is how the deferred register write lands at the safe moment.

```
    dapm_mixer_update_power: one control drives every gated path
    ────────────────────────────────────────────────────────────

                     ┌──────────────────┐
                     │ mixer kcontrol   │
                     │ connect = !!val  │
                     └────────┬─────────┘
            dapm_kcontrol_for_each_path (every gated edge)
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
       ┌─────────┐       ┌─────────┐       ┌─────────┐
       │ path A  │       │ path B  │       │ path C  │
       │ connect │       │ connect │       │ connect │
       └─────────┘       └─────────┘       └─────────┘
        every path set to the SAME connect bit, then one
        dapm_power_widgets() pass recomputes complete routes
```

### put_enum_double selects one path

[`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578) is the mux equivalent. It validates the item against the [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), translates the item to its register value with [`snd_soc_enum_item_to_val()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1314), caches it, and calls [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) with the chosen item:

```c
/* sound/soc/soc-dapm.c:3578 */
int snd_soc_dapm_put_enum_double(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_dapm_context *dapm = snd_soc_dapm_kcontrol_to_dapm(kcontrol);
	struct snd_soc_card *card = dapm->card;
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;
	unsigned int *item = ucontrol->value.enumerated.item;
	...
	if (item[0] >= e->items)
		return -EINVAL;

	val = snd_soc_enum_item_to_val(e, item[0]) << e->shift_l;
	mask = e->mask << e->shift_l;
	...
	change = dapm_kcontrol_set_value(kcontrol, val);

	if (e->reg != SND_SOC_NOPM)
		reg_change = dapm_test_bits(dapm, e->reg, mask, val);

	if (change || reg_change) {
		if (reg_change) {
			update.kcontrol = kcontrol;
			update.reg = e->reg;
			update.mask = mask;
			update.val = val;
			pupdate = &update;
		}
		ret = dapm_mux_update_power(card, kcontrol, pupdate, item[0], e);
	}

	snd_soc_dapm_mutex_unlock(card);
	...
	return change;
}
```

Where the mixer connects every gated path to the same value, [`dapm_mux_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2634) connects exactly one. It compares each path's [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L489) against the [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) entry for the selected item, connects that path, and disconnects the others, which is exactly the behavior of a selector. The Realtek RT722 worked example declares [`rt722_adc22_enum`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L754) over its mux register and binds it to the `"ADC 22 Mux"` widget through [`rt722_sdca_adc22_mux`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L766), so writing the `"ADC 22 Mux"` control runs [`snd_soc_dapm_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3578), connects the one capture path the selection names, and re-powers the ADC and its supply. An Intel SOF machine driver instead registers [`SOC_DAPM_PIN_SWITCH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L369) controls in its card control array, so toggling `"Headphone Switch"` runs [`snd_soc_dapm_put_pin_switch()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3725), flips the jack pin's connected state, and calls [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) to settle power across the card.

```
    dapm_mux_update_power: the selected item connects exactly one path
    ──────────────────────────────────────────────────────────────────

      selected item ▶ texts[item]   (compared to each path->name)

    ┌──────────────┬──────────────────┬──────────┐
    │ path->name   │ matches texts[i]?│ connect  │
    ├──────────────┼──────────────────┼──────────┤
    │ "MIC1"       │   no             │    0     │
    │ "MIC2"       │   yes (selected) │    1     │
    │ "LINE"       │   no             │    0     │
    └──────────────┴──────────────────┴──────────┘
        one path on, the rest off — a selector; then one
        dapm_power_widgets() pass re-powers the chosen branch
```
