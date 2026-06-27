# SoundWire SDCA microphone

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A SoundWire SDCA (SoundWire Device Class for Audio) codec presents a microphone as a Microphone Array Function whose firmware-described topology type is [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) or [`SDCA_FUNCTION_TYPE_SIMPLE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L76), the codec decimates the PDM stream internally and ships PCM over a SoundWire capture data port, and the kernel drives that mic through one capture-only [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) on the codec component, joined to a SoundWire stream by [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) at hw_params time. The worked example is the standalone DMIC peripheral driver [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c), a wholly separate SoundWire device (part id 0x1712) registered by [`rt712_sdca_dmic_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L968) and bound through a [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) named [`rt712_sdca_dmic_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L941), whose single DAI [`rt712_sdca_dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L737) carries the `DP2 Capture` stream and whose [`rt712_sdca_dmic_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630) programs SoundWire data port 2 and the [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) clock sources by a [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) write. On the machine side the Intel MTL/LNL SoundWire card adds a generic SoundWire DMIC with the helper [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24), which [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) passes as the `init` of the back-end link binding the PCH DMIC CPU DAI to the generic `dmic-hifi` codec.

```
    SDCA microphone path: function ─▶ capture port ─▶ CPU DAI ─▶ PCM
    ─────────────────────────────────────────────────────────────────

    SDCA SMART_MIC / SIMPLE_MIC Function  (firmware-described topology)
    ┌───────────────────────────────────────────────────────────┐
    │  DMIC1 ─┐                                                 │
    │  DMIC2 ─┴─▶ ADC mux ─▶ FU 1E (volume/mute) ─▶ IT/OT 26   │
    │            powered by PDE 11    clock CS1F/CS1C           │
    └───────────────────────────┬───────────────────────────────┘
                                ▼  codec decimates PDM ─▶ PCM
                       SoundWire DP capture port  (DP2 here)
                                │  SoundWire frame
                                ▼
    codec capture DAI  rt712_sdca_dmic_dai  "rt712-sdca-dmic-aif1"
       stream "DP2 Capture"  channels_max 4   ops rt712_sdca_dmic_ops
                                │  set_stream / hw_params
                                ▼  sdw_stream_add_slave()
                          CPU DAI (SOF ALH) ─▶ capture PCM (front end)


    Two ways an SDCA mic reaches a card
    ───────────────────────────────────

    standalone DMIC peripheral             machine generic DMIC link
    rt712-sdca-dmic.c (part 0x1712)        asoc_sdw_dmic_init (PCH PDM)
    ┌──────────────────────────┐           ┌──────────────────────────┐
    │ own sdw_driver + slave   │           │ create_dmic_dailinks ──▶ │
    │ own regmaps + component  │           │ asoc_sdw_init_simple_... │
    │ DP2 FU1E x4 capture      │           │ "DMIC01 Pin" ─▶ dmic-hifi│
    │ FUNC_NUM_MIC_ARRAY only  │           │ init = asoc_sdw_dmic_init│
    └──────────────────────────┘           └──────────────────────────┘
```

## SUMMARY

A SoundWire SDCA peripheral exposes one or more independent audio Functions, and a microphone is the Function whose [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) topology code is [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) (a smart microphone with acoustic triggers) or its subset [`SDCA_FUNCTION_TYPE_SIMPLE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L76). The firmware describes the Function's internal topology (input terminals from the PDM transducers, a feature unit for volume and mute, a power-domain entity, a clock source, an output terminal to the data port) and the kernel can read the whole tree into a [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), but the rt712 driver hardcodes the function, entity, and control ids in its header and reaches each control by the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address that packs a Function Number, Entity, Control Selector, and channel into one 32-bit SoundWire register address. The codec decimates the one-bit oversampled PDM internally and presents PCM on a SoundWire capture data port, so to the rest of ASoC the mic is a capture-only codec DAI rather than a PCH PDM back end.

The standalone DMIC driver in [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c) is a complete SoundWire peripheral driver for a device that exposes only the microphone Function. It binds on its own part ids through [`rt712_sdca_dmic_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L870) (0x1712/0x1713/0x1716/0x1717, distinct from the combined codec's 0x712 family), and [`rt712_sdca_dmic_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L946) builds the MBQ and single-byte regmaps and calls [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752), which allocates the private data [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14), stores the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and both regmaps, and registers the component [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L605). The slave ops [`rt712_sdca_dmic_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L941) fill only [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), there is no jack interrupt callback, so [`rt712_sdca_dmic_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L827) advertises the single source port (port 2) and [`rt712_sdca_dmic_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L808) runs the first-attach hardware init [`rt712_sdca_dmic_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L178) when the slave reports attached. The single DAI [`rt712_sdca_dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L737) points at [`rt712_sdca_dmic_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L730), whose [`rt712_sdca_dmic_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630) fixes the SoundWire port number to 2, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), and writes the sample rate to the two clock sources, and whose [`rt712_sdca_dmic_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L710) removes it with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228).

The same SDCA Microphone Function appears on the combined RT712 codec as a second component on the one SoundWire device, registered only when the parsed SDCA inventory lists a microphone. The main driver's [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) registers [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) only when [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96) reports [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55), which [`sdca_device_quirk_rt712_vb()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L50) returns true for only when the cached [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) inventory contains a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) Function. The broad RT712 codec, its jack and amplifier paths, the dual regmaps, and the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addressing it shares with the DMIC are documented separately; this page covers the microphone sub-function and the standalone DMIC peripheral.

The machine side adds a SoundWire card's DMIC link through one helper. [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) is the back-end-link `init` callback that adds a card-level `SoC DMIC` microphone widget and a route to the codec's `DMic` input, and [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) in the Intel [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine driver builds the two PCH DMIC back-end links through [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320), passing [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) as the `init` of the first link.

## SPECIFICATIONS

The microphone Function type is one code of [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72), whose kerneldoc cites "SDCA specification v1.0a Section 5.1.2" for the Function Type codes. The comment names [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) a "Smart microphone with acoustic triggers" and [`SDCA_FUNCTION_TYPE_SIMPLE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L76) a "Subset of SmartMic", and records that SIMPLE_MIC is "NOT defined in SDCA 1.0a, but they were defined in earlier drafts and are planned for 1.1". The on-wire control address that reaches every microphone control follows the MIPI SoundWire Device Class for Audio (SDCA) control-address format layered on the MIPI SoundWire bus, encoded by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), whose header comment reproduces the v1.2 SDCA address mapping the macro implements. These MIPI documents are membership-gated, so the encoding here is described from the kernel header rather than the specification text. The microphone Function the rt712 DMIC driver names is the single SDCA function number [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) (0x02). The sample formats and rates the DMIC DAI declares (S16_LE, S20_3LE, S24_LE at 16/32/44.1/48/96/192 kHz) and the SoundWire stream transport that carries them are defined by their respective standards.

## LINUX KERNEL

### SDCA microphone Function type (sdca_function.h)

- [`'\<enum sdca_function_type\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72): the SDCA Function topology codes; a microphone is [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) (0x03) or [`SDCA_FUNCTION_TYPE_SIMPLE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L76) (0x04), distinct from [`SDCA_FUNCTION_TYPE_SPEAKER_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L77) (0x05) and the jack/amp types
- [`'\<struct sdca_function_data\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419): the generic parsed-Function model a microphone Function would expand into; the rt712 DMIC driver hardcodes its function/entity/control ids instead of consuming this, but the combined codec reads the cached inventory of these to decide whether a mic is present
- [`'\<sdca_device_quirk_match\>':'sound/soc/sdca/sdca_device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96): test a peripheral against a known SDCA quirk; [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) dispatches to [`sdca_device_quirk_rt712_vb()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L50), which scans the cached Function inventory for a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) Function

### Standalone DMIC peripheral driver (rt712-sdca-dmic.c)

- [`'rt712_sdca_dmic_sdw_driver':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L968): the standalone [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) for the DMIC sub-function, registered with [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) and named `rt712-sdca-dmic`
- [`'rt712_sdca_dmic_id':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L870): the four-entry match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x1712, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) and its 0x1713/0x1716/0x1717 siblings, distinct part ids from the combined codec's 0x712 family
- [`'\<struct rt712_sdca_dmic_priv\>':'sound/soc/codecs/rt712-sdca-dmic.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14): the per-device state of the DMIC peripheral, holding the two [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L15)/[`mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L16) handles, the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L18), the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L17), the [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L19)/[`first_hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L20) flags, and the four-channel mute cache [`fu1e_mixer_mute`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L23)
- [`'rt712_sdca_dmic_slave_ops':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L941): the DMIC [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) with only [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), no jack [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<rt712_sdca_dmic_sdw_probe\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L946): builds the MBQ and single-byte regmaps with [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) and [`devm_regmap_init_sdw()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196), then calls [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752)
- [`'\<rt712_sdca_dmic_init\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752): allocates the [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14), stores the slave and regmaps, starts each regmap cache-only, initialises the four mute flags, and registers the component
- [`'\<rt712_sdca_dmic_update_status\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L808): runs first-attach init when the slave reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96), clears [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L19) on [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95)
- [`'\<rt712_sdca_dmic_io_init\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L178): the DMIC-only hardware init, writing the vendor float-control words and the input-terminal vendor-defined control, run once per attach
- [`'\<rt712_sdca_dmic_read_prop\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L827): fills the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) with [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) of BIT(2) and zero [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), then one [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) for port 2
- [`'soc_sdca_dev_rt712_dmic':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L605): the DMIC [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) carrying the FU1E capture controls and the DMIC DAPM graph
- [`'rt712_sdca_dmic_dapm_widgets':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L557) / [`'rt712_sdca_dmic_audio_map':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L576): the widget list (DMIC inputs, PDE 11 supply, FU 1E ADC, the two ADC muxes, and the `DP2TX` capture AIF) and the routes that connect them
- [`'rt712_sdca_dmic_ops':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L730) / [`'rt712_sdca_dmic_dai':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L737): the DMIC [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and the single `rt712-sdca-dmic-aif1` DAI carrying the `DP2 Capture` stream
- [`'\<rt712_sdca_dmic_hw_params\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630): the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op, fixed to data port 2; joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) and writes the rate to [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) and [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194)
- [`'\<rt712_sdca_dmic_hw_free\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L710): the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) op, removes the codec from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)
- [`'\<rt712_sdca_dmic_set_sdw_stream\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L616) / [`'\<rt712_sdca_dmic_shutdown\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L624): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op storing the stream handle with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506) and the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324) op clearing it
- [`'\<rt712_sdca_dmic_pde11_event\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L532): the power-domain supply event writing [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213) on [`RT712_SDCA_ENT_PDE11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L189)

### SDCA mic addressing on the MIC_ARRAY function (rt712-sdca.h, sdw_registers.h)

- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): packs the function number, entity, control selector, and channel into one 32-bit SoundWire register address; every DMIC control, power-domain entity, and clock source is reached through it
- [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173): the single SDCA function number (0x02) the DMIC driver addresses, the SoundWire-side identity of the SMART_MIC Function
- [`RT712_SDCA_ENT_USER_FU1E`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L185) / [`RT712_SDCA_ENT_PLATFORM_FU15`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L200): the user feature unit behind the four-channel capture volume and mute, and the platform boost feature unit behind the per-channel gain
- [`RT712_SDCA_ENT_PDE11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L189) / [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) / [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194) / [`RT712_SDCA_ENT_IT26`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L198): the power-domain, two clock-source, and input-terminal entities of the microphone Function
- [`RT712_SDCA_CTL_SAMPLE_FREQ_INDEX`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L204) (0x10) / [`RT712_SDCA_CTL_FU_MUTE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L205) (0x01) / [`RT712_SDCA_CTL_FU_VOLUME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L206) (0x02) / [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213): the control selectors the DMIC hw_params, mute controls, and power-domain event use
- [`RT712_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L232): the DAI id the single DMIC DAI carries

### Machine-side generic SoundWire DMIC link (soc_sdw_dmic.c, sof_sdw.c)

- [`'\<asoc_sdw_dmic_init\>':'sound/soc/sdw_utils/soc_sdw_dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24): the back-end-link `init` that adds the card-level `SoC DMIC` widget and routes it to the codec `DMic` input, exported in the [`SND_SOC_SDW_UTILS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L831) namespace
- [`'\<create_dmic_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092): builds the `dmic01` and `dmic16k` PCH back-end links, binding the SOF `DMIC01 Pin`/`DMIC16k Pin` CPU DAIs to the `dmic-hifi` generic codec DAI and passing [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) on the first link only
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): allocates the three [`struct snd_soc_dai_link_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L642) slots and fills one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702), the form the DMIC builder uses

### SoundWire stream and bind contract (generic infrastructure)

- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the generic peripheral callback contract the DMIC driver fills; for the DMIC only [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) are needed
- [`'\<struct sdw_slave\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665): the SoundWire peripheral the DMIC driver binds to; its embedded [`sdca_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is the cached SDCA inventory the quirk match reads
- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): allocate the slave runtime, configure its port, and advance the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928)
- [`'\<sdw_stream_remove_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228): free the slave port and runtime from the stream
- [`'\<devm_regmap_init_sdw_mbq\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) / [`'\<devm_regmap_init_sdw\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196): build the device-managed SoundWire MBQ and single-byte regmaps from their configs
- [`'\<regmap_write\>':'drivers/base/regmap/regmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c#L1981): the accessor the DMIC hw_params and power-domain event use against [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addresses

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the DMIC DAI joins from its hw_params op with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus model, master, peripheral, and data port concepts behind the DMIC source port
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): the bus-clash and parity handling the read_prop callback enables through [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L395)
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC codec component guide covering the component driver, DAI driver, and ops the DMIC peripheral uses
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the Dynamic Audio Power Management widget and route model the DMIC capture graph builds
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the ASoC machine driver concept the DMIC link helper plugs into
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end split the PCH DMIC link uses

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [SoundWire support on Linux, kernel.org driver-api](https://www.kernel.org/doc/html/latest/driver-api/soundwire/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The microphone path has three objects of interest with three different owners and lifetimes. The standalone DMIC peripheral creates one private-data structure and one component per SoundWire device, the combined codec creates the DMIC component as a second component on its one device, and the machine helper creates only the card-level mic widget through the back-end link. The DMIC private data and component are device-managed against the SoundWire peripheral, the SoundWire stream lives only between the hw_params and hw_free of the capture DAI, and the card-level `SoC DMIC` widget lives for the card.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14) | [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752), device-managed alloc | the standalone DMIC peripheral |
| [`rt712_sdca_dmic_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L105) / [`rt712_sdca_dmic_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L118) regmaps | [`rt712_sdca_dmic_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L946) via [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) | the standalone DMIC peripheral |
| [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L605) component | [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752) via [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | the standalone DMIC peripheral |
| DMIC component on the combined codec | [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) when [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96) reports a mic Function | the combined SoundWire peripheral |
| `DP2 Capture` SoundWire stream | [`rt712_sdca_dmic_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630) via [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) | between hw_params and hw_free |
| card-level `SoC DMIC` widget + route | [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) from the link `init` | the card |

## DETAILS

### The SDCA microphone Function type

A SoundWire SDCA peripheral exposes one or more independent audio Functions, and which kind each one is comes from its [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) topology code. A microphone is [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) (0x03) or its reduced form [`SDCA_FUNCTION_TYPE_SIMPLE_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L76) (0x04). According to the kerneldoc, SMART_MIC is a "Smart microphone with acoustic triggers" and SIMPLE_MIC is a "Subset of SmartMic", and the note records that SIMPLE_MIC is "NOT defined in SDCA 1.0a, but they were defined in earlier drafts and are planned for 1.1":

```c
/* include/sound/sdca_function.h:51 */
/**
 * enum sdca_function_type - SDCA Function Type codes
 * @SDCA_FUNCTION_TYPE_SMART_AMP: Amplifier with protection features.
 * @SDCA_FUNCTION_TYPE_SIMPLE_AMP: Subset of SmartAmp.
 * @SDCA_FUNCTION_TYPE_SMART_MIC: Smart microphone with acoustic triggers.
 * @SDCA_FUNCTION_TYPE_SIMPLE_MIC: Subset of SmartMic.
 * @SDCA_FUNCTION_TYPE_SPEAKER_MIC: Combination of SmartMic and SmartAmp.
 ...
 * SDCA Function Types from SDCA specification v1.0a Section 5.1.2
 * all Function types not described are reserved.
 *
 * Note that SIMPLE_AMP, SIMPLE_MIC and SIMPLE_JACK Function Types
 * are NOT defined in SDCA 1.0a, but they were defined in earlier
 * drafts and are planned for 1.1.
 */
enum sdca_function_type {
	SDCA_FUNCTION_TYPE_SMART_AMP			= 0x01,
	SDCA_FUNCTION_TYPE_SIMPLE_AMP			= 0x02,
	SDCA_FUNCTION_TYPE_SMART_MIC			= 0x03,
	SDCA_FUNCTION_TYPE_SIMPLE_MIC			= 0x04,
	SDCA_FUNCTION_TYPE_SPEAKER_MIC			= 0x05,
	SDCA_FUNCTION_TYPE_UAJ				= 0x06,
	SDCA_FUNCTION_TYPE_RJ				= 0x07,
	SDCA_FUNCTION_TYPE_SIMPLE_JACK			= 0x08,
	SDCA_FUNCTION_TYPE_HID				= 0x0A,
	SDCA_FUNCTION_TYPE_COMPANION_AMP		= 0x0B,
	SDCA_FUNCTION_TYPE_IMP_DEF			= 0x1F,
};
```

The kernel can read a microphone Function's full topology into a [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), a tree of input terminals from the PDM transducers, a feature unit for capture volume and mute, a power-domain entity, a clock source, and an output terminal that maps to a SoundWire data port. The rt712 DMIC driver does not consume that parsed model for its own controls; it names the function, entity, and control ids directly in its header and reaches each control by the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address. The microphone Function on the rt712 is the single SDCA function number [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173):

```c
/* sound/soc/codecs/rt712-sdca.h:172 */
#define FUNC_NUM_MIC_ARRAY 0x02
```

That function number sits apart from the topology codes the table lists, where two rows (SMART_MIC at 0x03 and SIMPLE_MIC at 0x04) mark a microphone among the amplifier, jack, and HID types:

```
    enum sdca_function_type: a mic is SMART_MIC or SIMPLE_MIC
    ─────────────────────────────────────────────────────────

    code   Function type                       class
    ┌────┬─────────────────────────────────┬──────────────┐
    │0x01│ SDCA_FUNCTION_TYPE_SMART_AMP    │ amplifier    │
    │0x02│ SDCA_FUNCTION_TYPE_SIMPLE_AMP   │ amplifier    │
    │0x03│ SDCA_FUNCTION_TYPE_SMART_MIC    │ microphone ◀ │
    │0x04│ SDCA_FUNCTION_TYPE_SIMPLE_MIC   │ microphone ◀ │
    │0x05│ SDCA_FUNCTION_TYPE_SPEAKER_MIC  │ mic + amp    │
    │0x06│ SDCA_FUNCTION_TYPE_UAJ          │ jack         │
    │0x0A│ SDCA_FUNCTION_TYPE_HID          │ HID buttons  │
    └────┴─────────────────────────────────┴──────────────┘

    topology type (SMART_MIC) ≠ SoundWire function number:
    on the rt712 the mic Function is FUNC_NUM_MIC_ARRAY = 0x02
```

### The combined codec registers the mic component only when a mic Function is present

On the combined RT712 codec the microphone Function shares one SoundWire device with the jack and amplifier Functions, and the main driver registers a second ASoC component for it only when the parsed SDCA inventory advertises a microphone. [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) registers [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) after the main component, gated on [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96). According to the comment, the gate exists so the driver adds "the dmic component if a SMART_MIC function is exposed in ACPI":

```c
/* sound/soc/codecs/rt712-sdca.c:1641 (continued) */
	/* only add the dmic component if a SMART_MIC function is exposed in ACPI */
	if (sdca_device_quirk_match(slave, SDCA_QUIRKS_RT712_VB)) {
		ret =  devm_snd_soc_register_component(dev,
						       &soc_sdca_dev_rt712_dmic,
						       rt712_sdca_dmic_dai,
						       ARRAY_SIZE(rt712_sdca_dmic_dai));
		if (ret < 0)
			return ret;
		rt712->dmic_function_found = true;
	}
```

[`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96) dispatches [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) to [`sdca_device_quirk_rt712_vb()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L50), which requires a v08r01-draft interface revision, the Realtek manufacturer and a 712-family part id, and then scans the cached Function descriptors for a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) entry:

```c
/* sound/soc/sdca/sdca_device.c:50 */
static bool sdca_device_quirk_rt712_vb(struct sdw_slave *slave)
{
	struct sdw_slave_id *id = &slave->id;
	int i;

	/*
	 * The RT712_VA relies on the v06r04 draft, and the
	 * RT712_VB on a more recent v08r01 draft.
	 */
	if (slave->sdca_data.interface_revision < 0x0801)
		return false;

	if (id->mfg_id != 0x025d)
		return false;

	if (id->part_id != 0x712 &&
	    id->part_id != 0x713 &&
	    id->part_id != 0x716 &&
	    id->part_id != 0x717)
		return false;

	for (i = 0; i < slave->sdca_data.num_functions; i++) {
		if (slave->sdca_data.function[i].type == SDCA_FUNCTION_TYPE_SMART_MIC)
			return true;
	}

	return false;
}
```

The cached [`num_functions`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) count and the [`function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) descriptor array were filled at SoundWire enumeration, before any codec driver probed, so the topology type is available to this decision without parsing the full DisCo tree. The combined-codec DMIC component and the standalone driver below carry the same Microphone Array controls and DAPM graph; the difference is whether the device exposes the mic alongside other Functions or by itself.

### The standalone DMIC peripheral is its own SoundWire device

A device that exposes only the microphone Function is driven by the standalone driver in [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c), a complete SoundWire peripheral driver registered by [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34). Its [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) names the bind callbacks, the slave ops, and the id table:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:968 */
static struct sdw_driver rt712_sdca_dmic_sdw_driver = {
	.driver = {
		.name = "rt712-sdca-dmic",
		.pm = pm_ptr(&rt712_sdca_dmic_pm),
	},
	.probe = rt712_sdca_dmic_sdw_probe,
	.remove = rt712_sdca_dmic_sdw_remove,
	.ops = &rt712_sdca_dmic_slave_ops,
	.id_table = rt712_sdca_dmic_id,
};
module_sdw_driver(rt712_sdca_dmic_sdw_driver);
```

The match table [`rt712_sdca_dmic_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L870) holds the four MIPI ids whose part numbers are the 0x17xx siblings of the combined codec, a distinct device address from the 0x712 family the combined codec binds:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:870 */
static const struct sdw_device_id rt712_sdca_dmic_id[] = {
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x1712, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x1713, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x1716, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x1717, 0x3, 0x1, 0),
	{},
};
MODULE_DEVICE_TABLE(sdw, rt712_sdca_dmic_id);
```

On a match the bus calls [`rt712_sdca_dmic_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L946), which builds the two regmaps and hands them to [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752). The MBQ regmap carries the two-byte feature-unit volumes and channel gains and the single-byte regmap carries the one-byte controls (mutes, power states, sample-rate index) and the vendor index window:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:946 */
static int rt712_sdca_dmic_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap, *mbq_regmap;

	/* Regmap Initialization */
	mbq_regmap = devm_regmap_init_sdw_mbq(slave, &rt712_sdca_dmic_mbq_regmap);
	if (IS_ERR(mbq_regmap))
		return PTR_ERR(mbq_regmap);

	regmap = devm_regmap_init_sdw(slave, &rt712_sdca_dmic_regmap);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt712_sdca_dmic_init(&slave->dev, regmap, mbq_regmap, slave);
}
```

### rt712_sdca_dmic_init allocates the private data and registers the component

[`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752) allocates the [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14), stores the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and both regmaps, starts each regmap in cache-only mode until the device attaches, marks the four capture channels muted, and registers the component. According to the comment, the [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L19) flag is left false because "HW init will be performed when device reports present":

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:752 */
static int rt712_sdca_dmic_init(struct device *dev, struct regmap *regmap,
			struct regmap *mbq_regmap, struct sdw_slave *slave)
{
	struct rt712_sdca_dmic_priv *rt712;
	int ret;

	rt712 = devm_kzalloc(dev, sizeof(*rt712), GFP_KERNEL);
	if (!rt712)
		return -ENOMEM;

	dev_set_drvdata(dev, rt712);
	rt712->slave = slave;
	rt712->regmap = regmap;
	rt712->mbq_regmap = mbq_regmap;

	regcache_cache_only(rt712->regmap, true);
	regcache_cache_only(rt712->mbq_regmap, true);

	/*
	 * Mark hw_init to false
	 * HW init will be performed when device reports present
	 */
	rt712->hw_init = false;
	rt712->first_hw_init = false;
	rt712->fu1e_dapm_mute = true;
	rt712->fu1e_mixer_mute[0] = rt712->fu1e_mixer_mute[1] =
		rt712->fu1e_mixer_mute[2] = rt712->fu1e_mixer_mute[3] = true;

	ret =  devm_snd_soc_register_component(dev,
			&soc_sdca_dev_rt712_dmic,
			rt712_sdca_dmic_dai,
			ARRAY_SIZE(rt712_sdca_dmic_dai));
	if (ret < 0)
		return ret;
	...
}
```

The [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14) is a reduced version of the combined codec's private data, with no jack pointer, no delayed works, and no interrupt-status cache, since the microphone Function has no jack detection or HID buttons. It holds the two regmaps, the slave, the component, the two init flags, and the four-channel mute cache:

```c
/* sound/soc/codecs/rt712-sdca-dmic.h:14 */
struct  rt712_sdca_dmic_priv {
	struct regmap *regmap;
	struct regmap *mbq_regmap;
	struct snd_soc_component *component;
	struct sdw_slave *slave;
	struct sdw_bus_params params;
	bool hw_init;
	bool first_hw_init;
	bool fu1e_dapm_mute;
	bool fu1e_mixer_mute[4];
};
```

The two regmaps split the work by register width, the MBQ one carrying the two-byte volumes and gains and the plain one the single-byte mutes, power states, and rate index:

```
    rt712_sdca_dmic_priv: two regmaps by control width
    ──────────────────────────────────────────────────

    struct rt712_sdca_dmic_priv
    ┌───────────────────────────────────────────────────┐
    │ struct regmap           *regmap       (one byte)  │
    │ struct regmap           *mbq_regmap   (MBQ 2-byte)│
    │ struct snd_soc_component *component               │
    │ struct sdw_slave        *slave                    │
    │ struct sdw_bus_params    params                   │
    │ bool hw_init / first_hw_init                      │
    │ bool fu1e_dapm_mute / fu1e_mixer_mute[4]          │
    └───────────────────────────────────────────────────┘

    mbq_regmap  ─▶ FU volumes, per-channel gains   (2-byte)
    regmap      ─▶ mutes, power states, rate index  (1-byte)
```

### The slave ops have no jack interrupt callback

The DMIC peripheral fills only two members of [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616). A microphone Function has nothing to report on the SDCA interrupt line, so [`rt712_sdca_dmic_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L941) supplies [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) but no [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:941 */
static const struct sdw_slave_ops rt712_sdca_dmic_slave_ops = {
	.read_prop = rt712_sdca_dmic_read_prop,
	.update_status = rt712_sdca_dmic_update_status,
};
```

[`rt712_sdca_dmic_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L827) fills the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) with the bus-clash and parity interrupt masks, declares one source port (port 2) and no sink ports, then builds one [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) for the bit set in [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:827 */
static int rt712_sdca_dmic_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	int nval, i;
	u32 bit;
	unsigned long addr;
	struct sdw_dpn_prop *dpn;

	prop->scp_int1_mask = SDW_SCP_INT1_BUS_CLASH | SDW_SCP_INT1_PARITY;
	prop->quirks = SDW_SLAVE_QUIRKS_INVALID_INITIAL_PARITY;

	prop->paging_support = true;

	/* first we need to allocate memory for set bits in port lists */
	prop->source_ports = BIT(2); /* BITMAP: 00000100 */
	prop->sink_ports = 0;

	nval = hweight32(prop->source_ports);
	prop->src_dpn_prop = devm_kcalloc(&slave->dev, nval,
		sizeof(*prop->src_dpn_prop), GFP_KERNEL);
	if (!prop->src_dpn_prop)
		return -ENOMEM;

	i = 0;
	dpn = prop->src_dpn_prop;
	addr = prop->source_ports;
	for_each_set_bit(bit, &addr, 32) {
		dpn[i].num = bit;
		dpn[i].type = SDW_DPN_FULL;
		dpn[i].simple_ch_prep_sm = true;
		dpn[i].ch_prep_timeout = 10;
		i++;
	}
	...
}
```

[`rt712_sdca_dmic_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L808) runs the first-attach hardware init when the slave reaches [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96), and resets the [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L19) flag when the device detaches so the init runs again on the next attach:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:808 */
static int rt712_sdca_dmic_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt712_sdca_dmic_priv *rt712 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt712->hw_init = false;

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt712->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt712_sdca_dmic_io_init(&slave->dev, slave);
}
```

[`rt712_sdca_dmic_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L178) takes the regmaps out of cache-only mode and writes the vendor float-control words that wire the codec's internal ADC, DMIC, and power-domain entities, then writes the input-terminal vendor-defined control and the RC-calibration register. It is the DMIC-only counterpart of the combined codec's I/O init, and it programs only the Microphone Array Function:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:178 */
static int rt712_sdca_dmic_io_init(struct device *dev, struct sdw_slave *slave)
{
	struct rt712_sdca_dmic_priv *rt712 = dev_get_drvdata(dev);

	if (rt712->hw_init)
		return 0;

	regcache_cache_only(rt712->regmap, false);
	regcache_cache_only(rt712->mbq_regmap, false);
	...
	regmap_write(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_IT26, RT712_SDCA_CTL_VENDOR_DEF, 0), 0x01);
	...
	/* Mark Slave initialization complete */
	rt712->hw_init = true;

	pm_runtime_put_autosuspend(&slave->dev);

	dev_dbg(&slave->dev, "%s hw_init complete\n", __func__);
	return 0;
}
```

The status callback runs that init once, firing it when the slave reaches ATTACHED with hw_init still false and clearing the flag again on UNATTACHED so the next attach repeats it:

```
    rt712_sdca_dmic_update_status: attach drives first-time init
    ───────────────────────────────────────────────────────────

          ┌──────────────────────────┐
          │ SDW_SLAVE_UNATTACHED     │
          │   hw_init = false        │
          └────────────┬─────────────┘
                       │ slave enumerated / attaches
                       ▼
          ┌──────────────────────────┐  hw_init already true
          │ SDW_SLAVE_ATTACHED       │ ───────────────▶ return 0
          │   if !hw_init:           │
          │     rt712_sdca_dmic_     │
          │       io_init()          │  un-cache regmaps,
          │     hw_init = true       │  write vendor controls
          └────────────┬─────────────┘
                       │ device detaches
                       ▼   back to UNATTACHED (hw_init = false)
```

### The component carries the capture controls and the DMIC DAPM graph

The ASoC face of the DMIC peripheral is [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L605), a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that binds the FU1E capture controls, the DMIC widget and route arrays, and the component probe. There is no [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) hook. The [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) bit is set because the SoundWire transport fixes the wire byte order:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:605 */
static const struct snd_soc_component_driver soc_sdca_dev_rt712_dmic = {
	.probe = rt712_sdca_dmic_probe,
	.controls = rt712_sdca_dmic_snd_controls,
	.num_controls = ARRAY_SIZE(rt712_sdca_dmic_snd_controls),
	.dapm_widgets = rt712_sdca_dmic_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt712_sdca_dmic_dapm_widgets),
	.dapm_routes = rt712_sdca_dmic_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt712_sdca_dmic_audio_map),
	.endianness = 1,
};
```

The DAPM graph in [`rt712_sdca_dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L557) names the two physical DMIC inputs, the power-domain supply widget for [`RT712_SDCA_ENT_PDE11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L189), the FU 1E ADC widget, the two ADC mux widgets, and the `DP2TX` capture AIF that carries the `DP2 Capture` stream:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:557 */
static const struct snd_soc_dapm_widget rt712_sdca_dmic_dapm_widgets[] = {
	SND_SOC_DAPM_INPUT("DMIC1"),
	SND_SOC_DAPM_INPUT("DMIC2"),

	SND_SOC_DAPM_SUPPLY("PDE 11", SND_SOC_NOPM, 0, 0,
		rt712_sdca_dmic_pde11_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),

	SND_SOC_DAPM_ADC_E("FU 1E", NULL, SND_SOC_NOPM, 0, 0,
		rt712_sdca_dmic_fu1e_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_MUX("ADC 25 Mux", SND_SOC_NOPM, 0, 0,
		&rt712_sdca_dmic_adc25_mux),
	SND_SOC_DAPM_MUX("ADC 26 Mux", SND_SOC_NOPM, 0, 0,
		&rt712_sdca_dmic_adc26_mux),

	SND_SOC_DAPM_AIF_OUT("DP2TX", "DP2 Capture", 0, SND_SOC_NOPM, 0, 0),
};
```

The routes in [`rt712_sdca_dmic_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L576) wire the two physical inputs through the ADC muxes and the FU 1E feature unit to the `DP2TX` AIF, and pull in the PDE 11 power-domain supply, so enabling the capture stream powers the whole chain from the physical mic to the data port:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:576 */
static const struct snd_soc_dapm_route rt712_sdca_dmic_audio_map[] = {
	{"DP2TX", NULL, "FU 1E"},

	{"FU 1E", NULL, "PDE 11"},
	{"FU 1E", NULL, "ADC 25 Mux"},
	{"FU 1E", NULL, "ADC 26 Mux"},
	{"ADC 25 Mux", "DMIC1", "DMIC1"},
	{"ADC 25 Mux", "DMIC2", "DMIC2"},
	{"ADC 26 Mux", "DMIC1", "DMIC1"},
	{"ADC 26 Mux", "DMIC2", "DMIC2"},
};
```

The PDE 11 supply widget runs [`rt712_sdca_dmic_pde11_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L532), which writes the [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213) control of [`RT712_SDCA_ENT_PDE11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L189) on the [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) function, requesting power state 0 on power-up and power state 3 on power-down:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:532 */
static int rt712_sdca_dmic_pde11_event(struct snd_soc_dapm_widget *w,
	struct snd_kcontrol *kcontrol, int event)
{
	struct snd_soc_component *component =
		snd_soc_dapm_to_component(w->dapm);
	struct rt712_sdca_dmic_priv *rt712 = snd_soc_component_get_drvdata(component);
	unsigned char ps0 = 0x0, ps3 = 0x3;

	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_PDE11,
				RT712_SDCA_CTL_REQ_POWER_STATE, 0),
				ps0);
		break;
	case SND_SOC_DAPM_PRE_PMD:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_PDE11,
				RT712_SDCA_CTL_REQ_POWER_STATE, 0),
				ps3);
		break;
	}
	return 0;
}
```

That supply takes its place in the routed capture chain, the two ADC muxes picking DMIC1 or DMIC2 into the FU 1E feature unit it powers, which then drives the DP2TX port:

```
    DMIC capture DAPM graph (rt712_sdca_dmic_audio_map)
    ──────────────────────────────────────────────────

    ┌──────────────────┐    ┌──────────────────┐
    │ ADC 25 Mux       │    │ ADC 26 Mux       │
    │  in: DMIC1/DMIC2 │    │  in: DMIC1/DMIC2 │
    └─────────┬────────┘    └────────┬─────────┘
              │                      │
              └──────────┬───────────┘     ┌────────────┐
                         ▼                 │ PDE 11     │
                     ┌───────┐             │ (supply)   │
                     │ FU 1E │ ◀───────────┤            │
                     └───┬───┘             └────────────┘
                         ▼
                     ┌───────┐
                     │ DP2TX │   AIF_OUT  "DP2 Capture"
                     └───────┘
```

### The single capture DAI and its stream operations

The DMIC peripheral registers one DAI. [`rt712_sdca_dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L737) is a single capture-only [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) named `rt712-sdca-dmic-aif1`, with [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of 4 and the stream name `DP2 Capture`, pointing at [`rt712_sdca_dmic_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L730):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:737 */
static struct snd_soc_dai_driver rt712_sdca_dmic_dai[] = {
	{
		.name = "rt712-sdca-dmic-aif1",
		.id = RT712_AIF1,
		.capture = {
			.stream_name = "DP2 Capture",
			.channels_min = 1,
			.channels_max = 4,
			.rates = RT712_STEREO_RATES,
			.formats = RT712_FORMATS,
		},
		.ops = &rt712_sdca_dmic_ops,
	},
};
```

[`rt712_sdca_dmic_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L730) fills four callbacks of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), the same shape the combined codec's DAIs use:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:730 */
static const struct snd_soc_dai_ops rt712_sdca_dmic_ops = {
	.hw_params	= rt712_sdca_dmic_hw_params,
	.hw_free	= rt712_sdca_dmic_hw_free,
	.set_stream	= rt712_sdca_dmic_set_sdw_stream,
	.shutdown	= rt712_sdca_dmic_shutdown,
};
```

[`rt712_sdca_dmic_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L616) stores the SoundWire stream handle the machine driver assigned, by [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506), and [`rt712_sdca_dmic_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L624) clears it:

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:616 */
static int rt712_sdca_dmic_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}
```

### rt712_sdca_dmic_hw_params binds the data port and programs the rate

The capture path is established when the front end runs hw_params. [`rt712_sdca_dmic_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630) reads the stream handle stored by set_stream, builds a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L887) from the PCM parameters, fixes the SoundWire port number to 2 with a channel mask derived from the channel count, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:630 */
static int rt712_sdca_dmic_hw_params(struct snd_pcm_substream *substream,
				struct snd_pcm_hw_params *params,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt712_sdca_dmic_priv *rt712 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_config stream_config;
	struct sdw_port_config port_config;
	struct sdw_stream_runtime *sdw_stream;
	int retval, num_channels;
	unsigned int sampling_rate;

	dev_dbg(dai->dev, "%s %s", __func__, dai->name);
	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);

	if (!sdw_stream)
		return -EINVAL;

	if (!rt712->slave)
		return -EINVAL;

	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = SDW_DATA_DIR_TX;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = 2;

	retval = sdw_stream_add_slave(rt712->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
	...
```

The direction is fixed to [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L850) and the port number is the constant 2, so unlike the combined codec, which selects a data port from the DAI id and direction, the standalone DMIC always uses port 2 for capture. After the port is configured, the op maps the PCM rate to a sample-rate index constant and writes it to the two clock sources [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) and [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194) through the [`RT712_SDCA_CTL_SAMPLE_FREQ_INDEX`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L204) control of [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:630 (continued) */
	/* sampling rate configuration */
	switch (params_rate(params)) {
	case 16000:
		sampling_rate = RT712_SDCA_RATE_16000HZ;
		break;
	...
	case 192000:
		sampling_rate = RT712_SDCA_RATE_192000HZ;
		break;
	default:
		dev_err(component->dev, "%s: Rate %d is not supported\n",
			__func__, params_rate(params));
		return -EINVAL;
	}

	/* set sampling frequency */
	regmap_write(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1F, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);
	regmap_write(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1C, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);

	return 0;
}
```

[`rt712_sdca_dmic_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L710) tears the path down by reading the stored stream handle and removing the codec from it with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:710 */
static int rt712_sdca_dmic_hw_free(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt712_sdca_dmic_priv *rt712 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_runtime *sdw_stream =
		snd_soc_dai_get_dma_data(dai, substream);

	if (!rt712->slave)
		return -EINVAL;

	sdw_stream_remove_slave(rt712->slave, sdw_stream);
	return 0;
}
```

The stream that hw_free later removes is assembled at hw_params from the PCM parameters, the rate, channel count, and width filling the stream config and a port-2 mask the port config before the slave is added:

```
    hw_params: PCM params feed the SoundWire stream join
    ───────────────────────────────────────────────────

    snd_pcm_hw_params
    ┌──────────────────────────┐
    │ params_rate              │──┐
    │ params_channels          │  │ ┌──────────────────────────┐
    │ params_format            │  └▶│ struct sdw_stream_config │
    └──────────────────────────┘    │   frame_rate = rate      │
                                    │   ch_count   = channels  │
                                    │   bps        = width     │
                                    │   direction  = DIR_TX    │
                                    └──────────────────────────┘
                                    ┌──────────────────────────┐
    num_channels ─▶ GENMASK ──────▶ │ struct sdw_port_config   │
                                    │  ch_mask = GENMASK(n-1,0)│
                                    │  num     = 2             │
                                    └─────────────┴────────────┘
                                                  │  both structs
                                                  ▼
                                    sdw_stream_add_slave(slave,
                                      &stream_config, &port_config,
                                      1, sdw_stream)
```

### The machine helper adds a generic SoundWire DMIC to the card

The codec-side DAI above is the SoundWire half of one back-end link; the machine driver supplies the CPU side and the card-level mic widget. On the Intel MTL/LNL platform the SoundWire card is the SOF machine driver [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c), and its [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) builds the two PCH DMIC back-end links that bind the SOF `DMIC01 Pin` and `DMIC16k Pin` CPU DAIs to the generic `dmic-hifi` codec DAI. It passes [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) as the `init` of the first link only, and leaves the second link's init NULL so the widgets are added once:

```c
/* sound/soc/intel/boards/sof_sdw.c:1092 */
static int create_dmic_dailinks(struct snd_soc_card *card,
				struct snd_soc_dai_link **dai_links, int *be_id)
{
	struct device *dev = card->dev;
	int ret;

	ret = asoc_sdw_init_simple_dai_link(dev, *dai_links, be_id, "dmic01",
					    0, 1, // DMIC only supports capture
					    "DMIC01 Pin", "dummy",
					    "dmic-codec", "dmic-hifi", 1,
					    asoc_sdw_dmic_init, NULL);
	if (ret)
		return ret;

	(*dai_links)++;

	ret = asoc_sdw_init_simple_dai_link(dev, *dai_links, be_id, "dmic16k",
					    0, 1, // DMIC only supports capture
					    "DMIC16k Pin", "dummy",
					    "dmic-codec", "dmic-hifi", 1,
					    /* don't call asoc_sdw_dmic_init() twice */
					    NULL, NULL);
	if (ret)
		return ret;

	(*dai_links)++;

	return 0;
}
```

The card builds the DMIC links only when the NHLT table reported PDM mics. The caller in [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) guards the call on a non-zero `dmic_num`, so a board with no PCH mics never creates them:

```c
/* sound/soc/intel/boards/sof_sdw.c:1367 */
	/* dmic */
	if (dmic_num) {
		ret = create_dmic_dailinks(card, &dai_links, &be_id);
		if (ret)
			goto err_end;
	}
```

[`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) is the back-end-link `init` the core runs once the link is created. It adds a card-level `SoC DMIC` microphone widget and a route from that widget to the codec's `DMic` input, so the full graph from the board mic to the front-end PCM is connected. According to the comment, the route covers the "digital mics":

```c
/* sound/soc/sdw_utils/soc_sdw_dmic.c:15 */
static const struct snd_soc_dapm_widget dmic_widgets[] = {
	SND_SOC_DAPM_MIC("SoC DMIC", NULL),
};

static const struct snd_soc_dapm_route dmic_map[] = {
	/* digital mics */
	{"DMic", NULL, "SoC DMIC"},
};

int asoc_sdw_dmic_init(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_card *card = rtd->card;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	int ret;

	ret = snd_soc_dapm_new_controls(dapm, dmic_widgets,
					ARRAY_SIZE(dmic_widgets));
	if (ret) {
		dev_err(card->dev, "DMic widget addition failed: %d\n", ret);
		/* Don't need to add routes if widget addition failed */
		return ret;
	}

	ret = snd_soc_dapm_add_routes(dapm, dmic_map,
				      ARRAY_SIZE(dmic_map));

	if (ret)
		dev_err(card->dev, "DMic map addition failed: %d\n", ret);

	return ret;
}
EXPORT_SYMBOL_NS(asoc_sdw_dmic_init, "SND_SOC_SDW_UTILS");
```

The `DMic` pin the route names is the physical input of the generic [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) codec that the `dmic-hifi` DAI belongs to, so the helper joins the card's `SoC DMIC` source onto that codec's input. This machine link is the PCH PDM path the card adds independently of any SoundWire codec; a SoundWire SDCA microphone such as the rt712 DMIC reaches the card through its own codec DAI link instead, and the codec decimates the PDM before the audio crosses the SoundWire bus, while the generic `dmic-hifi` path leaves decimation to the host or DSP behind the `DMIC01 Pin` back end.
