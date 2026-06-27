# RT712 SDCA codec

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Realtek RT712 is a combined headset codec and mono speaker amplifier exposed as an SDCA (SoundWire Device Class for Audio) peripheral that an x86-64 ACPI platform enumerates over a SoundWire link, and the kernel drives it through the ASoC component [`soc_sdca_dev_rt712`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1407) with its [`rt712_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L713), [`rt712_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L944), [`rt712_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L969), and headset jack, paired with the SoundWire peripheral driver [`rt712_sdca_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L493) that binds the device through a [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) named [`rt712_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L354), builds the two regmaps [`rt712_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L129) and the MBQ regmap [`rt712_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L142), and routes the codec interrupt. Every register access is a SoundWire control read or write whose address the [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) macro builds from an SDCA function number, an entity, a control selector, and a channel, so the driver names a control on a function entity (a feature unit, a power-domain entity, a clock source) rather than a raw offset. The two interfaces in [`rt712_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1592) map to SoundWire data ports, DP1 carries headphone playback and DP4 the headset-mic capture on `aif1`, DP3 carries speaker playback on `aif2`, and a digital-microphone capture sub-function appears either as a second component [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) on the same device or as the wholly separate codec driver in [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c). The shared function pointer struct [`rt712_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1585) joins each DAI to its SoundWire stream from [`rt712_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1447).

```
    rt712-sdca codec  (SoundWire peripheral 0x025d:0x712, SDCA)
    ──────────────────────────────────────────────────────────

    ASoC component  soc_sdca_dev_rt712   (rt712-sdca.c + rt712-sdca-sdw.c)
    ┌──────────────────────────────────────────────────────────┐
    │ controls (FU05/FU0F/FU44 volume + switch; FU06 spk add)  │
    │ dapm_widgets + audio_map (PDE/FU/Mux + AIF endpoints)   │
    │ set_jack ─▶ rt712_sdca_set_jack_detect                  │
    │                                                         │
    │  rt712_sdca_dai[2]            ops ─▶ rt712_sdca_ops      │
    │ ┌──────────┬──────────┐                                 │
    │ │  aif1    │  aif2    │                                 │
    │ └────┬─────┴────┬─────┘                                 │
    │      │ DP1/DP4  │ DP3                                   │
    │  ┌───┴──────────┴────────────────────────────────────┐ │
    │  │ soc_sdca_dev_rt712_dmic (VB only, same device)    │  │
    │  │  aif3 ── DP8  FU1E x4 capture                     │  │
    │  └───────────────────────────────────────────────────┘   │
    └───────┬──────────┬───────────────────────────────────────┘
        DP1 ▼ DP4      ▼ DP3                  DP8 (dmic component)
       headphone     speaker
       + headset
        mic cap
            │          │
            ▼          ▼
    regmap rt712_sdca_regmap (val_bits 8)  +  rt712_sdca_mbq_regmap (val_bits 16)
    ┌──────────────────────────────────────────────────────────┐
    │ SDW_SDCA_CTL(func, entity, control, channel) addressing  │
    └───────┬───────────────┬───────────────┬──────────────────┘
            ▼               ▼               ▼
    FUNC_NUM_JACK_CODEC  FUNC_NUM_AMP   FUNC_NUM_MIC_ARRAY
       (0x01)              (0x04)          (0x02)
    CS01/CS11 FU05 FU0F  CS31 FU06 OT23  CS1F/CS1C FU1E FU15 IT26
    PDE40 PDE12 GE49     PDE23           PDE11

    Separate peripheral: rt712-sdca-dmic.c  (part 0x1712, own sdw_driver)
       aif1 ── DP2  FU1E x4 capture  (FUNC_NUM_MIC_ARRAY only)
```

## SUMMARY

The RT712 meets the kernel through the private data [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18), shared by the main codec and its SoundWire bind. On the SoundWire side, [`rt712_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L360) builds two regmaps, the MBQ regmap with [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) and the single-byte regmap with [`devm_regmap_init_sdw()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196), and hands both to [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641), which allocates the private data, stores the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and the two [`struct regmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L35) handles, arms the two delayed works for jack and button handling, registers the main component, and conditionally registers the DMIC component when the SDCA inventory advertises a microphone function. The bus driver supplies [`rt712_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L354), whose [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt712_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L190) advertises the source and sink data ports, whose [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt712_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L156) runs the first-attach hardware init, and whose [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback [`rt712_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L254) reads the SDCA interrupt status registers and queues the jack work. The generic SoundWire bind contract is [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and the generic SDCA function model is [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419); this page documents the rt712 concrete use of both.

The component driver [`soc_sdca_dev_rt712`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1407) carries the mixer controls in [`rt712_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L713), the DAPM graph in [`rt712_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L944) and [`rt712_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L969), and the jack hook [`rt712_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L457) in its [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) field. The two [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries in [`rt712_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1592) and the third in [`rt712_sdca_dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1626) all point at [`rt712_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1585), which fills only four callbacks. [`rt712_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1433) stores the SoundWire stream handle, [`rt712_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1447) selects the data port from the DAI id and direction, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), then programs the clock-source sample rate by a [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) write, [`rt712_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1565) removes it with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228), and [`rt712_sdca_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1441) clears the stored handle. The controls, the DAPM power-domain widgets, and the jack all reach hardware through the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address space, so the entire codec is expressed as a set of SDCA function entities and their controls.

The DMIC sub-function is documented in two forms on this device. The main driver registers a second ASoC component [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) on the same SoundWire peripheral when [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96) reports [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55), which it does only when the parsed SDCA inventory lists a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) function. The separate driver in [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c) is a distinct SoundWire peripheral driver, its own [`rt712_sdca_dmic_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L968) bound on a separate device address, with its own private data [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14), regmaps, slave ops, and component.

## SPECIFICATIONS

The register addressing follows the MIPI SoundWire Device Class for Audio (SDCA) control-address format layered on the MIPI SoundWire bus, encoded by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The header comment above the macro reproduces the v1.2 SDCA address mapping the macro implements, naming the control-prefix, function-number, entity, control-selector, and control-number fields and the bit positions they occupy, and the REGISTERS section below draws it. These documents are membership-gated, so the encoding here is described from that kernel header rather than from the specification text. The four SDCA function numbers the driver uses, [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L172) (0x01), [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) (0x02), [`FUNC_NUM_HID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L174) (0x03), and [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L175) (0x04), are the SDCA function types the device exposes, and the [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) quirk distinguishes the v06r04-draft RT712_VA silicon from the v08r01-draft RT712_VB. The audio sample formats and rates the DAIs declare (S16_LE, S20_3LE, S24_LE at 44.1/48/96/192 kHz for the codec, plus 16/32 kHz for the microphone) and the SoundWire stream transport that carries them are defined by their respective standards.

## LINUX KERNEL

### Private data and SDCA address encoding (rt712-sdca.h, sdw_registers.h)

- [`'\<struct rt712_sdca_priv\>':'sound/soc/codecs/rt712-sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18): the per-device state shared by the main codec and its SoundWire bind; holds the two regmaps [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L19)/[`mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L20), the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L23), the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L21) and [`dmic_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L22), the jack pointer [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27), the two delayed works, the cached interrupt status [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L35)/[`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L36), and the [`hw_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L37)/[`version_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L38) read from hardware
- [`'\<struct rt712_sdca_dmic_priv\>':'sound/soc/codecs/rt712-sdca-dmic.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14): the per-device state of the separate DMIC peripheral driver, a reduced struct with its own [`regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L15)/[`mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L16), [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L18), [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L17), and the four-channel mute cache
- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): packs the function number, entity, control selector, and channel into one 32-bit register address; every codec control, power-domain entity, and clock source is reached through it
- [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L172) / [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) / [`FUNC_NUM_HID`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L174) / [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L175): the four SDCA function numbers (0x01, 0x02, 0x03, 0x04) the codec presents
- [`RT712_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L181) / [`RT712_SDCA_ENT_USER_FU0F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L183) / [`RT712_SDCA_ENT_USER_FU06`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L182) / [`RT712_SDCA_ENT_USER_FU1E`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L185): the feature-unit entities behind the headphone, headset-mic, amp, and DMIC volume and switch controls
- [`RT712_SDCA_ENT_FU15`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L186) / [`RT712_SDCA_ENT_PLATFORM_FU15`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L200) / [`RT712_SDCA_ENT_PLATFORM_FU44`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L201): the DMIC and headphone boost feature units whose [`RT712_SDCA_CTL_FU_CH_GAIN`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L215) control the boost mixer addresses
- [`RT712_SDCA_ENT_PDE40`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L188) / [`RT712_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L187) / [`RT712_SDCA_ENT_PDE11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L189) / [`RT712_SDCA_ENT_PDE12`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L190): the power-domain entities the DAPM supply widgets drive
- [`RT712_SDCA_ENT_CS01`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L191) / [`RT712_SDCA_ENT_CS11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L192) / [`RT712_SDCA_ENT_CS31`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L195) / [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) / [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194): the clock-source entities whose [`RT712_SDCA_CTL_SAMPLE_FREQ_INDEX`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L204) (0x10) control selects the sample rate
- [`RT712_SDCA_ENT_GE49`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L180): the group entity whose [`RT712_SDCA_CTL_DETECTED_MODE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L212) (0x02) control reports the detected jack insertion mode and whose [`RT712_SDCA_CTL_SELECTED_MODE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L211) (0x01) control latches it
- [`RT712_SDCA_ENT_HID01`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L179): the HID entity whose [`RT712_SDCA_CTL_HIDTX_CURRENT_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L207) and message-offset controls carry the button-press UMP report
- [`RT712_SDCA_CTL_FU_VOLUME`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L206) (0x02) / [`RT712_SDCA_CTL_FU_MUTE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L205) (0x01) / [`RT712_SDCA_CTL_FU_CH_GAIN`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L215) (0x0b) / [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213) (0x01): the SDCA control selectors the controls, DAPM events, and jack use

### Component driver and DAIs (rt712-sdca.c)

- [`'soc_sdca_dev_rt712':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1407): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) wiring controls, DAPM, [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), and [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99)
- [`'soc_sdca_dev_rt712_dmic':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419): the second [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) on the same device, registered only on RT712_VB, carrying the DMIC controls and DAPM
- [`'rt712_sdca_controls':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L713) / [`'rt712_sdca_spk_controls':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L735): the headset mixer control array and the speaker control added at probe, each control addressing a feature unit by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335)
- [`'rt712_sdca_dapm_widgets':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L944) / [`'rt712_sdca_audio_map':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L969): the DAPM widget list and routes that connect the AIF endpoints to the feature units and power-domain entities
- [`'\<rt712_sdca_probe\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1015): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78) op recording the back pointer, adding the speaker route on non-713 parts, and resuming the device
- [`'\<rt712_sdca_set_jack_detect\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L457): the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op storing [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27) and calling [`rt712_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L404)
- [`'\<rt712_sdca_jack_init\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L404): enables the HID and detected-mode events, unmasks the two SDCA interrupt sources, and triggers the group-entity detection interrupt
- [`'\<rt712_sdca_jack_detect_handler\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L261): the [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L28) handler that reads insertion and button state and reports through [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33)
- [`'\<rt712_sdca_headset_detect\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L218) / [`'\<rt712_sdca_button_detect\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L134): read the group-entity detected mode and the HID UMP message to classify the jack and the pressed button
- [`'\<rt712_sdca_pde23_event\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L906): the speaker power-domain supply event that writes [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213) on [`RT712_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L187)
- [`'rt712_sdca_ops':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1585): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) shared by all three DAIs, populating [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324)
- [`'\<rt712_sdca_dai\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1592) / [`'\<rt712_sdca_dmic_dai\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1626): the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries `aif1`, `aif2` (codec) and `aif3` (DMIC), declaring the DP1/DP4/DP3/DP8 streams
- [`'\<rt712_sdca_pcm_hw_params\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1447): selects the SoundWire data port, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), then writes the clock-source sample rate
- [`'\<rt712_sdca_pcm_hw_free\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1565): removes the codec from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)
- [`'\<rt712_sdca_set_sdw_stream\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1433): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op storing the stream handle with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506)
- [`'\<rt712_sdca_shutdown\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1441): the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L324) op clearing the stored handle with [`snd_soc_dai_set_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L505)
- [`'\<rt712_sdca_init\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641): allocates the private data, stores the slave and both regmaps, arms the jack works, registers the main component, and conditionally registers the DMIC component
- [`'\<rt712_sdca_io_init\>':'sound/soc/codecs/rt712-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1846): the first-attach hardware init run from [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), reading the hardware id and dispatching to [`rt712_sdca_va_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1722) or [`rt712_sdca_vb_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1768)

### SoundWire peripheral driver (rt712-sdca-sdw.c)

- [`'rt712_sdca_sdw_driver':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L493): the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) registered with [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34)
- [`'rt712_sdca_id':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L392): the four-entry match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x712, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) and its 0x713/0x716/0x717 siblings
- [`'rt712_sdca_slave_ops':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L354): the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) with [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<rt712_sdca_sdw_probe\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L360): builds the MBQ and single-byte regmaps and calls [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641)
- [`'\<rt712_sdca_update_status\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L156): runs hardware init when the slave reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) and restores interrupt masks
- [`'\<rt712_sdca_read_prop\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L190): fills the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) with the source and sink port bitmaps and per-port [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) after calling [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411)
- [`'\<rt712_sdca_interrupt_callback\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L254): reads [`SDW_SCP_SDCA_INT1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L136)/[`SDW_SCP_SDCA_INT2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L146), caches them, clears them in a retry loop, and queues [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L28)
- [`'rt712_sdca_regmap':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L129): the single-byte [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit addresses, 8-bit values, [`REGCACHE_MAPLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L73)) for the single-byte SDCA controls and the vendor index window
- [`'rt712_sdca_mbq_regmap':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L142): the MBQ [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) (32-bit addresses, 16-bit values) for the two-byte feature-unit volumes and channel gains
- [`'\<rt712_sdca_mbq_readable_register\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L74) / [`'\<rt712_sdca_readable_register\>':'sound/soc/codecs/rt712-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L18): the per-regmap readability switches deciding which addresses are valid in each window

### DMIC sub-function as a separate codec (rt712-sdca-dmic.c)

- [`'rt712_sdca_dmic_sdw_driver':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L968): a wholly separate [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) for the DMIC sub-function bound on its own SoundWire device address
- [`'rt712_sdca_dmic_id':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L870): the match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x1712, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) and its 0x1713/0x1716/0x1717 siblings, distinct part ids from the main codec
- [`'soc_sdca_dev_rt712_dmic':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L605): the DMIC [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), carrying the FU1E controls and the DMIC DAPM graph
- [`'rt712_sdca_dmic_slave_ops':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L941): the DMIC [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), with only [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) (no jack interrupt)
- [`'\<rt712_sdca_dmic_init\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752) / [`'\<rt712_sdca_dmic_io_init\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L178): allocate the DMIC private data and run the DMIC-only first-attach hardware init
- [`'\<rt712_sdca_dmic_hw_params\>':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630): the DMIC [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op, fixed to data port 2 and the [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) clock sources
- [`'rt712_sdca_dmic_ops':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L730) / [`'rt712_sdca_dmic_dai':'sound/soc/codecs/rt712-sdca-dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L737): the DMIC DAI ops and the single `aif1` DAI carrying the `DP2 Capture` stream

### SoundWire stream, SDCA model, and regmap helpers (generic infrastructure)

- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the generic peripheral callback contract the codec fills; documented as a separate SoundWire-bind page
- [`'\<struct sdca_function_data\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419): the generic parsed-SDCA-function model; the rt712 driver hardcodes its function/entity/control ids rather than parsing this, but it reads the cached SDCA inventory through [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96)
- [`'\<sdca_device_quirk_match\>':'sound/soc/sdca/sdca_device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96): test a peripheral against a known SDCA quirk; [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) routes to [`sdca_device_quirk_rt712_vb()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L50)
- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): allocate the slave runtime, configure its ports, and advance the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928)
- [`'\<sdw_stream_remove_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228): free the slave port and runtime from the stream
- [`'\<devm_regmap_init_sdw_mbq\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) / [`'\<devm_regmap_init_sdw\>':'include/linux/regmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196): build the device-managed SoundWire MBQ and single-byte regmaps from their configs
- [`'\<snd_soc_jack_report\>':'sound/soc/soc-jack.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33): apply the reported status to the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80), enable or disable the associated DAPM pins, and notify userspace
- [`'\<regmap_write\>':'drivers/base/regmap/regmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c#L1981) / [`'\<regmap_read\>':'drivers/base/regmap/regmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regmap.c#L2867): the accessors the codec uses against [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addresses
- [`'\<sdw_write_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480) / [`'\<sdw_read_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L557) / [`'\<sdw_update_no_pm\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L570): the no-PM bus accessors the interrupt and jack paths use for the SCP interrupt registers

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the codec joins from its hw_params op with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus model, master, peripheral, and data port concepts behind the rt712 ports
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the bus locking the stream add and remove paths take
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): the bus-clash and parity error handling the read_prop callback enables through [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L395)
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC codec component guide covering the component driver, DAI driver, and ops the page describes
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the Dynamic Audio Power Management widget and route model the codec's DAPM graph builds
- [`Documentation/sound/soc/jack.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/jack.rst): the ASoC jack abstraction the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) callback drives

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [SoundWire support on Linux, kernel.org driver-api](https://www.kernel.org/doc/html/latest/driver-api/soundwire/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The codec has no flat register window. Every register is an SDCA control reached by [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335), which packs four operands into one 32-bit address. The header comment in [`sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L315) gives the v1.2 SDCA address mapping the macro implements, and the figure below plots where each operand lands in the 32-bit word. The mapping splits two operands across the word, the Entity into a high bit and a low six-bit field, and the Control Selector into a high two-bit field and a low four-bit field, so the macro recombines each from two shifts. The channel the driver passes occupies the same low bits the mapping labels Control Number, since the addressed control instance is the per-channel copy of the named control.

```
    SDW_SDCA_CTL(fun, ent, ctl, ch)  SDCA control address (32-bit)
    ──────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │0│ prefix  │0│ fun │E│cS │0│ cN  │N│M│    ent    │  cS   │ cN  │
          │ │  (P)    │ │24:22│ │ H │ │  H  │ │ │   12:7    │   L   │  L  │
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

    P      = Control Prefix, bits 30:26 = 0b10000  (set by BIT(30))
    fun    = Function Number[2:0], bits 24:22
    E      = Entity[6], bit 21
    cS H   = Control Selector[5:4], bits 20:19
    cN H   = Control Number[5:3], bits 17:15
    N      = Next, bit 14            M = MBQ, bit 13
    ent    = Entity[5:0], bits 12:7
    cS L   = Control Selector[3:0], bits 6:3
    cN L   = Control Number[2:0], bits 2:0
    bits 31, 25, 18 are 0 (reserved)
    Entity = (E << 6) | ent;  Control Selector = (cS H << 4) | cS L
    the channel operand is encoded into the Control Number field (cN H, cN L)
```

The driver passes mnemonic operands that the macro resolves to bit positions. A headphone playback volume write goes to `SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU05, RT712_SDCA_CTL_FU_VOLUME, CH_01)`, a speaker power-domain request to `SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_PDE23, RT712_SDCA_CTL_REQ_POWER_STATE, 0)`, and a DMIC clock-source rate to `SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1F, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0)`. The two regmaps split the address space by value width. Single-byte controls (mutes, power states) and the vendor index window go through [`rt712_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L129) with [`val_bits`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L131) of 8, and two-byte controls (feature-unit volumes, channel gains) go through [`rt712_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L142) with [`val_bits`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L145) of 16, and the [`max_register`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L134) of the single-byte map is 0x44ffffff to cover both the SDCA control space and the vendor HID buffer at [`RT712_BUF_ADDR_HID1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L168).

## DETAILS

### Object model and lifecycle

The main codec driver creates one private-data structure and up to two ASoC components against a single SoundWire peripheral, while the separate DMIC driver creates its own private data and component against a different peripheral. The [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18) is allocated by [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) at SoundWire probe and lives for the lifetime of the peripheral device; both regmaps are device-managed against the same device. The two ASoC components register through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) and unregister when the driver unbinds. The jack pointer is owned by the machine driver and only referenced through [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27).

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18) | [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641), device-managed alloc | the SoundWire peripheral |
| [`rt712_sdca_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L129) / [`rt712_sdca_mbq_regmap`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L142) regmaps | [`rt712_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L360) via [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) | the SoundWire peripheral |
| [`soc_sdca_dev_rt712`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1407) component | [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) via [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | the SoundWire peripheral |
| [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) component (VB) | [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) on [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) | the SoundWire peripheral |
| [`struct rt712_sdca_dmic_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.h#L14) | [`rt712_sdca_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L752), device-managed alloc | the separate DMIC peripheral |
| `aif1`/`aif2`/`aif3` SoundWire streams | [`rt712_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1447) via [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) | between hw_params and hw_free |
| [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27) reference | machine driver via [`rt712_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L457) | the card |

### The SDCA model the driver hardcodes

The generic SDCA layer parses one [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) per Function from firmware DisCo properties, a tree of Entities each carrying its Controls. The RT712 driver does not consume that parsed model for its controls; it hardcodes the Function/Entity/Control ids in its header and addresses them directly with [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335). The one place it reads the parsed inventory is the DMIC-component decision. [`sdca_device_quirk_match()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L96) dispatches [`SDCA_QUIRKS_RT712_VB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L55) to [`sdca_device_quirk_rt712_vb()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L50), which walks the cached SDCA function list and returns true only when a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) function is present on a recent-enough interface revision:

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
	...
	for (i = 0; i < slave->sdca_data.num_functions; i++) {
		if (slave->sdca_data.function[i].type == SDCA_FUNCTION_TYPE_SMART_MIC)
			return true;
	}

	return false;
}
```

The function entities the driver does name are constants in the codec header. The four SDCA function numbers select which Function each address targets:

```c
/* sound/soc/codecs/rt712-sdca.h:171 */
/* RT712 SDCA Control - function number */
#define FUNC_NUM_JACK_CODEC 0x01
#define FUNC_NUM_MIC_ARRAY 0x02
#define FUNC_NUM_HID 0x03
#define FUNC_NUM_AMP 0x04
```

### The codec is registered over a SoundWire peripheral

The RT712 binds first as a SoundWire peripheral. The match table [`rt712_sdca_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L392) holds the four MIPI ids for the 712/713/716/717 parts, and on a match the bus calls [`rt712_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L360), which creates both regmaps and passes them to [`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641):

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:392 */
static const struct sdw_device_id rt712_sdca_id[] = {
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x712, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x713, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x716, 0x3, 0x1, 0),
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x717, 0x3, 0x1, 0),
	{},
};
MODULE_DEVICE_TABLE(sdw, rt712_sdca_id);
```

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:360 */
static int rt712_sdca_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap, *mbq_regmap;

	/* Regmap Initialization */
	mbq_regmap = devm_regmap_init_sdw_mbq(slave, &rt712_sdca_mbq_regmap);
	if (IS_ERR(mbq_regmap))
		return PTR_ERR(mbq_regmap);

	regmap = devm_regmap_init_sdw(slave, &rt712_sdca_regmap);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt712_sdca_init(&slave->dev, regmap, mbq_regmap, slave);
}
```

[`rt712_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1641) allocates the [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18), stores the slave and both regmaps, starts each regmap in cache-only mode until the device attaches, initializes the two delayed works, registers the main component, and then conditionally registers the DMIC component. According to the comment "HW init will be performed when device reports present", the function sets the [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L25) flags false and defers the real device programming to attach time:

```c
/* sound/soc/codecs/rt712-sdca.c:1641 */
int rt712_sdca_init(struct device *dev, struct regmap *regmap,
			struct regmap *mbq_regmap, struct sdw_slave *slave)
{
	struct rt712_sdca_priv *rt712;
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

	mutex_init(&rt712->calibrate_mutex);
	mutex_init(&rt712->disable_irq_lock);

	INIT_DELAYED_WORK(&rt712->jack_detect_work, rt712_sdca_jack_detect_handler);
	INIT_DELAYED_WORK(&rt712->jack_btn_check_work, rt712_sdca_btn_check_handler);
	...
	if (slave->id.part_id != RT712_PART_ID_713)
		ret =  devm_snd_soc_register_component(dev,
				&soc_sdca_dev_rt712, rt712_sdca_dai, ARRAY_SIZE(rt712_sdca_dai));
	else
		ret =  devm_snd_soc_register_component(dev,
				&soc_sdca_dev_rt712, rt712_sdca_dai, 1);
	if (ret < 0)
		return ret;

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
	...
}
```

The [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18) is the meeting point between the SoundWire bind and the ASoC components. The SoundWire side stores the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L23), the two regmaps, and the cached interrupt status, and the ASoC side stores the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L21) and [`dmic_component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L22), the [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27) pointer, the per-feature-unit mute caches, and the [`hw_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L37)/[`version_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L38) read at first attach:

```c
/* sound/soc/codecs/rt712-sdca.h:18 */
struct  rt712_sdca_priv {
	struct regmap *regmap;
	struct regmap *mbq_regmap;
	struct snd_soc_component *component;
	struct snd_soc_component *dmic_component;
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
	int jack_type;
	int jd_src;
	unsigned int scp_sdca_stat1;
	unsigned int scp_sdca_stat2;
	unsigned int hw_id;
	unsigned int version_id;
	bool dmic_function_found;
	bool fu0f_dapm_mute;
	bool fu0f_mixer_l_mute;
	bool fu0f_mixer_r_mute;
	bool fu1e_dapm_mute;
	bool fu1e_mixer_mute[4];
	bool fu05_dapm_mute;
	bool fu05_mixer_l_mute;
	bool fu05_mixer_r_mute;
};
```

The figure sorts those same members into the two faces, the slave and both regmaps on the SoundWire-bind side and the components and the jack hook on the ASoC side:

```
    struct rt712_sdca_priv: the meeting point of two driver faces
    ───────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────┐
    │ struct rt712_sdca_priv  (drvdata, shared by both components) │
    ├───────────────────────────────┬──────────────────────────────┤
    │ SoundWire-bind side           │ ASoC side                    │
    │   slave                       │   component                  │
    │   regmap, mbq_regmap          │   dmic_component             │
    │   params                      │   hs_jack, jd_src, jack_type │
    │   hw_init, first_hw_init      │   jack_detect_work           │
    │   scp_sdca_stat1/stat2        │   jack_btn_check_work        │
    │   hw_id, version_id           │   fu0f_*, fu1e_*, fu05_* mute│
    │   dmic_function_found         │   calibrate_mutex            │
    │   disable_irq, disable_irq_lock                              │
    └───────────────────────────────┴──────────────────────────────┘
```

### Two regmaps split the address space by value width

The single-byte controls and the two-byte feature-unit values do not share a regmap, because their value widths differ. [`rt712_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L360) builds the MBQ regmap with [`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) and the single-byte regmap with [`devm_regmap_init_sdw()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1196). The single-byte [`struct regmap_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L408) declares 8-bit values and covers the SDCA mutes, power states, group-entity controls, HID owner controls, and the vendor index window:

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:129 */
static const struct regmap_config rt712_sdca_regmap = {
	.reg_bits = 32,
	.val_bits = 8,
	.readable_reg = rt712_sdca_readable_register,
	.volatile_reg = rt712_sdca_volatile_register,
	.max_register = 0x44ffffff,
	.reg_defaults = rt712_sdca_reg_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt712_sdca_reg_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};

static const struct regmap_config rt712_sdca_mbq_regmap = {
	.name = "sdw-mbq",
	.reg_bits = 32,
	.val_bits = 16,
	.readable_reg = rt712_sdca_mbq_readable_register,
	.volatile_reg = rt712_sdca_mbq_volatile_register,
	.max_register = 0x41000312,
	.reg_defaults = rt712_sdca_mbq_defaults,
	.num_reg_defaults = ARRAY_SIZE(rt712_sdca_mbq_defaults),
	.cache_type = REGCACHE_MAPLE,
	.use_single_read = true,
	.use_single_write = true,
};
```

The two readability switches assign each address to a window. [`rt712_sdca_mbq_readable_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L74) lists the two-byte controls, the feature-unit volumes on [`RT712_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L181), [`RT712_SDCA_ENT_USER_FU0F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L183), [`RT712_SDCA_ENT_USER_FU06`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L182), and [`RT712_SDCA_ENT_USER_FU1E`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L185), plus the per-channel gains on the platform boost units:

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:74 */
static bool rt712_sdca_mbq_readable_register(struct device *dev, unsigned int reg)
{
	switch (reg) {
	...
	case SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU05, RT712_SDCA_CTL_FU_VOLUME, CH_01):
	case SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU05, RT712_SDCA_CTL_FU_VOLUME, CH_02):
	...
	case SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_USER_FU06, RT712_SDCA_CTL_FU_VOLUME, CH_01):
	case SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_USER_FU06, RT712_SDCA_CTL_FU_VOLUME, CH_02):
	...
	case SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_PLATFORM_FU15, RT712_SDCA_CTL_FU_CH_GAIN, CH_04):
		return true;
	default:
		return false;
	}
}
```

[`devm_regmap_init_sdw_mbq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h#L1210) is the two-argument MBQ initializer the rt712 driver uses, taking the slave and the config and inferring the per-register byte count from the MBQ bit in the address rather than from a size callback:

```c
/* include/linux/regmap.h:1210 */
#define devm_regmap_init_sdw_mbq(sdw, config)			\
	__regmap_lockdep_wrapper(__devm_regmap_init_sdw_mbq, #config,   \
				&sdw->dev, sdw, config, NULL)
```

### The component driver presents controls, DAPM, and the jack

The ASoC face of the codec is [`soc_sdca_dev_rt712`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1407), a [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that binds the control array, the DAPM widget and route arrays, the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), and the [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) hook. The [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) bit is set because the SoundWire transport fixes the wire byte order:

```c
/* sound/soc/codecs/rt712-sdca.c:1407 */
static const struct snd_soc_component_driver soc_sdca_dev_rt712 = {
	.probe = rt712_sdca_probe,
	.controls = rt712_sdca_controls,
	.num_controls = ARRAY_SIZE(rt712_sdca_controls),
	.dapm_widgets = rt712_sdca_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt712_sdca_dapm_widgets),
	.dapm_routes = rt712_sdca_audio_map,
	.num_dapm_routes = ARRAY_SIZE(rt712_sdca_audio_map),
	.set_jack = rt712_sdca_set_jack_detect,
	.endianness = 1,
};
```

The speaker controls and widgets are not in the base arrays; [`rt712_sdca_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1015) adds them at probe time on every part except the headphone-only 713, so a 713 device exposes no speaker path:

```c
/* sound/soc/codecs/rt712-sdca.c:1015 */
static int rt712_sdca_probe(struct snd_soc_component *component)
{
	struct snd_soc_dapm_context *dapm = snd_soc_component_to_dapm(component);
	struct rt712_sdca_priv *rt712 = snd_soc_component_get_drvdata(component);
	int ret;

	rt712_sdca_parse_dt(rt712, &rt712->slave->dev);
	rt712->component = component;

	/* add SPK route */
	if (rt712->hw_id != RT712_DEV_ID_713) {
		snd_soc_add_component_controls(component,
			rt712_sdca_spk_controls, ARRAY_SIZE(rt712_sdca_spk_controls));
		snd_soc_dapm_new_controls(dapm,
			rt712_sdca_spk_dapm_widgets, ARRAY_SIZE(rt712_sdca_spk_dapm_widgets));
		snd_soc_dapm_add_routes(dapm,
			rt712_sdca_spk_dapm_routes, ARRAY_SIZE(rt712_sdca_spk_dapm_routes));
	}
	...
}
```

Each entry in [`rt712_sdca_controls`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L713) is a mixer control whose register operands are a [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) address into a feature unit. The headphone playback volume reads and writes [`RT712_SDCA_ENT_USER_FU05`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L181) on [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L172), the headset-mic capture volume reads [`RT712_SDCA_ENT_USER_FU0F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L183), and the headphone boost reads [`RT712_SDCA_ENT_PLATFORM_FU44`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L201):

```c
/* sound/soc/codecs/rt712-sdca.c:713 */
static const struct snd_kcontrol_new rt712_sdca_controls[] = {
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU05, RT712_SDCA_CTL_FU_VOLUME, CH_01),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU05, RT712_SDCA_CTL_FU_VOLUME, CH_02),
		0, 0x57, 0,
		rt712_sdca_set_gain_get, rt712_sdca_set_gain_put, out_vol_tlv),
	SOC_DOUBLE_EXT("FU0F Capture Switch", SND_SOC_NOPM, 0, 1, 1, 0,
		rt712_sdca_fu0f_capture_get, rt712_sdca_fu0f_capture_put),
	SOC_DOUBLE_R_EXT_TLV("FU0F Capture Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU0F, RT712_SDCA_CTL_FU_VOLUME, CH_01),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_USER_FU0F, RT712_SDCA_CTL_FU_VOLUME, CH_02),
		0, 0x3f, 0,
		rt712_sdca_set_gain_get, rt712_sdca_set_gain_put, mic_vol_tlv),
	SOC_DOUBLE_R_EXT_TLV("FU44 Boost Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_PLATFORM_FU44, RT712_SDCA_CTL_FU_CH_GAIN, CH_01),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_PLATFORM_FU44, RT712_SDCA_CTL_FU_CH_GAIN, CH_02),
		8, 3, 0,
		rt712_sdca_set_gain_get, rt712_sdca_set_gain_put, boost_vol_tlv),
	SOC_DOUBLE_EXT("FU05 Playback Switch", SND_SOC_NOPM, 0, 1, 1, 0,
		rt712_sdca_fu05_playback_get, rt712_sdca_fu05_playback_put),
};
```

The DAPM graph in [`rt712_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L944) names the analog pins, the feature-unit DAC and ADC widgets, the input mux, the power-domain supply widgets, and one AIF endpoint per data port. The AIF widgets carry the same stream names the DAIs declare, so the core can connect the playback and capture paths to the front end:

```c
/* sound/soc/codecs/rt712-sdca.c:944 */
static const struct snd_soc_dapm_widget rt712_sdca_dapm_widgets[] = {
	SND_SOC_DAPM_OUTPUT("HP"),
	SND_SOC_DAPM_INPUT("MIC2"),
	SND_SOC_DAPM_INPUT("LINE2"),

	SND_SOC_DAPM_SUPPLY("PDE 40", SND_SOC_NOPM, 0, 0,
		rt712_sdca_pde40_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_SUPPLY("PDE 12", SND_SOC_NOPM, 0, 0,
		rt712_sdca_pde12_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),

	SND_SOC_DAPM_DAC_E("FU 05", NULL, SND_SOC_NOPM, 0, 0,
		rt712_sdca_fu05_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_ADC_E("FU 0F", NULL, SND_SOC_NOPM, 0, 0,
		rt712_sdca_fu0f_event,
		SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_MUX("ADC 23 Mux", SND_SOC_NOPM, 0, 0,
		&rt712_sdca_adc23_mux),

	SND_SOC_DAPM_AIF_IN("DP1RX", "DP1 Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("DP4TX", "DP4 Capture", 0, SND_SOC_NOPM, 0, 0),
};
```

The routes in [`rt712_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L969) connect those endpoints to the feature units and pull in the matching power-domain supply for each path, so that powering up the headphone output (`HP`) requires the `PDE 40` supply and the headset-mic capture (`DP4TX`) requires `PDE 12`:

```c
/* sound/soc/codecs/rt712-sdca.c:969 */
static const struct snd_soc_dapm_route rt712_sdca_audio_map[] = {
	{ "FU 05", NULL, "DP1RX" },
	{ "DP4TX", NULL, "FU 0F" },

	{ "FU 0F", NULL, "PDE 12" },
	{ "FU 0F", NULL, "ADC 23 Mux" },
	{ "ADC 23 Mux", "LINE2", "LINE2" },
	{ "ADC 23 Mux", "MIC2", "MIC2" },

	{ "HP", NULL, "PDE 40" },
	{ "HP", NULL, "FU 05" },
};
```

A power-domain supply widget runs an event handler that writes the SDCA [`RT712_SDCA_CTL_REQ_POWER_STATE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L213) control of its entity, requesting power state 0 on power-up and power state 3 on power-down. The speaker handler [`rt712_sdca_pde23_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L906) writes [`RT712_SDCA_ENT_PDE23`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L187) on [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L175):

```c
/* sound/soc/codecs/rt712-sdca.c:906 */
static int rt712_sdca_pde23_event(struct snd_soc_dapm_widget *w,
	struct snd_kcontrol *kcontrol, int event)
{
	struct snd_soc_component *component =
		snd_soc_dapm_to_component(w->dapm);
	struct rt712_sdca_priv *rt712 = snd_soc_component_get_drvdata(component);
	unsigned char ps0 = 0x0, ps3 = 0x3;

	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_PDE23,
				RT712_SDCA_CTL_REQ_POWER_STATE, 0),
				ps0);
		break;
	case SND_SOC_DAPM_PRE_PMD:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_PDE23,
				RT712_SDCA_CTL_REQ_POWER_STATE, 0),
				ps3);
		break;

	default:
		break;
	}

	return 0;
}
```

Each such supply hangs off a path entity by a ▲ edge in the wider graph, the playback DP1RX running through FU 05 to HP and the capture mux feeding FU 0F out to DP4TX:

```
    rt712_sdca_audio_map: DAPM graph, supplies hang off via ▲
    ───────────────────────────────────────────────────────────

    playback   DP1RX ──▶ FU 05 ──▶ HP ◀── PDE 40   (supply)

    capture    MIC2 ──┐
                      ▼
              ADC 23 Mux ──▶ FU 0F ──▶ DP4TX
                      ▲          ▲
               LINE2 ─┘          │
                              PDE 12        (supply)

    each edge {sink, NULL, source} from rt712_sdca_audio_map[]
    speaker path added at probe (non-713): DP3 ▶ FU 06, PDE 23 supply
```

### Two codec DAIs plus a microphone DAI

The codec presents two interfaces in [`rt712_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1592). The `aif1` entry declares both a playback capability with the `DP1 Playback` stream name and a capture capability with the `DP4 Capture` stream name, and the `aif2` entry declares the `DP3 Playback` speaker stream, both pointing at [`rt712_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1585):

```c
/* sound/soc/codecs/rt712-sdca.c:1592 */
static struct snd_soc_dai_driver rt712_sdca_dai[] = {
	{
		.name = "rt712-sdca-aif1",
		.id = RT712_AIF1,
		.playback = {
			.stream_name = "DP1 Playback",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT712_STEREO_RATES,
			.formats = RT712_FORMATS,
		},
		.capture = {
			.stream_name = "DP4 Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT712_STEREO_RATES,
			.formats = RT712_FORMATS,
		},
		.ops = &rt712_sdca_ops,
	},
	{
		.name = "rt712-sdca-aif2",
		.id = RT712_AIF2,
		.playback = {
			.stream_name = "DP3 Playback",
			...
		},
		.ops = &rt712_sdca_ops,
	}
};

static struct snd_soc_dai_driver rt712_sdca_dmic_dai[] = {
	{
		.name = "rt712-sdca-aif3",
		.id = RT712_AIF3,
		.capture = {
			.stream_name = "DP8 Capture",
			.channels_min = 1,
			.channels_max = 4,
			.rates = RT712_STEREO_RATES,
			.formats = RT712_FORMATS,
		},
		.ops = &rt712_sdca_ops,
	}
};
```

The DAI ids are an enum in the codec header, with [`RT712_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L232) for the headset and headphone, [`RT712_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L233) for the speaker, and [`RT712_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L234) for the on-device DMIC component:

```c
/* sound/soc/codecs/rt712-sdca.h:231 */
enum {
	RT712_AIF1,
	RT712_AIF2,
	RT712_AIF3,
};
```

All three DAIs share one function pointer struct, and it fills only four callbacks, so the ASoC core treats every other op as a no-op behind its wrapper guards:

```c
/* sound/soc/codecs/rt712-sdca.c:1585 */
static const struct snd_soc_dai_ops rt712_sdca_ops = {
	.hw_params	= rt712_sdca_pcm_hw_params,
	.hw_free	= rt712_sdca_pcm_hw_free,
	.set_stream	= rt712_sdca_set_sdw_stream,
	.shutdown	= rt712_sdca_shutdown,
};
```

The machine layer hands the codec a SoundWire stream handle through the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op, and [`rt712_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1433) stores it per direction with [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506), while [`rt712_sdca_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1441) clears it:

```c
/* sound/soc/codecs/rt712-sdca.c:1433 */
static int rt712_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}

static void rt712_sdca_shutdown(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	snd_soc_dai_set_dma_data(dai, substream, NULL);
}
```

### hw_params selects the data port and joins the stream

[`rt712_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1447) reads the stored handle back with [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497), rejects [`RT712_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L234) on RT712_VA silicon, then maps the DAI id and the substream direction to one SoundWire data port. The mapping uses [`RT712_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L232) port 1 for headphone playback, [`RT712_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L232) port 4 for headset-mic capture, [`RT712_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L233) port 3 for speaker playback, and [`RT712_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L234) port 8 for digital-mic capture:

```c
/* sound/soc/codecs/rt712-sdca.c:1447 */
	/* VA doesn't support AIF3 */
	if (dai->id == RT712_AIF3 && rt712->version_id == RT712_VA)
		return -EINVAL;

	/* SoundWire specific configuration */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		direction = SDW_DATA_DIR_RX;
		if (dai->id == RT712_AIF1)
			port = 1;
		else if (dai->id == RT712_AIF2)
			port = 3;
		else
			return -EINVAL;
	} else {
		direction = SDW_DATA_DIR_TX;
		if (dai->id == RT712_AIF1)
			port = 4;
		else if (dai->id == RT712_AIF3)
			port = 8;
		else
			return -EINVAL;
	}
```

It then fills a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) from the negotiated parameters and a [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) with the channel mask and the chosen port, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt712-sdca.c:1447 */
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt712->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
```

[`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) allocates the master and slave runtimes, configures the slave port, and advances the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) on the first slave add. After the slave is added, the op programs the sample rate into the SDCA clock-source entity for the active interface, again by name. For [`RT712_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L232) it writes both [`RT712_SDCA_ENT_CS01`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L191) and [`RT712_SDCA_ENT_CS11`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L192) on [`FUNC_NUM_JACK_CODEC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L172); for [`RT712_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L233) it writes [`RT712_SDCA_ENT_CS31`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L195) on [`FUNC_NUM_AMP`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L175); for [`RT712_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L234) it writes [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) and [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194) on [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173):

```c
/* sound/soc/codecs/rt712-sdca.c:1534 */
	/* set sampling frequency */
	switch (dai->id) {
	case RT712_AIF1:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_CS01, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
			sampling_rate);
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_CS11, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
			sampling_rate);
		break;
	case RT712_AIF2:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_AMP, RT712_SDCA_ENT_CS31, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
			sampling_rate);
		break;
	case RT712_AIF3:
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1F, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
			sampling_rate);
		regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1C, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
			sampling_rate);
		break;
	...
	}
```

The teardown is the mirror image. [`rt712_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1565) reads the same stored handle and removes the codec from the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228), which frees the slave port and runtime:

```c
/* sound/soc/codecs/rt712-sdca.c:1565 */
static int rt712_sdca_pcm_hw_free(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt712_sdca_priv *rt712 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_runtime *sdw_stream =
		snd_soc_dai_get_dma_data(dai, substream);

	if (!rt712->slave)
		return -EINVAL;

	sdw_stream_remove_slave(rt712->slave, sdw_stream);
	return 0;
}
```

On the way in the params op pairs the stream direction with the DAI id, a playback landing on port 1 for aif1 and port 3 for aif2 and a capture on port 4 for aif1 and port 8 for aif3:

```
    rt712_sdca_pcm_hw_params(): direction x DAI id selects port
    ─────────────────────────────────────────────────────────────

    stream            dai->id        direction        port
    ┌───────────────┬────────────┬───────────────┬───────────┐
    │ PLAYBACK      │ RT712_AIF1 │ SDW_DIR_RX    │  1        │
    │ PLAYBACK      │ RT712_AIF2 │ SDW_DIR_RX    │  3        │
    │ CAPTURE       │ RT712_AIF1 │ SDW_DIR_TX    │  4        │
    │ CAPTURE       │ RT712_AIF3 │ SDW_DIR_TX    │  8        │
    └───────────────┴────────────┴───────────────┴───────────┘
    guard: RT712_AIF3 on RT712_VA silicon → -EINVAL
    any other id for the direction        → -EINVAL
```

### The bus driver binds the device and advertises its ports

The SoundWire peripheral driver [`rt712_sdca_sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L493) supplies the probe, the remove, the PM ops, the [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), and the slave ops:

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:493 */
static struct sdw_driver rt712_sdca_sdw_driver = {
	.driver = {
		.name = "rt712-sdca",
		.pm = pm_ptr(&rt712_sdca_pm),
	},
	.probe = rt712_sdca_sdw_probe,
	.remove = rt712_sdca_sdw_remove,
	.ops = &rt712_sdca_slave_ops,
	.id_table = rt712_sdca_id,
};
module_sdw_driver(rt712_sdca_sdw_driver);
```

The bus calls back into the codec through [`rt712_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L354), which fills the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) members of the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616):

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:354 */
static const struct sdw_slave_ops rt712_sdca_slave_ops = {
	.read_prop = rt712_sdca_read_prop,
	.interrupt_callback = rt712_sdca_interrupt_callback,
	.update_status = rt712_sdca_update_status,
};
```

[`rt712_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L190) first calls the generic [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) to read the firmware-described properties, then overrides the data ports the device drives by setting the [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L390) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L391) bitmaps in the [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and allocating a [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) for each set bit. The source ports are 8 and 4 (the DMIC and headset-mic capture ports), the sink ports are 3 and 1 (the speaker and headphone playback ports), matching the data ports the DAIs select, and it sets [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L395) so the bus enables the bus-clash and parity interrupts:

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:190 */
static int rt712_sdca_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	...
	sdw_slave_read_prop(slave);

	prop->scp_int1_mask = SDW_SCP_INT1_BUS_CLASH | SDW_SCP_INT1_PARITY;
	prop->quirks = SDW_SLAVE_QUIRKS_INVALID_INITIAL_PARITY;

	prop->paging_support = true;

	/* first we need to allocate memory for set bits in port lists */
	prop->source_ports = BIT(8) | BIT(4); /* BITMAP: 100010000 */
	prop->sink_ports = BIT(3) | BIT(1); /* BITMAP:  00001010 */

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

### update_status runs the deferred hardware init

[`rt712_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L156) is the entry point that turns an attach event into device programming. When the slave reports [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) it marks [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L25) false, and when it reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) with [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L25) still false it runs [`rt712_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1846). On re-attach with the jack already in use it rewrites the SDCA interrupt masks, because, according to the comment, "the SCP_SDCA_INTMASK will be cleared by any reset":

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:156 */
static int rt712_sdca_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt712_sdca_priv *rt712 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt712->hw_init = false;

	if (status == SDW_SLAVE_ATTACHED) {
		if (rt712->hs_jack) {
			...
			sdw_write_no_pm(rt712->slave, SDW_SCP_SDCA_INTMASK1,
				SDW_SCP_SDCA_INTMASK_SDCA_0);
			sdw_write_no_pm(rt712->slave, SDW_SCP_SDCA_INTMASK2,
				SDW_SCP_SDCA_INTMASK_SDCA_8);
		}
	}

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt712->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt712_sdca_io_init(&slave->dev, slave);
}
```

[`rt712_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1846) takes both regmaps out of cache-only mode, reads the [`hw_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L37) and [`version_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L38) from the vendor index window, and dispatches to the VA or VB hardware-init path. For RT712_VB it also enables multilane support and runs [`rt712_sdca_vb_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1768), which programs each of the three functions only when its [`FUNCTION_NEEDS_INITIALIZATION`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L219) status bit is set:

```c
/* sound/soc/codecs/rt712-sdca.c:1846 */
int rt712_sdca_io_init(struct device *dev, struct sdw_slave *slave)
{
	struct rt712_sdca_priv *rt712 = dev_get_drvdata(dev);
	unsigned int val;
	struct sdw_slave_prop *prop = &slave->prop;
	...
	rt712_sdca_index_read(rt712, RT712_VENDOR_REG, RT712_JD_PRODUCT_NUM, &val);
	rt712->hw_id = (val & 0xf000) >> 12;
	rt712->version_id = (val & 0x0f00) >> 8;
	...
	if (rt712->version_id == RT712_VA) {
		if (rt712->dmic_function_found) {
			dev_err(&slave->dev, "%s RT712 VA detected but SMART_MIC function exposed in ACPI\n",
				__func__);
			goto suspend;
		}

		rt712_sdca_va_io_init(rt712);
	} else {
		...
		/* multilanes and DMIC are supported by rt712vb */
		prop->lane_control_support = true;
		rt712_sdca_vb_io_init(rt712);
	}

	/*
	 * if set_jack callback occurred early than io_init,
	 * we set up the jack detection function now
	 */
	if (rt712->hs_jack)
		rt712_sdca_jack_init(rt712);
	...
	/* Mark Slave initialization complete */
	rt712->hw_init = true;
	...
}
```

### The interrupt routes through the SDCA cascade to the jack work

A device interrupt arrives at [`rt712_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-sdw.c#L254) in thread context. It reads the two SDCA interrupt status registers [`SDW_SCP_SDCA_INT1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L136) (0x58) and [`SDW_SCP_SDCA_INT2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L146) (0x59) with [`sdw_read_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L557), caches them in [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L35) and [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L36), clears the SDCA_0 and SDCA_8 bits in a retry loop with [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480), and queues [`jack_detect_work`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L28) when the [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L529) status in the [`struct sdw_slave_intr_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) argument is set:

```c
/* sound/soc/codecs/rt712-sdca-sdw.c:254 */
	ret = sdw_read_no_pm(rt712->slave, SDW_SCP_SDCA_INT1);
	if (ret < 0)
		goto io_error;
	rt712->scp_sdca_stat1 = ret;
	ret = sdw_read_no_pm(rt712->slave, SDW_SCP_SDCA_INT2);
	if (ret < 0)
		goto io_error;
	rt712->scp_sdca_stat2 = ret;
	...
	if (status->sdca_cascade && !rt712->disable_irq)
		mod_delayed_work(system_power_efficient_wq,
			&rt712->jack_detect_work, msecs_to_jiffies(30));
```

The cached status drives the work handler. [`rt712_sdca_jack_detect_handler()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L261) runs headset detection when [`SDW_SCP_SDCA_INT_SDCA_0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L137) is set in the cached [`scp_sdca_stat1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L35), runs button detection when [`SDW_SCP_SDCA_INT_SDCA_8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L147) is set in [`scp_sdca_stat2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L36), and reports the result with [`snd_soc_jack_report()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-jack.c#L33):

```c
/* sound/soc/codecs/rt712-sdca.c:261 */
	/* SDW_SCP_SDCA_INT_SDCA_0 is used for jack detection */
	if (rt712->scp_sdca_stat1 & SDW_SCP_SDCA_INT_SDCA_0) {
		ret = rt712_sdca_headset_detect(rt712);
		if (ret < 0)
			return;
	}

	/* SDW_SCP_SDCA_INT_SDCA_8 is used for button detection */
	if (rt712->scp_sdca_stat2 & SDW_SCP_SDCA_INT_SDCA_8)
		btn_type = rt712_sdca_button_detect(rt712);
	...
	snd_soc_jack_report(rt712->hs_jack, rt712->jack_type | btn_type,
			SND_JACK_HEADSET |
			SND_JACK_BTN_0 | SND_JACK_BTN_1 |
			SND_JACK_BTN_2 | SND_JACK_BTN_3);
```

[`rt712_sdca_headset_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L218) reads the group-entity detected mode and maps it to a jack type, then latches the selected mode back, so a TRS plug becomes a headphone and a TRRS plug a full headset:

```c
/* sound/soc/codecs/rt712-sdca.c:218 */
	/* get detected_mode */
	ret = regmap_read(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_GE49, RT712_SDCA_CTL_DETECTED_MODE, 0),
		&det_mode);
	if (ret < 0)
		goto io_error;

	switch (det_mode) {
	case 0x00:
		rt712->jack_type = 0;
		break;
	case 0x03:
		rt712->jack_type = SND_JACK_HEADPHONE;
		break;
	case 0x05:
		rt712->jack_type = SND_JACK_HEADSET;
		break;
	}

	/* write selected_mode */
	if (det_mode) {
		ret = regmap_write(rt712->regmap,
			SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT712_SDCA_ENT_GE49, RT712_SDCA_CTL_SELECTED_MODE, 0),
			det_mode);
		...
	}
```

The jack is wired in when the machine driver calls the component [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L99) op. [`rt712_sdca_set_jack_detect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L457) stores the [`struct snd_soc_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-jack.h#L80) pointer in [`hs_jack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L27) and calls [`rt712_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L404):

```c
/* sound/soc/codecs/rt712-sdca.c:457 */
static int rt712_sdca_set_jack_detect(struct snd_soc_component *component,
	struct snd_soc_jack *hs_jack, void *data)
{
	struct rt712_sdca_priv *rt712 = snd_soc_component_get_drvdata(component);
	int ret;

	rt712->hs_jack = hs_jack;

	if (!rt712->first_hw_init)
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

	rt712_sdca_jack_init(rt712);

	pm_runtime_put_autosuspend(component->dev);

	return 0;
}
```

[`rt712_sdca_jack_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L404) enables the HID1 button event and the detected-mode-change event through the vendor index window, unmasks the two SDCA interrupt sources with [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L480) by writing [`SDW_SCP_SDCA_INTMASK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L176) (0x5C) and [`SDW_SCP_SDCA_INTMASK2`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L186) (0x5D), and triggers the group-entity interrupt so an already-inserted jack is reported at init:

```c
/* sound/soc/codecs/rt712-sdca.c:404 */
static void rt712_sdca_jack_init(struct rt712_sdca_priv *rt712)
{
	mutex_lock(&rt712->calibrate_mutex);

	if (rt712->hs_jack) {
		/* Enable HID1 event & set button RTC mode */
		rt712_sdca_index_write(rt712, RT712_VENDOR_HDA_CTL,
			RT712_UMP_HID_CTL5, 0xfff0);
		...
		/* detected_mode_change_event_en & hid1_push_button_event_en */
		rt712_sdca_index_update_bits(rt712, RT712_VENDOR_HDA_CTL,
			RT712_GE_RELATED_CTL1, 0x0c00, 0x0c00);
		...
		/* set SCP_SDCA_IntMask1[0]=1 */
		sdw_write_no_pm(rt712->slave, SDW_SCP_SDCA_INTMASK1, SDW_SCP_SDCA_INTMASK_SDCA_0);
		/* set SCP_SDCA_IntMask2[0]=1 */
		sdw_write_no_pm(rt712->slave, SDW_SCP_SDCA_INTMASK2, SDW_SCP_SDCA_INTMASK_SDCA_8);
		...
		/* trigger GE interrupt */
		rt712_sdca_index_update_bits(rt712, RT712_VENDOR_HDA_CTL,
			RT712_GE_RELATED_CTL1, 0x0080, 0x0080);
		rt712_sdca_index_update_bits(rt712, RT712_VENDOR_HDA_CTL,
			RT712_GE_RELATED_CTL1, 0x0080, 0x0000);
	} else {
		...
	}

	mutex_unlock(&rt712->calibrate_mutex);
}
```

Once those sources are unmasked the cascade bit schedules the detect worker after 30ms, its GE49 detected_mode reading 0x03 as headphone and 0x05 as headset while the HID branch adds the button bits to the report:

```
    SDCA cascade gates the jack work; GE49 detected_mode picks the type
    ────────────────────────────────────────────────────────────────────

    interrupt_callback: read SCP_SDCA_INT1/INT2 into stat1/stat2
              │
              │ status->sdca_cascade && !disable_irq
              ▼  mod_delayed_work +30ms
    jack_detect_work ─▶ rt712_sdca_jack_detect_handler
              │ stat1 & SDCA_0          │ stat2 & SDCA_8
              ▼                         ▼
        headset_detect             button_detect
        (GE49 detected_mode)       (HID UMP)
              │
        ┌─────┴───────────┬──────────────────┐
        ▼                 ▼                  ▼
     0x00              0x03               0x05
     jack_type=0   SND_JACK_HEADPHONE  SND_JACK_HEADSET
        │                 │                  │
        └─────────────────┴────────┬─────────┘
                                   ▼
        snd_soc_jack_report(jack_type + btn_type,
                            mask = SND_JACK_HEADSET + BTN_0..3)
```

### The DMIC sub-function as a distinct codec

The microphone array appears in two driver forms. On an RT712_VB device, the main driver registers the second component [`soc_sdca_dev_rt712_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.c#L1419) on the same SoundWire peripheral, with its own `aif3` DAI on DP8 and its own FU1E controls and DMIC DAPM graph; that component shares the [`struct rt712_sdca_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L18) and both regmaps with the headset and amp. Separately, [`rt712-sdca-dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c) is a wholly independent SoundWire peripheral driver, registered by its own [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) and bound on a different device address. Its match table [`rt712_sdca_dmic_id`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L870) holds part ids 0x1712 through 0x1717, distinct from the 0x712 family of the main codec:

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

The separate driver carries its own slave ops, and because it has no headset jack it fills only [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), with no [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:941 */
static const struct sdw_slave_ops rt712_sdca_dmic_slave_ops = {
	.read_prop = rt712_sdca_dmic_read_prop,
	.update_status = rt712_sdca_dmic_update_status,
};

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

Its [`rt712_sdca_dmic_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L630) is simpler than the codec path because the microphone has one capture interface on a fixed data port. It always uses [`SDW_DATA_DIR_TX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L174) and port 2, supports the wider 16 kHz to 192 kHz rate set, and writes the [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173) clock sources [`RT712_SDCA_ENT_CS1F`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L193) and [`RT712_SDCA_ENT_CS1C`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L194):

```c
/* sound/soc/codecs/rt712-sdca-dmic.c:630 */
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = SDW_DATA_DIR_TX;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = 2;

	retval = sdw_stream_add_slave(rt712->slave, &stream_config,
					&port_config, 1, sdw_stream);
	...
	/* set sampling frequency */
	regmap_write(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1F, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);
	regmap_write(rt712->regmap,
		SDW_SDCA_CTL(FUNC_NUM_MIC_ARRAY, RT712_SDCA_ENT_CS1C, RT712_SDCA_CTL_SAMPLE_FREQ_INDEX, 0),
		sampling_rate);
```

The separate driver also runs its own first-attach init [`rt712_sdca_dmic_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca-dmic.c#L178), which programs only the microphone-related float controls and the [`RT712_SDCA_ENT_IT26`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L198) input terminal of [`FUNC_NUM_MIC_ARRAY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt712-sdca.h#L173), with no headset calibration or jack path. The two forms reach the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) FU1E controls; they differ only in whether the microphone shares the codec's device and private data or stands as its own peripheral.

The whole codec reduces to this one model. The controls, the DAPM power-domain widgets, the clock-source rate writes, and the jack-detection group-entity reads all address SDCA function entities through the same [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) space, and the DAIs differ only in which function and data port their [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op selects, so adding a feature to the codec is a matter of naming a new entity and control rather than decoding a new register block.

```
    The DMIC array reaches the same FU1E controls through two drivers
    ──────────────────────────────────────────────────────────────────

                  FUNC_NUM_MIC_ARRAY  FU1E capture controls
                          ▲                       ▲
          same wire model │                       │ same wire model
        ┌─────────────────┴───────┐   ┌───────────┴──────────────────┐
        │ form A: on 0x712 device │   │ form B: 0x1712 peripheral    │
        ├─────────────────────────┤   ├──────────────────────────────┤
        │ soc_sdca_dev_rt712_dmic │   │ rt712_sdca_dmic_sdw_driver   │
        │ aif3  DP8 Capture       │   │ aif1  DP2 Capture            │
        │ shares rt712_sdca_priv  │   │ own rt712_sdca_dmic_priv     │
        │ shares both regmaps     │   │ own regmaps + slave_ops      │
        │ registered on VB only   │   │ own match table 0x1712..7    │
        └─────────────────────────┘   └──────────────────────────────┘
```
