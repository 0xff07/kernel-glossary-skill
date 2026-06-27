# DAPM stream widgets

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The stream-domain widgets are the DAPM nodes that tie a PCM substream to the power graph, so opening a substream powers up exactly the codec blocks the audio passes through and closing it powers them down. ASoC builds one [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) or [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widget per DAI direction in [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) and stores it in the DAI's [`widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L425) field, then the codec's own [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255), [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265), [`SND_SOC_DAPM_DAC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L275), and [`SND_SOC_DAPM_ADC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L286) widgets carry the signal from that anchor down to the analog pins. The DAI widget is the anchor, joined to the codec AIF widget by name in [`snd_soc_dapm_connect_dai_link_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4567), and powered on by a [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) event when the PCM starts. The Realtek rt722-sdca codec, an SDCA part on SoundWire driven by an x86 ACPI machine driver, is the worked example, declaring four AIF widgets, two [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) and two [`SND_SOC_DAPM_ADC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290) function-unit widgets, and three DAIs whose DAI widgets the core creates from the stream names.

```
    Stream-domain widgets joining a DAI to the DAPM graph
    ─────────────────────────────────────────────────────

    playback (DAC path, snd_soc_dapm_dai_in anchor)

       snd_soc_dai (codec)
       ┌────────────────────────────┐
       │ stream[PLAYBACK].widget ───┼──▶ DAI widget  (dai_in)
       └────────────────────────────┘    "DP1 Headphone Playback"
                                                │  connect_dai_link
                                                ▼
                                          AIF_IN widget  (aif_in)
                                          "DP1RX"
                                                │  route
                                                ▼
                                          DAC widget  (dac)
                                          "FU 42"
                                                │  route
                                                ▼
                                          rest of graph ──▶ output pin "HP"

    capture (ADC path, snd_soc_dapm_dai_out anchor)

       input pin "MIC2" ──▶ rest of graph
                                  │  route
                                  ▼
                            ADC widget  (adc)  "FU 36"
                                  │  route
                                  ▼
                            AIF_OUT widget  (aif_out)  "DP2TX"
                                  ▲  connect_dai_link
                                  │
       snd_soc_dai (codec)        │
       ┌──────────────────────────┴─┐
       │ stream[CAPTURE].widget ────┼──▶ DAI widget  (dai_out)
       └────────────────────────────┘    "DP2 Headset Capture"

    SND_SOC_DAPM_STREAM_START sets DAI-widget.active = 1, then
    dapm_power_widgets() powers every widget reachable along the route.
```

## SUMMARY

DAPM is a directed graph whose nodes are widgets and whose edges are routes, and a widget powers up only when a path of connected widgets reaches an active endpoint. The stream-domain widgets are the subset that brings a running PCM into that graph. For each direction a DAI supports, [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) creates one DAI widget, of type [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) for playback or [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) for capture, names it after the DAI's [`stream_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610), and records it in the DAI's per-direction [`widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L425) field through [`snd_soc_dai_set_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L490). The codec driver separately declares the widgets that carry the signal, placing an [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) or [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265) widget at the serial-bus port, an [`SND_SOC_DAPM_DAC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L275) or [`SND_SOC_DAPM_ADC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L286) widget at the converter, and the mixers and pins beyond them, so the codec widgets carry the types [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L446), [`snd_soc_dapm_aif_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447), [`snd_soc_dapm_dac`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L433), and [`snd_soc_dapm_adc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L432).

At card bind time [`snd_soc_dapm_connect_dai_link_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4567) joins the DAI widget to the codec AIF widget, and [`dapm_connect_dai_pair()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4484) reads each side's widget back with [`snd_soc_dai_get_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482) and adds the route. The DAI widget is the only stream-domain widget whose power state the stream event sets directly. When a PCM starts, [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) runs with [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378), [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) sets the DAI widget's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) bit and marks it an endpoint, and [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) powers up every widget on a connected path from that endpoint. The AIF, DAC, and ADC widgets are never powered by the stream event itself; they power on because the now-active DAI widget makes a path through them reach an endpoint, and on [`SND_SOC_DAPM_STREAM_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L379) the same recompute powers them back down.

## SPECIFICATIONS

The DAPM widget graph is a Linux kernel software construct and has no standalone hardware specification. The SoundWire data ports the rt722-sdca AIF widgets correspond to, and the function-unit entities the DAC and ADC widgets represent, are tracked in the kernel by the SDCA function and entity numbers the codec driver registers.

## LINUX KERNEL

### Stream-domain widget macros (soc-dapm.h)

- [`'\<SND_SOC_DAPM_AIF_IN\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255): an audio-interface-input widget at a serial-bus receive port; sets `.id = snd_soc_dapm_aif_in` and the stream name `stname`
- [`'\<SND_SOC_DAPM_AIF_IN_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L259): the same widget with an `event` callback and `event_flags`
- [`'\<SND_SOC_DAPM_AIF_OUT\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265): an audio-interface-output widget at a serial-bus transmit port; sets `.id = snd_soc_dapm_aif_out`
- [`'\<SND_SOC_DAPM_AIF_OUT_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L269): the same with an event callback
- [`'\<SND_SOC_DAPM_DAC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L275): a digital-to-analog converter widget; sets `.id = snd_soc_dapm_dac`
- [`'\<SND_SOC_DAPM_DAC_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279): a DAC widget with an event callback (rt722-sdca uses this for its playback function units)
- [`'\<SND_SOC_DAPM_ADC\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L286): an analog-to-digital converter widget; sets `.id = snd_soc_dapm_adc`
- [`'\<SND_SOC_DAPM_ADC_E\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290): an ADC widget with an event callback (rt722-sdca uses this for its capture function units)

### Widget types and stream-event constants (soc-dapm.h)

- [`'\<enum snd_soc_dapm_type\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L423): the widget-id enum; the stream-domain values are [`snd_soc_dapm_aif_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L446), [`snd_soc_dapm_aif_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L447), [`snd_soc_dapm_dac`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L433), [`snd_soc_dapm_adc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L432), [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451), [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452), and [`snd_soc_dapm_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L453)
- [`'\<struct snd_soc_dapm_widget\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516): the widget object, carrying the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), the widget [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L518), the stream name [`sname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L519), the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) and [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) state, and the [`priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523) back pointer the DAI widgets use
- [`'\<SND_SOC_DAPM_STREAM_START\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) (0x1), [`'\<SND_SOC_DAPM_STREAM_STOP\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L379) (0x2), and the suspend/resume/pause codes [`SND_SOC_DAPM_STREAM_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L380), [`SND_SOC_DAPM_STREAM_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L381), [`SND_SOC_DAPM_STREAM_PAUSE_PUSH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L382), [`SND_SOC_DAPM_STREAM_PAUSE_RELEASE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L383): the stream-event codes

### DAI-to-widget binding (soc-dai.h)

- [`'\<struct snd_soc_dai_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424): the per-direction DAI state whose first field is the bound [`widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L425)
- [`'\<snd_soc_dai_get_widget\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482): read [`dai->stream[stream].widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L425) for one direction
- [`'\<snd_soc_dai_set_widget\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L490): store the DAI widget, reached through [`snd_soc_dai_set_widget_playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L487) and [`snd_soc_dai_set_widget_capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L488)

### DAI-widget creation and connection (soc-dapm.c)

- [`'\<snd_soc_dapm_new_dai_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359): create the [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) and [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widgets and store each with [`snd_soc_dai_set_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L490)
- [`'\<snd_soc_dapm_connect_dai_link_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4567): for each non-dynamic link, pair the CPU and codec DAIs and connect their widgets
- [`'\<dapm_connect_dai_pair\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4484): read both DAI widgets and route them through [`dapm_connect_dai_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4463)
- [`'\<dapm_connect_dai_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4463): add the path edges from source DAI widget through any bridge to sink widget with [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604)
- [`'\<snd_soc_dapm_link_dai_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407): link DAI widgets to same-named AIF widgets inside one component
- [`'\<dapm_new_dai\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4278): create the [`snd_soc_dapm_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L453) widget between two DAIs on a codec-to-codec link

### Stream-event power path (soc-dapm.c)

- [`'\<snd_soc_dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620): the exported entry, taking the DAPM mutex and calling [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598)
- [`'\<dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598): run [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) over each DAI of the runtime, then call [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252)
- [`'\<dapm_dai_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530): set the DAI widget's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) and [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) state on start and stop and invalidate the cached endpoints
- [`'\<dapm_power_widgets\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252): recompute every widget's power from the active endpoints and apply the register writes

### rt722-sdca and tas2783 worked examples (codecs)

- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the widget array, including the four AIF widgets `DP1RX`, `DP2TX`, `DP3RX`, `DP6TX`
- [`'rt722_sdca_dai':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three DAI descriptors whose [`stream_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) values name the DAI widgets
- [`'tas_dapm_widgets':'sound/soc/codecs/tas2783-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L856): the TAS2783 stream-domain widgets (`ASI`, `ASI OUT`, `FU21`, `FU23`)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget types, the stream-domain widgets, and the power-management model
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide, where the AIF, DAC, and ADC widgets are declared
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, where front-end and back-end stream events are sent independently
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the rt722-sdca AIF widgets correspond to

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The stream-domain widgets divide into two groups by who creates them. The DAI widgets are created by the core from the DAI descriptor and never appear in a codec driver's widget array, while the AIF, DAC, and ADC widgets are declared by the codec driver with the macros below. Each macro expands to a compound-literal [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) with a fixed [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L517), so the only difference between the plain and `_E` forms is an [`event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L550) callback that runs at power transitions.

| widget macro | expands to id | role in the stream path |
|---|---|---|
| `SND_SOC_DAPM_AIF_IN` / `_E` | `snd_soc_dapm_aif_in` | playback entry from the serial bus into the codec |
| `SND_SOC_DAPM_AIF_OUT` / `_E` | `snd_soc_dapm_aif_out` | capture exit from the codec onto the serial bus |
| `SND_SOC_DAPM_DAC` / `_E` | `snd_soc_dapm_dac` | digital-to-analog converter on the playback path |
| `SND_SOC_DAPM_ADC` / `_E` | `snd_soc_dapm_adc` | analog-to-digital converter on the capture path |
| (core-created) | `snd_soc_dapm_dai_in` | playback DAI anchor, named after the playback stream |
| (core-created) | `snd_soc_dapm_dai_out` | capture DAI anchor, named after the capture stream |
| (core-created) | `snd_soc_dapm_dai_link` | bridge widget between two DAIs on a codec-to-codec link |

The stream event is delivered as one of the constants below, and only [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) and [`SND_SOC_DAPM_STREAM_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L379) change a DAI widget's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) state; the suspend, resume, and pause codes reach [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) but fall through its switch without touching the active bit.

| stream event | value | effect on the DAI widget |
|---|---|---|
| `SND_SOC_DAPM_STREAM_START` | 0x1 | set `active = 1`, mark endpoint, then power up the path |
| `SND_SOC_DAPM_STREAM_STOP` | 0x2 | set `active = 0`, clear endpoint, then power down the path |
| `SND_SOC_DAPM_STREAM_SUSPEND` | 0x4 | no change to the widget; handled in suspend |
| `SND_SOC_DAPM_STREAM_RESUME` | 0x8 | no change to the widget |
| `SND_SOC_DAPM_STREAM_PAUSE_PUSH` | 0x10 | no change to the widget |
| `SND_SOC_DAPM_STREAM_PAUSE_RELEASE` | 0x20 | no change to the widget |

## DETAILS

### The DAI widget and the codec AIF widget are two separate nodes

A running stream reaches the power graph at one node, the DAI widget, which the core owns, and the signal then flows into nodes the codec owns. The DAI widget is created by [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) for whichever directions the DAI declares a stream name. It fills a template with [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) for playback and [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) for capture, names the widget after the matching [`stream_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610), sets [`w->priv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L523) back to the DAI, and stores the widget in the DAI's per-direction slot:

```c
/* sound/soc/soc-dapm.c:4359 */
int snd_soc_dapm_new_dai_widgets(struct snd_soc_dapm_context *dapm,
				 struct snd_soc_dai *dai)
{
	struct device *dev = snd_soc_dapm_to_dev(dapm);
	struct snd_soc_dapm_widget template;
	struct snd_soc_dapm_widget *w;

	WARN_ON(dev != dai->dev);

	memset(&template, 0, sizeof(template));
	template.reg = SND_SOC_NOPM;

	if (dai->driver->playback.stream_name) {
		template.id = snd_soc_dapm_dai_in;
		template.name = dai->driver->playback.stream_name;
		template.sname = dai->driver->playback.stream_name;
		...
		w = snd_soc_dapm_new_control_unlocked(dapm, &template);
		if (IS_ERR(w))
			return PTR_ERR(w);

		w->priv = dai;
		snd_soc_dai_set_widget_playback(dai, w);
	}

	if (dai->driver->capture.stream_name) {
		template.id = snd_soc_dapm_dai_out;
		template.name = dai->driver->capture.stream_name;
		template.sname = dai->driver->capture.stream_name;
		...
		w = snd_soc_dapm_new_control_unlocked(dapm, &template);
		if (IS_ERR(w))
			return PTR_ERR(w);

		w->priv = dai;
		snd_soc_dai_set_widget_capture(dai, w);
	}

	return 0;
}
```

The template's [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L528) is [`SND_SOC_NOPM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L26), so the DAI widget has no register of its own; its power is purely a graph property. [`snd_soc_dai_set_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L490) writes the per-direction [`widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L425) field of [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424):

```c
/* include/sound/soc-dai.h:490 */
static inline
void snd_soc_dai_set_widget(struct snd_soc_dai *dai, int stream, struct snd_soc_dapm_widget *widget)
{
	dai->stream[stream].widget = widget;
}
```

This call is made once per DAI from [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602), right after the component's own declared widgets have been registered:

```c
/* sound/soc/soc-core.c:1644 */
	for_each_component_dais(component, dai) {
		ret = snd_soc_dapm_new_dai_widgets(dapm, dai);
		if (ret != 0) {
			dev_err(component->dev,
				"Failed to create DAI widgets %d\n", ret);
			goto err_probe;
		}
	}
```

By the time this loop runs, the codec's AIF, DAC, and ADC widgets from its [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) array already exist as separate nodes, so the DAI widget and the AIF widget that shares its stream name are two distinct entries in the same component's widget list, waiting to be joined.

```
    snd_soc_dapm_new_dai_widgets links each DAI direction to a widget
    ────────────────────────────────────────────────────────────────
    (boxes are structs; arrows = populates / points-to)

      struct snd_soc_dai        created DAI widgets
      ┌──────────────────────┐          ┌──────────────────────────┐
      │ stream[PLAYBACK]     │          │ id = snd_soc_dapm_dai_in │
      │   .widget        ────┼────────▶ │ name = playback sname    │
      └──────────────────────┘          │ priv ──▶ back to dai     │
      ┌──────────────────────┐          └──────────────────────────┘
      │ stream[CAPTURE]      │          ┌──────────────────────────┐
      │   .widget        ────┼────────▶ │ id = snd_soc_dapm_dai_out│
      └──────────────────────┘          │ name = capture sname     │
                                        │ priv ──▶ back to dai     │
                                        └──────────────────────────┘
        snd_soc_dai_set_widget stores each; reg = SND_SOC_NOPM on both
```

### Reading the DAI widget back

Both the connection step and the stream-event step reach the DAI widget through [`snd_soc_dai_get_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482), which returns the pointer stored in the DAI's per-direction stream state, the first member of [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424):

```c
/* include/sound/soc-dai.h:482 */
static inline
struct snd_soc_dapm_widget *snd_soc_dai_get_widget(struct snd_soc_dai *dai, int stream)
{
	return dai->stream[stream].widget;
}
```

### Connecting the DAI widget to the codec AIF widget

The edge from the DAI widget to the codec AIF widget is added when the card binds, by [`snd_soc_dapm_connect_dai_link_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4567). It walks every PCM runtime, skips dynamic front-end links that have no fixed DAI mapping, and for each channel map pairs the CPU DAI with the codec DAI:

```c
/* sound/soc/soc-dapm.c:4567 */
void snd_soc_dapm_connect_dai_link_widgets(struct snd_soc_card *card)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_dai *cpu_dai;
	struct snd_soc_dai *codec_dai;

	/* for each BE DAI link... */
	for_each_card_rtds(card, rtd)  {
		struct snd_soc_dai_link_ch_map *ch_maps;
		int i;
		...
		if (rtd->dai_link->dynamic)
			continue;

		for_each_rtd_ch_maps(rtd, i, ch_maps) {
			cpu_dai   = snd_soc_rtd_to_cpu(rtd,   ch_maps->cpu);
			codec_dai = snd_soc_rtd_to_codec(rtd, ch_maps->codec);

			dapm_connect_dai_pair(card, rtd, codec_dai, cpu_dai);
		}
	}
}
```

[`dapm_connect_dai_pair()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4484) handles both directions in one loop. For each direction it reads the CPU-side and codec-side DAI widgets with [`snd_soc_dai_get_widget()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L482), skips the direction when either is absent, and passes them to [`dapm_connect_dai_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4463) with `src`/`sink` arrays that flip the edge direction between playback and capture:

```c
/* sound/soc/soc-dapm.c:4484 */
	struct snd_soc_dai *src_dai[]		= { cpu_dai,	codec_dai };
	struct snd_soc_dai *sink_dai[]		= { codec_dai,	cpu_dai };
	struct snd_soc_dapm_widget **src[]	= { &cpu,	&codec };
	struct snd_soc_dapm_widget **sink[]	= { &codec,	&cpu };
	...
	for_each_pcm_streams(stream) {
		...
		cpu	= snd_soc_dai_get_widget(cpu_dai,	stream_cpu);
		codec	= snd_soc_dai_get_widget(codec_dai,	stream_codec);

		if (!cpu || !codec)
			continue;
		...
		dapm_connect_dai_routes(dapm, src_dai[stream], *src[stream],
					rtd->c2c_widget[stream],
					sink_dai[stream], *sink[stream]);
	}
```

[`dapm_connect_dai_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4463) then adds the edges with [`dapm_add_path()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L604), inserting the optional codec-to-codec bridge widget when one is present:

```c
/* sound/soc/soc-dapm.c:4463 */
	if (dai) {
		dapm_add_path(dapm, src, dai, NULL, NULL);
		src = dai;
	}

	dapm_add_path(dapm, src, sink, NULL, NULL);
```

The edge from the codec DAI widget to the codec's own AIF widget is added separately by [`snd_soc_dapm_link_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407), which matches a DAI widget to every non-DAI widget in the same component whose stream name is a substring of the DAI widget's stream name, then adds the path in the right direction by the DAI widget's id:

```c
/* sound/soc/soc-dapm.c:4445 */
		if (!w->sname || !strstr(w->sname, dai_w->sname))
			continue;

		if (dai_w->id == snd_soc_dapm_dai_in) {
			src = dai_w;
			sink = w;
		} else {
			src = w;
			sink = dai_w;
		}
		dev_dbg(dai->dev, "%s -> %s\n", src->name, sink->name);
		dapm_add_path(w->dapm, src, sink, NULL, NULL);
```

For a [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) widget the path runs from the DAI widget into the AIF widget, and for a [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widget it runs from the AIF widget into the DAI widget, so the chain direction matches the data flow. Both functions run from [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) in sequence:

```c
/* sound/soc/soc-core.c:2250 */
	snd_soc_dapm_link_dai_widgets(card);
	snd_soc_dapm_connect_dai_link_widgets(card);
```

Inside the second call, the stream index picks which DAI is source and which is sink, playback running the edge from cpu to codec and capture running it from codec to cpu:

```
    dapm_connect_dai_pair: stream index flips the edge source and sink
    ─────────────────────────────────────────────────────────────────

    ┌────────────┬───────────────────┬───────────────────┬────────────┐
    │ stream     │ src_dai / src     │ sink_dai / sink   │ edge runs  │
    ├────────────┼───────────────────┼───────────────────┼────────────┤
    │ PLAYBACK 0 │ cpu_dai   / cpu   │ codec_dai / codec │ cpu ▶ codec│
    │ CAPTURE  1 │ codec_dai / codec │ cpu_dai   / cpu   │ codec ▶ cpu│
    └────────────┴───────────────────┴───────────────────┴────────────┘
        a present c2c_widget[stream] bridge is spliced between the two
        with dapm_add_path(src, dai), then dapm_add_path(src, sink)
```

### The stream event powers the DAI widget, the graph powers the rest

When userspace prepares a substream, [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) sends a [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) event, and after the pmdown delay [`snd_soc_close_delayed_work()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L427) sends [`SND_SOC_DAPM_STREAM_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L379). [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) takes the DAPM mutex and hands to [`dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4598), which runs [`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) over each DAI then calls [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) once:

```c
/* sound/soc/soc-dapm.c:4598 */
static void dapm_stream_event(struct snd_soc_pcm_runtime *rtd, int stream, int event)
{
	struct snd_soc_dai *dai;
	int i;

	for_each_rtd_dais(rtd, i, dai)
		dapm_dai_stream_event(dai, stream, event);

	dapm_power_widgets(rtd->card, event, NULL);
}
```

[`dapm_dai_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4530) is where a stream-domain widget's power state is set by the stream rather than by the graph. It reads the DAI widget, marks it dirty, computes whether it is a source endpoint ([`SND_SOC_DAPM_EP_SOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L607) for a [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451)) or a sink endpoint ([`SND_SOC_DAPM_EP_SINK`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L608)), and sets [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) and [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) by the event:

```c
/* sound/soc/soc-dapm.c:4530 */
static void dapm_dai_stream_event(struct snd_soc_dai *dai, int stream, int event)
{
	struct snd_soc_dapm_widget *w;

	w = snd_soc_dai_get_widget(dai, stream);

	if (w) {
		unsigned int ep;

		dapm_mark_dirty(w, "stream event");

		if (w->id == snd_soc_dapm_dai_in) {
			ep = SND_SOC_DAPM_EP_SOURCE;
			dapm_widget_invalidate_input_paths(w);
		} else {
			ep = SND_SOC_DAPM_EP_SINK;
			dapm_widget_invalidate_output_paths(w);
		}

		switch (event) {
		case SND_SOC_DAPM_STREAM_START:
			w->active = 1;
			w->is_ep = ep;
			break;
		case SND_SOC_DAPM_STREAM_STOP:
			w->active = 0;
			w->is_ep = 0;
			break;
		case SND_SOC_DAPM_STREAM_SUSPEND:
		case SND_SOC_DAPM_STREAM_RESUME:
		case SND_SOC_DAPM_STREAM_PAUSE_PUSH:
		case SND_SOC_DAPM_STREAM_PAUSE_RELEASE:
			break;
		}
	}
}
```

Only the DAI widget is touched here, and only on start or stop. The suspend, resume, and pause events reach the switch but leave [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) and [`is_ep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L542) unchanged, so they do not by themselves move the converter widgets. After the DAI widget becomes an active endpoint, [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) powers the AIF, DAC, and ADC widgets. They have no [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L534) flag set on them, but a connected path now runs from the active DAI-widget endpoint through them to the opposite endpoint, and they power back down at [`SND_SOC_DAPM_STREAM_STOP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L379) when clearing the DAI widget's endpoint status breaks that path.

```
    dapm_dai_stream_event: DAI-widget id and event set active and is_ep
    ──────────────────────────────────────────────────────────────────

    ep = EP_SOURCE if id == dai_in   else EP_SINK   (dai_out)

    ┌────────────────┬───────────┬──────────────────────────────┐
    │ event          │ active    │ is_ep                        │
    ├────────────────┼───────────┼──────────────────────────────┤
    │ STREAM_START   │   1       │ ep  (SOURCE for dai_in,      │
    │                │           │      SINK for dai_out)       │
    │ STREAM_STOP    │   0       │ 0                            │
    │ SUSPEND/RESUME │ unchanged │ unchanged                    │
    │ PAUSE_*        │ unchanged │ unchanged                    │
    └────────────────┴───────────┴──────────────────────────────┘
        only the DAI widget is touched; dapm_power_widgets then
        powers the AIF/DAC/ADC reachable from the active endpoint
```

### Worked example: rt722-sdca stream-domain widgets over SoundWire

The Realtek RT722 declares its stream-domain widgets in [`rt722_sdca_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996), with four AIF widgets at the SoundWire data ports and four converter function units as [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) and [`SND_SOC_DAPM_ADC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L290) widgets:

```c
/* sound/soc/codecs/rt722-sdca.c:1018 */
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

The second argument to each AIF macro is the stream name, and it is the same string the codec's DAI descriptor uses, which is how the DAI widget and the AIF widget come to share a name. The string `"DP1 Headphone Playback"` names both the [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) widget `DP1RX` and the playback stream of the codec's `aif1` DAI:

```c
/* sound/soc/codecs/rt722-sdca.c:1253 */
static struct snd_soc_dai_driver rt722_sdca_dai[] = {
	{
		.name = "rt722-sdca-aif1",
		.id = RT722_AIF1,
		.playback = {
			.stream_name = "DP1 Headphone Playback",
			...
		},
		.capture = {
			.stream_name = "DP2 Headset Capture",
			...
		},
		.ops = &rt722_sdca_ops,
	},
	...
```

When the codec probes, [`snd_soc_dapm_new_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4359) creates a [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) widget also named `"DP1 Headphone Playback"`, and [`snd_soc_dapm_link_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407) matches it against the AIF widget `DP1RX` whose [`sname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L519) is the same string, adding the edge from the DAI widget into `DP1RX`. The routes in [`rt722_sdca_audio_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043) carry the signal the rest of the way: `{"FU 42", NULL, "DP1RX"}` joins the DAC `FU 42` to `DP1RX`, and `{"HP", NULL, "FU 42"}` joins the `HP` output pin to `FU 42`, completing a chain from the DAI widget through `DP1RX` and `FU 42` to the `HP` endpoint. When a playback substream on `aif1` runs, the [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) event sets the `"DP1 Headphone Playback"` DAI widget active, and [`dapm_power_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L2252) powers `DP1RX`, `FU 42`, and the supply `PDE 47` that `HP` depends on, firing each converter's event callback at the right moment.

```
    rt722-sdca: shared stream name joins core DAI widget to AIF widget
    ─────────────────────────────────────────────────────────────────

    stream name (rt722_sdca_dai)     core DAI widget   codec AIF widget
    ┌───────────────────────────┐    ┌──────────────┐  ┌──────────────┐
    │ "DP1 Headphone Playback"  │ ─▶ │ dai_in       │  │ DP1RX aif_in │
    │ "DP2 Headset Capture"     │ ─▶ │ dai_out      │  │ DP2TX aif_out│
    │ "DP3 Speaker Playback"    │ ─▶ │ dai_in       │  │ DP3RX aif_in │
    │ "DP6 DMic Capture"        │ ─▶ │ dai_out      │  │ DP6TX aif_out│
    └───────────────────────────┘    └──────────────┘  └──────────────┘
        link_dai_widgets matches a DAI widget to the AIF widget whose
        sname is a substring; then routes: DP1RX ─▶ FU 42 ─▶ HP
```

### Additional example: tas2783 SDCA smart amplifier over SoundWire

The Texas Instruments TAS2783 is an SDCA smart amplifier on SoundWire, and it shows the same stream-domain pattern with a single playback amplifier and an IV-sense feedback capture path. Its [`tas_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L856) array declares one [`SND_SOC_DAPM_AIF_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L255) widget `ASI` carrying the playback stream `"ASI Playback"`, one [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265) widget `ASI OUT` carrying the IV-sense capture stream `"ASI Capture"`, and two [`SND_SOC_DAPM_DAC_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L279) function-unit widgets `FU21` and `FU23` whose [`tas_fu21_event`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L812) and [`tas_fu23_event`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/tas2783-sdw.c#L834) callbacks enable the function unit when DAPM powers each one up:

```c
/* sound/soc/codecs/tas2783-sdw.c:856 */
static const struct snd_soc_dapm_widget tas_dapm_widgets[] = {
	SND_SOC_DAPM_AIF_IN("ASI", "ASI Playback", 0, SND_SOC_NOPM, 0, 0),
	SND_SOC_DAPM_AIF_OUT("ASI OUT", "ASI Capture", 0, SND_SOC_NOPM,
			     0, 0),
	SND_SOC_DAPM_DAC_E("FU21", NULL, SND_SOC_NOPM, 0, 0, tas_fu21_event,
			   SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_DAC_E("FU23", NULL, SND_SOC_NOPM, 0, 0, tas_fu23_event,
			   SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_PRE_PMD),
	SND_SOC_DAPM_OUTPUT("SPK"),
	SND_SOC_DAPM_INPUT("DMIC"),
};
```

The stream-name strings `"ASI Playback"` and `"ASI Capture"` are what DAPM matches against the DAI stream, the same name-matching [`snd_soc_dapm_link_dai_widgets()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4407) does for the rt722-sdca part, so the core-created [`snd_soc_dapm_dai_in`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L451) widget named `"ASI Playback"` joins to the `ASI` aif_in widget and the [`snd_soc_dapm_dai_out`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L452) widget named `"ASI Capture"` joins to the `ASI OUT` aif_out widget.
