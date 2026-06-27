# Digital microphones (DMIC)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A digital microphone is a PDM (Pulse Density Modulation) transducer whose output is a one-bit oversampled bit stream that some decimation stage converts to PCM, and on an x86-64 ACPI laptop the kernel models one of two capture paths depending on where that decimation runs, with the generic [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) codec in [`dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c) standing in as the codec half whenever a board's PDM mics terminate on a plain DMIC port rather than on a SoundWire device.

```
    Two digital-microphone capture paths on an x86-64 ACPI laptop
    ─────────────────────────────────────────────────────────────

    PDM mics ─────▶ PCH DMIC port             SDCA Microphone Array
       clock+data        │                     on a SoundWire codec
                         ▼                            │ PDM or PCM mics
    ┌────────────────────────────────┐               ▼
    │ SOF DSP / PCH                  │   ┌────────────────────────────┐
    │  decimate PDM ──▶ PCM          │   │ codec decimates on-device  │
    │  (SOF_DAI_INTEL_DMIC gateway)  │   │  PDM ──▶ PCM               │
    └────────────────┬───────────────┘   └─────────────┬──────────────┘
                     │ back-end DAI                     │ SoundWire frame
                     ▼                                  ▼
        ┌────────────────────────┐         ┌────────────────────────┐
        │ DMIC01 Pin / DMIC16k   │         │ SDCA capture DAI       │
        │ Pin   (SOF skl_dai)    │         │ (DPn over SoundWire)   │
        └───────────┬────────────┘         └───────────┬────────────┘
              │ codec DAI = dmic-hifi                  │
              │ (generic soc_dmic)                     │
              └───────────────┬──────────────────────┬─┘
                              ▼                       ▼
                          ┌────────────────────────────────┐
                          │ ALSA capture PCM (userspace)   │
                          └────────────────────────────────┘

    Path 1: SOF PDM DMIC DAI + NHLT geometry
    Path 2: SDCA SoundWire microphone path
    this page: the overview and the generic dmic-codec
```

## SUMMARY

The first path runs the PDM bit stream into the PCH DMIC port, where the Sound Open Firmware (SOF) DSP decimates it. ASoC sees that endpoint as a Dynamic-PCM back-end CPU DAI in the SOF [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) array, named [`DMIC01 Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) for the 48 kHz family and [`DMIC16k Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863) for the 16 kHz wake and voice family, each [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)-only with [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) of 4. The DSP gateway is selected by [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594), which returns [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) for a DAI whose SOF [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L98) is [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79), and the number of PDM mics is read from the ACPI NHLT table by [`intel_nhlt_get_dmic_geo()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29).

The second path is an SDCA (SoundWire Device Class for Audio) Microphone Array function on a SoundWire codec. The mics may be PDM or PCM, but the codec decimates on-device and ships PCM over a SoundWire data port, so ASoC sees a codec capture DAI rather than a PCH back end. The Realtek rt722-sdca codec exposes its mic interface as the four-channel capture DAI [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1286) named `DP6 DMic Capture`, fed from the codec inputs [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) `DMIC1_2` and `DMIC3_4` through the codec ADC chain.

The generic codec is the shared piece this page documents. The [`dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c) component [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) registers one capture DAI [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) named `dmic-hifi`, a [`dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146) array carrying the [`SND_SOC_DAPM_AIF_OUT_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L269) `DMIC AIF` and the [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) `DMic` pin, and the route [`intercon`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L153). Its component callback [`dmic_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L108) reads firmware properties and an optional enable GPIO and vref regulator into a private [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27), and its platform probe [`dmic_dev_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168) registers the whole thing through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). On a SOF SoundWire laptop the machine driver [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) builds the two PCH DMIC back-end links, naming this generic codec's `dmic-hifi` DAI as the codec end of the first path's `DMIC01 Pin` and `DMIC16k Pin` CPU DAIs.

## SPECIFICATIONS

PDM is the wire format of the microphone bit stream and is defined by the microphone vendors. The PDM clock and data lines carry a one-bit oversampled signal that a decimation filter converts to PCM, and the kernel never sees the bit stream directly; it only ever reads the decimated PCM from whichever stage ran the filter. The generic [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) codec is a Linux kernel software construct with no standalone hardware specification; it models a passive PDM transducer that the host or DSP clocks and decimates, so the codec itself carries no register map and exposes only an enable GPIO and an optional vref supply. The capture format set of [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) is read straight from the [`formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) field of its [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) and accepts both decimated PCM (`S16`, `S24`, `S32`) and the raw DSD bit-stream formats a host that captures PDM directly would deliver.

- Intel High Definition Audio Specification: the legacy HD-Audio link and its NHLT companion table describe the PCH DMIC endpoints of the first path
- MIPI SoundWire and SDCA specifications: the bus and the Microphone Array function class describe the on-device-decimating codecs of the second path

## LINUX KERNEL

### Generic DMIC codec (codecs/dmic.c)

- [`'soc_dmic':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) describing the generic codec; supplies the probe, the DAPM widgets, and the route, and sets [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179), [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181), and [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191)
- [`'\<struct snd_soc_dai_driver dmic_dai\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89): the single capture DAI `dmic-hifi`, [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) 8, [`SNDRV_PCM_RATE_CONTINUOUS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h) rates, and PCM plus DSD formats
- [`'dmic_dai_ops':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L52): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) for the generic DAI, populating only the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) callback
- [`'\<dmic_daiops_trigger\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L35): the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) handler; applies a mode-switch delay on stop and otherwise returns 0
- [`'\<dmic_component_probe\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L108): the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78); allocates [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27), gets the optional vref and enable GPIO, reads the delay properties, and stores the private pointer
- [`'\<dmic_dev_probe\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168): the platform-driver probe; registers [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) and [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)
- [`'\<dmic_aif_event\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L56): the DAPM event callback on the `DMIC AIF` widget; drives the enable GPIO and the vref regulator on power up and down
- [`'dmic_dapm_widgets':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146): the [`SND_SOC_DAPM_AIF_OUT_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L269) `DMIC AIF` capture endpoint and the [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) `DMic` physical input
- [`'intercon':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L153): the route `{"DMIC AIF", NULL, "DMic"}` connecting the input pin to the capture AIF
- [`'\<struct dmic\>':'sound/soc/codecs/dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27): the codec's private state (the enable [`gpio_en`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L28), the [`vref`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L29) regulator, and the wakeup and mode-switch delays)

### Generic component and DAPM machinery (soc-component.h, soc-core.c, soc-dapm.c)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): the static, const description a codec registers; carries [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L71), [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75), and the component callbacks
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): the runtime component allocated at registration; holds the back pointer to the [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221), the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and the [`dapm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L240) context
- [`'\<snd_soc_component_get_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356) / [`'\<snd_soc_component_set_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L350): read and write the codec's private pointer on the component device
- [`'\<snd_soc_dapm_to_component\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L644): resolve the owning [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) from a DAPM widget's context, used by [`dmic_aif_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L56)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): device-managed registration of a component driver plus its DAI array; wraps [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932)
- [`'\<soc_probe_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602): at card bind, create the widgets with [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932), run the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), then add controls and routes with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272)
- [`'\<snd_soc_dapm_new_controls\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932): create one [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) per template, building the `DMIC AIF` and `DMic` graph nodes
- [`'\<snd_soc_dapm_add_routes\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272): connect the widget pair named by [`intercon`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L153) into a graph edge

### Path 1 entry: SOF PCH DMIC back end (sof/intel, sound/hda)

- [`'\<struct snd_soc_dai_driver skl_dai\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788): the SOF Intel CPU-DAI array; the two DMIC entries [`DMIC01 Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) and [`DMIC16k Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863) are the PCH DMIC back ends
- [`'\<enum sof_ipc_dai_type\>':'include/sound/sof/dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L76): the SOF DAI-type enumeration; [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) marks the PCH PDM interface, distinct from [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) for the SoundWire aggregated link
- [`'dmic_ipc4_dma_ops':'sound/soc/sof/intel/hda-dai-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465): the per-widget DMA gateway [`hda_select_dai_widget_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L594) returns for a [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) widget on an [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) (LunarLake) or later part
- [`'\<intel_nhlt_get_dmic_geo\>':'sound/hda/core/intel-nhlt.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-nhlt.c#L29): walks the [`struct nhlt_acpi_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L78) endpoints, finds the [`NHLT_LINK_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/intel-nhlt.h#L16) one, and returns the PDM channel count

### Path 2 entry: SDCA SoundWire microphone (codecs/rt722-sdca.c)

- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the rt722-sdca DAI array; [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1286) (`DP6 DMic Capture`, [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) 4, [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228)) is the SoundWire DMIC capture DAI
- [`'rt722_sdca_dapm_widgets':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L996): the codec DAPM widgets; the inputs [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) `DMIC1_2`/`DMIC3_4` and the capture AIF [`SND_SOC_DAPM_AIF_OUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L265) `DP6TX`
- [`'rt722_sdca_audio_map':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1043): the route table feeding `DP6TX` from the DMIC inputs through the ADC mux and feature-unit widgets

### Machine wiring of the generic codec (intel/boards/sof_sdw.c, sdw_utils)

- [`'\<create_dmic_dailinks\>':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092): builds the `dmic01` and `dmic16k` back-end links, binding the SOF `DMIC01 Pin`/`DMIC16k Pin` CPU DAIs to the generic `dmic-hifi` codec DAI
- [`'\<asoc_sdw_init_simple_dai_link\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320): fills one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) from the cpu/codec name pair the DMIC builder passes
- [`'\<asoc_sdw_dmic_init\>':'sound/soc/sdw_utils/soc_sdw_dmic.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24): the `dmic01` link [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback; adds the card-level `SoC DMIC` mic widget and its route to the codec's `DMic` input

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the ASoC codec class driver guide covering the component, its DAPM, and its DAI, the shape [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) follows
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the widget and route model the [`dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146) and [`intercon`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L153) tables build
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model the PCH DMIC back ends of the first path belong to
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver that binds the CPU and codec DAIs of the DMIC links
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the SDCA microphone DAI of the second path joins for capture

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A userspace capture client always opens an ALSA capture PCM, and the two paths differ in which stage decimated the PDM and over which transport the resulting PCM arrived. The generic [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) codec is the codec end of the first path and is created on a board whenever the PDM mics terminate on a plain DMIC port; the second path uses the SoundWire codec's own capture DAI and never instantiates this generic codec.

| object | created by | lifetime |
|--------|-----------|----------|
| [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) (component driver) | static const in [`dmic.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c), registered by [`dmic_dev_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168) | module lifetime; one runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) per probed `dmic-codec` device |
| [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27) (private state) | [`dmic_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L108) via [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) | device-managed; freed when the component device is removed |
| [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) (`dmic-hifi` capture DAI) | registered alongside [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) by [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) on the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) |
| `DMIC AIF` / `DMic` DAPM widgets | [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) from [`dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146) at card bind | live for the card's lifetime; torn down when the card is freed |
| `dmic01` / `dmic16k` back-end links | [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) on a SOF SoundWire board | one [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) each, allocated for the card |

The first path's PCH DMIC DAI is the back-end half of a Dynamic-PCM link; userspace opens a front-end PCM device and the core triggers the [`DMIC01 Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) back end behind it, with the generic [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) named on the codec side of that link. The second path's SDCA DAI is a codec DAI bound directly into a back-end link by the SoundWire machine driver, and the DSP sees its audio as [`SOF_DAI_INTEL_ALH`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L81) because it arrives over the aggregated SoundWire link rather than the dedicated PDM port that [`SOF_DAI_INTEL_DMIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof/dai.h#L79) marks.

## DETAILS

### The two capture paths and where they decimate

A PDM microphone emits a one-bit oversampled stream rather than PCM samples, so something downstream runs a decimation filter, and the path the kernel models is decided by where the mic's clock and data lines terminate. When they reach the PCH DMIC port, the SOF DSP owns the decimation and the mic surfaces as a back-end CPU DAI under [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), with the generic [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) codec supplying the codec half of the link. When the mic is part of a SoundWire codec such as the rt722-sdca, the codec decimates on-device and ships PCM over a SoundWire data port, so the mic surfaces as the codec's own capture DAI [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1286). The shared outcome is that userspace always opens an ALSA capture PCM and reads PCM frames; the representation only records which stage produced them. This page documents the generic codec, leaving the SOF PDM DMIC DAI with its NHLT geometry to the SOF PCH DMIC back-end path and the on-device decimation to the SDCA SoundWire microphone path.

### The generic codec component gathers the DMIC description

The generic codec is one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157). It supplies a [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), a [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) array, and a [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) array, and it sets three flags that are characteristic of a passive analog-free codec, [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179), [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181), and [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191):

```c
/* sound/soc/codecs/dmic.c:157 */
static const struct snd_soc_component_driver soc_dmic = {
	.probe			= dmic_component_probe,
	.dapm_widgets		= dmic_dapm_widgets,
	.num_dapm_widgets	= ARRAY_SIZE(dmic_dapm_widgets),
	.dapm_routes		= intercon,
	.num_dapm_routes	= ARRAY_SIZE(intercon),
	.idle_bias_on		= 1,
	.use_pmdown_time	= 1,
	.endianness		= 1,
};
```

The leading [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73), and [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) fields are the description the codec layer reads at card bind. The header groups the description first and the callbacks after:

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
	...
	unsigned int idle_bias_on:1;
	unsigned int use_pmdown_time:1;		/* care pmdown_time at stop */
	unsigned int endianness:1;
	...
};
```

The [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191) bit makes the core register both little-endian and big-endian variants of each used format, which suits a codec that sits behind a transport that abstracts away PCM endian. The [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179) bit keeps the DAPM bias level above off while idle, and [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181) applies the power-down debounce time when a stream stops.

```
    soc_dmic: struct snd_soc_component_driver, by field group
    ──────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ struct snd_soc_component_driver  soc_dmic                │
    ├──────────────────────────────────────────────────────────┤
    │ description (read at card bind)                          │
    │   controls          = NULL                               │
    │   dapm_widgets       = dmic_dapm_widgets                 │
    │   dapm_routes        = intercon                          │
    ├──────────────────────────────────────────────────────────┤
    │ callbacks                                                │
    │   probe              = dmic_component_probe              │
    ├──────────────────────────────────────────────────────────┤
    │ flags (1-bit)                                            │
    │   idle_bias_on=1  use_pmdown_time=1  endianness=1        │
    └──────────────────────────────────────────────────────────┘
```

### dmic_dev_probe registers the component and the DAI

The platform driver's probe registers the description and the DAI together. [`dmic_dev_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L168) hands [`soc_dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L157) and a pointer to the single [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) descriptor to [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) with a DAI count of 1. A firmware-supplied channel-count property can override the descriptor's [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) by copying the static template and patching the copy, so the static [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) is left untouched:

```c
/* sound/soc/codecs/dmic.c:168 */
static int dmic_dev_probe(struct platform_device *pdev)
{
	int err;
	u32 chans;
	struct snd_soc_dai_driver *dai_drv = &dmic_dai;

	if (pdev->dev.of_node) {
		err = of_property_read_u32(pdev->dev.of_node, "num-channels", &chans);
		if (err && (err != -EINVAL))
			return err;

		if (!err) {
			if (chans < 1 || chans > 8)
				return -EINVAL;

			dai_drv = devm_kzalloc(&pdev->dev, sizeof(*dai_drv), GFP_KERNEL);
			if (!dai_drv)
				return -ENOMEM;

			memcpy(dai_drv, &dmic_dai, sizeof(*dai_drv));
			dai_drv->capture.channels_max = chans;
		}
	}

	return devm_snd_soc_register_component(&pdev->dev,
			&soc_dmic, dai_drv, 1);
}
```

On an x86-64 ACPI laptop the SOF SoundWire machine driver instantiates the `dmic-codec` platform device with no channel-count property, so the channel-override branch is skipped and the unmodified [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) is registered. [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) wraps [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) in a devres action so the component unregisters automatically when the device goes away:

```c
/* sound/soc/soc-devres.c:29 */
int devm_snd_soc_register_component(struct device *dev,
			 const struct snd_soc_component_driver *cmpnt_drv,
			 struct snd_soc_dai_driver *dai_drv, int num_dai)
{
	const struct snd_soc_component_driver **ptr;
	int ret;

	ptr = devres_alloc(devm_component_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_soc_register_component(dev, cmpnt_drv, dai_drv, num_dai);
	if (ret == 0) {
		*ptr = cmpnt_drv;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

### The capture DAI is the codec end of the link

The one DAI the generic codec registers is [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89), a capture-only [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) named `dmic-hifi`. Its [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) declares up to eight channels, a continuous rate range, and a format set that spans the decimated PCM formats and the raw DSD bit-stream formats:

```c
/* sound/soc/codecs/dmic.c:89 */
static struct snd_soc_dai_driver dmic_dai = {
	.name = "dmic-hifi",
	.capture = {
		.stream_name = "Capture",
		.channels_min = 1,
		.channels_max = 8,
		.rates = SNDRV_PCM_RATE_CONTINUOUS,
		.formats = SNDRV_PCM_FMTBIT_S32_LE
			| SNDRV_PCM_FMTBIT_S24_LE
			| SNDRV_PCM_FMTBIT_S16_LE
			| SNDRV_PCM_FMTBIT_DSD_U8
			| SNDRV_PCM_FMTBIT_DSD_U16_LE
			| SNDRV_PCM_FMTBIT_DSD_U32_LE
			| SNDRV_PCM_FMTBIT_DSD_U16_BE
			| SNDRV_PCM_FMTBIT_DSD_U32_BE,
	},
	.ops    = &dmic_dai_ops,
};
```

The DAI's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) is [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L52), which fills only the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) field and leaves the rest of [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) NULL, because a passive PDM codec has no serial port to program for a capture stream:

```c
/* sound/soc/codecs/dmic.c:52 */
static const struct snd_soc_dai_ops dmic_dai_ops = {
	.trigger	= dmic_daiops_trigger,
};
```

[`dmic_daiops_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L35) does the minimum a DMIC needs at the DAI level. It reads the codec's [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27) through [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356) and, only on stop, waits out the configured mode-switch delay so the next mode change does not race a still-settling microphone:

```c
/* sound/soc/codecs/dmic.c:35 */
static int dmic_daiops_trigger(struct snd_pcm_substream *substream,
			       int cmd, struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct dmic *dmic = snd_soc_component_get_drvdata(component);

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_STOP:
		if (dmic->modeswitch_delay)
			mdelay(dmic->modeswitch_delay);

		break;
	}

	return 0;
}
```

### dmic_component_probe reads the GPIO, the regulator, and the delays

The component callback runs once from [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) at card bind. [`dmic_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L108) allocates the private [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27), looks up the optional vref regulator and the optional `dmicen` enable GPIO, reads the wakeup and mode-switch delays from firmware properties with [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) (which resolves ACPI `_DSD` device properties on an ACPI system), clamps the mode-switch delay, and stores the pointer with [`snd_soc_component_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L350):

```c
/* sound/soc/codecs/dmic.c:108 */
static int dmic_component_probe(struct snd_soc_component *component)
{
	struct dmic *dmic;

	dmic = devm_kzalloc(component->dev, sizeof(*dmic), GFP_KERNEL);
	if (!dmic)
		return -ENOMEM;

	dmic->vref = devm_regulator_get_optional(component->dev, "vref");
	if (IS_ERR(dmic->vref)) {
		if (PTR_ERR(dmic->vref) != -ENODEV)
			return dev_err_probe(component->dev, PTR_ERR(dmic->vref),
					     "Failed to get vref\n");
		dmic->vref = NULL;
	}

	dmic->gpio_en = devm_gpiod_get_optional(component->dev,
						"dmicen", GPIOD_OUT_LOW);
	if (IS_ERR(dmic->gpio_en))
		return PTR_ERR(dmic->gpio_en);

	device_property_read_u32(component->dev, "wakeup-delay-ms",
				 &dmic->wakeup_delay);
	device_property_read_u32(component->dev, "modeswitch-delay-ms",
				 &dmic->modeswitch_delay);
	if (wakeup_delay)
		dmic->wakeup_delay  = wakeup_delay;
	if (modeswitch_delay)
		dmic->modeswitch_delay  = modeswitch_delay;

	if (dmic->modeswitch_delay > MAX_MODESWITCH_DELAY)
		dmic->modeswitch_delay = MAX_MODESWITCH_DELAY;

	snd_soc_component_set_drvdata(component, dmic);

	return 0;
}
```

The private state every callback dereferences is [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27), holding the enable GPIO, the vref regulator, and the two delays:

```c
/* sound/soc/codecs/dmic.c:27 */
struct dmic {
	struct gpio_desc *gpio_en;
	struct regulator *vref;
	int wakeup_delay;
	/* Delay after DMIC mode switch */
	int modeswitch_delay;
};
```

When the optional vref and enable GPIO are both absent (the firmware describes neither), [`dmic->vref`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L29) and [`dmic->gpio_en`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L28) stay NULL and the event callback below becomes a no-op, which is the common case for PCH-attached PDM mics whose power and clock the DSP gateway owns rather than the codec.

```
    dmic_component_probe fills struct dmic from firmware
    ──────────────────────────────────────────────────────────

    ┌────────────────────────────────────────────────────────────┐
    │ struct dmic  (codec private state)                         │
    ├────────────────────────────────────────────────────────────┤
    │ gpio_en          ◀── gpiod_get_optional("dmicen")          │
    │ vref             ◀── regulator_get_optional("vref")        │
    │ wakeup_delay     ◀── prop "wakeup-delay-ms"                │
    │ modeswitch_delay ◀── prop "modeswitch-delay-ms"            │
    │                      clamp ≤ MAX_MODESWITCH_DELAY          │
    └────────────────────────────────────────────────────────────┘
```

### The DAPM widgets and route wire the pin to a capture AIF

The codec's audio graph is two widgets and one edge. [`dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146) declares the capture endpoint [`SND_SOC_DAPM_AIF_OUT_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L269) `DMIC AIF`, whose stream name `Capture` matches the DAI's [`stream_name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610), and the physical input pin [`SND_SOC_DAPM_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L60) `DMic`. The `_E` form carries an event callback that fires after power up and after power down:

```c
/* sound/soc/codecs/dmic.c:146 */
static const struct snd_soc_dapm_widget dmic_dapm_widgets[] = {
	SND_SOC_DAPM_AIF_OUT_E("DMIC AIF", "Capture", 0,
			       SND_SOC_NOPM, 0, 0, dmic_aif_event,
			       SND_SOC_DAPM_POST_PMU | SND_SOC_DAPM_POST_PMD),
	SND_SOC_DAPM_INPUT("DMic"),
};

static const struct snd_soc_dapm_route intercon[] = {
	{"DMIC AIF", NULL, "DMic"},
};
```

The route [`intercon`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L153) is the triple `{sink, control, source}` with a NULL control, an unconditional edge from the `DMic` pin to the `DMIC AIF` capture endpoint. The constructor [`SND_SOC_DAPM_AIF_OUT_E`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L269) records the widget id, name, stream name, event callback, and event flags into a [`struct snd_soc_dapm_widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L516) template:

```c
/* include/sound/soc-dapm.h:269 */
#define SND_SOC_DAPM_AIF_OUT_E(wname, stname, wchan, wreg, wshift, winvert, \
			     wevent, wflags)				\
(struct snd_soc_dapm_widget) { \
	.id = snd_soc_dapm_aif_out, .name = wname, .sname = stname, \
	.channel = wchan, SND_SOC_DAPM_INIT_REG_VAL(wreg, wshift, winvert), \
	.event = wevent, .event_flags = wflags }
```

At card bind, [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) instantiates these templates into live graph nodes before the component [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78) runs, then connects the route after the probe. The ordering is fixed. It calls [`snd_soc_dapm_new_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3932) on the [`dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L73) array, runs the codec [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L78), then calls [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272) on the [`dapm_routes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L75) array:

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

Built that way, the two nodes form one edge, the DMic pin feeding the capture endpoint whose Capture stream binds the codec DAI:

```
    dmic codec graph: input pin ──▶ capture AIF endpoint
    ──────────────────────────────────────────────────────
    intercon route: {"DMIC AIF", NULL, "DMic"}

    ┌──────────────┐      ┌───────────────────────────┐
    │ "DMic"       │      │ "DMIC AIF"                │
    │ INPUT pin    │ ──▶  │ AIF_OUT_E                 │
    │ transducer   │      │ stream "Capture"          │
    └──────────────┘      └────────────┬──────────────┘
                                       ▼
                  dmic_dai capture, stream_name "Capture"
```

### The event callback powers the mic on and off

Powering the `DMIC AIF` widget up or down runs [`dmic_aif_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L56), which is where the codec's only hardware actions happen. It resolves the component from the widget's DAPM context with [`snd_soc_dapm_to_component()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L644), reads the [`struct dmic`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L27) back with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), and on [`SND_SOC_DAPM_POST_PMU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L387) drives the enable GPIO high, enables the vref regulator, and waits the wakeup delay; on [`SND_SOC_DAPM_POST_PMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L389) it reverses the GPIO and regulator:

```c
/* sound/soc/codecs/dmic.c:56 */
static int dmic_aif_event(struct snd_soc_dapm_widget *w,
			  struct snd_kcontrol *kcontrol, int event) {
	struct snd_soc_component *component = snd_soc_dapm_to_component(w->dapm);
	struct dmic *dmic = snd_soc_component_get_drvdata(component);
	int ret = 0;

	switch (event) {
	case SND_SOC_DAPM_POST_PMU:
		if (dmic->gpio_en)
			gpiod_set_value_cansleep(dmic->gpio_en, 1);

		if (dmic->vref) {
			ret = regulator_enable(dmic->vref);
			if (ret)
				return ret;
		}

		if (dmic->wakeup_delay)
			msleep(dmic->wakeup_delay);
		break;
	case SND_SOC_DAPM_POST_PMD:
		if (dmic->gpio_en)
			gpiod_set_value_cansleep(dmic->gpio_en, 0);

		if (dmic->vref)
			ret = regulator_disable(dmic->vref);

		break;
	}

	return ret;
}
```

The wakeup delay after power up gives the transducer time to settle before the first samples are read, and the mode-switch delay in [`dmic_daiops_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L35) covers the gap on stop. Because the GPIO and regulator are both optional, a board that wires neither leaves this callback as a no-op and relies on the DSP gateway to clock and decimate the mic.

### The machine driver names the generic codec on the PCH DMIC links

On a SOF SoundWire laptop, the [`create_dmic_dailinks()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L1092) helper in the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c) machine driver builds the two PCH DMIC back-end links of the first path. It calls [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) twice, binding the SOF CPU DAIs `DMIC01 Pin` and `DMIC16k Pin` to the `dmic-hifi` codec DAI of this generic codec on the `dmic-codec` device, both links created capture-only:

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

The `dmic01` link passes [`asoc_sdw_dmic_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L24) as its [`init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) callback. That callback adds a card-level `SoC DMIC` microphone widget and routes it into the codec's `DMic` input, completing the graph from the board mic through the generic codec to the front-end PCM:

```c
/* sound/soc/sdw_utils/soc_sdw_dmic.c:24 */
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
```

The card-level `SoC DMIC` widget and its `{"DMic", NULL, "SoC DMIC"}` route are declared next to the init callback, and the `dmic16k` link reuses the same `dmic-codec` and passes no init so the widgets are added only once:

```c
/* sound/soc/sdw_utils/soc_sdw_dmic.c:15 */
static const struct snd_soc_dapm_widget dmic_widgets[] = {
	SND_SOC_DAPM_MIC("SoC DMIC", NULL),
};

static const struct snd_soc_dapm_route dmic_map[] = {
	/* digital mics */
	{"DMic", NULL, "SoC DMIC"},
};
```

The `DMic` sink named in [`dmic_map`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_dmic.c#L19) is the same `DMic` input pin the generic codec's [`dmic_dapm_widgets`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L146) declares, so the card-level widget and the codec graph join at that pin. The comment `DMIC only supports capture` on both [`asoc_sdw_init_simple_dai_link()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1320) calls records why each link is created with a capture-only direction.

```
    create_dmic_dailinks: two PCH back ends ──▶ one codec DAI
    ──────────────────────────────────────────────────────────
    (both links capture-only; codec dev "dmic-codec")

    ┌──────────────────────────────────────────────────────────┐
    │ back-end link "dmic01"   init = asoc_sdw_dmic_init       │
    │   cpu DAI   = "DMIC01 Pin"  (skl_dai, SOF PCH)           │
    │   codec DAI = "dmic-hifi"                                │
    ├──────────────────────────────────────────────────────────┤
    │ back-end link "dmic16k"  init = NULL                     │
    │   cpu DAI   = "DMIC16k Pin" (skl_dai, SOF PCH)           │
    │   codec DAI = "dmic-hifi"                                │
    └──────────────────────────────────────────────────────────┘
                       both codec DAIs ─────┐
                                            ▼
                              soc_dmic "dmic-hifi" (one DAI)
```

### The single capture-stream outcome

The two paths terminate identically at an ALSA capture PCM, and they differ only in which stage decimated the PDM and over which transport the PCM arrived. On the first path the PCH DMIC back end is triggered behind a Dynamic-PCM front end, the DSP gateway selected as [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465) moves decimated PCM into a host DMA buffer, and the generic [`dmic_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/dmic.c#L89) is the codec half of the [`DMIC01 Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) link that supplies the DAPM endpoint and the optional GPIO and regulator power. On the second path the rt722-sdca codec decimates on-device and ships PCM over a SoundWire data port through its own [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1286) capture DAI, and the generic codec is not instantiated at all. A userspace client opens an ALSA capture PCM in both cases and never sees the PDM bit stream or the transport, while the platform-specific machinery behind each path is handled by the SOF PCH DMIC back-end path and the SDCA SoundWire microphone path.

### Two digital-microphone paths converging on one capture PCM

This figure contrasts the PCH PDM path, where the SOF DSP decimates the stream behind the [`DMIC01 Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L856) and [`DMIC16k Pin`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L863) back-end DAIs through the gateway [`dmic_ipc4_dma_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai-ops.c#L465), with the SoundWire SDCA path, where the rt722-sdca codec decimates on-device and ships PCM over data port 6 through its [`rt722-sdca-aif3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1286) capture DAI, both ending at one ALSA capture PCM.

```
    Two digital-microphone paths on an x86 ACPI laptop
    ───────────────────────────────────────────────────

    PDM mics ─────▶ PCH DMIC port          SDCA Microphone Array
       (clock+data)      │                  on SoundWire codec (rt722)
                         ▼                          │
    ┌────────────────────────────────┐              ▼
    │ SOF DSP (IPC4 gateway)         │   ┌────────────────────────────┐
    │  decimate PDM ──▶ PCM          │   │ codec decimates PDM ──▶ PCM│
    │  dmic_ipc4_dma_ops             │   │ DP6 capture (aif3)         │
    └────────────────┬───────────────┘   └──────────────┬─────────────┘
                     │ back-end DAI                     │ SoundWire frame
                     ▼                                  ▼
        ┌────────────────────────┐         ┌────────────────────────┐
        │ DMIC01 Pin / DMIC16k   │         │ rt722-sdca-aif3        │
        │ Pin  (skl_dai BEs)     │         │ DP6 DMic Capture       │
        └───────────┬────────────┘         └───────────┬────────────┘
                    │                                  │
                    └───────────────┬──────────────────┘
                                    ▼
                          ┌───────────────────┐
                          │ ALSA capture PCM  │
                          └───────────────────┘
```
