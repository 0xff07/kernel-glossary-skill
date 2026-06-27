# ALSA Use Case Manager (UCM)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Use Case Manager is the userspace layer that selects an audio path on a card by name, reading a card's verb, device, and modifier profile from the alsa-ucm-conf tree and driving it onto the kernel surfaces a card publishes, the control node /dev/snd/controlC%d that [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) creates, the PCM nodes pcmC%dD%d that [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) names, and the card identity in [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) that [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) reports, where each high-level use case becomes a sequence of writes to the kcontrols an ASoC machine driver and topology built with [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) plus a choice of PCM device.

```
    UCM profile for one card (alsa-ucm-conf, userspace)
    ───────────────────────────────────────────────────

    Card identity (matched by name)
    ┌───────────────────────────────────────────────────────────────┐
    │ struct snd_card .id "sof-soundwire"  .longname "..."          │
    │ reported by SNDRV_CTL_IOCTL_CARD_INFO over controlC%d         │
    └───────────────────────────────┬───────────────────────────────┘
                                    │  conf/<driver>/<longname>.conf
                                    ▼
    Verb  "HiFi"  (one SectionUseCase)
    ┌───────────────────────────────────────────────────────────────┐
    │  EnableSequence   ── cset "name='...Switch' 1"                │
    │  Devices ───────┬────────────────┬───────────────┐           │
    │     ┌───────────▼──┐  ┌──────────▼─┐  ┌──────────▼─┐         │
    │     │ "Speaker"    │  │"Headphones"│  │  "Mic"     │         │
    │     │ EnableSeq    │  │ EnableSeq  │  │ EnableSeq  │         │
    │     │  cset ...    │  │  cset ...  │  │  cset ...  │         │
    │     │ PlaybackPCM  │  │ PlaybackPCM│  │ CapturePCM │         │
    │     │  pcmC0D0p    │  │  pcmC0D0p  │  │  pcmC0D1c  │         │
    │     └──────┬───────┘  └─────┬──────┘  └─────┬──────┘         │
    │  Modifiers (overlay on a device, e.g. "Mic")                 │
    └─────────┼────────────────────┼───────────────┼───────────────┘
              │ cset writes         │               │ device choice
              ▼                     ▼               ▼
    ┌───────────────────────┐              ┌─────────────────────────┐
    │ controlC%d            │              │ pcmC%dD%d  (p | c)      │
    │  SNDRV_CTL_IOCTL_     │              │  snd_pcm_new_stream()   │
    │  ELEM_WRITE           │              │  named node             │
    │   → struct snd_kcontrol .put         │   → one substream       │
    └───────────────────────┘              └─────────────────────────┘
              one ALSA card built by the ASoC machine + topology
```

## SUMMARY

UCM is an alsa-lib construct. It carries no kernel code of its own; it is a configuration tree (alsa-ucm-conf) plus the snd_use_case_mgr_* API in libasound that a manager (PulseAudio, PipeWire, the [alsaucm](https://github.com/alsa-project/alsa-utils) tool) loads. The kernel side of UCM is the set of surfaces a card publishes that the profile names and drives. The card carries an identity in [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), whose [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84) and [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87) [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) copies out through [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200), and UCM selects which profile to load by matching that name. The card publishes one control node /dev/snd/controlC%d that [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) creates with [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249), and one PCM node pcmC%dD%d per stream direction that [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) names as `pcmC%iD%i%c`.

The profile is three nested object kinds. A verb (a SectionUseCase such as `"HiFi"`) is the top-level use case for the card. A device (a SectionDevice such as `"Speaker"`, `"Headphones"`, or `"Mic"`) is one selectable endpoint inside a verb. A modifier (a SectionModifier) is an overlay applied on top of a device for a sub-use such as voice capture. Each carries an EnableSequence and a DisableSequence, lists of `cset` commands, and a `PlaybackPCM` or `CapturePCM` line. A `cset` command names a kcontrol by its [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) and a value, and libasound resolves it with [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204), which runs the addressed [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) `put` callback after [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) resolves it. The exact `cset`/`cget` to ioctl path is the subject of the sibling kcontrol-mapping page; this page is the conceptual model and the kernel surfaces UCM binds to.

The kcontrols a `cset` names exist because an ASoC machine driver and the DSP topology created them. A codec or board control template is a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) built with one of the `SOC_*` macros ([`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), [`SOC_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110), [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336)), which [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) turns into a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) with [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) registers on the card. A DAPM widget control passes through [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909), which prepends the component [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) so the control name a UCM profile writes is stable across a card. The reference platform is an Intel SoundWire/SOF laptop card, where the machine driver is the generic SoundWire board and the controls come from the codec drivers and the SOF topology loaded for that machine.

## SPECIFICATIONS

UCM is an ALSA userspace construct and has no kernel hardware specification. The configuration syntax (the SectionUseCase, SectionDevice, SectionModifier, EnableSequence, and `cset`/`PlaybackPCM` keywords) is defined by the alsa-ucm-conf project and the snd_use_case_mgr_* API in alsa-lib, both referenced under OTHER SOURCES. The kernel surfaces UCM drives are defined by the ALSA kernel/userspace ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). The control element address a `cset` names is a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), whose [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) carries one of the `SNDRV_CTL_ELEM_IFACE_*` values, with [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) the value for the mixer controls UCM writes. The card identity UCM matches is reported through [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063). The control name string fits [`SNDRV_CTL_ELEM_ID_NAME_MAXLEN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1119) bytes. The codecs of the reference platform reach the host over SoundWire and the DSP firmware interface, each described by its own specification.

## LINUX KERNEL

### Card identity (core.h, init.c, control.c)

- [`'\<struct snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80): the card object; its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84), [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L85), [`shortname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L86), [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87), and [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L90) strings are the identity UCM matches a profile against
- [`'\<snd_card_new\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171): allocate the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) and seed its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84) from the given identifier string
- [`'\<snd_card_register\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870): register every device of the card and finalize a unique [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84) from the [`shortname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L86) or [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87)
- [`'\<snd_ctl_card_info\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867): copy the identity strings into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063) for [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200)

### Control char device (control.c, sound.c)

- [`'\<snd_ctl_dev_register\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291): publish /dev/snd/controlC%d, the node every UCM `cset`/`cget` opens
- [`'\<snd_register_device\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249): allocate the minor and create the device file with the [`SNDRV_DEVICE_TYPE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) type, [`SNDRV_MINOR_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L17) being index 0 on the card
- [`'\<snd_ctl_find_id\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840): resolve the [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) a `cset` names to a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) on [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105)
- [`'\<struct snd_kcontrol\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70): one control element; the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72) UCM addresses and the [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callbacks a `cget`/`cset` runs
- [`'\<struct snd_ctl_elem_id\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121): the element address; the [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), and [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127) a UCM `cset` string encodes

### PCM device naming (pcm.c)

- [`'\<snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767): create one PCM instance with a device index, the `D%d` in a UCM `PlaybackPCM`/`CapturePCM` line
- [`'\<snd_pcm_new_stream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627): name the per-direction node `pcmC%iD%i%c`, with the trailing `p` or `c` a UCM device selects

### ASoC control creation (soc-core.c, soc-dapm.c, soc.h)

- [`'\<struct snd_kcontrol_new\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47): the control template a codec or board declares with a `SOC_*` macro, carrying the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L50) a UCM profile writes
- [`'\<SOC_SINGLE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) / [`'\<SOC_DOUBLE_R\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110): mixer control templates wiring [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c) and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c) onto the [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) interface
- [`'\<SOC_DAPM_SINGLE\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336): a routing-switch template a DAPM widget owns
- [`'\<snd_soc_cnew\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440): build a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) from a template, prepending the optional name prefix
- [`'\<snd_soc_add_card_controls\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521): add a board's control array to the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80)
- [`'\<snd_soc_dapm_new_control\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909): create a DAPM widget, applying the component [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) to the widget and its kcontrol name
- [`'\<snd_ctl_new1\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260): allocate a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) from a template and copy its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) into the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72)
- [`'\<snd_ctl_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546): add the control to [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) and assign a unique numid

## KERNEL DOCUMENTATION

- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the source, direction, and function naming convention the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) field follows, the same string a UCM `cset` encodes
- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter defining the element [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) and the info/get/put callbacks a `cset`/`cget` drives, and the PCM Interface chapter for the device a `PlaybackPCM` names
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the widget graph that produces the routing-switch controls a UCM EnableSequence toggles
- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver that fills the card name UCM matches and adds the board controls UCM writes

## OTHER SOURCES

- [ALSA Use Case Manager configuration (alsa-ucm-conf)](https://github.com/alsa-project/alsa-ucm-conf)
- [ALSA project library documentation, Use Case Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__ucm.html)
- [alsa-utils (alsaucm, amixer, alsactl)](https://github.com/alsa-project/alsa-utils)
- [PipeWire ALSA Use Case Manager support](https://docs.pipewire.org/page_module_alsa_seq.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

UCM selects a use case in userspace and drives it onto three kernel surfaces of one card. It matches the profile against the card identity, writes the control node, and opens the PCM node. The objects below are what a UCM profile names; each is created by the card's drivers and outlives a single open.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| card identity [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) ([`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84), [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87)) | [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), finalized by [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) | whole card lifetime |
| control node /dev/snd/controlC%d | [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) via [`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) | whole card lifetime |
| PCM node pcmC%dD%d (p\|c) | [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) then [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) | whole card lifetime |
| control element [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) | [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) + [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546) (board) or topology | added at probe, until card teardown |
| ASoC control template [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) | a `SOC_*` macro in a codec or board | static, compiled in |
| DAPM-named control | [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909) (applies [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207)) | added at probe, until card teardown |
| element address [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) | filled per `cset` by libasound | per ioctl |

## DETAILS

### The card identity a UCM profile matches

UCM does not address a card by minor number. It loads a profile by the card's name, so the kernel side begins with the identity strings in [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80). The card holds a short machine-readable [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84), a [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L85) key, human [`shortname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L86) and [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87) strings, and a [`components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L90) list:

```c
/* include/sound/core.h:80 */
struct snd_card {
	int number;			/* number of soundcard (index to
								snd_cards) */

	char id[16];			/* id string of this card */
	char driver[16];		/* driver name */
	char shortname[32];		/* short name of this soundcard */
	char longname[80];		/* name of this soundcard */
	char irq_descr[32];		/* Interrupt description */
	char mixername[80];		/* mixer name */
	char components[128];		/* card components delimited with
								space */
	...
	struct device *ctl_dev;		/* control device */
	...
	struct list_head controls;	/* all controls for this card */
	struct list_head ctl_files;	/* active control files */
	...
};
```

[`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) seeds the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84) from the identifier the driver passes, and [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) makes it unique at register time, deriving one from the [`shortname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L86) or [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87) when the driver gave none:

```c
/* sound/core/init.c:870 (excerpt) */
	scoped_guard(mutex, &snd_card_mutex) {
		if (snd_cards[card->number]) {
			/* already registered */
			return snd_info_card_register(card); /* register pending info */
		}
		if (*card->id) {
			/* make a unique id name from the given string */
			char tmpid[sizeof(card->id)];

			memcpy(tmpid, card->id, sizeof(card->id));
			snd_card_set_id_no_lock(card, tmpid, tmpid);
		} else {
			/* create an id from either shortname or longname */
			const char *src;

			src = *card->shortname ? card->shortname : card->longname;
			snd_card_set_id_no_lock(card, src,
						retrieve_id_from_card_name(src));
		}
		snd_cards[card->number] = card;
	}
```

A UCM manager reads the same strings through the control device. [`snd_ctl_card_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L867) answers [`SNDRV_CTL_IOCTL_CARD_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1200) by copying [`card->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L84), [`card->driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L85), [`card->longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87), and [`card->components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L90) into a [`struct snd_ctl_card_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1063):

```c
/* sound/core/control.c:867 */
static int snd_ctl_card_info(struct snd_card *card, struct snd_ctl_file * ctl,
			     unsigned int cmd, void __user *arg)
{
	struct snd_ctl_card_info *info __free(kfree) =
		kzalloc(sizeof(*info), GFP_KERNEL);

	if (! info)
		return -ENOMEM;
	scoped_guard(rwsem_read, &snd_ioctl_rwsem) {
		info->card = card->number;
		strscpy(info->id, card->id, sizeof(info->id));
		strscpy(info->driver, card->driver, sizeof(info->driver));
		strscpy(info->name, card->shortname, sizeof(info->name));
		strscpy(info->longname, card->longname, sizeof(info->longname));
		strscpy(info->mixername, card->mixername, sizeof(info->mixername));
		strscpy(info->components, card->components, sizeof(info->components));
	}
	if (copy_to_user(arg, info, sizeof(struct snd_ctl_card_info)))
		return -EFAULT;
	return 0;
}
```

UCM looks for a configuration file under the alsa-ucm-conf tree keyed by the [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L85) and [`longname`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L87) (for the SoundWire generic board the conf directory is keyed by the `"sof-soundwire"` card name). On the reference Intel SoundWire/SOF laptop the SoundWire machine driver fills [`card->components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L90) with substrings such as `"cfg-amp:2"` and `"mic:dmic cfg-mics:2"`, which a profile reads to decide how many speaker amplifiers and digital microphones the verb should enable:

```c
/* sound/soc/intel/boards/sof_sdw.c:1498 (excerpt) */
	card->components = devm_kasprintf(card->dev, GFP_KERNEL,
					  " cfg-amp:%d", amp_num);
	if (!card->components)
		return -ENOMEM;

	if (mach->mach_params.dmic_num) {
		card->components = devm_kasprintf(card->dev, GFP_KERNEL,
						  "%s mic:dmic cfg-mics:%d",
						  card->components,
						  mach->mach_params.dmic_num);
		if (!card->components)
			return -ENOMEM;
	}
```

The read side mirrors that build, each field copied out for the manager keying a different part of the lookup, the id and driver picking a config directory, the longname picking a file, and the components carrying the amp and mic counts a verb reads to size its sequence:

```
    snd_ctl_card_info fields a UCM manager reads to pick a profile
    ──────────────────────────────────────────────────────────────

    SNDRV_CTL_IOCTL_CARD_INFO on controlC%d
    ┌───────────────────────────────────┐
    │ struct snd_ctl_card_info          │       used by UCM as
    ├───────────────────────────────────┤
    │ id        ◀── card->id            │ ────▶ conf dir key
    │ driver    ◀── card->driver        │ ────▶ conf dir key
    │ longname  ◀── card->longname      │ ────▶ conf file key
    │ components ◀─ card->components    │ ────▶ verb decisions
    └─────────────────┬─────────────────┘
                      │ components (sof_sdw board)
                      ▼
    ┌───────────────────────────────────┐
    │ " cfg-amp:2"            2 amps    │
    │ " mic:dmic cfg-mics:2"  2 DMIC    │
    └───────────────────────────────────┘
       a verb reads these counts to size its EnableSequence
```

### The control node a cset and cget open

Every card publishes exactly one control node, /dev/snd/controlC%d, and that is the single descriptor through which a UCM EnableSequence applies all of its `cset` writes. [`snd_ctl_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2291) registers it when the card's control component comes up, passing [`card->ctl_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L99) and the control file operations:

```c
/* sound/core/control.c:2291 */
static int snd_ctl_dev_register(struct snd_device *device)
{
	struct snd_card *card = device->device_data;
	int err;

	err = snd_register_device(SNDRV_DEVICE_TYPE_CONTROL, card, -1,
				  &snd_ctl_f_ops, card, card->ctl_dev);
	if (err < 0)
		return err;
	call_snd_ctl_lops(card, lregister);
	return 0;
}
```

[`snd_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L249) records the type, the card, and the file operations in a [`struct snd_minor`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L215), assigns a free minor, and adds the device so the node appears under /dev/snd:

```c
/* sound/core/sound.c:249 */
int snd_register_device(int type, struct snd_card *card, int dev,
			const struct file_operations *f_ops,
			void *private_data, struct device *device)
{
	int minor;
	int err = 0;
	struct snd_minor *preg;

	if (snd_BUG_ON(!device))
		return -EINVAL;

	preg = kmalloc_obj(*preg);
	if (preg == NULL)
		return -ENOMEM;
	preg->type = type;
	preg->card = card ? card->number : -1;
	preg->device = dev;
	preg->f_ops = f_ops;
	preg->private_data = private_data;
	preg->card_ptr = card;
	guard(mutex)(&sound_mutex);
	minor = snd_find_free_minor(type, card, dev);
	if (minor < 0) {
		err = minor;
		goto error;
	}

	preg->dev = device;
	device->devt = MKDEV(major, minor);
	err = device_add(device);
	if (err < 0)
		goto error;

	snd_minors[minor] = preg;
 error:
	if (err < 0)
		kfree(preg);
	return err;
}
```

The [`SNDRV_DEVICE_TYPE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L30) type maps to [`SNDRV_MINOR_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/minors.h#L17), which is index 0 in a card's minor block, so the control node is `controlC%d` with no device suffix:

```c
/* include/sound/minors.h:17 */
#define SNDRV_MINOR_CONTROL		0	/* 0 */
...
#define SNDRV_MINOR_PCM_PLAYBACK	16	/* 16 - 23 */
#define SNDRV_MINOR_PCM_CAPTURE		24	/* 24 - 31 */
```

When libasound applies a `cset`, it opens this node and issues [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204); a `cget` issues [`SNDRV_CTL_IOCTL_ELEM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203). Both first resolve the element the UCM string named. [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) matches the [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121), either by the numeric [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or by the interface-name-index tuple, walking [`card->controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) as the last resort:

```c
/* sound/core/control.c:840 */
struct snd_kcontrol *snd_ctl_find_id(struct snd_card *card,
				     const struct snd_ctl_elem_id *id)
{
	struct snd_kcontrol *kctl;

	if (snd_BUG_ON(!card || !id))
		return NULL;

	if (id->numid != 0)
		return snd_ctl_find_numid(card, id->numid);
#ifdef CONFIG_SND_CTL_FAST_LOOKUP
	kctl = xa_load(&card->ctl_hash, get_ctl_id_hash(id));
	if (kctl && elem_id_matches(kctl, id))
		return kctl;
	if (!card->ctl_hash_collision)
		return NULL; /* we can rely on only hash table */
#endif
	/* no matching in hash table - try all as the last resort */
	guard(read_lock_irqsave)(&card->controls_rwlock);
	list_for_each_entry(kctl, &card->controls, list)
		if (elem_id_matches(kctl, id))
			return kctl;

	return NULL;
}
```

The element a `cset` names is the [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), whose [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callback the write runs and whose [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L74) callback the read runs:

```c
/* include/sound/control.h:70 */
struct snd_kcontrol {
	struct list_head list;		/* list of controls */
	struct snd_ctl_elem_id id;
	unsigned int count;		/* count of same elements */
	snd_kcontrol_info_t *info;
	snd_kcontrol_get_t *get;
	snd_kcontrol_put_t *put;
	union {
		snd_kcontrol_tlv_rw_t *c;
		const unsigned int *p;
	} tlv;
	unsigned long private_value;
	void *private_data;
	void (*private_free)(struct snd_kcontrol *kcontrol);
	struct snd_kcontrol_volatile vd[] __counted_by(count);	/* volatile data */
};
```

The string a UCM `cset` carries names the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72) of this control. The address is a [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121) whose [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) selects the interface and whose [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126) holds the control name:

```c
/* include/uapi/sound/asound.h:1121 */
struct snd_ctl_elem_id {
	unsigned int numid;		/* numeric identifier, zero = invalid */
	snd_ctl_elem_iface_t iface;	/* interface identifier */
	unsigned int device;		/* device/client number */
	unsigned int subdevice;		/* subdevice (substream) number */
	unsigned char name[SNDRV_CTL_ELEM_ID_NAME_MAXLEN];		/* ASCII name of item */
	unsigned int index;		/* index of item */
};
```

A UCM line `cset "name='Speaker Switch' on"` encodes [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) and the name `"Speaker Switch"` into this [`struct snd_ctl_elem_id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1121). The [`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123) values come from the `SNDRV_CTL_ELEM_IFACE_*` constants, with the mixer interface the one a UCM profile uses for nearly every control:

```c
/* include/uapi/sound/asound.h:1085 */
typedef int __bitwise snd_ctl_elem_iface_t;
#define	SNDRV_CTL_ELEM_IFACE_CARD	((__force snd_ctl_elem_iface_t) 0) /* global control */
#define	SNDRV_CTL_ELEM_IFACE_HWDEP	((__force snd_ctl_elem_iface_t) 1) /* hardware dependent device */
#define	SNDRV_CTL_ELEM_IFACE_MIXER	((__force snd_ctl_elem_iface_t) 2) /* virtual mixer device */
#define	SNDRV_CTL_ELEM_IFACE_PCM	((__force snd_ctl_elem_iface_t) 3) /* PCM device */
#define	SNDRV_CTL_ELEM_IFACE_RAWMIDI	((__force snd_ctl_elem_iface_t) 4) /* RawMidi device */
#define	SNDRV_CTL_ELEM_IFACE_TIMER	((__force snd_ctl_elem_iface_t) 5) /* timer device */
#define	SNDRV_CTL_ELEM_IFACE_SEQUENCER	((__force snd_ctl_elem_iface_t) 6) /* sequencer client */
```

The concrete copy-in of the value, the [`SNDRV_CTL_ELEM_ACCESS_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1096) check, and the [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) invocation are the subject of the kcontrol-mapping sibling page. This page stops at the resolved [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70), which is the object a UCM device's EnableSequence drives.

```
    Minor-number block of one card (SNDRV_MINOR_*)
    ──────────────────────────────────────────────

    minor   constant                  node             UCM opens
    ┌─────┬──────────────────────┬───────────────┬───────────────┐
    │  0  │ SNDRV_MINOR_CONTROL  │ controlC%d    │ cset / cget   │
    ├─────┼──────────────────────┼───────────────┼───────────────┤
    │16-23│ SNDRV_MINOR_PCM_     │ pcmC%dD%dp    │ PlaybackPCM   │
    │     │   PLAYBACK           │ (D = 0..7)    │               │
    ├─────┼──────────────────────┼───────────────┼───────────────┤
    │24-31│ SNDRV_MINOR_PCM_     │ pcmC%dD%dc    │ CapturePCM    │
    │     │   CAPTURE            │ (D = 0..7)    │               │
    └─────┴──────────────────────┴───────────────┴───────────────┘
      control node is index 0, so it has no D-suffix; the one node
      every EnableSequence opens for all of its cset writes
```

### The PCM device a verb chooses

Alongside its `cset` writes, a UCM device or modifier names a PCM device with a `PlaybackPCM` or `CapturePCM` line, for example `PlaybackPCM "hw:${CardId},0"`. The trailing `0` is the device index of a node the card created. A driver creates the PCM instance with [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), which takes the device index and the substream counts for each direction:

```c
/* sound/core/pcm.c:767 */
int snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, struct snd_pcm **rpcm)
{
	return _snd_pcm_new(card, id, device, playback_count, capture_count,
			false, rpcm);
}
```

[`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) then names the per-direction node. It sets the device name to `pcmC%iD%i%c`, filling the card number, the device index, and `p` for playback or `c` for capture, the exact suffix a UCM `PlaybackPCM` or `CapturePCM` line addresses:

```c
/* sound/core/pcm.c:627 (excerpt) */
	err = snd_device_alloc(&pstr->dev, pcm->card);
	if (err < 0)
		return err;
	dev_set_name(pstr->dev, "pcmC%iD%i%c", pcm->card->number, pcm->device,
		     stream == SNDRV_PCM_STREAM_PLAYBACK ? 'p' : 'c');
```

A UCM verb maps high-level use cases onto these nodes. On the reference card the `"HiFi"` verb owns devices `"Speaker"` and `"Headphones"` that both set `PlaybackPCM` to the front playback device pcmC0D0p, and a `"Mic"` device that sets `CapturePCM` to the DMIC capture device, perhaps pcmC0D1c. Selecting a device thus does two things at once. It applies the device's EnableSequence of `cset` writes to route audio to that endpoint, and it tells the manager which pcmC%dD%d node to open for the stream. The kernel keeps the two independent, the control node carries the routing and the PCM node carries the audio, and the UCM device is the userspace object that pairs them.

### A machine driver and topology produce the controls UCM expects

The control names a UCM profile writes are not invented by UCM. They are the names the card's drivers gave their kcontrols, and a profile is written against a specific card precisely so the names line up. On an ASoC card the controls come from two places, the codec and board drivers that declare static control arrays, and the DSP topology that the SOF firmware loads, which adds further controls at probe time. A static control begins as a [`struct snd_kcontrol_new`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) template, the type every `SOC_*` macro expands to:

```c
/* include/sound/control.h:47 */
struct snd_kcontrol_new {
	snd_ctl_elem_iface_t iface;	/* interface identifier */
	unsigned int device;		/* device/client number */
	unsigned int subdevice;		/* subdevice (substream) number */
	const char *name;		/* ASCII name of item */
	unsigned int index;		/* index of item */
	unsigned int access;		/* access rights */
	unsigned int count;		/* count of same elements */
	snd_kcontrol_info_t *info;
	snd_kcontrol_get_t *get;
	snd_kcontrol_put_t *put;
	union {
		snd_kcontrol_tlv_rw_t *c;
		const unsigned int *p;
	} tlv;
	unsigned long private_value;
};
```

The [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) macro fills that template for a one-register switch or volume, setting the [`SNDRV_CTL_ELEM_IFACE_MIXER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1088) interface, the control name, and the standard mixer info/get/put callbacks:

```c
/* include/sound/soc.h:61 */
#define SOC_SINGLE(xname, reg, shift, max, invert) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = xname, \
	.info = snd_soc_info_volsw, .get = snd_soc_get_volsw,\
	.put = snd_soc_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(reg, shift, 0, max, invert, 0) }
```

A codec driver lists such templates in a control array, where the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L50) is the human string a UCM `cset` will name. A speaker amplifier codec, for example, declares a `"Speaker Volume"` and a switch:

```c
/* sound/soc/codecs/max98926.c:230 (excerpt) */
static const struct snd_kcontrol_new max98926_snd_controls[] = {
	SOC_SINGLE_TLV("Speaker Volume", MAX98926_GAIN,
		MAX98926_SPK_GAIN_SHIFT,
		(1<<MAX98926_SPK_GAIN_WIDTH)-1, 0,
		max98926_spk_tlv),
	SOC_SINGLE("Ramp Switch", MAX98926_GAIN_RAMPING,
		MAX98926_SPK_RMP_EN_SHIFT, 1, 0),
	...
};
```

The board adds its own control array to the card with [`snd_soc_add_card_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2521), which loops over the templates and runs each through [`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) and [`snd_ctl_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L546):

```c
/* sound/soc/soc-core.c:2472 */
static int snd_soc_add_controls(struct snd_card *card, struct device *dev,
	const struct snd_kcontrol_new *controls, int num_controls,
	const char *prefix, void *data)
{
	int i;

	for (i = 0; i < num_controls; i++) {
		const struct snd_kcontrol_new *control = &controls[i];
		int err = snd_ctl_add(card, snd_soc_cnew(control, data,
							 control->name, prefix));
		if (err < 0) {
			dev_err(dev, "ASoC: Failed to add %s: %d\n",
				control->name, err);
			return err;
		}
	}

	return 0;
}
```

[`snd_soc_cnew()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2440) is where the control name is finalized. It copies the template, builds the final name from an optional `prefix` and the template name, and hands the result to [`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260):

```c
/* sound/soc/soc-core.c:2440 */
struct snd_kcontrol *snd_soc_cnew(const struct snd_kcontrol_new *_template,
				  void *data, const char *long_name,
				  const char *prefix)
{
	struct snd_kcontrol_new template;
	struct snd_kcontrol *kcontrol;
	char *name = NULL;

	memcpy(&template, _template, sizeof(template));
	template.index = 0;

	if (!long_name)
		long_name = template.name;

	if (prefix) {
		name = kasprintf(GFP_KERNEL, "%s %s", prefix, long_name);
		if (!name)
			return NULL;

		template.name = name;
	} else {
		template.name = long_name;
	}

	kcontrol = snd_ctl_new1(&template, data);

	kfree(name);

	return kcontrol;
}
```

[`snd_ctl_new1()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L260) allocates the runtime [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and copies the template name straight into the element [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L72), the field [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) later matches against the UCM string:

```c
/* sound/core/control.c:260 (excerpt) */
	/* The 'numid' member is decided when calling snd_ctl_add(). */
	kctl->id.iface = ncontrol->iface;
	kctl->id.device = ncontrol->device;
	kctl->id.subdevice = ncontrol->subdevice;
	if (ncontrol->name) {
		strscpy(kctl->id.name, ncontrol->name, sizeof(kctl->id.name));
		if (strcmp(ncontrol->name, kctl->id.name) != 0)
			pr_warn("ALSA: Control name '%s' truncated to '%s'\n",
				ncontrol->name, kctl->id.name);
	}
	kctl->id.index = ncontrol->index;

	kctl->info = ncontrol->info;
	kctl->get = ncontrol->get;
	kctl->put = ncontrol->put;
	kctl->tlv.p = ncontrol->tlv.p;
```

The same Speaker Volume string travels down from the compiled template into the live control id.name and back up when a cset by that name resolves to the control, the prefix builder and the copy doing the two steps between:

```
    A control name becomes a kcontrol.id a UCM cset later matches
    ─────────────────────────────────────────────────────────────

    struct snd_kcontrol_new   (SOC_* template, compiled in)
    ┌─────────────────────────────┐
    │ .iface  MIXER               │
    │ .name   "Speaker Volume"    │
    └──────────────┬──────────────┘
                   │ snd_soc_cnew(): name = prefix + template name
                   │ snd_ctl_new1(): strscpy into id.name
                   ▼
    struct snd_kcontrol       (runtime, on card->controls)
    ┌─────────────────────────────┐
    │ id.iface  MIXER             │
    │ id.name   "Speaker Volume"  │
    │ get / put callbacks         │
    └──────────────▲──────────────┘
                   │ snd_ctl_find_id() matches id by name+iface
                   │
    UCM line:  cset "name='Speaker Volume' 80"
```

### The name prefix that keeps control names stable

A laptop card carries several codecs, and two codecs may each declare a `"Speaker Volume"`. To keep the names unique and predictable for a UCM profile, ASoC prepends a per-component prefix. A DAPM widget control routes through [`snd_soc_dapm_new_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3909):

```c
/* sound/soc/soc-dapm.c:3909 */
struct snd_soc_dapm_widget *
snd_soc_dapm_new_control(struct snd_soc_dapm_context *dapm,
			 const struct snd_soc_dapm_widget *widget)
{
	struct snd_soc_dapm_widget *w;

	snd_soc_dapm_mutex_lock(dapm);
	w = snd_soc_dapm_new_control_unlocked(dapm, widget);
	snd_soc_dapm_mutex_unlock(dapm);

	return w;
}
```

That reaches [`dapm_cnew_widget()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L355), which builds the widget name from the component prefix and the widget's own name, the prefix coming from the component's [`name_prefix`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207):

```c
/* sound/soc/soc-dapm.c:355 */
static inline struct snd_soc_dapm_widget *dapm_cnew_widget(
	const struct snd_soc_dapm_widget *_widget,
	const char *prefix)
{
	struct snd_soc_dapm_widget *w __free(kfree) = kmemdup(_widget,
							      sizeof(*_widget),
							      GFP_KERNEL);
	if (!w)
		return NULL;

	if (prefix)
		w->name = kasprintf(GFP_KERNEL, "%s %s", prefix, _widget->name);
	else
		w->name = kstrdup_const(_widget->name, GFP_KERNEL);
	...
}
```

The prefix is a field of [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207), set by the machine driver per codec through a [`struct snd_soc_codec_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L946):

```c
/* include/sound/soc-component.h:207 */
struct snd_soc_component {
	const char *name;
	const char *name_prefix;
	struct device *dev;
	struct snd_soc_card *card;
	...
};
```

A board that gives one amplifier the prefix `"Left"` and another `"Right"` produces controls named `"Left Speaker Volume"` and `"Right Speaker Volume"`, and the UCM profile for that card writes those exact names. The prefix lets one UCM profile address the right codec when several declare the same template name.

```
    name_prefix disambiguates one template name across two codecs
    ─────────────────────────────────────────────────────────────

    same template ".name = Speaker Volume" in both codec drivers

    codec_conf[0]             codec_conf[1]
    ┌─────────────────┐       ┌─────────────────┐
    │ dlc -> amp L    │       │ dlc -> amp R    │
    │ name_prefix     │       │ name_prefix     │
    │   "Left"        │       │   "Right"       │
    └────────┬────────┘       └────────┬────────┘
             │ snd_soc_cnew prepends the prefix
             ▼                         ▼
    ┌───────────────────────┐ ┌───────────────────────┐
    │ "Left Speaker Volume" │ │ "Right Speaker Volume"│
    └───────────────────────┘ └───────────────────────┘
             ▲                         ▲
             └─ UCM cset names the exact prefixed control
```

### The verb, device, and modifier structure over these surfaces

A UCM profile binds the surfaces above into a tree the manager walks at runtime. The verb is the card-wide use case; `"HiFi"` is the common verb, and a card may also offer `"Voice Call"` or `"Pro Audio"`. Loading a verb runs its EnableSequence, a list of `cset` writes that put the card into a known base routing, and it makes the verb's devices available. A device is one selectable endpoint, `"Speaker"`, `"Headphones"`, `"Headset Mic"`, or `"Mic"`, and enabling a device runs its own EnableSequence to route audio to that endpoint and names the PCM device to open. A modifier is an overlay on a device for a finer use, such as a low-latency or echo-reference capture path; enabling a modifier runs a further EnableSequence without replacing the device.

Mapping `"HiFi" -> "Speaker"` onto the kernel is therefore a sequence of [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204) calls on /dev/snd/controlC%d, each resolving a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) by name through [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) and running its [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L75) callback, followed by opening the pcmC%dD%d node the device named. Mapping `"HiFi" -> "Mic"` is the same with [`CapturePCM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1203) and a capture node. Mutual exclusion between `"Speaker"` and `"Headphones"` is expressed in the profile as a DisableSequence that the manager runs for the old device before the new one's EnableSequence, so the two never drive the same output at once. The kernel does not know about verbs, devices, or modifiers; it sees only the writes to the controls its drivers built and the opens of the PCM nodes its drivers named, and the whole UCM model is the userspace policy that orders those writes and opens by name.

### The DAPM routing-switch controls a sequence toggles

Many UCM `cset` writes do not set a volume; they flip a routing switch that powers up a path through the DAPM graph. Such a control is declared with [`SOC_DAPM_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L336) rather than [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), wiring the DAPM-aware get and put so a write also runs the power-management pass:

```c
/* include/sound/soc-dapm.h:336 */
#define SOC_DAPM_SINGLE(xname, reg, shift, max, invert) \
	SOC_SINGLE_EXT(xname, reg, shift, max, invert, \
		       snd_soc_dapm_get_volsw, snd_soc_dapm_put_volsw)
```

The mixer-input controls these declare are attached to a widget by [`dapm_new_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L1274), which matches each kcontrol name to a route into the widget so toggling the control connects or disconnects that path:

```c
/* sound/soc/soc-dapm.c:1274 */
static int dapm_new_mixer(struct snd_soc_dapm_widget *w)
{
	int i, ret;
	struct snd_soc_dapm_path *path;
	struct dapm_kcontrol_data *data;

	/* add kcontrol */
	for (i = 0; i < w->num_kcontrols; i++) {
		/* match name */
		snd_soc_dapm_widget_for_each_source_path(w, path) {
			/* mixer/mux paths name must match control name */
			if (path->name != (char *)w->kcontrol_news[i].name)
				continue;
			...
		}
	}

	return 0;
}
```

A UCM EnableSequence for `"Speaker"` typically writes both kinds. One is a routing switch like `"Speaker Switch"` that powers the DAPM path, and the other is a gain like `"Speaker Volume"` that sets the level. Because the routing switch runs the DAPM power pass on write, a single `cset` can bring up a chain of widgets and the codec hardware behind them, which is why a UCM device's EnableSequence is short even though it activates a whole signal path. The board's static routes, added with [`snd_soc_dapm_add_routes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3272), define which widgets the switch connects, and the UCM profile only has to name the switch.

```
    Two kinds of cset write in one EnableSequence
    ──────────────────────────────────────────────

    cset name            declared by      put callback         effect
    ┌──────────────────┬───────────────┬──────────────────┬───────────┐
    │ "Speaker Switch" │ SOC_DAPM_     │ snd_soc_dapm_    │ run DAPM  │
    │                  │   SINGLE      │   put_volsw      │ power pass│
    ├──────────────────┼───────────────┼──────────────────┼───────────┤
    │ "Speaker Volume" │ SOC_SINGLE    │ snd_soc_put_     │ set gain  │
    │                  │               │   volsw          │ only      │
    └──────────────────┴───────────────┴──────────────────┴───────────┘
      the switch put runs the power pass, so one cset brings up a whole
      widget chain; the volume put only writes the level register
```
