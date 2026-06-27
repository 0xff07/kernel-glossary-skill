# ASoC PCM setup path (soc-pcm)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The setup phase of an ASoC PCM is the three operations [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) that run before audio flows. When a userspace client opens a substream and sets its parameters, the ALSA core dispatches through the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) that ASoC installed, reaching [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), and [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) for an ordinary DAI link. Each handler takes the card-wide [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001) through [`snd_soc_dpcm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1548), runs an inner double-underscore worker, and drops the mutex. The worker fans the one operation out across three layers in turn, starting with the machine link, then the components (through a [`snd_soc_pcm_component_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) wrapper, run once per component of the runtime), and finally the DAIs (through a [`snd_soc_dai_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) wrapper, run once per CPU DAI and once per codec DAI). On an x86-64 ACPI system the platform component is Sound Open Firmware, whose [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536) and [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) run from the component wrappers and program the DSP. The trigger, pointer, and teardown half of the operation set is documented separately.

```
       One setup operation (open / hw_params / prepare)
       ─────────────────────────────────────────────────

       struct snd_pcm_ops in rtd->ops
       ┌──────────────────────────────────────────────────────────┐
       │  .open       = soc_pcm_open                              │
       │  .hw_params  = soc_pcm_hw_params                         │
       │  .prepare    = soc_pcm_prepare                           │
       └──────────────────────────────┬───────────────────────────┘
                                      │ snd_soc_dpcm_mutex_lock(rtd)
                                      │ __soc_pcm_<op>(rtd, substream)
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
        machine link            components              DAIs of the runtime
        snd_soc_link_*       snd_soc_pcm_component_*    snd_soc_dai_* wrapper
              │              │ for_each_rtd_components   │ for_each_rtd_dais
              ▼              ▼                           ▼
        link->ops      ┌────────────┐            ┌──────────┬──────────┐
                       ▼            ▼            ▼          ▼          ▼
                  platform      (other       CPU DAI    codec DAI  (more
                  component    components)    ops        ops        codecs)
                  (SOF on x86)
```

## SUMMARY

[`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) installs the setup handlers into the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) field of each link's [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) during card bind and attaches them to the substreams with [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510). An ordinary link receives [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), and [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979); a Dynamic PCM front end receives the `dpcm_fe_dai_*` variants instead. Each of the three is a lock wrapper around an inner [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854), [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070), or [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) that asserts the mutex with [`snd_soc_dpcm_mutex_assert_held()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1556) and does the real work, so the same inner body is reusable by the Dynamic PCM back-end paths that take the lock once at the front end.

[`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) runtime-resumes each component with [`snd_soc_pcm_component_pm_runtime_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1170), opens each component through [`soc_pcm_components_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L718), runs the machine link [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) through [`snd_soc_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54), and runs every DAI [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) through [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437). It then intersects the CPU and codec capability records into the runtime hardware description with [`snd_soc_runtime_calc_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L631), rejects an empty intersection with [`soc_hw_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L812), and bumps the usage counts with [`snd_soc_runtime_activate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L486). [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) applies the negotiated [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) to each codec DAI, each CPU DAI, and the components through [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) and [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080), giving each DAI a private copy fixed up for its TDM slot or channel mask and recording the result with [`soc_pcm_set_dai_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L426). [`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) runs link, component, and DAI prepare, raises [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) through [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620), and unmutes the DAIs that do not mute at trigger with [`snd_soc_dai_digital_mute()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386). A failure at any step in open or hw_params jumps to a cleanup that rolls back only the layers whose setup op actually ran.

## SPECIFICATIONS

The soc-pcm setup layer is a Linux kernel software construct and has no standalone hardware specification. The operations it implements ([`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55)) are defined by the ALSA PCM userspace interface.

## LINUX KERNEL

### Operation install (soc-pcm.c, soc-core.c, pcm_lib.c)

- [`'\<soc_new_pcm\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909): create the ALSA PCM for a link, choose the operation set, and write it into [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)
- [`'\<soc_init_pcm_runtime\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512): the card-bind caller of [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) for every link
- [`'\<snd_pcm_set_ops\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510): point every substream of one direction at [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143)

### Setup handlers and their inner workers (soc-pcm.c)

- [`'\<soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) / [`'\<__soc_pcm_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854): open every component and DAI, merge the hardware constraints, and activate the runtime
- [`'\<soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) / [`'\<__soc_pcm_hw_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070): apply the negotiated parameters to each DAI and component with per-DAI fixups
- [`'\<soc_pcm_prepare\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) / [`'\<__soc_pcm_prepare\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933): run link/component/DAI prepare, raise the DAPM stream event, and unmute the DAIs

### Setup helpers (soc-pcm.c)

- [`'\<soc_pcm_components_open\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L718): take a module reference and call [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) for each component
- [`'\<soc_pcm_init_runtime_hw\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L701): seed the runtime hardware record from the merged DAI capabilities
- [`'\<snd_soc_runtime_calc_hw\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L631): intersect the rate, channel, and format limits across all CPUs and codecs of the link
- [`'\<soc_hw_sanity_check\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L812): reject a link whose merged capabilities leave no usable rate, format, or channel count
- [`'\<soc_pcm_codec_params_fixup\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L997): pin a per-DAI parameter copy's channel count from a TDM or channel mask
- [`'\<soc_pcm_set_dai_params\>':'sound/soc/soc-pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L426): record the per-DAI rate, channels, and sample bits for symmetry checks

### DAI fan-out wrappers (soc-dai.c)

- [`'\<snd_soc_dai_startup\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437): run a DAI's [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op and mark it on success
- [`'\<snd_soc_dai_hw_params\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405): run a DAI's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op and mark it
- [`'\<snd_soc_pcm_dai_prepare\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L588): iterate [`snd_soc_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L354) over every DAI of the runtime
- [`'\<snd_soc_dai_digital_mute\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L386): run a DAI's [`mute_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, used to unmute at the end of prepare
- [`'\<snd_soc_dai_tdm_mask_get\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L517): read the TDM slot mask the hw_params fixup applies

### Component and link fan-out wrappers (soc-component.c, soc-link.c)

- [`'\<snd_soc_component_open\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251): run a component's [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op and mark the substream
- [`'\<snd_soc_pcm_component_hw_params\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080): run every component's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op and mark each one
- [`'\<snd_soc_pcm_component_prepare\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063): run every component's [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op
- [`'\<snd_soc_pcm_component_pm_runtime_get\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1170): runtime-resume every component at open
- [`'\<snd_soc_link_startup\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L54), [`'\<snd_soc_link_hw_params\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98), [`'\<snd_soc_link_prepare\>':'sound/soc/soc-link.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86): run the machine link's matching ops

### Runtime, DAPM, and locking (headers, soc-dapm.c)

- [`'\<struct snd_pcm_ops\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55): the ALSA PCM operation set ASoC installs per substream
- [`'\<struct snd_soc_pcm_runtime\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143): the per-link runtime holding the embedded [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), the DAI array, and the component array
- [`'\<snd_soc_dpcm_mutex_lock\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1548) / [`'\<snd_soc_dpcm_mutex_assert_held\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1556): take and assert the card [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001)
- [`'\<snd_soc_runtime_activate\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L486): bump the runtime and DAI usage counts at the end of open
- [`'\<snd_soc_dapm_stream_event\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620): raise the DAPM stream event that powers the playback or capture path
- [`'\<snd_soc_dapm_update_dai\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3074): push the chosen parameters into the DAI widget at hw_params

### SOF platform component (sound/soc/sof)

- [`'\<sof_pcm_open\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536): the SOF component [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op the component wrapper reaches on x86, setting the runtime limits from topology
- [`'\<sof_pcm_hw_params\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116): the SOF component [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op that sets up the firmware widgets and host DMA

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component and its PCM operations
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the DAI families the per-DAI setup ops drive
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the component, DAI, and machine pieces the soc-pcm layer ties together

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__PCM.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The setup phase uses three of the seven fields [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) fills in [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143). Each maps to an inner worker and a fixed pair of fan-out wrappers, one for the DAIs and one for the components.

| Operation | soc-pcm handler | inner worker | DAI wrapper | component wrapper |
|-----------|-----------------|--------------|-------------|-------------------|
| `open()` | [`soc_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) | [`__soc_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) | [`snd_soc_dai_startup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) | [`snd_soc_component_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | [`soc_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172) | [`__soc_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) | [`snd_soc_dai_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) | [`snd_soc_pcm_component_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) |
| `SNDRV_PCM_IOCTL_PREPARE` | [`soc_pcm_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) | [`__soc_pcm_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) | [`snd_soc_pcm_dai_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L588) | [`snd_soc_pcm_component_prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063) |

[`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) runs once per substream open and never repeats while the substream is open. [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) can run more than once before audio starts, so its worker re-applies parameters from scratch and rolls back to a clean state on failure. [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) can also repeat (after an underrun, for example) and is the last setup op before [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) starts the transfer.

## DETAILS

### The card-bind caller of soc_new_pcm

[`soc_init_pcm_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1512) is the per-link card-bind step that reaches the PCM creation. It runs the machine link init, resolves the DAI format, and then calls [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) once for the link before creating the DAI-level PCM objects, so the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) install described below happens exactly once per [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143):

```c
/* sound/soc/soc-core.c:1512 */
static int soc_init_pcm_runtime(struct snd_soc_card *card,
				struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_dai_link *dai_link = rtd->dai_link;
	struct snd_soc_dai *cpu_dai = snd_soc_rtd_to_cpu(rtd, 0);
	int ret;

	/* do machine specific initialization */
	ret = snd_soc_link_init(rtd);
	if (ret < 0)
		return ret;

	snd_soc_runtime_get_dai_fmt(rtd);
	ret = snd_soc_runtime_set_dai_fmt(rtd, dai_link->dai_fmt);
	if (ret)
		goto err;
	...
	/* create the pcm */
	ret = soc_new_pcm(rtd);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: can't create pcm %s :%d\n",
			dai_link->stream_name, ret);
		goto err;
	}

	ret = snd_soc_pcm_dai_new(rtd);
	if (ret < 0)
		goto err;

	rtd->initialized = true;

	return 0;
err:
	snd_soc_link_exit(rtd);
	return ret;
}
```

### soc_new_pcm installs the setup handlers

[`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) runs once per DAI link during card bind and chooses the operation set by link kind. A [`no_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L792) back-end link installs no application-facing ops, a [`dynamic`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L795) front end installs the `dpcm_fe_dai_*` set, and an ordinary link installs the [`soc_pcm_*`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c) set whose setup half this page covers. It first creates the ALSA [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L506) through [`soc_create_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2862), then writes the operation set into [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143):

```c
/* sound/soc/soc-pcm.c:2909 */
int soc_new_pcm(struct snd_soc_pcm_runtime *rtd)
{
	struct snd_soc_component *component;
	struct snd_pcm *pcm;
	int ret = 0, playback = 0, capture = 0;
	int i;

	ret = soc_get_playback_capture(rtd, &playback, &capture);
	if (ret < 0)
		return ret;

	ret = soc_create_pcm(&pcm, rtd, playback, capture);
	if (ret < 0)
		return ret;
	...
	rtd->pcm = pcm;
	pcm->nonatomic = rtd->dai_link->nonatomic;
	pcm->private_data = rtd;
	pcm->no_device_suspend = true;

	if (rtd->dai_link->no_pcm || rtd->dai_link->c2c_params) {
		if (playback)
			pcm->streams[SNDRV_PCM_STREAM_PLAYBACK].substream->private_data = rtd;
		if (capture)
			pcm->streams[SNDRV_PCM_STREAM_CAPTURE].substream->private_data = rtd;
		goto out;
	}

	/* ASoC PCM operations */
	if (rtd->dai_link->dynamic) {
		rtd->ops.open		= dpcm_fe_dai_open;
		rtd->ops.hw_params	= dpcm_fe_dai_hw_params;
		rtd->ops.prepare	= dpcm_fe_dai_prepare;
		rtd->ops.trigger	= dpcm_fe_dai_trigger;
		rtd->ops.hw_free	= dpcm_fe_dai_hw_free;
		rtd->ops.close		= dpcm_fe_dai_close;
		rtd->ops.pointer	= soc_pcm_pointer;
	} else {
		rtd->ops.open		= soc_pcm_open;
		rtd->ops.hw_params	= soc_pcm_hw_params;
		rtd->ops.prepare	= soc_pcm_prepare;
		rtd->ops.trigger	= soc_pcm_trigger;
		rtd->ops.hw_free	= soc_pcm_hw_free;
		rtd->ops.close		= soc_pcm_close;
		rtd->ops.pointer	= soc_pcm_pointer;
	}
```

After the setup, trigger, and teardown ops are chosen, [`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) adds the component-supplied ops by scanning each component of the runtime, then calls [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) once per enabled direction to bind [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) to the substreams:

```c
/* sound/soc/soc-pcm.c:2972 */
	for_each_rtd_components(rtd, i, component) {
		const struct snd_soc_component_driver *drv = component->driver;

		if (drv->ioctl)
			rtd->ops.ioctl		= snd_soc_pcm_component_ioctl;
		if (drv->sync_stop)
			rtd->ops.sync_stop	= snd_soc_pcm_component_sync_stop;
		if (drv->copy)
			rtd->ops.copy		= snd_soc_pcm_component_copy;
		if (drv->page)
			rtd->ops.page		= snd_soc_pcm_component_page;
		if (drv->mmap)
			rtd->ops.mmap		= snd_soc_pcm_component_mmap;
		if (drv->ack)
			rtd->ops.ack            = snd_soc_pcm_component_ack;
	}

	if (playback)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK, &rtd->ops);

	if (capture)
		snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE, &rtd->ops);
```

[`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) is the ALSA core helper that walks the substream list of one direction and points every substream's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) at the table ASoC just filled in, so the ALSA core dispatches each later setup operation straight into the soc-pcm handler:

```c
/* sound/core/pcm_lib.c:510 */
void snd_pcm_set_ops(struct snd_pcm *pcm, int direction,
		     const struct snd_pcm_ops *ops)
{
	struct snd_pcm_str *stream = &pcm->streams[direction];
	struct snd_pcm_substream *substream;
	
	for (substream = stream->substream; substream != NULL; substream = substream->next)
		substream->ops = ops;
}
```

The chosen set follows the link kind, a back end installing no application-facing ops, a front end the Dynamic PCM front-end ops, and an ordinary link the soc_pcm handlers this page covers, before the bind above points every substream at it:

```
    soc_new_pcm: link kind selects the rtd->ops set
    ────────────────────────────────────────────────

    link kind          .open / .hw_params / .prepare / ...
    ─────────────────  ──────────────────────────────────────
    no_pcm /           (no application-facing ops installed;
      c2c_params        substream->private_data = rtd only)
    dynamic (FE)       dpcm_fe_dai_open / _hw_params / _prepare
                       _trigger / _hw_free / _close
    ordinary           soc_pcm_open / soc_pcm_hw_params /
      (this page)       soc_pcm_prepare / _trigger / _hw_free /
                        _close
                              │  .pointer = soc_pcm_pointer (FE + ordinary)
                              ▼
                    snd_pcm_set_ops(pcm, dir, &rtd->ops)
                    binds the chosen set to every substream
```

### The PCM operation set ASoC fills in

The table whose address [`snd_pcm_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L510) installs is a [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), the per-substream operation set the ALSA PCM core calls. The setup phase uses three of its function pointers, [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), and [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55), which ASoC points at [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), and [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) for an ordinary link:

```c
/* include/sound/pcm.h:55 */
struct snd_pcm_ops {
	int (*open)(struct snd_pcm_substream *substream);
	int (*close)(struct snd_pcm_substream *substream);
	int (*ioctl)(struct snd_pcm_substream * substream,
		     unsigned int cmd, void *arg);
	int (*hw_params)(struct snd_pcm_substream *substream,
			 struct snd_pcm_hw_params *params);
	int (*hw_free)(struct snd_pcm_substream *substream);
	int (*prepare)(struct snd_pcm_substream *substream);
	int (*trigger)(struct snd_pcm_substream *substream, int cmd);
	int (*sync_stop)(struct snd_pcm_substream *substream);
	snd_pcm_uframes_t (*pointer)(struct snd_pcm_substream *substream);
	int (*get_time_info)(struct snd_pcm_substream *substream,
			struct timespec64 *system_ts, struct timespec64 *audio_ts,
			struct snd_pcm_audio_tstamp_config *audio_tstamp_config,
			struct snd_pcm_audio_tstamp_report *audio_tstamp_report);
	int (*fill_silence)(struct snd_pcm_substream *substream, int channel,
			    unsigned long pos, unsigned long bytes);
	int (*copy)(struct snd_pcm_substream *substream, int channel,
		    unsigned long pos, struct iov_iter *iter, unsigned long bytes);
	struct page *(*page)(struct snd_pcm_substream *substream,
			     unsigned long offset);
	int (*mmap)(struct snd_pcm_substream *substream, struct vm_area_struct *vma);
	int (*ack)(struct snd_pcm_substream *substream);
};
```

### The lock-wrapper shape

The three setup handlers share one shape. The outer function takes the card mutex, calls its inner worker, and drops the mutex. [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917) is the template:

```c
/* sound/soc/soc-pcm.c:917 */
static int soc_pcm_open(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret;

	snd_soc_dpcm_mutex_lock(rtd);
	ret = __soc_pcm_open(rtd, substream);
	snd_soc_dpcm_mutex_unlock(rtd);
	return ret;
}
```

[`snd_soc_dpcm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1548) is a `_Generic` macro that takes the card-wide [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001) whether passed a card or a runtime, and each inner worker opens with [`snd_soc_dpcm_mutex_assert_held()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1556) so the body is safe to reuse from the Dynamic PCM paths that already hold the lock.

### open fans the startup across components, link, and DAIs

[`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) is where one open splits across the three layers. It runtime-resumes the components, opens each through [`soc_pcm_components_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L718), runs the machine link [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and iterates the runtime's DAIs with [`for_each_rtd_dais()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217) calling [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) on each:

```c
/* sound/soc/soc-pcm.c:854 */
static int __soc_pcm_open(struct snd_soc_pcm_runtime *rtd,
			  struct snd_pcm_substream *substream)
{
	struct snd_soc_component *component;
	struct snd_soc_dai *dai;
	int i, ret = 0;

	snd_soc_dpcm_mutex_assert_held(rtd);

	for_each_rtd_components(rtd, i, component)
		pinctrl_pm_select_default_state(component->dev);

	ret = snd_soc_pcm_component_pm_runtime_get(rtd, substream);
	if (ret < 0)
		goto err;

	ret = soc_pcm_components_open(substream);
	if (ret < 0)
		goto err;

	ret = snd_soc_link_startup(substream);
	if (ret < 0)
		goto err;

	/* startup the audio subsystem */
	for_each_rtd_dais(rtd, i, dai) {
		ret = snd_soc_dai_startup(dai, substream);
		if (ret < 0)
			goto err;
	}
	...
```

Any failure jumps to the `err` label, which runs the open-side cleanup with `rollback = 1` so only the layers that actually opened are torn down:

```c
/* sound/soc/soc-pcm.c:906 */
dynamic:
	snd_soc_runtime_activate(rtd, substream->stream);
	ret = 0;
err:
	if (ret < 0)
		soc_pcm_clean(rtd, substream, 1);

	return soc_pcm_ret(rtd, ret);
}
```

The component side of the fan-out is [`soc_pcm_components_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L718), which takes a per-open module reference and then calls [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) for each component:

```c
/* sound/soc/soc-pcm.c:718 */
static int soc_pcm_components_open(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int i, ret = 0;

	for_each_rtd_components(rtd, i, component) {
		ret = snd_soc_component_module_get_when_open(component, substream);
		if (ret < 0)
			break;

		ret = snd_soc_component_open(component, substream);
		if (ret < 0)
			break;
	}

	return ret;
}
```

[`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) calls the component's [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) op when one is present and records the substream with a mark so a later error path closes only the components that opened:

```c
/* sound/soc/soc-component.c:251 */
int snd_soc_component_open(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (component->driver->open)
		ret = component->driver->open(component, substream);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_component_mark_push(component, substream, open);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) is the DAI side, skipping a direction the DAI does not support, running the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, and recording its own mark on success.

### open merges the CPU and codec capabilities

After every DAI starts, [`__soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L854) computes what the link as a whole can do. The relevant slice of the worker shows the order: [`soc_pcm_init_runtime_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L701) seeds the runtime hardware record, [`soc_pcm_update_symmetry()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L389) collects the symmetry constraints, and [`soc_hw_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L812) validates the merge before the open is allowed to activate:

```c
/* sound/soc/soc-pcm.c:889 */
	/* Check that the codec and cpu DAIs are compatible */
	soc_pcm_init_runtime_hw(substream);

	soc_pcm_update_symmetry(substream);

	ret = soc_hw_sanity_check(substream);
	if (ret < 0)
		goto err;
```

[`soc_pcm_init_runtime_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L701) is a thin wrapper that runs the merge and then re-applies the substream's starting [`formats`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) mask, so a format already excluded by the platform component stays excluded after the DAI capabilities fold in:

```c
/* sound/soc/soc-pcm.c:701 */
static void soc_pcm_init_runtime_hw(struct snd_pcm_substream *substream)
{
	struct snd_pcm_hardware *hw = &substream->runtime->hw;
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	u64 formats = hw->formats;

	/*
	 * At least one CPU and one CODEC should match. Otherwise, we should
	 * have bailed out on a higher level, since there would be no CPU or
	 * CODEC to support the transfer direction in that case.
	 */
	snd_soc_runtime_calc_hw(rtd, hw, substream->stream);

	if (formats)
		hw->formats &= formats;
}
```

The merge itself is [`snd_soc_runtime_calc_hw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L631), which intersects the rate, channel, and format limits of every CPU DAI and every codec DAI into the substream's [`struct snd_pcm_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L32) so the negotiated parameters can satisfy both ends at once:

```c
/* sound/soc/soc-pcm.c:631 */
int snd_soc_runtime_calc_hw(struct snd_soc_pcm_runtime *rtd,
			    struct snd_pcm_hardware *hw, int stream)
{
	...
	/* first calculate min/max only for CPUs in the DAI link */
	for_each_rtd_cpu_dais(rtd, i, cpu_dai) {
		if (!snd_soc_dai_stream_valid(cpu_dai, stream))
			continue;

		cpu_stream = snd_soc_dai_get_pcm_stream(cpu_dai, stream);

		soc_pcm_hw_update_chan(hw, cpu_stream);
		soc_pcm_hw_update_rate(hw, cpu_stream);
		soc_pcm_hw_update_format(hw, cpu_stream);
	}
	...
	/* second calculate min/max only for CODECs in the DAI link */
	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		if (!snd_soc_dai_stream_valid(codec_dai, stream))
			continue;

		codec_stream = snd_soc_dai_get_pcm_stream(codec_dai, stream);

		soc_pcm_hw_update_chan(hw, codec_stream);
		soc_pcm_hw_update_rate(hw, codec_stream);
		soc_pcm_hw_update_format(hw, codec_stream);
	}

	/* Verify both a valid CPU DAI and a valid CODEC DAI were found */
	if (!hw->channels_min)
		return -EINVAL;
	...
}
```

[`soc_hw_sanity_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L812) then rejects the open with [`-EINVAL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/asm-generic/errno-base.h#L26) when the merged record has no rates, no formats, or an empty channel range, which is how a CPU and codec that share no common format fail the open instead of failing silently later:

```c
/* sound/soc/soc-pcm.c:812 */
static int soc_hw_sanity_check(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_pcm_hardware *hw = &substream->runtime->hw;
	const char *name_cpu = soc_cpu_dai_name(rtd);
	const char *name_codec = soc_codec_dai_name(rtd);
	const char *err_msg;
	struct device *dev = rtd->dev;

	err_msg = "rates";
	if (!hw->rates)
		goto config_err;

	err_msg = "formats";
	if (!hw->formats)
		goto config_err;

	err_msg = "channels";
	if (!hw->channels_min || !hw->channels_max ||
	     hw->channels_min  >  hw->channels_max)
		goto config_err;
	...
	return 0;

config_err:
	return snd_soc_ret(dev, -EINVAL,
			"%s <-> %s No matching %s\n", name_codec, name_cpu, err_msg);
}
```

The open ends by calling [`snd_soc_runtime_activate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L486), which raises the runtime and per-DAI usage counts so a second opener of a shared DAI sees it active.

```
    snd_soc_runtime_calc_hw: intersect every CPU and codec DAI
    ──────────────────────────────────────────────────────────

    each CPU DAI stream        each codec DAI stream
    ┌────────────────────┐     ┌────────────────────┐
    │ rate_min..rate_max │     │ rate_min..rate_max │
    │ channels_min..max  │     │ channels_min..max  │
    │ formats mask       │     │ formats mask       │
    └──────────┬─────────┘     └─────────┬──────────┘
               │  for_each_rtd_cpu_dais  │  for_each_rtd_codec_dais
               └───────────┬─────────────┘
                           ▼  raise min, lower max, AND the formats
              ┌──────────────────────────────────┐
              │ substream->runtime->hw           │
              │  rates  channels_min..max        │
              │  formats   (&= starting formats) │
              └────────────────┬─────────────────┘
                               ▼  soc_hw_sanity_check
              !rates  /  !formats  /  empty channels
                       ─▶ -EINVAL  "No matching ..."
```

### hw_params applies parameters codec-first, then CPU, then components

[`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) is the inner worker of [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172). It first re-checks symmetry against the caller's parameters, runs the machine link [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), then walks the codec DAIs and the CPU DAIs in separate loops, giving each DAI a private copy of the caller's [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) fixed up for that DAI. Its head establishes the order and the shared `out` rollback label:

```c
/* sound/soc/soc-pcm.c:1070 */
static int __soc_pcm_hw_params(struct snd_pcm_substream *substream,
			       struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *cpu_dai;
	struct snd_soc_dai *codec_dai;
	struct snd_pcm_hw_params tmp_params;
	int i, ret = 0;

	snd_soc_dpcm_mutex_assert_held(rtd);

	ret = soc_pcm_params_symmetry(substream, params);
	if (ret)
		goto out;

	ret = snd_soc_link_hw_params(substream, params);
	if (ret < 0)
		goto out;
	...
```

[`snd_soc_link_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L98) is the machine-link side of the fan-out, running the optional [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) op the board's [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L613) supplies and recording a mark for the rollback path, the same call-op-then-mark shape as the component and DAI wrappers:

```c
/* sound/soc/soc-link.c:98 */
int snd_soc_link_hw_params(struct snd_pcm_substream *substream,
			   struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	int ret = 0;

	if (rtd->dai_link->ops &&
	    rtd->dai_link->ops->hw_params)
		ret = rtd->dai_link->ops->hw_params(substream, params);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_link_mark_push(rtd, substream, hw_params);

	return soc_link_ret(rtd, ret);
}
```

The codec loop skips a codec that does not carry the current direction and narrows the channel count to the codec's TDM slot mask before [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) runs the op:

```c
/* sound/soc/soc-pcm.c:1089 */
	for_each_rtd_codec_dais(rtd, i, codec_dai) {
		unsigned int tdm_mask = snd_soc_dai_tdm_mask_get(codec_dai, substream->stream);
		...
		if (!snd_soc_dai_stream_valid(codec_dai, substream->stream))
			continue;

		/* copy params for each codec */
		tmp_params = *params;

		/* fixup params based on TDM slot masks */
		if (tdm_mask)
			soc_pcm_codec_params_fixup(&tmp_params, tdm_mask);

		ret = snd_soc_dai_hw_params(codec_dai, substream,
					    &tmp_params);
		if(ret < 0)
			goto out;

		soc_pcm_set_dai_params(codec_dai, &tmp_params);
		snd_soc_dapm_update_dai(substream, &tmp_params, codec_dai);
	}
```

[`soc_pcm_codec_params_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L997) is the per-DAI narrowing step, setting both ends of the channel interval to the population count of the mask so a codec on a four-slot TDM bus sees only its own slots:

```c
/* sound/soc/soc-pcm.c:997 */
static void soc_pcm_codec_params_fixup(struct snd_pcm_hw_params *params,
				       unsigned int mask)
{
	struct snd_interval *interval;
	int channels = hweight_long(mask);

	interval = hw_param_interval(params, SNDRV_PCM_HW_PARAM_CHANNELS);
	interval->min = channels;
	interval->max = channels;
}
```

The CPU loop is the mirror image, building each CPU DAI's channel mask by combining the masks of the codecs that map to it, then applying the same fixup and op. Each successful per-DAI op records its parameters with [`soc_pcm_set_dai_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L426), which stores the rate, channel count, and sample width that the symmetry checks compare against on the next open. After both DAI loops, [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) applies the unmodified parameters to every component and marks each one:

```c
/* sound/soc/soc-component.c:1080 */
int snd_soc_pcm_component_hw_params(struct snd_pcm_substream *substream,
				    struct snd_pcm_hw_params *params)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_component *component;
	int i, ret;

	for_each_rtd_components(rtd, i, component) {
		if (component->driver->hw_params) {
			ret = component->driver->hw_params(component,
							   substream, params);
			if (ret < 0)
				return soc_component_ret(component, ret);
		}
		/* mark substream if succeeded */
		soc_component_mark_push(component, substream, hw_params);
	}

	return 0;
}
```

The DAI wrapper [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) follows the same call-op-then-mark pattern as the component wrapper, calling the DAI's [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op and recording a mark for the rollback path:

```c
/* sound/soc/soc-dai.c:405 */
int snd_soc_dai_hw_params(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  struct snd_pcm_hw_params *params)
{
	int ret = 0;

	if (dai->driver->ops &&
	    dai->driver->ops->hw_params)
		ret = dai->driver->ops->hw_params(substream, params, dai);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_dai_mark_push(dai, substream, hw_params);

	return soc_dai_ret(dai, ret);
}
```

A failure anywhere in [`__soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1070) jumps to the `out` label, which runs the hw_free cleanup with `rollback = 1`, so the marks decide which DAIs and components get their resources released.

```
    __soc_pcm_hw_params: one params, a private fixed-up copy per DAI
    ───────────────────────────────────────────────────────────────

    caller's struct snd_pcm_hw_params  (params)
    ┌──────────────────────────────────────────┐
    │ rate   channels   format                 │
    └───┬──────────────┬──────────────┬────────┘
        │ link         │ each codec   │ each CPU DAI
        │ hw_params    │ DAI          │ (mask = OR of its
        ▼              ▼              ▼  codecs' tdm masks)
    link->ops    tmp_params=*params  tmp_params=*params
    hw_params    fixup: channels =   fixup: channels =
                  hweight(tdm_mask)   hweight(mask)
                 snd_soc_dai_         snd_soc_dai_
                  hw_params(codec)     hw_params(cpu)
                 soc_pcm_set_dai_params records each
                              │
                              ▼  after both DAI loops
    snd_soc_pcm_component_hw_params: every component gets
    the unmodified params  (SOF host DMA on x86)
```

### prepare runs the last setup ops and unmutes

[`__soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L933) runs link prepare through [`snd_soc_link_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-link.c#L86), component prepare through [`snd_soc_pcm_component_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1063), and DAI prepare through [`snd_soc_pcm_dai_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L588), then cancels any pending delayed close, raises the DAPM stream-start event, and unmutes the DAIs whose mute is not deferred to trigger:

```c
/* sound/soc/soc-pcm.c:933 */
static int __soc_pcm_prepare(struct snd_soc_pcm_runtime *rtd,
			     struct snd_pcm_substream *substream)
{
	struct snd_soc_dai *dai;
	int i, ret = 0;

	snd_soc_dpcm_mutex_assert_held(rtd);

	ret = snd_soc_link_prepare(substream);
	if (ret < 0)
		goto out;

	ret = snd_soc_pcm_component_prepare(substream);
	if (ret < 0)
		goto out;

	ret = snd_soc_pcm_dai_prepare(substream);
	if (ret < 0)
		goto out;

	/* cancel any delayed stream shutdown that is pending */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK &&
	    rtd->pop_wait) {
		rtd->pop_wait = 0;
		cancel_delayed_work(&rtd->delayed_work);
	}

	snd_soc_dapm_stream_event(rtd, substream->stream,
			SND_SOC_DAPM_STREAM_START);

	for_each_rtd_dais(rtd, i, dai) {
		if (!snd_soc_dai_mute_is_ctrled_at_trigger(dai))
			snd_soc_dai_digital_mute(dai, 0, substream->stream);
	}

out:
	...
	return ret;
}
```

[`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) raising [`SND_SOC_DAPM_STREAM_START`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L378) is the step that powers up the codec and platform widgets along the active path, so the audio route is electrically up by the time trigger starts the data flow. The prepare path deliberately does not pass its result through [`soc_pcm_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L29); according to the comment, "We don't want to log an error since we do not want to give userspace a way to do a denial-of-service attack on the syslog / diskspace", so a repeated failing prepare cannot flood the log.

### Worked example: SOF as the platform component on x86 ACPI

On an x86-64 ACPI machine the platform component is Sound Open Firmware, so each component wrapper above dispatches into a `sof_pcm_*` op. When [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) calls `component->driver->open`, that op is [`sof_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), which sets the runtime hardware limits from the topology-described stream caps:

```c
/* sound/soc/sof/pcm.c:536 */
static int sof_pcm_open(struct snd_soc_component *component,
			struct snd_pcm_substream *substream)
{
	...
	caps = &spcm->pcm.caps[substream->stream];

	/* set runtime config */
	runtime->hw.info = ops->hw_info; /* platform-specific */

	/* set any runtime constraints based on topology */
	runtime->hw.formats = le64_to_cpu(caps->formats);
	runtime->hw.period_bytes_min = le32_to_cpu(caps->period_size_min);
	runtime->hw.period_bytes_max = le32_to_cpu(caps->period_size_max);
	runtime->hw.periods_min = le32_to_cpu(caps->periods_min);
	runtime->hw.periods_max = le32_to_cpu(caps->periods_max);
	...
}
```

When [`snd_soc_pcm_component_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L1080) calls `component->driver->hw_params`, that op is [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), which sets up the connected firmware widgets and programs the host DMA, returning early for a back-end link that carries no PCM:

```c
/* sound/soc/sof/pcm.c:116 */
static int sof_pcm_hw_params(struct snd_soc_component *component,
			     struct snd_pcm_substream *substream,
			     struct snd_pcm_hw_params *params)
{
	...
	/* nothing to do for BE */
	if (rtd->dai_link->no_pcm)
		return 0;

	spcm = snd_sof_find_spcm_dai(component, rtd);
	if (!spcm)
		return -EINVAL;
	...
	ret = snd_sof_pcm_platform_hw_params(sdev, substream, params, platform_params);
	if (ret < 0) {
		spcm_err(spcm, substream->stream, "platform hw params failed\n");
		return ret;
	}
	...
}
```

The soc-pcm layer never reaches into the firmware itself; it only fans the open and the parameters out to the component, and the SOF component turns that into IPC and DMA programming. The same wrappers drive the codec DAIs over SoundWire on the other side of the link, so one application hw_params call configures the DSP host DMA, the SoundWire ports, and the codec in a single locked pass.

### The snd_pcm_ops dispatch to DAI and component wrappers

[`soc_new_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2909) installs the [`struct snd_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L55) into [`rtd->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1147), and each operation flows through its [`soc_pcm_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L917), [`soc_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L1172), or [`soc_pcm_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L979) handler (under [`snd_soc_dpcm_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1548)) to the DAI wrappers in [`sound/soc/soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) (such as [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437)) and the component wrappers in [`sound/soc/soc-component.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) (such as [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251)).

```
    snd_pcm_ops  (installed by soc_new_pcm, held in rtd->ops)
    ┌─────────────────────────────────────────────────────────────┐
    │ .open .hw_params .prepare .trigger .hw_free .close .pointer │
    └──────────────────────────────┬──────────────────────────────┘
                                   │  one PCM operation
                                   ▼
                          soc_pcm_<op>()
                  snd_soc_dpcm_mutex_lock(rtd)
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
       DAI wrappers (soc-dai.c)         component wrappers (soc-component.c)
       snd_soc_dai_startup / hw_params  snd_soc_pcm_component_open / hw_params
       snd_soc_dai_prepare              snd_soc_pcm_component_prepare
       snd_soc_pcm_dai_trigger          snd_soc_pcm_component_trigger
              │ for_each_rtd_dais                  │ for_each_rtd_components
       ┌──────┴──────┐                      ┌──────┴──────┐
       ▼             ▼                      ▼             ▼
    CPU DAI ops   codec DAI ops         platform        (other
    (.startup,    (.hw_params,          component        components)
     .trigger)     .shutdown)           ops (SOF)
```
