# Intel SoundWire CPU DAIs and PDI

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The SoundWire CPU DAIs on an Intel audio DSP are built one per PDI (Physical Data Interface) of the Cadence IP master by [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024), the [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) member of the ACE 2.x function pointer struct [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109), which reads the SHIM2 PCM stream capability into a [`struct sdw_cdns_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75), allocates the Cadence PDIs of [`struct sdw_cdns_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) through [`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297), and calls [`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) to fill one `SDWn PinM` [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) per PDI with the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) table [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919) so a SOF back-end DAI link can drive the SoundWire link as the master endpoint of a stream.

```
    PDI capability ─▶ Cadence PDI ─▶ CPU DAI ─▶ host/link DMA mapping
    ───────────────────────────────────────────────────────────────

    SHIM2 PCMSCAP (per link)         struct sdw_cdns_streams cdns.pcm
    ┌───────────────────────┐        ┌─────────────────────────────────┐
    │ ISS  in-only  streams │  ───▶  │ in[]  ─▶ INTEL_PDI_IN  (capture)│
    │ OSS  out-only streams │        │ out[] ─▶ INTEL_PDI_OUT (playbk) │
    │ BSS  bidirectional    │        │ bd[]  ─▶ INTEL_PDI_BD  (both)   │
    └───────────────────────┘        └───────────────┬─────────────────┘
       sdw_cdns_pdi_init()                           │ intel_create_dai()
       allocates one struct                          ▼ one DAI per PDI
       sdw_cdns_pdi per stream         struct snd_soc_dai_driver dais[]
                                       ┌────────────────────────────────┐
                                       │ "SDW0 Pin0"  ops = &intel_pcm_ │
                                       │ "SDW0 Pin1"      dai_ops        │
                                       │  ...            id = array idx  │
                                       └───────────────┬─────────────────┘
                                          hw_params op │ run time
                                                       ▼
          sdw_cdns_alloc_pdi() picks a free PDI by dai->id, then two halves:
            ┌─────────────────────────────┬───────────────────────────────┐
            │ link side (SoundWire wire)  │ host side (HDaudio DMA)       │
            │ sdw_cdns_config_stream()    │ res->ops->params_stream() to  │
            │ programs Cadence PORTCTRL / │ SOF: HDaudio DMA + ALH/SHIM   │
            │ PDI_CONFIG; sdw_stream_add_ │ stream tag via pdi->intel_alh_│
            │ master() joins the bus      │ id (intel_params_stream)      │
            └─────────────────────────────┴───────────────────────────────┘
```

## SUMMARY

A SoundWire CPU DAI on Intel is the ASoC front the SOF back-end binds to so that opening a PCM joins the codec and the controller to the same SoundWire stream. The DAIs are created late, during link startup. [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) powers the link and then calls the inline dispatcher [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157), which routes through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) to the [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) member of the per-version [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415). On Lunar Lake-class (ACE 2.x) hardware that member is [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024).

[`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024) reads the PDI inventory and turns it into DAIs. [`intel_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L935) reads the SHIM2 [`SDW_SHIM2_PCMSCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L132) register and splits the input-only, output-only, and bidirectional stream counts into a [`struct sdw_cdns_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75). [`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297) allocates the [`struct sdw_cdns_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) arrays for the [`in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), [`out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), and [`bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) groups of [`cdns->pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and records the total in [`num_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55). [`intel_pdi_stream_ch_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L978) reads the per-PDI channel capability from SHIM2 so each group carries its maximum channel count. The function then sizes the per-DAI runtime array [`cdns->dai_runtime_array`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array to [`num_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) entries.

[`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) runs three times, once per [`enum intel_pdi_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) value. [`INTEL_PDI_IN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) DAIs get a [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) channel range, [`INTEL_PDI_OUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) DAIs a [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) range, and [`INTEL_PDI_BD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L101) DAIs both, every DAI named `SDWn PinM` from the link [`instance`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and the array index, every DAI pointing [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919). The whole array is registered under the [`dai_component`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L928) ASoC component by [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29).

When a PCM opens, [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919) drives the link. The SOF machine layer first hands the CPU DAI its [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) through [`intel_pcm_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847), which calls [`cdns_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831) to allocate a [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) and stash it at [`cdns->dai_runtime_array[dai->id]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124). [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) picks a free PDI with [`sdw_cdns_alloc_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951), computes the HDaudio stream tag [`pdi->intel_alh_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), programs the Cadence port through [`sdw_cdns_config_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1912), tells SOF the PDI stream number through [`intel_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L651), and joins the SoundWire bus as the master endpoint through [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991). [`intel_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L812) reverses both halves, [`intel_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765) reinitializes the Cadence IP after a system resume, and [`intel_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L866) forwards start/stop to the SOF DMA op and tracks the suspend and pause flags in the runtime.

## SPECIFICATIONS

The PDI (Physical Data Interface) and the SoundWire wire format are defined by the MIPI Alliance SoundWire (Serial Low-power Inter-chip Media Bus) specification, which is membership-gated; the kernel SoundWire core and the Cadence IP master implement it. The CPU DAI is a Linux ASoC software construct with no standalone hardware specification. The host-side stream tag the CPU DAI programs into [`pdi->intel_alh_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) and reports through [`intel_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L651) is the HDaudio stream-tag concept from the Intel High Definition Audio specification, carried by the SHIM2 [`SDW_SHIM2_PCMSYCHM_STRM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L145) field. The per-link PCM stream capability the DAI count is derived from is read from the SHIM2 [`SDW_SHIM2_PCMSCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L132) register, whose [`SDW_SHIM2_PCMSCAP_ISS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L133), [`SDW_SHIM2_PCMSCAP_OSS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L134), and [`SDW_SHIM2_PCMSCAP_BSS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L135) fields are defined in [`include/linux/soundwire/sdw_intel.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h).

## LINUX KERNEL

### DAI registration and creation (intel_ace2x.c)

- [`'\<intel_register_dai\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024): the ACE 2.x [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) op; read the PDI capability, init the Cadence PDIs, size the runtime and DAI arrays, build one DAI per PDI, and register the component
- [`'\<intel_create_dai\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991): name each DAI `SDWn PinM`, set its [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) channel range from the [`enum intel_pdi_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98), and attach [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919)
- [`'\<intel_pdi_init\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L935): read [`SDW_SHIM2_PCMSCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L132) and split the stream counts into a [`struct sdw_cdns_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75)
- [`'\<intel_pdi_stream_ch_update\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L978): walk each PDI group calling [`intel_pdi_get_ch_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L961) to total the per-group channel counts
- [`'\<intel_pdi_get_ch_cap\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L952): read the per-PDI channel capability from [`SDW_SHIM2_PCMSYCHC`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L138)
- [`'dai_component':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L928): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) named `soundwire` the DAI array registers under

### The CPU DAI ops and their callbacks (intel_ace2x.c)

- [`'intel_pcm_dai_ops':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919): the [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) shared by every SoundWire CPU DAI, filling [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308), and [`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310)
- [`'\<intel_hw_params\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695): allocate a PDI, compute the stream tag, configure the Cadence port, tell SOF the stream number, and add the master to the SoundWire stream
- [`'\<intel_prepare\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765): on a resumed runtime, reconfigure the Cadence stream and re-announce the PDI stream number; on an underflow, only re-announce
- [`'\<intel_hw_free\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L812): remove the master from the stream with [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078), free the host-side stream, and clear [`dai_runtime->pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94)
- [`'\<intel_trigger\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L866): forward the command to the SOF DMA [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L228) op, then set [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) or [`paused`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) in the runtime
- [`'\<intel_pcm_set_sdw_stream\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op; hand the stream handle to [`cdns_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831)
- [`'\<intel_get_sdw_stream\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L853): the [`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310) op; return the [`stream`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) held in the runtime
- [`'\<intel_params_stream\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L651) / [`'\<intel_free_stream\>':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L672): call into the SOF [`params_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L224) and [`free_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L226) callbacks to program and release the HDaudio DMA path

### PDI types and the Cadence PDI model (intel.h, cadence_master.*)

- [`'\<enum intel_pdi_type\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98): the three PDI groups [`INTEL_PDI_IN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) (0), [`INTEL_PDI_OUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) (1), and [`INTEL_PDI_BD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L101) (2) that decide each DAI's direction
- [`'\<struct sdw_cdns_pdi\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31): one PDI instance, holding the [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), the [`intel_alh_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) host stream tag, the channel window [`l_ch_num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31)/[`h_ch_num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), the [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), and the [`dir`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31)
- [`'\<struct sdw_cdns_streams\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55): the three PDI arrays [`in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), [`out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), [`bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) and their per-group counts; held as [`cdns->pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124)
- [`'\<struct sdw_cdns_stream_config\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75): the [`pcm_in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75)/[`pcm_out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75)/[`pcm_bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75) counts read out of [`SDW_SHIM2_PCMSCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L132)
- [`'\<struct sdw_cdns_dai_runtime\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94): the per-DAI runtime, holding the [`stream`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) handle, the bound [`pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), the [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), the [`link_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), and the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94)/[`paused`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) flags
- [`'\<struct sdw_cdns\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124): the Cadence IP master context, owning the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) PDI streams and the [`dai_runtime_array`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) indexed by [`dai->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438)

### Cadence PDI allocation and stream config (cadence_master.c)

- [`'\<sdw_cdns_pdi_init\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297): copy the stream counts into [`cdns->pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and allocate the [`bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), [`in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), and [`out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) PDI arrays through [`cdns_allocate_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1269)
- [`'\<cdns_allocate_pdi\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1269): allocate one PDI array and number each entry by its index
- [`'\<sdw_cdns_alloc_pdi\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951): find a free PDI for a DAI by direction and [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) (falling back to a bidirectional one), then set its channel window
- [`'\<cdns_find_pdi\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1890): match a PDI in a group whose [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) equals the [`dai_id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438)
- [`'\<sdw_cdns_config_stream\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1912): program the Cadence [`CDNS_PORTCTRL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L143) direction and [`CDNS_PDI_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L156) channel mask for a PDI
- [`'\<cdns_set_sdw_stream\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831): allocate (or free) a [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) and place it at [`dai_runtime_array[dai->id]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124)

### Dispatch into the hw_ops (intel.h, intel_ace2x.c, sdw_intel.h)

- [`'sdw_intel_lnl_hw_ops':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109): the ACE 2.x [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) whose [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) is [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024)
- [`'\<struct sdw_intel_hw_ops\>':'include/linux/soundwire/sdw_intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415): the per-version function pointer struct; [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) "read all PDI information and register DAIs"
- [`'\<sdw_intel_register_dai\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157): inline dispatcher that runs [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) under the [`SDW_INTEL_CHECK_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L133) null-check
- [`'\<cdns_to_intel\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127): [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) wrapper recovering the [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) from a Cadence context (zero offset)
- [`'\<intel_link_startup\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377): the per-link startup that powers the link and then calls [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157)

### ASoC and SoundWire stream interfaces

- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): the static DAI descriptor [`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) fills, carrying [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403)
- [`'\<struct snd_soc_pcm_stream\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610): the per-direction capability record whose [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610)/[`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) the PDI type fills
- [`'\<struct sdw_stream_config\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) / [`'\<struct sdw_port_config\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893): the stream and port descriptors [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) passes to [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991)
- [`'\<sdw_stream_add_master\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) / [`'\<sdw_stream_remove_master\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078): add and remove the controller as the master endpoint of a SoundWire stream
- [`'\<snd_soc_dai_get_drvdata\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L542): recover the Cadence context the DAI ops use, set by [`auxiliary_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L205) in [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): register the DAI array and its component, unregistering it when the link device goes away

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the CPU DAI joins as the master endpoint, and the master/port runtime objects [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) builds
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire master/slave model and the data-port concept a PDI maps onto the host side
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) takes while building the master runtime
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept the SoundWire CPU DAIs implement
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the SOF front-end/back-end model that links a back-end DAI to a SoundWire CPU DAI

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The DAI subsystem of a SoundWire link is a small set of objects, each with one creator and a defined lifetime. The static objects (the DAI descriptor array, the Cadence PDIs, the per-DAI runtime array) are created once during link startup and torn down with the link; the per-stream object (the [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94)) is created when a stream handle is set and freed when it is cleared, and the bound PDI is reserved for the duration of one [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) to [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) window.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array | [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024) (via [`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991)) | the link, freed by devm on unbind |
| [`struct sdw_cdns_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) arrays | [`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297) (via [`cdns_allocate_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1269)) | the link |
| [`dai_runtime_array`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) | [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024) | the link |
| [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) | [`cdns_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831) (from [`intel_pcm_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847)) | set_stream to set_stream(NULL) |
| PDI binding ([`dai_runtime->pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94)) | [`sdw_cdns_alloc_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951) (from [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695)) | hw_params to hw_free |
| master runtime on the bus | [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) (from [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695)) | hw_params to hw_free |

The six fields of [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919) map to the ASoC PCM operations the SOF back-end issues. The [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op runs once from the machine layer before the PCM opens; the rest run per substream.

| ASoC operation | DAI op (field) | effect on the link |
|----------------|----------------|--------------------|
| machine set_stream | [`intel_pcm_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847) ([`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308)) | allocate the [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), store the stream handle |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) ([`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326)) | reserve a PDI, configure Cadence, add the master to the stream |
| `SNDRV_PCM_IOCTL_PREPARE` | [`intel_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765) ([`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L330)) | re-arm the Cadence IP after resume, re-announce the PDI |
| `SNDRV_PCM_IOCTL_*` triggers | [`intel_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L866) ([`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L339)) | drive the HDaudio DMA op, track suspend/pause |
| `SNDRV_PCM_IOCTL_HW_FREE` | [`intel_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L812) ([`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328)) | remove the master, free the host stream, drop the PDI |
| pointer/handle read | [`intel_get_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L853) ([`get_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L310)) | return the stored stream handle |

## DETAILS

### The PDI is the boundary between the wire and the host

A PDI (Physical Data Interface) is the Cadence IP's endpoint where SoundWire-side data ports meet the host-side audio fabric. The kernel represents one with a [`struct sdw_cdns_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), which keeps the PDI [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), the channel window [`l_ch_num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) to [`h_ch_num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), the direction [`dir`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), and the host-side stream tag [`intel_alh_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) that ties the PDI to an HDaudio DMA engine:

```c
/* drivers/soundwire/cadence_master.h:31 */
/**
 * struct sdw_cdns_pdi: PDI (Physical Data Interface) instance
 *
 * @num: pdi number
 * @intel_alh_id: link identifier
 * @l_ch_num: low channel for PDI
 * @h_ch_num: high channel for PDI
 * @ch_count: total channel count for PDI
 * @dir: data direction
 * @type: stream type, (only PCM supported)
 */
struct sdw_cdns_pdi {
	int num;
	int intel_alh_id;
	int l_ch_num;
	int h_ch_num;
	int ch_count;
	enum sdw_data_direction dir;
	enum sdw_stream_type type;
};
```

PDIs are grouped by direction. The Cadence context carries one [`struct sdw_cdns_streams`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) in its [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) member, holding the input-only array [`in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), the output-only array [`out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), the bidirectional array [`bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), each group's PDI count and channel total, and the grand total [`num_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55):

```c
/* drivers/soundwire/cadence_master.h:55 */
struct sdw_cdns_streams {
	unsigned int num_bd;
	unsigned int num_in;
	unsigned int num_out;
	unsigned int num_ch_bd;
	unsigned int num_ch_in;
	unsigned int num_ch_out;
	unsigned int num_pdi;
	struct sdw_cdns_pdi *bd;
	struct sdw_cdns_pdi *in;
	struct sdw_cdns_pdi *out;
};
```

### Link startup dispatches to the ACE 2.x register_dai

DAI registration is not called directly; it is reached through the per-version function pointer struct. After [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) powers the link, it calls the inline dispatcher [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157), which null-checks the op and routes to it through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135):

```c
/* drivers/soundwire/intel.h:157 */
static inline int sdw_intel_register_dai(struct sdw_intel *sdw)
{
	if (SDW_INTEL_CHECK_OPS(sdw, register_dai))
		return SDW_INTEL_OPS(sdw, register_dai)(sdw);
	return -ENOTSUPP;
}
```

[`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) reaches the chosen member off the link resources, so the auxiliary driver never names an ACE-version function. The [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) slot of the function pointer struct is documented to "read all PDI information and register DAIs":

```c
/* include/linux/soundwire/sdw_intel.h:415 */
struct sdw_intel_hw_ops {
	void (*debugfs_init)(struct sdw_intel *sdw);
	void (*debugfs_exit)(struct sdw_intel *sdw);

	int (*get_link_count)(struct sdw_intel *sdw);

	int (*register_dai)(struct sdw_intel *sdw);
	...
	int (*link_power_up)(struct sdw_intel *sdw);
	int (*link_power_down)(struct sdw_intel *sdw);
	...
};
```

On Lunar Lake-class hardware the struct instance is [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109), exported from [`intel_ace2x.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c) and selected by SOF for any DSP whose audio-controller engine is version 2.x. Its [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) member is [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024):

```c
/* drivers/soundwire/intel_ace2x.c:1109 */
const struct sdw_intel_hw_ops sdw_intel_lnl_hw_ops = {
	.debugfs_init = intel_ace2x_debugfs_init,
	.debugfs_exit = intel_ace2x_debugfs_exit,

	.get_link_count = intel_get_link_count,

	.register_dai = intel_register_dai,

	.check_clock_stop = intel_check_clock_stop,
	.start_bus = intel_start_bus,
	...
	.link_power_up = intel_link_power_up,
	.link_power_down = intel_link_power_down,
	...
};
```

### intel_register_dai reads the PDI capability and builds the DAI array

[`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024) is one function that performs the whole DAI build. It reads the PDI capability with [`intel_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L935), allocates the Cadence PDIs with [`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297), fills in each group's channel total with [`intel_pdi_stream_ch_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L978), sizes the runtime and DAI arrays to [`num_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), runs [`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) three times at increasing offsets, and registers the result:

```c
/* drivers/soundwire/intel_ace2x.c:1024 */
static int intel_register_dai(struct sdw_intel *sdw)
{
	struct sdw_cdns_dai_runtime **dai_runtime_array;
	struct sdw_cdns_stream_config config;
	struct sdw_cdns *cdns = &sdw->cdns;
	struct sdw_cdns_streams *stream;
	struct snd_soc_dai_driver *dais;
	int num_dai;
	int ret;
	int off = 0;

	/* Read the PDI config and initialize cadence PDI */
	intel_pdi_init(sdw, &config);
	ret = sdw_cdns_pdi_init(cdns, config);
	if (ret)
		return ret;

	intel_pdi_stream_ch_update(sdw, &sdw->cdns.pcm);

	/* DAIs are created based on total number of PDIs supported */
	num_dai = cdns->pcm.num_pdi;

	dai_runtime_array = devm_kcalloc(cdns->dev, num_dai,
					 sizeof(struct sdw_cdns_dai_runtime *),
					 GFP_KERNEL);
	if (!dai_runtime_array)
		return -ENOMEM;
	cdns->dai_runtime_array = dai_runtime_array;

	dais = devm_kcalloc(cdns->dev, num_dai, sizeof(*dais), GFP_KERNEL);
	if (!dais)
		return -ENOMEM;

	/* Create PCM DAIs */
	stream = &cdns->pcm;

	ret = intel_create_dai(cdns, dais, INTEL_PDI_IN, cdns->pcm.num_in,
			       off, stream->num_ch_in);
	if (ret)
		return ret;

	off += cdns->pcm.num_in;
	ret = intel_create_dai(cdns, dais, INTEL_PDI_OUT, cdns->pcm.num_out,
			       off, stream->num_ch_out);
	if (ret)
		return ret;

	off += cdns->pcm.num_out;
	ret = intel_create_dai(cdns, dais, INTEL_PDI_BD, cdns->pcm.num_bd,
			       off, stream->num_ch_bd);
	if (ret)
		return ret;

	return devm_snd_soc_register_component(cdns->dev, &dai_component,
					       dais, num_dai);
}
```

The three [`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) calls partition the one DAI array into contiguous spans. The `off` accumulator advances past the input span, then the output span, so the input PDIs occupy indices 0 to [`num_in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55)-1, the output PDIs the next [`num_out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), and the bidirectional PDIs the rest, with the DAI array index later serving as the [`dai->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) the ops use to find a PDI and a runtime.

```
    intel_register_dai(): one DAI array, three contiguous spans
    ──────────────────────────────────────────────────────────

    off advances past each span; the array index becomes dai->id

    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │   INTEL_PDI_IN  │  │  INTEL_PDI_OUT  │  │   INTEL_PDI_BD  │
    │     capture     │  │     playback    │  │       both      │
    │ [0 .. num_in-1] │  │   [num_in ..]   │  │  [.. num_pdi-1] │
    └─────────────────┘  └─────────────────┘  └─────────────────┘

    num_pdi = num_in + num_out + num_bd  (DAI array size)
    dai->id later selects the matching PDI and dai_runtime
```

### intel_pdi_init reads SHIM2 PCMSCAP

[`intel_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L935) reads the SHIM2 PCM stream capability register and decodes three bit fields into the [`struct sdw_cdns_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75):

```c
/* drivers/soundwire/intel_ace2x.c:935 */
static void intel_pdi_init(struct sdw_intel *sdw,
			   struct sdw_cdns_stream_config *config)
{
	void __iomem *shim = sdw->link_res->shim;
	int pcm_cap;

	/* PCM Stream Capability */
	pcm_cap = intel_readw(shim, SDW_SHIM2_PCMSCAP);

	config->pcm_bd = FIELD_GET(SDW_SHIM2_PCMSCAP_BSS, pcm_cap);
	config->pcm_in = FIELD_GET(SDW_SHIM2_PCMSCAP_ISS, pcm_cap);
	config->pcm_out = FIELD_GET(SDW_SHIM2_PCMSCAP_ISS, pcm_cap);

	dev_dbg(sdw->cdns.dev, "PCM cap bd:%d in:%d out:%d\n",
		config->pcm_bd, config->pcm_in, config->pcm_out);
}
```

The three [`SDW_SHIM2_PCMSCAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L132) sub-fields name the counts directly, [`SDW_SHIM2_PCMSCAP_ISS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L133) for input-only streams, [`SDW_SHIM2_PCMSCAP_OSS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L134) for output-only, [`SDW_SHIM2_PCMSCAP_BSS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L135) for bidirectional:

```c
/* include/linux/soundwire/sdw_intel.h:132 */
#define SDW_SHIM2_PCMSCAP		0x10
#define SDW_SHIM2_PCMSCAP_ISS		GENMASK(3, 0)	/* Input-only streams */
#define SDW_SHIM2_PCMSCAP_OSS		GENMASK(7, 4)	/* Output-only streams */
#define SDW_SHIM2_PCMSCAP_BSS		GENMASK(12, 8)	/* Bidirectional streams */
```

The [`struct sdw_cdns_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L75) it fills carries only the three counts, which [`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297) copies into [`cdns->pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124):

```c
/* drivers/soundwire/cadence_master.h:75 */
/**
 * struct sdw_cdns_stream_config: stream configuration
 *
 * @pcm_bd: number of bidirectional PCM streams supported
 * @pcm_in: number of input PCM streams supported
 * @pcm_out: number of output PCM streams supported
 */
struct sdw_cdns_stream_config {
	unsigned int pcm_bd;
	unsigned int pcm_in;
	unsigned int pcm_out;
};
```

The register packs three count fields that fill those members, ISS in the low four bits for input-only streams, OSS in the next four for output-only, and BSS for bidirectional:

```
    SDW_SHIM2_PCMSCAP (0x10, 16-bit) PCM stream counts
    ──────────────────────────────────────────────────

    bit   1   1   1   1   1   1
          5   4   3   2   1   0   9   8   7   6   5   4   3   2   1   0
        ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
        │    rsvd   │     BSS (12:8)    │   OSS (7:4)   │   ISS (3:0)   │
        └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

    ISS = GENMASK(3,0)   input-only streams    ▶ config.pcm_in
    OSS = GENMASK(7,4)   output-only streams   ▶ config.pcm_out
    BSS = GENMASK(12,8)  bidirectional streams ▶ config.pcm_bd
```

### sdw_cdns_pdi_init allocates the three PDI arrays

[`sdw_cdns_pdi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1297) copies the three counts into [`cdns->pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), allocates one PDI array per group through [`cdns_allocate_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1269), and records the total in [`num_pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55) and [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124):

```c
/* drivers/soundwire/cadence_master.c:1297 */
int sdw_cdns_pdi_init(struct sdw_cdns *cdns,
		      struct sdw_cdns_stream_config config)
{
	struct sdw_cdns_streams *stream;
	int ret;

	cdns->pcm.num_bd = config.pcm_bd;
	cdns->pcm.num_in = config.pcm_in;
	cdns->pcm.num_out = config.pcm_out;

	/* Allocate PDIs for PCMs */
	stream = &cdns->pcm;

	/* we allocate PDI0 and PDI1 which are used for Bulk */
	ret = cdns_allocate_pdi(cdns, &stream->bd, stream->num_bd);
	if (ret)
		return ret;

	ret = cdns_allocate_pdi(cdns, &stream->in, stream->num_in);
	if (ret)
		return ret;

	ret = cdns_allocate_pdi(cdns, &stream->out, stream->num_out);
	if (ret)
		return ret;

	/* Update total number of PCM PDIs */
	stream->num_pdi = stream->num_bd + stream->num_in + stream->num_out;
	cdns->num_ports = stream->num_pdi;

	return 0;
}
```

[`cdns_allocate_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1269) allocates the array for one group and numbers each PDI by its array index, so a PDI's [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) within its group is later matched against a DAI id:

```c
/* drivers/soundwire/cadence_master.c:1269 */
static int cdns_allocate_pdi(struct sdw_cdns *cdns,
			     struct sdw_cdns_pdi **stream,
			     u32 num)
{
	struct sdw_cdns_pdi *pdi;
	int i;

	if (!num)
		return 0;

	pdi = devm_kcalloc(cdns->dev, num, sizeof(*pdi), GFP_KERNEL);
	if (!pdi)
		return -ENOMEM;

	for (i = 0; i < num; i++) {
		pdi[i].num = i;
	}

	*stream = pdi;
	return 0;
}
```

After allocation, [`intel_pdi_stream_ch_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L978) reads each PDI's channel capability from the SHIM2 [`SDW_SHIM2_PCMSYCHC`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L138) register through [`intel_pdi_get_ch_cap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L952) and sums them per group into [`num_ch_in`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), [`num_ch_out`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), and [`num_ch_bd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L55), which become each DAI's maximum channel count:

```c
/* drivers/soundwire/intel_ace2x.c:978 */
static void intel_pdi_stream_ch_update(struct sdw_intel *sdw,
				       struct sdw_cdns_streams *stream)
{
	intel_pdi_get_ch_update(sdw, stream->bd, stream->num_bd,
				&stream->num_ch_bd);

	intel_pdi_get_ch_update(sdw, stream->in, stream->num_in,
				&stream->num_ch_in);

	intel_pdi_get_ch_update(sdw, stream->out, stream->num_out,
				&stream->num_ch_out);
}
```

### intel_create_dai names each DAI and sets its direction

[`intel_create_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L991) is called once per [`enum intel_pdi_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) and fills a span of the DAI array. It names each DAI `SDWn PinM` from the link [`instance`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and the array index, sets a [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) range for output and bidirectional PDIs, a [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) range for input and bidirectional PDIs, and points [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) at the shared table:

```c
/* drivers/soundwire/intel_ace2x.c:991 */
static int intel_create_dai(struct sdw_cdns *cdns,
			    struct snd_soc_dai_driver *dais,
			    enum intel_pdi_type type,
			    u32 num, u32 off, u32 max_ch)
{
	int i;

	if (!num)
		return 0;

	for (i = off; i < (off + num); i++) {
		dais[i].name = devm_kasprintf(cdns->dev, GFP_KERNEL,
					      "SDW%d Pin%d",
					      cdns->instance, i);
		if (!dais[i].name)
			return -ENOMEM;

		if (type == INTEL_PDI_BD || type == INTEL_PDI_OUT) {
			dais[i].playback.channels_min = 1;
			dais[i].playback.channels_max = max_ch;
		}

		if (type == INTEL_PDI_BD || type == INTEL_PDI_IN) {
			dais[i].capture.channels_min = 1;
			dais[i].capture.channels_max = max_ch;
		}

		dais[i].ops = &intel_pcm_dai_ops;
	}

	return 0;
}
```

The [`enum intel_pdi_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) decides which capability records are set, so an [`INTEL_PDI_BD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L101) DAI gets both [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) while an [`INTEL_PDI_IN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L98) DAI gets only [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403):

```c
/* drivers/soundwire/intel.h:98 */
enum intel_pdi_type {
	INTEL_PDI_IN = 0,
	INTEL_PDI_OUT = 1,
	INTEL_PDI_BD = 2,
};
```

Each [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) the loop fills carries the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403), the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) table, and the two [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) capability records [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403):

```c
/* include/sound/soc-dai.h:403 */
struct snd_soc_dai_driver {
	/* DAI description */
	const char *name;
	unsigned int id;
	...
	/* ops */
	const struct snd_soc_dai_ops *ops;
	const struct snd_soc_cdai_ops *cops;

	/* DAI capabilities */
	struct snd_soc_pcm_stream capture;
	struct snd_soc_pcm_stream playback;
	...
};
```

The capability record is where the channel range the PDI type filled lands; the [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) and [`channels_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) limit what the ASoC core lets a PCM negotiate on that DAI:

```c
/* include/sound/soc.h:610 */
struct snd_soc_pcm_stream {
	const char *stream_name;
	u64 formats;			/* SNDRV_PCM_FMTBIT_* */
	u32 subformats;			/* for S32_LE format, SNDRV_PCM_SUBFMTBIT_* */
	unsigned int rates;		/* SNDRV_PCM_RATE_* */
	unsigned int rate_min;		/* min rate */
	unsigned int rate_max;		/* max rate */
	unsigned int channels_min;	/* min channels */
	unsigned int channels_max;	/* max channels */
	unsigned int sig_bits;		/* number of bits of content */
};
```

The array is registered under one ASoC component, [`dai_component`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L928), named `soundwire`, which is otherwise empty because the SoundWire CPU DAIs carry no kcontrols or DAPM widgets of their own:

```c
/* drivers/soundwire/intel_ace2x.c:928 */
static const struct snd_soc_component_driver dai_component = {
	.name			= "soundwire",
};
```

Each DAI's direction follows from its PDI type, an input PDI getting capture, an output PDI playback, and a bidirectional PDI both, at the max_ch width under the SDWn PinM name:

```
    intel_create_dai(): PDI type sets the DAI direction
    ───────────────────────────────────────────────────

    ┌─────────────────────┬─────────┬──────────┐
    │ enum intel_pdi_type │ capture │ playback │
    ├─────────────────────┼─────────┼──────────┤
    │ INTEL_PDI_IN  (0)   │   yes   │    -     │
    │ INTEL_PDI_OUT (1)   │    -    │   yes    │
    │ INTEL_PDI_BD  (2)   │   yes   │   yes    │
    └─────────────────────┴─────────┴──────────┘

    channels_max = max_ch for each enabled direction; name = SDWn PinM
```

### intel_pcm_dai_ops is the CPU DAI op set

Every SoundWire CPU DAI shares one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) table. It supplies the six callbacks that map a PCM substream onto a SoundWire stream and a host DMA, leaving every other op of the table NULL:

```c
/* drivers/soundwire/intel_ace2x.c:919 */
static const struct snd_soc_dai_ops intel_pcm_dai_ops = {
	.hw_params = intel_hw_params,
	.prepare = intel_prepare,
	.hw_free = intel_hw_free,
	.trigger = intel_trigger,
	.set_stream = intel_pcm_set_sdw_stream,
	.get_stream = intel_get_sdw_stream,
};
```

The [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op runs first, when the SOF machine layer hands the CPU DAI the SoundWire stream handle it allocated. [`intel_pcm_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847) forwards to the Cadence helper, and [`intel_get_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L853) reads it back from the runtime:

```c
/* drivers/soundwire/intel_ace2x.c:847 */
static int intel_pcm_set_sdw_stream(struct snd_soc_dai *dai,
				    void *stream, int direction)
{
	return cdns_set_sdw_stream(dai, stream, direction);
}

static void *intel_get_sdw_stream(struct snd_soc_dai *dai,
				  int direction)
{
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_cdns_dai_runtime *dai_runtime;

	dai_runtime = cdns->dai_runtime_array[dai->id];
	if (!dai_runtime)
		return ERR_PTR(-EINVAL);

	return dai_runtime->stream;
}
```

[`cdns_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831) is where the per-DAI runtime is born. A non-NULL stream means the DAI is joining a stream, so the function allocates a [`struct sdw_cdns_dai_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94), records the stream type, the bus, the link id, the stream handle, and the direction, and stores it at [`dai_runtime_array[dai->id]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124); a NULL stream frees it:

```c
/* drivers/soundwire/cadence_master.c:1831 */
int cdns_set_sdw_stream(struct snd_soc_dai *dai,
			void *stream, int direction)
{
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_cdns_dai_runtime *dai_runtime;

	dai_runtime = cdns->dai_runtime_array[dai->id];

	if (stream) {
		/* first paranoia check */
		if (dai_runtime) {
			dev_err(dai->dev,
				"dai_runtime already allocated for dai %s\n",
				dai->name);
			return -EINVAL;
		}

		/* allocate and set dai_runtime info */
		dai_runtime = kzalloc_obj(*dai_runtime);
		if (!dai_runtime)
			return -ENOMEM;

		dai_runtime->stream_type = SDW_STREAM_PCM;

		dai_runtime->bus = &cdns->bus;
		dai_runtime->link_id = cdns->instance;

		dai_runtime->stream = stream;
		dai_runtime->direction = direction;

		cdns->dai_runtime_array[dai->id] = dai_runtime;
	} else {
		/* second paranoia check */
		if (!dai_runtime) {
			dev_err(dai->dev,
				"dai_runtime not allocated for dai %s\n",
				dai->name);
			return -EINVAL;
		}

		/* for NULL stream we release allocated dai_runtime */
		kfree(dai_runtime);
		cdns->dai_runtime_array[dai->id] = NULL;
	}
	return 0;
}
```

The runtime it allocates is the per-DAI scratch the rest of the ops read and write, carrying the stream handle, the PDI bound at hw_params time, the bus and link id, the direction, and the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) and [`paused`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) flags the trigger and prepare ops use:

```c
/* drivers/soundwire/cadence_master.h:94 */
/**
 * struct sdw_cdns_dai_runtime: Cadence DAI runtime data
 *
 * @name: SoundWire stream name
 * @stream: stream runtime
 * @pdi: PDI used for this dai
 * @bus: Bus handle
 * @stream_type: Stream type
 * @link_id: Master link id
 * @suspended: status set when suspended, to be used in .prepare
 * @paused: status set in .trigger, to be used in suspend
 * @direction: stream direction
 */
struct sdw_cdns_dai_runtime {
	char *name;
	struct sdw_stream_runtime *stream;
	struct sdw_cdns_pdi *pdi;
	struct sdw_bus *bus;
	enum sdw_stream_type stream_type;
	int link_id;
	bool suspended;
	bool paused;
	int direction;
};
```

### intel_hw_params maps the PDI to both the wire and the host

[`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) is the op that reserves a PDI and wires both halves of it. It recovers the Cadence context and the enclosing [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75), looks up the runtime by [`dai->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), and picks a free PDI for the requested direction and channel count with [`sdw_cdns_alloc_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951):

```c
/* drivers/soundwire/intel_ace2x.c:695 */
static int intel_hw_params(struct snd_pcm_substream *substream,
			   struct snd_pcm_hw_params *params,
			   struct snd_soc_dai *dai)
{
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_cdns_dai_runtime *dai_runtime;
	struct sdw_cdns_pdi *pdi;
	struct sdw_stream_config sconfig;
	int ch, dir;
	int ret;

	dai_runtime = cdns->dai_runtime_array[dai->id];
	if (!dai_runtime)
		return -EIO;

	ch = params_channels(params);
	if (substream->stream == SNDRV_PCM_STREAM_CAPTURE)
		dir = SDW_DATA_DIR_RX;
	else
		dir = SDW_DATA_DIR_TX;

	pdi = sdw_cdns_alloc_pdi(cdns, &cdns->pcm, ch, dir, dai->id);
	if (!pdi)
		return -EINVAL;

	/* use same definitions for alh_id as previous generations */
	pdi->intel_alh_id = (sdw->instance * 16) + pdi->num + 3;
	if (pdi->num >= 2)
		pdi->intel_alh_id += 2;

	/* the SHIM will be configured in the callback functions */

	sdw_cdns_config_stream(cdns, ch, dir, pdi);

	/* store pdi and state, may be needed in prepare step */
	dai_runtime->paused = false;
	dai_runtime->suspended = false;
	dai_runtime->pdi = pdi;
	...
}
```

The host side is announced through [`pdi->intel_alh_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31), a stream tag computed from the link [`instance`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and the PDI number, and passed to SOF through [`intel_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L651) so the audio firmware can bind an HDaudio DMA to the SHIM2 [`SDW_SHIM2_PCMSYCHM_STRM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L145) field of that PDI. According to the comment, on ACE 2.x the SHIM is configured in the callback functions rather than inline, so unlike the older path [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) does not call ALH or SHIM configuration helpers directly; it programs only the Cadence port through [`sdw_cdns_config_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1912). The wire side is joined at the tail, where the op fills a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and a [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) and adds the controller as the master endpoint:

```c
/* drivers/soundwire/intel_ace2x.c:695 (continued) */
	/* Inform DSP about PDI stream number */
	ret = intel_params_stream(sdw, substream, dai, params,
				  sdw->instance,
				  pdi->intel_alh_id);
	if (ret)
		return ret;

	sconfig.direction = dir;
	sconfig.ch_count = ch;
	sconfig.frame_rate = params_rate(params);
	sconfig.type = dai_runtime->stream_type;

	sconfig.bps = snd_pcm_format_width(params_format(params));

	/* Port configuration */
	struct sdw_port_config *pconfig __free(kfree) = kzalloc_obj(*pconfig);
	if (!pconfig)
		return -ENOMEM;

	pconfig->num = pdi->num;
	pconfig->ch_mask = (1 << ch) - 1;

	ret = sdw_stream_add_master(&cdns->bus, &sconfig,
				    pconfig, 1, dai_runtime->stream);
	if (ret)
		dev_err(cdns->dev, "add master to stream failed:%d\n", ret);

	return ret;
}
```

[`sdw_cdns_alloc_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951) does the PDI selection. It looks in the direction-matching group first through [`cdns_find_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1890), falls back to the bidirectional group, and on a hit fills the channel window the wire and the Cadence port will use:

```c
/* drivers/soundwire/cadence_master.c:1951 */
struct sdw_cdns_pdi *sdw_cdns_alloc_pdi(struct sdw_cdns *cdns,
					struct sdw_cdns_streams *stream,
					u32 ch, u32 dir, int dai_id)
{
	struct sdw_cdns_pdi *pdi = NULL;

	if (dir == SDW_DATA_DIR_RX)
		pdi = cdns_find_pdi(cdns, stream->num_in, stream->in,
				    dai_id);
	else
		pdi = cdns_find_pdi(cdns, stream->num_out, stream->out,
				    dai_id);

	/* check if we found a PDI, else find in bi-directional */
	if (!pdi)
		pdi = cdns_find_pdi(cdns, stream->num_bd, stream->bd,
				    dai_id);

	if (pdi) {
		pdi->l_ch_num = 0;
		pdi->h_ch_num = ch - 1;
		pdi->dir = dir;
		pdi->ch_count = ch;
	}

	return pdi;
}
```

[`sdw_cdns_config_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1912) programs the Cadence registers for the chosen PDI, setting the port direction in [`CDNS_PORTCTRL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L143) and the channel mask in [`CDNS_PDI_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L156). According to the comment, DataPort0 needs to be mapped to both PDI0 and PDI1, which is why the function special-cases [`pdi->num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L31) of 0 and 1:

```c
/* drivers/soundwire/cadence_master.c:1912 */
void sdw_cdns_config_stream(struct sdw_cdns *cdns,
			    u32 ch, u32 dir, struct sdw_cdns_pdi *pdi)
{
	u32 offset, val = 0;

	if (dir == SDW_DATA_DIR_RX) {
		val = CDNS_PORTCTRL_DIRN;

		if (cdns->bus.params.m_data_mode != SDW_PORT_DATA_MODE_NORMAL)
			val |= CDNS_PORTCTRL_TEST_FAILED;
	} else if (pdi->num == 0 || pdi->num == 1) {
		val |= CDNS_PORTCTRL_BULK_ENABLE;
	}
	offset = CDNS_PORTCTRL + pdi->num * CDNS_PORT_OFFSET;
	cdns_updatel(cdns, offset,
		     CDNS_PORTCTRL_DIRN | CDNS_PORTCTRL_TEST_FAILED |
		     CDNS_PORTCTRL_BULK_ENABLE,
		     val);

	/* The DataPort0 needs to be mapped to both PDI0 and PDI1 ! */
	if (pdi->num == 1)
		val = 0;
	else
		val = pdi->num;
	val |= CDNS_PDI_CONFIG_SOFT_RESET;
	val |= FIELD_PREP(CDNS_PDI_CONFIG_CHANNEL, (1 << ch) - 1);
	cdns_writel(cdns, CDNS_PDI_CONFIG(pdi->num), val);
}
```

[`intel_params_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L651) is the host-side half. It packs the substream, the DAI, the hw_params, the link id, and the stream tag into a [`struct sdw_intel_stream_params_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L200) and calls the SOF-supplied [`params_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L224) callback, which programs the HDaudio DMA and sends the IPC to the audio firmware:

```c
/* drivers/soundwire/intel_ace2x.c:651 */
static int intel_params_stream(struct sdw_intel *sdw,
			       struct snd_pcm_substream *substream,
			       struct snd_soc_dai *dai,
			       struct snd_pcm_hw_params *hw_params,
			       int link_id, int alh_stream_id)
{
	struct sdw_intel_link_res *res = sdw->link_res;
	struct sdw_intel_stream_params_data params_data;

	params_data.substream = substream;
	params_data.dai = dai;
	params_data.hw_params = hw_params;
	params_data.link_id = link_id;
	params_data.alh_stream_id = alh_stream_id;

	if (res->ops && res->ops->params_stream && res->dev)
		return res->ops->params_stream(res->dev,
					       &params_data);
	return -EIO;
}
```

[`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) is the wire-side half. It takes [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), allocates a master runtime for the stream if one does not exist, allocates the master ports, and configures the master runtime and the stream from the [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) the DAI passed, so the controller becomes one endpoint of the stream alongside the codec the bus enumerated.

### intel_prepare re-arms the Cadence IP after resume

[`intel_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765) runs before the stream starts and again after an underrun. It treats a resumed runtime and an underrun differently. A runtime marked [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) needs the Cadence stream reconfigured, so the op re-runs [`sdw_cdns_config_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1912); an underrun must not touch the ALH or SHIM registers, so the op only re-announces the PDI stream number:

```c
/* drivers/soundwire/intel_ace2x.c:765 */
static int intel_prepare(struct snd_pcm_substream *substream,
			 struct snd_soc_dai *dai)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_cdns_dai_runtime *dai_runtime;
	struct snd_pcm_hw_params *hw_params;
	int ch, dir;

	dai_runtime = cdns->dai_runtime_array[dai->id];
	if (!dai_runtime) {
		dev_err(dai->dev, "failed to get dai runtime in %s\n",
			__func__);
		return -EIO;
	}

	hw_params = &rtd->dpcm[substream->stream].hw_params;
	if (dai_runtime->suspended) {
		dai_runtime->suspended = false;

		/*
		 * .prepare() is called after system resume, where we
		 * need to reinitialize the SHIM/ALH/Cadence IP.
		 * .prepare() is also called to deal with underflows,
		 * but in those cases we cannot touch ALH/SHIM
		 * registers
		 */

		/* configure stream */
		ch = params_channels(hw_params);
		if (substream->stream == SNDRV_PCM_STREAM_CAPTURE)
			dir = SDW_DATA_DIR_RX;
		else
			dir = SDW_DATA_DIR_TX;

		/* the SHIM will be configured in the callback functions */

		sdw_cdns_config_stream(cdns, ch, dir, dai_runtime->pdi);
	}

	/* Inform DSP about PDI stream number */
	return intel_params_stream(sdw, substream, dai, hw_params, sdw->instance,
				   dai_runtime->pdi->intel_alh_id);
}
```

### intel_trigger forwards to the DMA op and tracks state

[`intel_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L866) does no SoundWire register work of its own. According to the comment, the trigger callback programs the HDaudio DMA and sends the required IPC to the audio firmware, both through the SOF-supplied [`res->ops->trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L228) callback, and then records the suspend or pause transition in the runtime so [`intel_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765) and the suspend path can act on it:

```c
/* drivers/soundwire/intel_ace2x.c:866 */
static int intel_trigger(struct snd_pcm_substream *substream, int cmd, struct snd_soc_dai *dai)
{
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_intel_link_res *res = sdw->link_res;
	struct sdw_cdns_dai_runtime *dai_runtime;
	int ret = 0;

	/*
	 * The .trigger callback is used to program HDaudio DMA and send required IPC to audio
	 * firmware.
	 */
	if (res->ops && res->ops->trigger) {
		ret = res->ops->trigger(substream, cmd, dai);
		if (ret < 0)
			return ret;
	}

	dai_runtime = cdns->dai_runtime_array[dai->id];
	if (!dai_runtime) {
		dev_err(dai->dev, "failed to get dai runtime in %s\n",
			__func__);
		return -EIO;
	}

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_SUSPEND:
		...
		dai_runtime->suspended = true;
		break;

	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		dai_runtime->paused = true;
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		dai_runtime->paused = false;
		break;
	default:
		break;
	}

	return ret;
}
```

According to the comment in the [`SNDRV_PCM_TRIGGER_SUSPEND`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L102) case, the prepare callback deals with xruns and resume, and the trigger callback tracks the suspend case only, so [`intel_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L866) sets [`dai_runtime->suspended`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) on a suspend and leaves the re-initialization to [`intel_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L765).

### intel_hw_free unwinds both halves

[`intel_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L812) reverses what [`intel_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L695) built. It removes the controller from the SoundWire stream through [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078), frees the host-side stream through [`intel_free_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L672), and clears [`dai_runtime->pdi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L94) so the PDI returns to the free pool:

```c
/* drivers/soundwire/intel_ace2x.c:812 */
static int
intel_hw_free(struct snd_pcm_substream *substream, struct snd_soc_dai *dai)
{
	struct sdw_cdns *cdns = snd_soc_dai_get_drvdata(dai);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_cdns_dai_runtime *dai_runtime;
	int ret;

	dai_runtime = cdns->dai_runtime_array[dai->id];
	if (!dai_runtime)
		return -EIO;

	/*
	 * The sdw stream state will transition to RELEASED when stream->
	 * master_list is empty. So the stream state will transition to
	 * DEPREPARED for the first cpu-dai and to RELEASED for the last
	 * cpu-dai.
	 */
	ret = sdw_stream_remove_master(&cdns->bus, dai_runtime->stream);
	if (ret < 0) {
		dev_err(dai->dev, "remove master from stream %s failed: %d\n",
			dai_runtime->stream->name, ret);
		return ret;
	}

	ret = intel_free_stream(sdw, substream, dai, sdw->instance);
	if (ret < 0) {
		dev_err(dai->dev, "intel_free_stream: failed %d\n", ret);
		return ret;
	}

	dai_runtime->pdi = NULL;

	return 0;
}
```

According to the comment, the SoundWire stream state transitions to RELEASED once the master list is empty, so removing the master for the last CPU DAI of a multi-link stream is what drives the stream into RELEASED while an earlier CPU DAI only drives it to DEPREPARED. [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) frees the master runtime and its ports, decrements the stream's master count, and on the empty list sets [`stream->state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964) to [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933). The runtime itself is not freed here; it persists until the machine layer clears the stream handle through [`intel_pcm_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L847) with a NULL stream, which is the symmetric teardown of the runtime [`cdns_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1831) allocated.

### The DAI ops recover the Cadence context the same way

Every op begins by recovering the Cadence context. The DAIs are registered under the [`dai_component`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L928) whose device is the aux device, and [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) set that device's drvdata to the Cadence context, so [`snd_soc_dai_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L542) returns the [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and [`cdns_to_intel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127) recovers the enclosing [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) from its first member:

```c
/* drivers/soundwire/intel.h:127 */
#define cdns_to_intel(_cdns) container_of(_cdns, struct sdw_intel, cdns)
```

From there the [`dai->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) the DAI carries indexes [`cdns->dai_runtime_array`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) to reach the per-DAI runtime, and the same id is the PDI number [`sdw_cdns_alloc_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1951) matches with [`cdns_find_pdi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1890). The array index assigned at creation in [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024) is the join between a DAI, its PDI, and its runtime for the whole life of the link.

```
    dai->id is the join across a DAI, its runtime, and its PDI
    ──────────────────────────────────────────────────────────

    snd_soc_dai_get_drvdata(dai) ▶ struct sdw_cdns
    cdns_to_intel(cdns)          ▶ struct sdw_intel (first member)

                      ┌───────────────┐
                      │  dai->id = N  │
                      └───────┬───────┘
                  ┌───────────┴────────────┐
                  ▼                        ▼
        ┌───────────────────┐  ┌───────────────────────┐
        │ dai_runtime_array │  │ cdns_find_pdi(): PDI  │
        │ [N] = per-DAI     │  │ whose num == N in the │
        │ sdw_cdns_dai_     │  │ in / out / bd group   │
        │ runtime           │  │ (sdw_cdns_alloc_pdi)  │
        └───────────────────┘  └───────────────────────┘
```
