# PCM subdevices

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A subdevice is the third part of the address ALSA gives every PCM stream, below the card and the device. One [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) carries numbered PCM devices, each a [`struct snd_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L534), and within one device and one direction the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) container holds a fixed number of interchangeable subdevices. Each subdevice is one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), identified inside its direction by the [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) field and named `subdevice #%i`. The count is set once when the device is created, by the playback and capture counts passed to [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767), and stored in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517). A subdevice exists for the life of the card and becomes busy only while a process holds it open, tracked by [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) and the per-direction [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) counter. When a process opens the per-direction node, the core picks a free subdevice from the list, optionally steered to a specific one through the preferred-subdevice request a control client leaves with [`snd_ctl_get_preferred_subdevice()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158).

```
    ALSA addresses a stream by card, device, and subdevice
    ──────────────────────────────────────────────────────
    snd_card "card N"
    └─ snd_pcm "device D"
       ├─ snd_pcm_str [PLAYBACK]   substream_count 3
       │  ├─ subdevice 0   ref_count 0   free
       │  ├─ subdevice 1   ref_count 1   busy
       │  └─ subdevice 2   ref_count 0   free
       └─ snd_pcm_str [CAPTURE]    substream_count 1
          └─ subdevice 0   ref_count 0   free

    control query → snd_pcm_info
    ┌───────────────────────────────────────────────┐
    │ card N   device D   subdevice i               │
    │ subdevices_count 3    subdevices_avail 2      │
    └───────────────────────────────────────────────┘
```

## SUMMARY

A subdevice and a substream are two sides of one kernel object, [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464). The substream side is the open-able stream instance and its per-open runtime; the subdevice side is how that same instance is addressed by [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) within a device and direction and selected from the free instances at open. The two sides draw on different fields of that one object, the subdevice side on its numbering and availability and the substream side on its runtime, linking, and locking.

The subdevice count is established at device-creation time and never changes afterward. [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) takes a `playback_count` and a `capture_count`, and [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) runs once per non-empty direction to allocate that many [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) instances, store the total in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), thread them onto the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) list through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484), set each [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) to its index, and write the `subdevice #%i` string into [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L469). A subdevice with a zero [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is free, the state [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) reports.

A process never names a subdevice in the open path beyond the device node it opens. [`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) calls [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875), which reads the caller's preferred subdevice with [`snd_ctl_get_preferred_subdevice()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158), walks the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list for the first free instance whose [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) matches that preference (or any free instance when the preference is -1), and increments [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518). A control client sets the preference for its own process with the [`SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1218) command, stored in [`preferred_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109). Userspace enumerates and inspects subdevices through the control device before opening one, where [`snd_pcm_control_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L83) answers [`SNDRV_CTL_IOCTL_PCM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1217) by filling a [`struct snd_pcm_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) through [`snd_pcm_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L221), reporting [`subdevices_count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) and the live [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339).

How many subdevices a device carries depends on the driver. A classic in-tree driver that programs the audio DMA engines, such as the HD-audio controller through [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692), passes the hardware [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L141) count and can expose several subdevices on one device. On an x86-64 ACPI machine an ASoC card instead passes a 0-or-1 direction flag from [`soc_get_playback_capture()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2799) and gives each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) its own device with a single subdevice per direction.

## SPECIFICATIONS

The subdevice is a Linux kernel software construct and has no standalone hardware specification. Its userspace surface is the ALSA control and PCM ABI in [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h): the [`struct snd_pcm_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) record returned for one subdevice, the [`SNDRV_CTL_IOCTL_PCM_NEXT_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1216), [`SNDRV_CTL_IOCTL_PCM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1217), and [`SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1218) control commands, and the `pcmC%iD%i%c` device-node naming whose middle index is the device and whose subdevice is selected at open. The audio transport beneath the subdevice (HD Audio, USB Audio, or a SoC link) carries its own specification.

## LINUX KERNEL

### Subdevice objects and addressing (pcm.h, asound.h)

- [`'\<struct snd_pcm_str\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513): the per-direction container; holds [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), the running [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) counter, and the head [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) of the subdevice list
- [`'\<struct snd_pcm_substream\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464): one subdevice instance; its [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) is the subdevice index within the direction, its [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L469) the `subdevice #%i` string, and its [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) the open count
- [`'\<SUBSTREAM_BUSY\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510): the free-or-busy test on a subdevice, true when [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is greater than zero
- [`'\<struct snd_pcm_info\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339): the userspace view of one subdevice; carries [`device`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339), [`subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339), [`subdevices_count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339), [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339), and the [`subname`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) copied from the substream name
- [`'\<struct snd_ctl_file\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105): the open control descriptor holding [`preferred_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109), the per-process bias indexed by [`SND_CTL_SUBDEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L100)

### Subdevice count and naming (sound/core/pcm.c)

- [`'\<snd_pcm_new\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767): creates one device; its `playback_count` and `capture_count` set the per-direction subdevice counts
- [`'\<snd_pcm_new_stream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627): allocates [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) subdevices for one direction, numbers each in [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468), and names each `subdevice #%i`
- [`'\<snd_pcm_substream_proc_init\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L547): creates the `sub%i` procfs node per subdevice under the per-direction directory

### Open-time selection (sound/core/pcm.c, pcm_native.c, control.c)

- [`'\<snd_pcm_open_substream\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767): the open entry that attaches a subdevice and then runs the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L56) op
- [`'\<snd_pcm_attach_substream\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875): scans the subdevice list for a free one matching the preference, allocates the [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1, and bumps [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518)
- [`'\<snd_ctl_get_preferred_subdevice\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158): returns the calling process's [`preferred_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) for the requested type, or -1 when none is set

### Control-device enumeration and info (sound/core/pcm.c, pcm_native.c)

- [`'\<snd_pcm_control_ioctl\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L83): the control-device handler for [`SNDRV_CTL_IOCTL_PCM_NEXT_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1216), [`SNDRV_CTL_IOCTL_PCM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1217), and [`SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1218)
- [`'\<snd_pcm_get\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L38) / [`'\<snd_pcm_next\>':'sound/core/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L49): look up a device by index and find the next device index on the card
- [`'\<snd_pcm_info\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L221): fills a [`struct snd_pcm_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) for one subdevice, setting [`subdevices_count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) from [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) and [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) from the unopened remainder
- [`'\<snd_pcm_info_user\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L242): runs [`snd_pcm_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L221) and copies the record back to userspace

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the PCM Interface chapter describes that a PCM stream consists of one or more substreams, that a free substream is assigned at each open, and that the middle layer performs the assignment
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated PCM Core API reference covering device creation with the playback and capture counts and the subdevice attach path
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the per-subdevice `sub%i` procfs entries created under each per-direction node

## OTHER SOURCES

- [ALSA project library documentation: PCM (digital audio) interface](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [aplay and arecord manual page](https://man7.org/linux/man-pages/man1/aplay.1.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A subdevice is addressed by the triple (card, device, subdevice). The card and device are fixed by the device node a process opens, and the subdevice is selected from the free instances at open time, either by the kernel or by a preference a control client supplies for its own process. The control device offers the queries that enumerate devices and report how many subdevices a direction has and how many are free, and the table below lists the entry points that create, select, and inspect subdevices.

| operation | kernel entry point | subdevice effect |
|-----------|--------------------|------------------|
| device creation | [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) | allocates [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) subdevices, each [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) = 0 |
| set preference | [`SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1218) | writes [`preferred_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) for the calling process |
| `open("...p")` | [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) | binds one free subdevice, honoring the preference, [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) = 1, [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518)++ |
| enumerate | [`SNDRV_CTL_IOCTL_PCM_NEXT_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1216) | returns the next device index through [`snd_pcm_next()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L49) |
| inspect | [`SNDRV_CTL_IOCTL_PCM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1217) | fills [`subdevices_count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) and [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) via [`snd_pcm_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L221) |
| `close()` | [`snd_pcm_detach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L980) | frees the runtime, [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518)-- |

## DETAILS

### A subdevice and a substream are the same object

A subdevice and a substream are two names for one kernel object, the [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) created once per device and direction. Code that opens, runs, links, and tears down the stream works with it as a substream, through its per-open [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), its driver [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L476), and its locking and linking state. Userspace that enumerates, addresses, and selects a stream works with the same object as a subdevice, through its [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) within a [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) direction and the availability the core tracks for it. The [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) field gives the subdevice its identity, and [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) marks the instance busy so a later open skips it. The subdevice side is the addressing, counting, and selection that act on that one object; the open lifecycle and the runtime it carries are the substream side of the same instance. The two sides draw on different sets of fields. Addressing, counting, and selection use the [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468), the [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517) and [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) counters, and the control-device queries, while opening, running, and linking a stream use the [`runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L478), the grouping fields, and the per-stream lock.

```
    One object, two names: which fields each name uses
    ─────────────────────────────────────────────────────
                  struct snd_pcm_substream

    subdevice side  (addressed, counted, selected)
    ┌──────────────────────────────────────────────┐
    │ number              subdevice identity       │
    │ ref_count → SUBSTREAM_BUSY    free-or-busy   │
    │ substream_count     subdevices total         │
    │ substream_opened    subdevices in use        │
    └──────────────────────────────────────────────┘

    substream side  (opened and run)
    ┌──────────────────────────────────────────────┐
    │ runtime             per-open state           │
    │ ops                 driver callbacks         │
    │ group / self_group  linking                  │
    │ self_group.lock     per-stream lock          │
    └──────────────────────────────────────────────┘
```

### A subdevice is one substream within a device and direction

The subdevice list is held by the per-direction [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513). It records how many subdevices the direction has in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), how many are open in [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518), and the head of the singly linked list in [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519):

```c
/* include/sound/pcm.h:513 */
struct snd_pcm_str {
	int stream;				/* stream (direction) */
	struct snd_pcm *pcm;
	/* -- substreams -- */
	unsigned int substream_count;
	unsigned int substream_opened;
	struct snd_pcm_substream *substream;
	...
};
```

Each subdevice is one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464). The [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) field is the subdevice index within the direction, the value userspace passes as the subdevice part of the address, and [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) is the open count that marks the subdevice busy:

```c
/* include/sound/pcm.h:464 */
struct snd_pcm_substream {
	struct snd_pcm *pcm;
	struct snd_pcm_str *pstr;
	void *private_data;		/* copied from pcm->private_data */
	int number;
	char name[32];			/* substream name */
	int stream;			/* stream (direction) */
	...
	struct snd_pcm_substream *next;
	...
	int ref_count;
	...
};
```

The [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) and [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L469) are the two pieces of identity a subdevice keeps for its whole life, and the free-or-busy state is derived from [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) by the [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) macro:

```c
/* include/sound/pcm.h:510 */
#define SUBSTREAM_BUSY(substream) ((substream)->ref_count > 0)
```

That free-or-busy flag rides on each subdevice the container chains through its next pointers, the list head reaching subdevice 0, then 1, then 2:

```
    snd_pcm_str threads its subdevices on a next list
    ───────────────────────────────────────────────────
    struct snd_pcm_str  [one direction]
    ┌────────────────────────┐
    │ substream_count        │
    │ substream_opened       │
    │ substream  (list head) │
    └───────────┬────────────┘
                ▼   next       next
       subdevice #0 ────▶ #1 ────▶ #2 ────▶ NULL
       ┌──────────────┐
       │ number = 0   │
       │ name "#0"    │
       │ ref_count    │
       └──────────────┘
```

### The subdevice count is fixed at device creation

A driver chooses the number of subdevices per direction when it creates the device. [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) takes a `playback_count` and a `capture_count`, documented in its own header comment as the number of substreams for each direction:

```c
/* sound/core/pcm.c:767 */
int snd_pcm_new(struct snd_card *card, const char *id, int device,
		int playback_count, int capture_count, struct snd_pcm **rpcm)
{
	return _snd_pcm_new(card, id, device, playback_count, capture_count,
			false, rpcm);
}
```

[`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) runs once for each non-empty direction. It records the count in [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), then allocates one [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464) per subdevice, sets each [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) to its loop index, names it `subdevice #%i`, and threads it onto the [`struct snd_pcm_str`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L513) list through [`next`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L484):

```c
/* sound/core/pcm.c:627 */
int snd_pcm_new_stream(struct snd_pcm *pcm, int stream, int substream_count)
{
	int idx, err;
	struct snd_pcm_str *pstr = &pcm->streams[stream];
	struct snd_pcm_substream *substream, *prev;
	...
	pstr->substream_count = substream_count;
	if (!substream_count)
		return 0;
	...
	for (idx = 0, prev = NULL; idx < substream_count; idx++) {
		substream = kzalloc(sizeof(*substream), GFP_KERNEL);
		...
		substream->pcm = pcm;
		substream->pstr = pstr;
		substream->number = idx;
		substream->stream = stream;
		sprintf(substream->name, "subdevice #%i", idx);
		...
	}
	return 0;
}
```

After this runs, the number of subdevices in the direction is fixed for the life of the card. The list is never grown or shrunk; an open binds one of the existing subdevices and a close releases it.

### Open selects a free subdevice, honoring the preferred one

[`snd_pcm_open_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L2767) is the open entry. It first calls [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) to bind a subdevice, and only then runs the driver [`open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L56) op on it:

```c
/* sound/core/pcm_native.c:2767 */
int snd_pcm_open_substream(struct snd_pcm *pcm, int stream,
			   struct file *file,
			   struct snd_pcm_substream **rsubstream)
{
	struct snd_pcm_substream *substream;
	int err;

	err = snd_pcm_attach_substream(pcm, stream, file, &substream);
	if (err < 0)
		return err;
	...
	err = substream->ops->open(substream);
	if (err < 0)
		goto error;
	...
}
```

[`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) reads the caller's preference with [`snd_ctl_get_preferred_subdevice()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158), then walks the [`substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L519) list for the first instance that is not [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) and whose [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) matches the preference, accepting any free subdevice when the preference is -1. It returns `-EAGAIN` when none is free:

```c
/* sound/core/pcm.c:875 */
int snd_pcm_attach_substream(struct snd_pcm *pcm, int stream,
			     struct file *file,
			     struct snd_pcm_substream **rsubstream)
{
	struct snd_pcm_str * pstr;
	struct snd_pcm_substream *substream;
	...
	int prefer_subdevice;
	...
	pstr = &pcm->streams[stream];
	if (pstr->substream == NULL || pstr->substream_count == 0)
		return -ENODEV;

	card = pcm->card;
	prefer_subdevice = snd_ctl_get_preferred_subdevice(card, SND_CTL_SUBDEV_PCM);
	...
	for (substream = pstr->substream; substream; substream = substream->next) {
		if (!SUBSTREAM_BUSY(substream) &&
		    (prefer_subdevice == -1 ||
		     substream->number == prefer_subdevice))
			break;
	}
	if (substream == NULL)
		return -EAGAIN;
	...
	substream->ref_count = 1;
	substream->f_flags = file->f_flags;
	substream->pid = get_pid(task_pid(current));
	pstr->substream_opened++;
	*rsubstream = substream;
	...
	return 0;
}
```

Binding the subdevice sets [`ref_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L490) to 1, which makes [`SUBSTREAM_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L510) true for it, and increments the per-direction [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518). The next open scanning the list skips this subdevice and takes the next free one.

### A control client biases the next open with PREFER_SUBDEVICE

The preference is per-process state held on a control descriptor rather than on the PCM device. A client opens the card's control node, then issues [`SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1218), and [`snd_pcm_control_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L83) stores the value in the descriptor's [`preferred_subdevice`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) array at the [`SND_CTL_SUBDEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L100) index:

```c
/* sound/core/pcm.c:137 */
	case SNDRV_CTL_IOCTL_PCM_PREFER_SUBDEVICE:
		{
			int val;

			if (get_user(val, (int __user *)arg))
				return -EFAULT;
			control->preferred_subdevice[SND_CTL_SUBDEV_PCM] = val;
			return 0;
		}
```

The array is a field of [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105), one slot per subdevice type, with [`SND_CTL_SUBDEV_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L100) selecting the PCM slot:

```c
/* include/sound/control.h:99 */
enum {
	SND_CTL_SUBDEV_PCM,
	SND_CTL_SUBDEV_RAWMIDI,
	SND_CTL_SUBDEV_ITEMS,
};

struct snd_ctl_file {
	struct list_head list;		/* list of all control files */
	struct snd_card *card;
	struct pid *pid;
	int preferred_subdevice[SND_CTL_SUBDEV_ITEMS];
	...
};
```

At the next PCM open, [`snd_ctl_get_preferred_subdevice()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2158) recovers that value. It walks the card's open control files for one whose [`pid`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L108) is the current process and returns the stored subdevice, or -1 when the process set none:

```c
/* sound/core/control.c:2158 */
int snd_ctl_get_preferred_subdevice(struct snd_card *card, int type)
{
	struct snd_ctl_file *kctl;
	int subdevice = -1;

	guard(read_lock_irqsave)(&card->controls_rwlock);
	list_for_each_entry(kctl, &card->ctl_files, list) {
		if (kctl->pid == task_pid(current)) {
			subdevice = kctl->preferred_subdevice[type];
			if (subdevice != -1)
				break;
		}
	}
	return subdevice;
}
```

Matching on the current process is what ties the preference set on the control descriptor to the open performed on the PCM node, so a process that wants a specific subdevice sets the preference on its own control handle and then opens the device.

```
    The preference is written on one fd, read at open on another
    ──────────────────────────────────────────────────────────────
    earlier: ioctl on the control fd        later: open on the PCM fd

    struct snd_ctl_file                     snd_pcm_attach_substream
    ┌──────────────────────────────┐        ┌──────────────────────────┐
    │ pid                          │        │ snd_ctl_get_preferred_   │
    │ preferred_subdevice[         │        │   subdevice(SUBDEV_PCM)  │
    │   SND_CTL_SUBDEV_PCM ] = val │        │ walk free list for       │
    └──────────────┬───────────────┘        │   number == preference   │
                   │                        └────────────▲─────────────┘
                   └─── matched by pid == task_pid() ────┘
```

### snd_pcm_info reports the subdevice count and availability

Userspace inspects subdevices through the control device before opening one. [`snd_pcm_control_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L83) handles [`SNDRV_CTL_IOCTL_PCM_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1217) by reading the requested device, stream, and subdevice from the [`struct snd_pcm_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339), validating the subdevice index against [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), and walking the list to the subdevice whose [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468) matches:

```c
/* sound/core/pcm.c:100 */
	case SNDRV_CTL_IOCTL_PCM_INFO:
		{
			...
			pstr = &pcm->streams[stream];
			if (pstr->substream_count == 0)
				return -ENOENT;
			if (subdevice >= pstr->substream_count)
				return -ENXIO;
			for (substream = pstr->substream; substream;
			     substream = substream->next)
				if (substream->number == (int)subdevice)
					break;
			if (substream == NULL)
				return -ENXIO;
			guard(mutex)(&pcm->open_mutex);
			return snd_pcm_info_user(substream, info);
		}
```

[`snd_pcm_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L221) then fills the record. It copies the three address parts (the card number, the device, and the subdevice taken from [`number`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L468)), sets [`subdevices_count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) to the direction's [`substream_count`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L517), and computes [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) as the count minus [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518):

```c
/* sound/core/pcm_native.c:221 */
int snd_pcm_info(struct snd_pcm_substream *substream, struct snd_pcm_info *info)
{
	struct snd_pcm *pcm = substream->pcm;
	struct snd_pcm_str *pstr = substream->pstr;

	memset(info, 0, sizeof(*info));
	info->card = pcm->card->number;
	info->device = pcm->device;
	info->stream = substream->stream;
	info->subdevice = substream->number;
	strscpy(info->id, pcm->id, sizeof(info->id));
	strscpy(info->name, pcm->name, sizeof(info->name));
	info->dev_class = pcm->dev_class;
	info->dev_subclass = pcm->dev_subclass;
	info->subdevices_count = pstr->substream_count;
	info->subdevices_avail = pstr->substream_count - pstr->substream_opened;
	strscpy(info->subname, substream->name, sizeof(info->subname));

	return 0;
}
```

The [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) value is live, computed from the current [`substream_opened`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L518) counter each time the query runs, so a client can read how many subdevices remain free before it attempts an open. The [`subname`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) it returns is the `subdevice #%i` string [`snd_pcm_new_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L627) wrote at creation. The [`struct snd_pcm_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) layout the call fills is the userspace record:

```c
/* include/uapi/sound/asound.h:339 */
struct snd_pcm_info {
	unsigned int device;		/* RO/WR (control): device number */
	unsigned int subdevice;		/* RO/WR (control): subdevice number */
	int stream;			/* RO/WR (control): stream direction */
	int card;			/* R: card number */
	unsigned char id[64];		/* ID (user selectable) */
	unsigned char name[80];		/* name of this device */
	unsigned char subname[32];	/* subdevice name */
	int dev_class;			/* SNDRV_PCM_CLASS_* */
	int dev_subclass;		/* SNDRV_PCM_SUBCLASS_* */
	unsigned int subdevices_count;
	unsigned int subdevices_avail;
	unsigned char pad1[16];		/* was: hardware synchronization ID */
	unsigned char reserved[64];	/* reserved for future... */
};
```

Each field of that record draws from one kernel source, the card and device numbers, the subdevice taken from number, the count, the count less the opened total for the available figure, and the subdevice name:

```
    Where snd_pcm_info fills each field from
    ──────────────────────────────────────────────────────────
    kernel source                        struct snd_pcm_info
    ┌──────────────────────────┐         ┌──────────────────────┐
    │ pcm->card->number        │ ──────▶ │ card                 │
    │ pcm->device              │ ──────▶ │ device               │
    │ substream->number        │ ──────▶ │ subdevice            │
    │ pstr->substream_count    │ ──────▶ │ subdevices_count     │
    │ substream_count          │         │                      │
    │   − substream_opened     │ ──────▶ │ subdevices_avail     │
    │ substream->name          │ ──────▶ │ subname              │
    └──────────────────────────┘         └──────────────────────┘
```

### ASoC creates one subdevice per direction, where a classic driver passes a count

On an x86-64 ACPI machine the PCM devices come from the ASoC layer, and ASoC fixes the subdevice count at one per active direction. [`soc_get_playback_capture()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2799) reduces the link's capabilities for one direction to a single flag, `has_playback` or `has_capture`, each 0 or 1, and returns the two flags as the playback and capture counts:

```c
/* sound/soc/soc-pcm.c:2799 */
static int soc_get_playback_capture(struct snd_soc_pcm_runtime *rtd,
				    int *playback, int *capture)
{
	...
	int has_playback = 0;
	int has_capture  = 0;
	...
	*playback = has_playback;
	*capture  = has_capture;

	return 0;
}
```

[`soc_create_pcm()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-pcm.c#L2867) passes those two flags to [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767) as the per-direction subdevice counts, with the per-link [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1176) of the [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) as the device index:

```c
/* sound/soc/soc-pcm.c:2896 */
		ret = snd_pcm_new(rtd->card->snd_card, new_name, rtd->id, playback,
			capture, pcm);
```

Because each count is the 0-or-1 flag, an ASoC PCM holds a single subdevice per direction, always numbered 0, and ASoC gives each [`struct snd_soc_dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L702) its own device index instead of stacking subdevices on a shared device. The free-subdevice scan in [`snd_pcm_attach_substream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L875) on such a device has one candidate, so the preferred-subdevice steering and a [`subdevices_avail`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L339) above 1 stay dormant on an ASoC card.

A driver that programs the audio DMA engines directly can pass a count above 1. The HD-audio controller is one such driver. [`snd_hda_attach_pcm_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/common/controller.c#L692) passes the per-direction [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L141) count of the codec's [`struct hda_pcm`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L164) straight into [`snd_pcm_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm.c#L767):

```c
/* sound/hda/common/controller.c:711 */
	err = snd_pcm_new(chip->card, cpcm->name, pcm_dev,
			  cpcm->stream[SNDRV_PCM_STREAM_PLAYBACK].substreams,
			  cpcm->stream[SNDRV_PCM_STREAM_CAPTURE].substreams,
			  &pcm);
```

The [`substreams`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hda_codec.h#L141) value comes from the codec parser. When a codec exposes several ADCs, [`snd_hda_gen_build_pcms()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/codecs/generic.c#L5734) sets the alternate analog capture stream's count to one per extra converter:

```c
/* sound/hda/codecs/generic.c:5825 */
		if (have_multi_adcs) {
			setup_pcm_stream(&info->stream[SNDRV_PCM_STREAM_CAPTURE],
					 &pcm_analog_alt_capture,
					 spec->stream_analog_alt_capture,
					 spec->adc_nids[1]);
			info->stream[SNDRV_PCM_STREAM_CAPTURE].substreams =
				spec->num_adc_nids - 1;
		} else {
```

With `have_multi_adcs` true, the capture direction of that PCM carries `spec->num_adc_nids - 1` subdevices, so several processes capture from different converters at once by binding different subdevices of the same device. That is the case the free-subdevice scan and the preferred-subdevice request serve, and it is the path an ASoC card replaces with one device per DAI link.

```
    What each driver passes as the snd_pcm_new() per-direction count
    ──────────────────────────────────────────────────────────────────
    ASoC card                            classic DMA driver (HD-audio)
    ┌────────────────────────────┐       ┌────────────────────────────┐
    │ soc_get_playback_capture() │       │ snd_hda_attach_pcm_stream()│
    │ has_playback / has_capture │       │ cpcm->stream[dir].         │
    │   each 0 or 1              │       │   substreams  (may be > 1) │
    └──────────────┬─────────────┘       └──────────────┬─────────────┘
                   ▼                                    ▼
            snd_pcm_new(playback_count, capture_count)
                   │                                    │
                   ▼                                    ▼
        one subdevice per direction          several subdevices per
        (always number 0)                    direction (numbers 0..N)
```
